#!/usr/bin/env python3
"""recompute.py — reviewer 的獨立重算（不 import analyze.py 或 collect_lvr.py）。

用法：
  python scripts/recompute.py --run <run> --stage data   [--cache data/lvr-cache]   # V1–V7、V12、V13
  python scripts/recompute.py --run <run> --stage report                            # V8–V11（final_report.md 寫好後）
兩個階段都寫入同一份 05_review_log.json；任一項 FAIL → verdict = FAIL。
報告階段若前一次 FAIL，再跑時自動記錄 report_retry、report_first_issues（第一次的問題原文）與
report_first_issues_summary（不含原始數字的摘要，給報告第 8 節引用）。
V8 的可追溯來源包含本次資料階段檢核（V1–V7、V12、V13）的 expected／recomputed 值。
"""
import argparse, csv, hashlib, io, json, random, re, sys, zipfile
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parent.parent
EN_ROW2 = "The villages and towns urban district"


def rcsv(p):
    p = Path(p)
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def roc(s):
    s = str(s or "").strip().zfill(7)
    if not s.isdigit():
        return ""
    y, m, d = int(s[:3]) + 1911, int(s[3:5]), int(s[5:7])
    try:
        import datetime
        return datetime.date(y, m, d).isoformat()
    except ValueError:
        return ""


def raw_rows(manifest, cache):
    """依 manifest 的 data_mode 重新讀原始資料：官方 zip 快取或 sample-data。回傳 {(season, code): [row]}。"""
    out = {}
    codes = [c["city_code"] for c in manifest["county_files"]]
    if manifest["data_mode"] == "online":
        for d in manifest["downloads"]:
            z = Path(cache) / f"{d['season']}.zip"
            data = z.read_bytes()
            if hashlib.sha256(data).hexdigest() != d["sha256"]:
                raise ValueError(f"{z.name} 的 SHA-256 與 manifest 不符")
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for c in codes:
                    rows = list(csv.reader(io.StringIO(zf.read(f"{c}_lvr_land_c.csv").decode("utf-8-sig"))))
                    head, body = rows[0], rows[1:]
                    if body and body[0][0] == EN_ROW2:
                        body = body[1:]
                    out[(d["season"], c)] = [dict(zip(head, r)) for r in body]
    else:
        for r in rcsv(SKILL / "sample-data/lvr_rent_sample_areas.csv"):
            if r["city_code"] in codes:
                out.setdefault((r["season"], r["city_code"]), []).append(r)
    return out


def check(log, cid, target, expected, recomputed, ok, tol, note=""):
    log["checks"].append({"check_id": cid, "target": target, "expected": expected, "recomputed": recomputed,
                          "tolerance": tol, "status": "PASS" if ok else "FAIL", "note": note})


def stage_data(run, cache, log):
    man = json.loads((run / "01_collect_manifest.json").read_text(encoding="utf-8"))
    area = json.loads((run / "01_area.json").read_text(encoding="utf-8"))
    counties = {r["city_code"]: r["city"] for r in rcsv(SKILL / "references/county-codes.csv")}
    col = rcsv(run / "01_collected.csv")
    raw = raw_rows(man, cache)
    keys = {t["area_key"] for t in area["targets"]}
    # V1 筆數與地區
    for (s, c), rows in sorted(raw.items()):
        for k in keys:
            if k.split("|")[0] != counties.get(c):
                continue
            n_raw = sum(1 for r in rows if f"{counties[c]}|{r['鄉鎮市區']}" == k)
            n_man = man["row_counts"].get(s, {}).get(k, 0)
            check(log, "V1", f"{s} {k}", n_man, n_raw, n_raw == n_man, "0")
    ok_src = all(t.get("area_source") in ("user_explicit", "user_confirmed", "school_lookup", "address_parse") for t in area["targets"])
    check(log, "V1", "area_source", "允許值", [t.get("area_source") for t in area["targets"]], ok_src, "—")
    ok_code = all(counties.get(t["city_code"]) == t["city"] for t in area["targets"])
    check(log, "V1", "city_code", "與 county-codes.csv 一致", [t["city_code"] for t in area["targets"]], ok_code, "—")
    # V2 單位換算抽查（seed 42、5 筆）
    by_id = {(s, r["編號"]): r for (s, c), rows in raw.items() for r in rows}
    sample = random.Random(42).sample(col, min(5, len(col)))
    log["spot_sample_ids"] = [r["record_id"] for r in sample]
    for r in sample:
        src = by_id.get((r["season"], r["record_id"]))
        if not src:
            check(log, "V2", r["record_id"], "原始列", "找不到", False, "—"); continue
        ping = round(((fnum(src["建物總面積平方公尺"]) or 0) - (fnum(src["車位面積平方公尺"]) or 0)) * 0.3025, 2)
        rpp = round(((fnum(src["總額元"]) or 0) - (fnum(src["車位總額元"]) or 0)) / ping, 1) if ping > 0 else ""
        ok = abs(ping - float(r["area_ping"])) <= 0.01 and roc(src["租賃年月日"]) == r["rent_date"] and \
            (rpp == "" and r["rent_per_ping"] == "" or rpp != "" and abs(rpp - float(r["rent_per_ping"])) <= 0.1)
        check(log, "V2", r["record_id"], {"area_ping": r["area_ping"], "rent_date": r["rent_date"], "rpp": r["rent_per_ping"]},
              {"area_ping": ping, "rent_date": roc(src["租賃年月日"]), "rpp": rpp}, ok, "坪 ±0.01；日期相同")
    # V3 官方單價對帳
    tot = good = 0
    for (s, c), rows in raw.items():
        for r in rows:
            if f"{counties[c]}|{r['鄉鎮市區']}" not in keys or "房" not in r["交易標的"] and r["交易標的"] != "建物":
                continue
            up = fnum(r["單價元平方公尺"]); a = fnum(r["建物總面積平方公尺"]) or 0; pa = fnum(r["車位面積平方公尺"]) or 0
            t = fnum(r["總額元"]) or 0; pt = fnum(r["車位總額元"]) or 0
            if not up or a <= 0:
                continue
            tot += 1
            cands = [t / a] + ([(t - pt) / (a - pa)] if a - pa > 0 else [])
            if any(abs(up - x) <= 2 or abs(up - x) <= 0.02 * x for x in cands):
                good += 1
    check(log, "V3", "目標區房屋類", "全部可對帳", f"{good}/{tot}", tot > 0 and good / tot >= 0.99, "±2 元或 ±2%（容許 1% 例外並列出）")
    # V4 分組統計（同一分位數方法獨立重算）
    inc = rcsv(run / "03_inclusion_log.csv")
    ms = rcsv(run / "03_market_stats.csv")
    okset = {(r["record_id"], r["season"]) for r in inc if r["included"] == "True"}
    for m in ms:
        if m["area_level"] != "district" or not m.get("rpp_median"):
            continue
        groups = ("student_suite", "student_room") if m["rent_type_group"] == "student_all" else (m["rent_type_group"],)
        vals = [float(r["rent_per_ping"]) for r in col if (r["record_id"], r["season"]) in okset
                and r["area_key"] == f"{m['city']}|{m['district']}" and r["rent_type_group"] in groups
                and (m["include_social_housing"] == "True" or r["is_social_housing"] != "True")]
        if not vals:
            check(log, "V4", m["group_key"], m["n"], 0, False, "0"); continue
        rec = {"n": len(vals), "median": round(float(np.percentile(vals, 50)), 1),
               "q1": round(float(np.percentile(vals, 25)), 1), "q3": round(float(np.percentile(vals, 75)), 1)}
        exp = {"n": int(m["n"]), "median": float(m["rpp_median"]), "q1": float(m["rpp_q1"]), "q3": float(m["rpp_q3"])}
        check(log, "V4", f"{m['group_key']} 社宅={m['include_social_housing']}", exp, rec, rec == exp, "0")
    # V5 真實總成本
    P = {k: v["value"] for k, v in json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8")).items() if isinstance(v, dict)}
    cands = {r["listing_id"]: r for r in rcsv(run / "01_candidates.csv")}
    cb = rcsv(run / "03_cost_breakdown.csv")
    for r in cb:
        c = cands[r["listing_id"]]
        total = int(float(c["rent_monthly"]))
        for k in ("mgmt", "water", "gas", "internet"):
            if c[f"{k}_status"] == "stated":
                total += int(round(float(c[f"{k}_fee"])))
        if c["elec_status"] == "per_kwh":
            total += int(round(float(c["elec_price_per_kwh"]) * P["kwh_per_month"]))
        if c["commute_minutes_oneway"]:
            total += int(round(2 * float(c["commute_minutes_oneway"]) * P["school_days_per_month"] / 60 * P["hourly_value"]))
            if c.get("commute_fare_per_trip"):
                total += int(round(2 * float(c["commute_fare_per_trip"]) * P["school_days_per_month"]))
        exp = int(float(r["true_monthly_cost_known"]))
        check(log, "V5", r["listing_id"], exp, total, abs(exp - total) <= 1, "±1 元")
    # V6 排序
    rk = rcsv(run / "03_ranking.csv")
    if rk:
        costs = [int(float(x["true_monthly_cost_known"])) for x in rk]
        check(log, "V6", "03_ranking.csv", "依已知項目合計遞增", costs, costs == sorted(costs), "完全一致")
    # V7 不刪資料
    summ = json.loads((run / "02_factcheck_summary.json").read_text(encoding="utf-8"))
    n_inc = sum(r["included"] == "True" for r in inc); n_exc = len(inc) - n_inc
    check(log, "V7", "01 筆數 = 納入 + 排除；rows_deleted = 0", len(col), f"{n_inc}+{n_exc}; rows_deleted={summ['rows_deleted']}",
          len(col) == len(inc) and summ["rows_deleted"] == 0, "0")
    # V12 路由一致
    sig = json.loads((run / "03_signals.json").read_text(encoding="utf-8"))["signals"] if (run / "03_signals.json").exists() else []
    has_risk = (run / "04_risk_report.json").exists()
    check(log, "V12", "有 R 訊號 ⇔ 04_risk_report.json", bool(sig), has_risk, bool(sig) == has_risk, "一致")
    # V13 刊登租金不得混入行情
    ids = {(r["record_id"], r["season"]) for r in col}
    leak = [r["record_id"] for r in inc if (r["record_id"], r["season"]) not in ids]
    asking_in_ms = [m["group_key"] for m in ms if "591" in json.dumps(m, ensure_ascii=False)]
    check(log, "V13", "03_market_stats 只含實價登錄", 0, len(leak) + len(asking_in_ms), not leak and not asking_in_ms, "0")


DATA_CHECKS = ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V12", "V13")


def first_issue_summary(issues):
    """把第一次報告檢核的問題改寫成不含原始數字的摘要，給 final_report.md 第 8 節引用。
    例：「V8 final_report.md 的數字：無法追溯：4446、4446、3588」→「V8 final_report.md 的數字：3 個數字無法追溯」。"""
    out = []
    for s in issues:
        m = re.match(r"(.*?)：無法追溯：(.*)$", s)
        if m:
            out.append(f"{m.group(1)}：{len([x for x in re.split(r'[、,，]', m.group(2)) if x.strip()])} 個數字無法追溯")
        else:
            out.append(re.sub(r"\d+(?:\.\d+)?", "#", s))
    return out


def stage_report(run, log):
    rep_full = (run / "final_report.md").read_text(encoding="utf-8")
    # 不檢查：run_id、程式碼片段、連結與圖片路徑、檢核代號（V1–V13、R1–R7、CR-xx、E1–E23）
    rep = rep_full.replace(run.name, "")
    # 第 8 節原文抄錄的第一次問題（report_first_issues）是審查紀錄，不是報告主張，不納入 V8
    for s in log.get("report_first_issues", []):
        rep = rep.replace(s, " ")
    rep = re.sub(r"`[^`]*`|\]\([^)]*\)|\b(V|R|E|CR-|RT)\d+\b", " ", rep)
    # V8 數字可追溯：報告中 ≥3 位數的金額與百分比要能在 03_*.csv／03_signals.json／參數中找到
    pool = set()

    def add(text):
        for tok in re.findall(r"-?\d+(?:\.\d+)?", text):
            v = float(tok); pool.update({v, round(v), round(v, 1), abs(v)})

    # 05_review_log.json 不整份納入：它的 issues／note／report_first_issues 記錄了上一次 V8 的「無法追溯」數字，
    # 納入會讓重跑自我通過。只納入本次資料階段檢核（V1–V7、V12、V13）的 expected／recomputed 值，
    # 例如 V3 對帳筆數「4446/4446」、V7「3588+912」——這些是本次 run 自己重算出來的數字，第 8 節可以引用。
    srcs = [p for p in run.glob("0[0-5]_*.json") if p.name != "05_review_log.json"] + list(run.glob("03_*.csv")) + [run / "01_candidates.csv", run / "591_sources.json",
            SKILL / "references/cost-params.json"]
    for p in srcs:
        if p.exists():
            add(p.read_text(encoding="utf-8-sig"))
    for c in log.get("checks", []):
        if c.get("check_id") in DATA_CHECKS:
            add(json.dumps([c.get("expected"), c.get("recomputed")], ensure_ascii=False))
    nums = [t for t in re.findall(r"(?<![\w.])[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])[+-]?\d{3,}(?:\.\d+)?|[+-]?\d+(?:\.\d+)?(?=\s*%)", rep)]
    bad = []
    for t in nums:
        v = float(t.replace(",", ""))
        if 1900 <= v <= 2100 or v in pool or abs(v) in pool or round(v) in pool:
            continue
        bad.append(t)
    check(log, "V8", "final_report.md 的數字", "全部可追溯", f"{len(nums) - len(bad)}/{len(nums)}", not bad, "全部",
          ("無法追溯：" + "、".join(bad[:10])) if bad else "")
    # V9 假設揭露
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    missing = [k for k, v in params.items() if isinstance(v, dict) and v.get("kind") != "分析設定" and k not in rep_full]
    check(log, "V9", "假設參數表", "列出全部使用者情境參數與門檻", missing or "全部列出", not missing, "全部")
    # V10 隱私：只檢查文字欄位與報告（數值欄的長串小數不是電話）
    leaks = []
    phone = re.compile(r"(?<![\d.])09\d{2}-?\d{3}-?\d{3}(?![\d.])")
    addr = re.compile(r"[^\s，,。〔]{1,10}(路|街)[^\s，,。]{0,6}?\d+\s*號")
    text_cols = ("note_raw", "notes_text", "fee_mentions", "text", "risk_hits_591", "label")
    for p in list(run.glob("*.csv")):
        rows = rcsv(p)
        if rows and "土地位置建物門牌" in rows[0]:
            leaks.append(f"{p.name}: 門牌欄")
        for r in rows:
            for k in text_cols:
                v = r.get(k) or ""
                if phone.search(v) or addr.search(v):
                    leaks.append(f"{p.name}: {k} 含電話或門牌樣式"); break
    for p in list(run.glob("*.md")) + list(run.glob("*.json")):
        t = p.read_text(encoding="utf-8")
        if phone.search(t) or addr.search(t):
            leaks.append(f"{p.name}: 電話或門牌樣式")
    leaks = sorted(set(leaks))
    check(log, "V10", "所有輸出", "不含門牌與個資", leaks or "無", not leaks, "0")
    # V11 模擬標示：本 Skill 不使用模擬資料；若有使用者提供的評論，不得被標成模擬
    rv = rcsv(run / "01_reviews.csv")
    sim = [r for r in rv if r.get("is_simulated") == "true"]
    check(log, "V11", "模擬資料", "無模擬資料或皆已標示", f"{len(sim)} 則模擬", not sim or "模擬" in rep, "全部")
    # 報告章節
    heads = ["一句話結論", "你問的問題", "行情摘要", "真實每月總成本", "風險提醒", "資料限制", "假設參數", "審查紀錄", "看房殺價話術"]
    miss_h = [h for h in heads if h not in rep_full]
    check(log, "V8", "報告章節與第一行地區", "九個章節＋第一行寫分析地區", miss_h or "齊全", not miss_h and "分析地區" in rep_full[:300], "全部")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True); ap.add_argument("--stage", choices=["data", "report"], required=True)
    ap.add_argument("--cache", default="data/lvr-cache")
    a = ap.parse_args()
    run = Path(a.run)
    lp = run / "05_review_log.json"
    log = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else {"verdict": None, "retry_count": 0, "checks": [], "issues": []}
    prefix = ("V8", "V9", "V10", "V11") if a.stage == "report" else DATA_CHECKS
    if a.stage == "report":
        # 報告階段重試紀錄：上一次報告檢核 FAIL 時，保留第一次的問題，report_retry 加 1（最多 1 次，見 SKILL.md RT16）
        prev_fail = [f"{c['check_id']} {c['target']}：{c.get('note') or c.get('recomputed')}"
                     for c in log["checks"] if c["check_id"] in prefix and c["status"] == "FAIL"]
        log.setdefault("report_retry", 0)
        if prev_fail:
            log["report_retry"] += 1
            log.setdefault("report_first_issues", prev_fail)
            log.setdefault("report_first_issues_summary", first_issue_summary(log["report_first_issues"]))
    log["checks"] = [c for c in log["checks"] if c["check_id"] not in prefix]
    try:
        (stage_report if a.stage == "report" else lambda r, l: stage_data(r, a.cache, l))(run, log)
    except Exception as e:  # noqa: BLE001
        log["checks"].append({"check_id": prefix[0], "target": "執行", "status": "FAIL", "note": f"{type(e).__name__}: {e}"})
    fails = [c for c in log["checks"] if c["status"] == "FAIL"]
    log["issues"] = [f"{c['check_id']} {c['target']}：{c.get('note') or c.get('recomputed')}" for c in fails]
    log["verdict"] = "FAIL" if fails else "PASS"
    lp.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    out = {"stage": a.stage, "verdict": log["verdict"], "checks": len(log["checks"]), "issues": log["issues"]}
    if a.stage == "report":
        out["report_retry"] = log.get("report_retry", 0)
        if log.get("report_first_issues_summary"):
            out["report_first_issues_summary"] = log["report_first_issues_summary"]
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
