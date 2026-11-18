#!/usr/bin/env python3
"""flag.py — fact-checker 的旗標腳本：只標記、不刪除。

用法：python scripts/flag.py --run <run>
讀 01_collected.csv、01_candidates.csv、01_reviews.csv（可無）、01_area.json、01_collect_manifest.json；
寫 02_flags.csv（一列一旗標）與 02_factcheck_summary.json。旗標代碼與規則 ID 見 references/cleaning-rules.md。
"""
import argparse, collections, csv, datetime as dt, json, statistics, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
NON_RES_BUILD = ("店面", "工廠", "辦公商業大樓", "倉庫")
NON_RES_TARGET = ("土地", "車位")
TZ = dt.timezone(dt.timedelta(hours=8))


def load_csv(p):
    p = Path(p)
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def season_window(params):
    """分析窗：最新季的租賃日期最大值往前 12 個月（以資料本身決定，不寫死）。"""
    return params["seasons_current"]["value"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True)
    ap.add_argument("--today", help="分析日（YYYY-MM-DD），預設今天")
    a = ap.parse_args()
    run = Path(a.run)
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(TZ).date()
    market = load_csv(run / "01_collected.csv")
    cands = load_csv(run / "01_candidates.csv")
    reviews = load_csv(run / "01_reviews.csv")
    area = json.loads((run / "01_area.json").read_text(encoding="utf-8"))
    current = set(season_window(params))
    flags = []

    def add(rid, kind, code, sev, rule, detail):
        flags.append({"record_id": rid, "record_kind": kind, "flag_code": code, "severity": sev,
                      "rule_id": rule, "detail": detail})

    # 分析窗起點：最新季最大 rent_date 往前 12 個月
    latest = max((r["rent_date"] for r in market if r["season"] == max(current) and r["rent_date"]), default="")
    start = (dt.date.fromisoformat(latest) - dt.timedelta(days=365)).isoformat() if latest else ""
    season_min = {}
    for r in market:
        if r["rent_date"]:
            season_min.setdefault(r["season"], []).append(r["rent_date"])
    season_med = {s: sorted(v)[len(v) // 2] for s, v in season_min.items()}

    ids = collections.Counter(r["record_id"] for r in market)
    cross = collections.defaultdict(list)
    for r in market:
        cross[(r["addr_hash"], r["rent_date"], r["rent_total"])].append(r["season"])

    for r in market:
        rid = r["record_id"]
        if r["date_invalid"] == "True":
            add(rid, "market", "DATE_INVALID", "warn", "CR-05", "租賃年月日無法換算")
        elif start and r["season"] in current and r["rent_date"] < start:
            add(rid, "market", "STALE", "info", "CR-05", f"rent_date {r['rent_date']} 早於分析窗起點 {start}")
        if r["rent_date"] and r["season"] in season_med:
            med = dt.date.fromisoformat(season_med[r["season"]])
            if dt.date.fromisoformat(r["rent_date"]) < med - dt.timedelta(days=180):
                add(rid, "market", "LATE_FILING", "info", "CR-05", f"{r['season']} 季中位日 {med}，本筆 {r['rent_date']}")
        if ids[rid] > 1:
            add(rid, "market", "DUP_ID", "warn", "CR-07", f"record_id 出現 {ids[rid]} 次")
        seasons = cross[(r["addr_hash"], r["rent_date"], r["rent_total"])]
        if len(set(seasons)) > 1 and r["season"] != max(seasons):
            add(rid, "market", "DUP_CROSS_SEASON", "warn", "CR-07", f"同一案件也出現在 {max(seasons)}")
        if r["building_type"].startswith(NON_RES_BUILD) or r["target_type"] in NON_RES_TARGET:
            add(rid, "market", "NON_RESIDENTIAL", "info", "CR-08", f"{r['building_type']}／{r['target_type']}")
        if r["is_social_housing"] == "True":
            add(rid, "market", "SOCIAL_HOUSING", "info", "CR-10", r["rental_service"] or "備註含社會住宅")
        if "車位" in r["target_type"] and r["target_type"] != "車位":
            add(rid, "market", "PARKING_BUNDLED", "info", "CR-09", "使用 rent_excl_parking")
        ap_ = fnum(r["area_ping"])
        if ap_ is None or ap_ <= 0 or ap_ > 200:
            add(rid, "market", "AREA_INVALID", "warn", "CR-09", f"area_ping={r['area_ping']}")
        if r["rent_type_group"] == "unknown":
            add(rid, "market", "TYPE_MISSING", "info", "CR-08", "出租型態空白")
        if r["mgmt_fee_status"] == "unknown" or (r["has_mgmt_org"] == "True" and r["mgmt_fee_status"] == "not_mentioned"):
            add(rid, "market", "MGMT_FEE_UNKNOWN", "info", "CR-08", "備註未能解析管理費")
        if "TAX_INCLUDED" in r["note_tags"]:
            add(rid, "market", "TAX_INCLUDED", "info", "CR-08", "備註含「含稅」")
        if "STEP_RENT" in r["note_tags"]:
            add(rid, "market", "STEP_RENT", "info", "CR-08", "約定不同租金")

    # IQR 初篩（全區粗分組；只供 quant 參考）
    by_group = collections.defaultdict(list)
    for r in market:
        v = fnum(r["rent_per_ping"])
        if v and r["season"] in current:
            by_group[(r["area_key"], r["rent_type_group"])].append((r["record_id"], v))
    for g, vals in by_group.items():
        if len(vals) < 4:
            continue
        q = statistics.quantiles([v for _, v in vals], n=4, method="inclusive")
        iqr = q[2] - q[0]
        lo, hi = q[0] - 1.5 * iqr, q[2] + 1.5 * iqr
        for rid, v in vals:
            if v < lo or v > hi:
                add(rid, "market", "OUTLIER_PRELIM", "info", "CR-09", f"{g[0]} {g[1]} 粗分組 IQR 外（{v:.0f}）")

    in_data = {t["area_key"]: t.get("in_rent_data", True) for t in area.get("targets", [])}
    for c in cands:
        lid = c["listing_id"]
        if c["source_type"] in ("", "unknown"):
            add(lid, "candidate", "UNKNOWN_SOURCE", "warn", "CR-11", "使用者未說明刊登來源")
        pd_ = c.get("posted_date")
        if not pd_:
            add(lid, "candidate", "STALE_LISTING", "warn", "CR-11", "沒有刊登日期")
        elif (today - dt.date.fromisoformat(pd_)).days > params["stale_listing_days"]["value"]:
            add(lid, "candidate", "STALE_LISTING", "warn", "CR-11", f"刊登日期 {pd_} 距今超過 {params['stale_listing_days']['value']} 天")
        if c.get("price_basis") == "asking_591":
            add(lid, "candidate", "ASKING_PRICE", "info", "CR-13", "月租為 591 刊登租金，非成交價")
        if not c.get("commute_minutes_oneway"):
            add(lid, "candidate", "COMMUTE_UNSTATED", "info", "CR-14", "未提供通勤分鐘，時間成本不計")
        if c.get("area_source") in ("school_lookup", "address_parse"):
            add(lid, "candidate", "AREA_FROM_LOOKUP", "info", "CR-12", f"地區來源 {c['area_source']}")
        if not in_data.get(c["area_key"], True) or area.get("district_quirk"):
            add(lid, "candidate", "AREA_NO_DISTRICT_DATA", "warn", "CR-12", "該區無分區租賃資料，行情以全市計算")
        unstated = [k for k in ("mgmt", "elec", "water", "gas", "internet") if c.get(f"{k}_status") in ("unstated", "taipower")]
        if unstated:
            add(lid, "candidate", "COST_UNSTATED", "info", "CR-14", "未提供：" + "、".join(unstated))
        if c.get("status") == "incomplete":
            add(lid, "candidate", "INCOMPLETE", "warn", "CR-11", c.get("status_reason", ""))
    for rv in reviews:
        if rv.get("is_simulated") == "true":
            add(rv["review_id"], "review", "SIMULATED", "info", "CR-15", "模擬評論")

    with open(run / "02_flags.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["record_id", "record_kind", "flag_code", "severity", "rule_id", "detail"])
        w.writeheader(); w.writerows(flags)
    summ = {"rows_in": len(market), "rows_flagged": len({x["record_id"] for x in flags if x["record_kind"] == "market"}),
            "by_flag": dict(collections.Counter(x["flag_code"] for x in flags).most_common()),
            "rows_deleted": 0, "analysis_window_start": start, "latest_rent_date": latest,
            "candidate_flags": {c["listing_id"]: [x["flag_code"] for x in flags if x["record_id"] == c["listing_id"]] for c in cands},
            "notes": []}
    for k in {r["area_key"] for r in market}:
        cur = [r for r in market if r["area_key"] == k and r["season"] in current]
        sh = sum(r["is_social_housing"] == "True" for r in cur)
        if cur:
            summ["notes"].append(f"{k} 目前行情窗內社會住宅相關案件 {sh}/{len(cur)} 筆，需做排除社宅的敏感度比較")
    (run / "02_factcheck_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summ[k] for k in ("rows_in", "rows_flagged", "rows_deleted", "candidate_flags")}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
