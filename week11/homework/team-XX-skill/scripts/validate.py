#!/usr/bin/env python3
"""validate.py — 檢查一次執行的輸出是否符合規格（沿用老師範本的結構改寫）。

用法：python scripts/validate.py --input output/<run_id>/
檢查：必要檔案存在、JSON 可解析、CSV 欄名、final_report.md 九個章節且開頭寫分析地區、
area_source 為允許值、rows_deleted = 0、輸出不含門牌欄、路由與檔案一致。
area_status = unresolved 時只檢查 00_routing.json、01_area.json、final_report.md。
"""
import argparse, csv, json, sys
from pathlib import Path

REQUIRED = ["00_routing.json", "01_area.json", "01_collected.csv", "01_candidates.csv", "01_collect_manifest.json",
            "02_flags.csv", "02_factcheck_summary.json", "03_market_stats.csv", "03_inclusion_log.csv",
            "03_signals.json", "05_review_log.json", "final_report.md"]
COLS = {"02_flags.csv": ["record_id", "record_kind", "flag_code", "severity", "rule_id", "detail"],
        "03_market_stats.csv": ["group_key", "n", "fallback", "rpp_median", "rpp_q1", "rpp_q3", "lower_fence", "upper_fence"],
        "03_cost_breakdown.csv": ["listing_id", "rent", "true_monthly_cost_known", "unstated_items", "market_percentile"],
        "03_ranking.csv": ["rank", "listing_id", "true_monthly_cost_known", "comparable", "rank_common_items"]}
HEADS = ["一句話結論", "你問的問題", "行情摘要", "真實每月總成本", "風險提醒", "資料限制", "假設參數", "審查紀錄", "看房殺價話術"]
SOURCES = {"user_explicit", "user_confirmed", "school_lookup", "address_parse"}


def validate(d: Path) -> list[str]:
    errs = []
    if not d.is_dir():
        return [f"找不到資料夾：{d}"]
    for p in d.glob("*.json"):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errs.append(f"{p.name} 不是合法 JSON：{e}")
    area = json.loads((d / "01_area.json").read_text(encoding="utf-8")) if (d / "01_area.json").exists() else {}
    unresolved = area.get("area_status") == "unresolved"
    need = ["00_routing.json", "01_area.json", "final_report.md"] if unresolved else REQUIRED
    errs += [f"缺少必要檔案：{f}" for f in need if not (d / f).exists()]
    if unresolved:
        if not area.get("question"):
            errs.append("unresolved 但 01_area.json 沒有追問句")
        if any((d / f).exists() for f in ("03_market_stats.csv", "03_cost_breakdown.csv")):
            errs.append("unresolved 卻產生了 03 檔（不應計算）")
        return errs
    for t in area.get("targets", []):
        if t.get("area_source") not in SOURCES:
            errs.append(f"area_source 不是允許值：{t.get('area_source')}")
    for f, cols in COLS.items():
        p = d / f
        if p.exists():
            with open(p, encoding="utf-8-sig") as fh:
                head = next(csv.reader(fh), [])
            errs += [f"{f} 缺欄位 {c}" for c in cols if c not in head]
    s = d / "02_factcheck_summary.json"
    if s.exists() and json.loads(s.read_text(encoding="utf-8")).get("rows_deleted") != 0:
        errs.append("rows_deleted 不是 0")
    rep = (d / "final_report.md").read_text(encoding="utf-8") if (d / "final_report.md").exists() else ""
    errs += [f"final_report.md 缺少章節：{h}" for h in HEADS if h not in rep]
    if "分析地區" not in rep[:300]:
        errs.append("final_report.md 開頭沒有寫分析地區")
    for p in d.rglob("*"):
        if p.suffix in (".csv", ".md") and "土地位置建物門牌" in p.read_text(encoding="utf-8-sig"):
            errs.append(f"{p.name} 含門牌欄")
    routing = json.loads((d / "00_routing.json").read_text(encoding="utf-8")) if (d / "00_routing.json").exists() else {}
    sig = json.loads((d / "03_signals.json").read_text(encoding="utf-8")).get("signals", []) if (d / "03_signals.json").exists() else []
    if bool(sig) != (d / "04_risk_report.json").exists():
        errs.append("路由不一致：有 R 訊號 ⇔ 04_risk_report.json 應同時成立")
    if not sig and not any(x.get("agent") == "devil-advocate" for x in routing.get("agents_skipped", [])):
        errs.append("沒有 R 訊號，但 00_routing.json.agents_skipped 沒記錄略過 devil-advocate")
    mode = routing.get("mode")
    if mode == "compare" and not (d / "03_ranking.csv").exists():
        errs.append("compare 模式缺 03_ranking.csv")
    rv = d / "05_review_log.json"
    if rv.exists() and json.loads(rv.read_text(encoding="utf-8")).get("verdict") not in ("PASS", "FAIL"):
        errs.append("05_review_log.json 沒有 verdict")
    return errs


def main():
    ap = argparse.ArgumentParser(description="驗證輸出格式")
    ap.add_argument("--input", required=True, help="output/<run_id>/ 資料夾")
    errs = validate(Path(ap.parse_args().input))
    if errs:
        print("❌ 驗證失敗：")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
    print("✅ 驗證通過")


if __name__ == "__main__":
    main()
