#!/usr/bin/env python3
"""analyze.py — quant-analyst 的計算腳本：行情統計、IQR、候選物件真實每月總成本、排序、刊登租金對照、高風險訊號、圖表。

用法：python scripts/analyze.py --run <run> [--asking <dir 含 591_list.csv>]
輸出：03_inclusion_log.csv、03_market_stats.csv、03_cost_breakdown.csv、03_ranking.csv（≥2 間）、
     03_mgmt_fee_status.csv（管理費解析狀態筆數）、03_asking_stats.csv（有 591 資料時）、03_signals.json、charts/*.png
原則：物件事實沒寫就是「未提供」，不補預設值；刊登租金與實價登錄租金永不合併。
"""
import argparse, csv, json, sys
from pathlib import Path

import numpy as np
import pandas as pd

SKILL = Path(__file__).resolve().parent.parent
STUDENT = ("student_suite", "student_room")
EXCLUDE_FLAGS = {"STALE": "過時（分析窗外）", "LATE_FILING": "遲延申報", "DATE_INVALID": "日期無效",
                 "NON_RESIDENTIAL": "非住宅", "TAX_INCLUDED": "含稅（商用）", "AREA_INVALID": "面積無效",
                 "DUP_CROSS_SEASON": "跨季重複（保留最新季）"}
RISK_WORDS = None


def read(p):
    p = Path(p)
    return pd.read_csv(p, encoding="utf-8-sig", dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame()


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def q(vals, p):
    return float(np.percentile(vals, p))  # linear，與 pandas.quantile 預設相同


def load_risk_words():
    text = (SKILL / "references/risk-signals.md").read_text(encoding="utf-8")
    block = text.split("<!-- R3_KEYWORDS -->")[1].split("<!-- /R3_KEYWORDS -->")[0]
    return [w.strip() for w in block.replace("\n", "、").split("、") if w.strip()]


def inclusion(market, flags, current):
    fl = flags[flags.record_kind == "market"].groupby("record_id").flag_code.apply(set).to_dict() if len(flags) else {}
    seen, rows = set(), []
    for r in market.itertuples():
        reasons = []
        if r.season not in current:
            reasons.append("趨勢對照季（不進目前行情）")
        for code in sorted(fl.get(r.record_id, set()) & EXCLUDE_FLAGS.keys()):
            reasons.append(EXCLUDE_FLAGS[code])
        key = (r.record_id, r.season)
        if r.record_id in seen:
            reasons.append("DUP_ID（只保留第一列）")
        seen.add(r.record_id)
        if f(r.rent_per_ping) is None:
            reasons.append("無每坪租金")
        rows.append({"record_id": r.record_id, "season": r.season, "area_key": r.area_key,
                     "rent_type_group": r.rent_type_group, "included": not reasons, "reasons": "；".join(reasons)})
    return pd.DataFrame(rows)


def city_eligible(city, current):
    c = city[city.season.isin(current)].copy()
    c = c[(c.date_invalid != "True") & ~c.building_type.str.startswith(("店面", "工廠", "辦公商業大樓", "倉庫"))
          & ~c.target_type.isin(["土地", "車位"]) & ~c.note_tags.str.contains("TAX_INCLUDED")]
    c["rpp"] = pd.to_numeric(c.rent_per_ping, errors="coerce")
    c["ap"] = pd.to_numeric(c.area_ping, errors="coerce")
    c = c[(c.ap > 0) & (c.ap <= 200) & c.rpp.notna()]
    return c.drop_duplicates("record_id")


def stats_row(df, city, district, level, group, scope, sh, fallback, n_excl):
    rpp = df.rpp.astype(float).values
    rent = pd.to_numeric(df.rent_excl_parking).astype(float).values
    q1, q3 = q(rpp, 25), q(rpp, 75)
    iqr = q3 - q1
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    k = params["iqr_k"]["value"]
    lo, hi = q1 - k * iqr, q3 + k * iqr
    return {"group_key": f"{city}|{district}|{group}|{scope}", "city": city, "district": district, "area_level": level,
            "rent_type_group": group, "scope": scope, "include_social_housing": sh, "n": len(rpp),
            "n_excluded": n_excl, "fallback": fallback,
            "rent_median": round(q(rent, 50), 1), "rent_q1": round(q(rent, 25), 1), "rent_q3": round(q(rent, 75), 1),
            "rpp_median": round(q(rpp, 50), 1), "rpp_q1": round(q1, 1), "rpp_q3": round(q3, 1),
            "rpp_p10": round(q(rpp, 10), 1), "rpp_p90": round(q(rpp, 90), 1), "iqr": round(iqr, 1),
            "lower_fence": round(lo, 1), "upper_fence": round(hi, 1),
            "area_ping_median": round(q(pd.to_numeric(df.area_ping).astype(float).values, 50), 2),
            "outlier_count": int(((rpp < lo) | (rpp > hi)).sum())}


def market_group(pool, city_pool, area_key, group, scope, min_n):
    """回傳 (統計用資料, area_level, district, group 名稱, fallback 步驟)。退回只擴大，不跨縣市。"""
    city, district = area_key.split("|")
    steps = []
    groups = [group]
    df = pool[(pool.area_key == area_key) & pool.rent_type_group.isin(groups)]
    if len(df) >= min_n:
        return df, "district", district, group, None
    if group in STUDENT:
        steps.append("type_merged"); groups = list(STUDENT); group = "student_all"
        df = pool[(pool.area_key == area_key) & pool.rent_type_group.isin(groups)]
        if len(df) >= min_n:
            return df, "district", district, group, ";".join(steps)
    steps.append("window_8q_unavailable")
    cdf = city_pool[(city_pool.city == city) & city_pool.rent_type_group.isin(groups)]
    steps.append("city_wide")
    if len(cdf) >= min_n:
        return cdf, "city", "(全市)", group, ";".join(steps)
    steps.append("insufficient")
    return None, "city", "(全市)", group, ";".join(steps)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--asking")
    a = ap.parse_args()
    run = Path(a.run)
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    P = {k: v["value"] for k, v in params.items() if isinstance(v, dict)}
    current = P["seasons_current"]
    scope = f"{current[0]}-{current[-1]}"
    market, city, flags = read(run / "01_collected.csv"), read(run / "01_collected_city.csv"), read(run / "02_flags.csv")
    cands, reviews = read(run / "01_candidates.csv"), read(run / "01_reviews.csv")
    area = json.loads((run / "01_area.json").read_text(encoding="utf-8"))
    routing = json.loads((run / "00_routing.json").read_text(encoding="utf-8")) if (run / "00_routing.json").exists() else {}

    inc = inclusion(market, flags, current)
    inc.to_csv(run / "03_inclusion_log.csv", index=False, encoding="utf-8-sig")
    ok_ids = set(zip(inc[inc.included].record_id, inc[inc.included].season))
    pool = market[[(r, s) in ok_ids for r, s in zip(market.record_id, market.season)]].copy()
    pool["rpp"] = pd.to_numeric(pool.rent_per_ping)
    city_pool = city_eligible(city, current)

    # 行情分組：每個目標區 × 學生型與整層；外加候選物件需要的分組
    need = {(t["area_key"], g) for t in area["targets"] for g in ("student_suite", "student_room", "whole_unit")}
    for c in cands.itertuples():
        if c.rent_type_group:
            need.add((c.area_key, c.rent_type_group))
    stats, group_of = [], {}
    for key, g in sorted(need):
        df, level, district, gname, fb = market_group(pool, city_pool, key, g, scope, P["min_group_n"])
        city_name = key.split("|")[0]
        gk = f"{city_name}|{district}|{gname}|{scope}"
        group_of[(key, g)] = (gk, df, fb)
        if df is None:
            stats.append({"group_key": gk, "city": city_name, "district": district, "area_level": level,
                          "rent_type_group": gname, "scope": scope, "include_social_housing": True, "n": 0,
                          "fallback": fb})
            continue
        n_excl = int((~inc.included & (inc.area_key == key)).sum()) if level == "district" else None
        if gk not in {s["group_key"] for s in stats}:
            stats.append(stats_row(df, city_name, district, level, gname, scope, True, fb, n_excl))
            nsh = df[df.is_social_housing != "True"]
            if len(nsh) >= P["min_group_n"]:
                stats.append(stats_row(nsh, city_name, district, level, gname, scope, False, fb, None))
    ms = pd.DataFrame(stats)
    ms.to_csv(run / "03_market_stats.csv", index=False, encoding="utf-8-sig")

    # 管理費解析狀態統計：報告若要寫各狀態筆數，抄這個檔（V8 才能追溯）
    mf = []
    if len(market) and "mgmt_fee_status" in market.columns:
        st = market.mgmt_fee_status.fillna("").replace("", "blank")
        mf = [{"area_key": "ALL", "mgmt_fee_status": k, "n": int(v)} for k, v in st.value_counts().items()]
        for (ak, k), v in market.assign(_s=st).groupby(["area_key", "_s"]).size().items():
            mf.append({"area_key": ak, "mgmt_fee_status": k, "n": int(v)})
    pd.DataFrame(mf, columns=["area_key", "mgmt_fee_status", "n"]).to_csv(
        run / "03_mgmt_fee_status.csv", index=False, encoding="utf-8-sig")

    # 真實每月總成本（已知項目合計＋未提供清單）
    costs = []
    for c in cands.itertuples():
        if c.status != "ok":
            continue
        rent = int(float(c.rent_monthly))
        known, missing, detail = {"rent": rent}, [], {}
        for k in ("mgmt", "water", "gas", "internet"):
            st = getattr(c, f"{k}_status")
            fee = f(getattr(c, f"{k}_fee"))
            if st == "included":
                known[k] = 0
            elif st == "stated" and fee is not None:
                known[k] = int(round(fee))
            else:
                missing.append(k)
        if c.elec_status == "per_kwh" and f(c.elec_price_per_kwh) is not None:
            known["elec"] = int(round(float(c.elec_price_per_kwh) * P["kwh_per_month"]))
            detail["elec_assumption"] = f"{float(c.elec_price_per_kwh):g} 元/度 × {P['kwh_per_month']} 度（使用者情境參數）"
        elif c.elec_status == "included":
            known["elec"] = 0; detail["elec_assumption"] = "租金含電費"
        else:
            missing.append("elec")
            detail["elec_assumption"] = "台電計價（電價未驗證）" if c.elec_status == "taipower" else "未提供"
        mins = f(c.commute_minutes_oneway)
        if mins is not None:
            known["commute_time"] = int(round(2 * mins * P["school_days_per_month"] / 60 * P["hourly_value"]))
            fare = f(c.commute_fare_per_trip)
            if fare is not None:
                known["commute_fare"] = int(round(2 * fare * P["school_days_per_month"]))
        else:
            missing.append("commute")
        ap_ = f(c.area_ping)
        rpp = round(rent / ap_, 1) if ap_ else None
        gk, df, fb = group_of.get((c.area_key, c.rent_type_group), (None, None, None))
        pct = vs = anchor = None
        outlier = "n/a"
        mrow = ms[(ms.group_key == gk) & (ms.include_social_housing.astype(str) == "True")] if gk else pd.DataFrame()
        comparable = c.area_basis == "user"
        if rpp and df is not None and len(mrow) and comparable:
            vals = df.rpp.astype(float).values
            pct = round(float((vals <= rpp).sum()) / len(vals) * 100, 1)
            med = float(mrow.rpp_median.iloc[0])
            vs = round((rpp - med) / med * 100, 1)
            anchor = int(round(med * ap_ / 100.0) * 100)  # 以行情中位數每坪租金換算的月租（殺價錨點）
            lo, hi, p10 = float(mrow.lower_fence.iloc[0]), float(mrow.upper_fence.iloc[0]), float(mrow.rpp_p10.iloc[0])
            outlier = "low" if (rpp < lo or rpp < p10) else "high" if rpp > hi else "none"
        total = sum(known.values())
        costs.append({"listing_id": c.listing_id, "label": c.label, "area_key": c.area_key, "price_basis": c.price_basis,
                      "rent": rent, "mgmt_fee": known.get("mgmt", ""), "mgmt_status": c.mgmt_status,
                      "elec_cost": known.get("elec", ""), "elec_assumption": detail["elec_assumption"],
                      "water_fee": known.get("water", ""), "gas_fee": known.get("gas", ""),
                      "internet_fee": known.get("internet", ""), "destination_label": c.destination_label,
                      "commute_minutes_oneway": c.commute_minutes_oneway,
                      "commute_source": "user" if mins is not None else "unstated",
                      "commute_time_cost": known.get("commute_time", ""), "commute_fare_cost": known.get("commute_fare", ""),
                      "true_monthly_cost_known": total, "unstated_items": ";".join(missing),
                      "cost_complete": not missing, "area_ping": c.area_ping, "area_basis": c.area_basis,
                      "rent_per_ping": rpp if rpp else "",
                      "true_cost_per_ping": round(total / ap_, 1) if ap_ else "",
                      "market_group_key": gk or "", "market_fallback": fb or "",
                      "market_percentile": pct if pct is not None else "", "vs_median_pct": vs if vs is not None else "",
                      "outlier": outlier, "anchor_rent_at_median": anchor if anchor is not None else "",
                      "_parts": known})
    cb = pd.DataFrame(costs)
    if len(cb):
        cb.drop(columns="_parts").to_csv(run / "03_cost_breakdown.csv", index=False, encoding="utf-8-sig")

    # 高風險訊號
    words = load_risk_words()
    fl = flags[flags.record_kind == "candidate"] if len(flags) else pd.DataFrame(columns=["record_id", "flag_code", "severity"])
    signals, paused = [], []
    for c in cands.itertuples():
        lid = c.listing_id
        row = cb[cb.listing_id == lid] if len(cb) else pd.DataFrame()
        if len(row):
            o = row.outlier.iloc[0]
            if o == "low":
                signals.append({"listing_id": lid, "signal": "R1", "evidence": f"每坪 {row.rent_per_ping.iloc[0]} 元低於該組下界或 P10", "source": "03_market_stats.csv"})
            elif o == "high":
                signals.append({"listing_id": lid, "signal": "R2", "evidence": f"每坪 {row.rent_per_ping.iloc[0]} 元高於該組上界", "source": "03_market_stats.csv"})
            elif o == "n/a":
                paused.append(f"{lid} 的 R1／R2 不判定：" + ("坪數為 591 使用坪數，與實價登錄登記坪數基準不同" if c.area_basis == "591_use_area" else "缺坪數或行情樣本不足"))
        text = f"{c.notes_text} {c.risk_hits_591}"
        hit = [w for w in words if w in text]
        if hit:
            signals.append({"listing_id": lid, "signal": "R3", "evidence": "命中：" + "、".join(hit), "source": "user_input" if c.source_type != "591" else "591 刊登內容"})
        dm = f(c.deposit_months)
        if dm is not None and dm > P["deposit_cap_months"]:
            signals.append({"listing_id": lid, "signal": "R4", "evidence": f"押金 {dm:g} 個月 > {P['deposit_cap_months']} 個月", "source": c.source_type})
        if P.get("elec_cap_per_kwh") is None:
            if c.elec_status == "per_kwh":
                paused.append(f"{lid} 的 R5 不判定：電費上限未驗證（電價 {c.elec_price_per_kwh} 元/度）")
        elif f(c.elec_price_per_kwh) and float(c.elec_price_per_kwh) > P["elec_cap_per_kwh"]:
            signals.append({"listing_id": lid, "signal": "R5", "evidence": f"每度 {c.elec_price_per_kwh} 元", "source": c.source_type})
        mine = fl[fl.record_id == lid]
        codes = set(mine.flag_code)
        if {"UNKNOWN_SOURCE", "STALE_LISTING"} <= codes or (mine.severity.isin(["warn", "high"]).sum() >= 2):
            signals.append({"listing_id": lid, "signal": "R6", "evidence": "＋".join(sorted(mine[mine.severity != "info"].flag_code)), "source": "02_flags.csv"})
    if len(reviews):
        negw = ["漏水", "壁癌", "隔音差", "蟑螂", "押金不退", "房東擅自進入"]
        for key, grp in reviews.groupby("area_key"):
            neg = grp[grp.text.apply(lambda t: any(w in t for w in negw))]
            if len(neg) >= P["neg_review_min"]:
                for lid in cands[cands.area_key == key].listing_id:
                    signals.append({"listing_id": lid, "signal": "R7", "evidence": f"{key} 負面評論 {len(neg)} 則", "source": "01_reviews.csv"})
    else:
        paused.append("R7 不判定：使用者沒有提供評論，此地區無評論資料")
    (run / "03_signals.json").write_text(json.dumps({"signals": signals, "not_evaluated": paused}, ensure_ascii=False, indent=2), encoding="utf-8")

    # 排序（compare）
    if len(cb) >= 2:
        miss = cb.unstated_items.tolist()
        same = len(set(miss)) == 1
        common = set.intersection(*[set(p) for p in cb._parts])
        cb["_common"] = [sum(v for k, v in p.items() if k in common) for p in cb._parts]
        cb["_time_free"] = [sum(v for k, v in p.items() if k != "commute_time") for p in cb._parts]
        cb["_excl"] = [sum(v for k, v in p.items() if k not in ("commute_time", "commute_fare")) for p in cb._parts]
        cb = cb.sort_values(["true_monthly_cost_known", "listing_id"]).reset_index(drop=True)
        rk = lambda col: cb[col].rank(method="min").astype(int)
        nsig = {lid: sum(s["listing_id"] == lid for s in signals) for lid in cb.listing_id}
        rank = pd.DataFrame({"rank": range(1, len(cb) + 1), "listing_id": cb.listing_id,
                             "true_monthly_cost_known": cb.true_monthly_cost_known,
                             "delta_vs_best": cb.true_monthly_cost_known - cb.true_monthly_cost_known.iloc[0],
                             "comparable": same, "unstated_items": cb.unstated_items,
                             "common_items": ";".join(sorted(common)), "cost_common_items": cb._common,
                             "rank_common_items": rk("_common"), "rank_if_time_free": rk("_time_free"),
                             "rank_excl_commute": rk("_excl"), "risk_signal_count": cb.listing_id.map(nsig)})
        rank.to_csv(run / "03_ranking.csv", index=False, encoding="utf-8-sig")

    # 刊登租金對照（永不與實價登錄合併）
    if a.asking and (Path(a.asking) / "591_list.csv").exists():
        al = read(Path(a.asking) / "591_list.csv")
        al["rent"] = pd.to_numeric(al.asking_rent, errors="coerce")
        al["ping"] = pd.to_numeric(al.use_area_ping, errors="coerce")
        rows = []
        for t in area["targets"]:
            for g in ("student_suite", "student_room", "whole_unit"):
                d = al[(al.area_key == t["area_key"]) & (al.rent_type_group == g) & al.rent.notna()]
                if not len(d):
                    continue
                lv = ms[(ms.group_key == f"{t['city']}|{t['district']}|{g}|{scope}") & (ms.include_social_housing.astype(str) == "True")]
                lmed = float(lv.rent_median.iloc[0]) if len(lv) and "rent_median" in lv and pd.notna(lv.rent_median.iloc[0]) else None
                amed = q(d.rent.values, 50)
                pp = (d.rent / d.ping).dropna()
                rows.append({"area_key": t["area_key"], "rent_type_group": g, "price_basis": "asking_591",
                             "n_listings": len(d), "asking_rent_median": round(amed, 1),
                             "asking_rent_q1": round(q(d.rent.values, 25), 1), "asking_rent_q3": round(q(d.rent.values, 75), 1),
                             "asking_per_use_ping_median": round(q(pp.values, 50), 1) if len(pp) else "",
                             "lvr_rent_median": lmed if lmed else "",
                             "asking_vs_lvr_pct": round((amed - lmed) / lmed * 100, 1) if lmed else "",
                             "crawled_at": d.crawled_at.max(), "note": "刊登價≠成交價；坪數為使用坪數，不與實價登錄合併"})
        pd.DataFrame(rows).to_csv(run / "03_asking_stats.csv", index=False, encoding="utf-8-sig")

    charts(run, pool, ms, cb, market, area, scope)
    print(json.dumps({"groups": len(ms), "candidates": len(cb), "signals": signals, "not_evaluated": paused}, ensure_ascii=False))


def charts(run, pool, ms, cb, market, area, scope):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    cjk = next((n for n in ("Noto Sans CJK TC", "Noto Sans TC", "WenQuanYi Zen Hei", "Microsoft JhengHei", "PingFang TC") if n in names), None)
    if cjk:
        plt.rcParams["font.family"] = cjk
    L = (lambda zh, en: zh) if cjk else (lambda zh, en: en)  # E15：無中文字型改英文標籤
    out = run / "charts"; out.mkdir(exist_ok=True)
    keys = [t["area_key"] for t in area["targets"]]
    # 1 箱型圖
    fig, ax = plt.subplots(figsize=(8, 4.5))
    data, labels = [], []
    for k in keys:
        for g in ("student_suite", "student_room", "whole_unit"):
            v = pool[(pool.area_key == k) & (pool.rent_type_group == g)].rpp.dropna()
            if len(v):
                data.append(v.values); labels.append(f"{k.split('|')[1]}\n{g}")
    if data:
        ax.boxplot(data, showfliers=False)
        ax.set_xticks(range(1, len(labels) + 1), labels, fontsize=8)
        for i, c in enumerate(cb.itertuples() if len(cb) else []):
            if c.rent_per_ping != "" and c.rent_per_ping is not None:
                for j, lab in enumerate(labels):
                    if lab.startswith(c.area_key.split("|")[1]) and c.market_group_key and lab.endswith(c.market_group_key.split("|")[2]):
                        ax.plot(j + 1, float(c.rent_per_ping), "r*", ms=12)
                        ax.annotate(c.listing_id, (j + 1, float(c.rent_per_ping)), xytext=(6, 4), textcoords="offset points")
    ax.set_ylabel(L("每坪租金（元／坪）", "Rent per ping (NTD)")); ax.set_title(L(f"實價登錄每坪租金 {scope}", f"Rent per ping {scope}"))
    fig.tight_layout(); fig.savefig(out / "rpp_box_by_group.png", dpi=150); plt.close(fig)
    # 2 趨勢
    fig, ax = plt.subplots(figsize=(8, 4))
    m = market.copy(); m["rpp"] = pd.to_numeric(m.rent_per_ping, errors="coerce")
    m = m[m.rent_type_group.isin(STUDENT) & m.rpp.notna()]
    for k in keys:
        s = m[m.area_key == k].groupby("season").rpp.median()
        if len(s):
            ax.plot(s.index, s.values, marker="o", label=k.replace("|", ""))
    ax.set_ylabel(L("學生型每坪租金中位數", "Median rent/ping (student types)")); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "rpp_trend_by_season.png", dpi=150); plt.close(fig)
    # 3 堆疊
    if len(cb):
        fig, ax = plt.subplots(figsize=(7, 4))
        parts = ["rent", "mgmt", "elec", "water", "gas", "internet", "commute_time", "commute_fare"]
        names_zh = {"rent": "租金", "mgmt": "管理費", "elec": "電費", "water": "水費", "gas": "瓦斯", "internet": "網路",
                    "commute_time": "通勤時間成本", "commute_fare": "交通費"}
        bottom = np.zeros(len(cb))
        for p in parts:
            vals = np.array([d.get(p, 0) for d in cb._parts], dtype=float)
            if vals.any():
                ax.bar(cb.listing_id, vals, bottom=bottom, label=L(names_zh[p], p)); bottom += vals
        for i, c in enumerate(cb.itertuples()):
            if c.unstated_items:
                ax.annotate(L("未提供：", "unstated: ") + c.unstated_items, (i, bottom[i]), ha="center", va="bottom", fontsize=7)
        ax.set_ylabel(L("元／月（已知項目）", "NTD/month (known items)")); ax.legend(fontsize=7)
        fig.tight_layout(); fig.savefig(out / "true_cost_stacked.png", dpi=150); plt.close(fig)
    # 4 社宅對照
    fig, ax = plt.subplots(figsize=(7, 4))
    s = pool[pool.rent_type_group.isin(STUDENT)]
    for flag, lab in (("True", L("社會住宅相關", "social housing")), ("False", L("非社宅", "non-social"))):
        v = s[s.is_social_housing == flag].rpp.dropna()
        if len(v):
            ax.hist(v.clip(upper=v.quantile(0.98)), bins=30, alpha=.6, label=f"{lab} n={len(v)}")
    ax.set_xlabel(L("每坪租金（元／坪）", "Rent per ping")); ax.legend()
    fig.tight_layout(); fig.savefig(out / "rpp_hist_social_vs_non.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
