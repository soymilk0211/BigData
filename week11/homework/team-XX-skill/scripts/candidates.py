#!/usr/bin/env python3
"""candidates.py — 把 collector 從使用者訊息整理出的候選物件 JSON 轉成 01_candidates.csv。

用法：
  python scripts/candidates.py --input <run>/candidates_input.json --area <run>/01_area.json \
      --out <run> [--detail591 <dir>/591_detail.csv]

candidates_input.json 是一個陣列，每筆只寫使用者「有說」的欄位；沒說的欄位不要寫，
本腳本會標成 unstated（＝未提供）。可用欄位見 references/field-mapping.md「候選物件」。
若某筆有 listing_591_id，會從 591_detail.csv 補上刊登內容（押金、管理費、水電、踩雷字詞），
使用者自己說的值優先。
"""
import argparse, csv, json, re, sys
from pathlib import Path

COLS = ["listing_id", "label", "city", "district", "area_key", "area_source", "rent_type_group", "rent_monthly",
        "price_basis", "area_ping", "area_basis", "mgmt_fee", "mgmt_status", "elec_price_per_kwh", "elec_status",
        "water_fee", "water_status", "gas_fee", "gas_status", "internet_fee", "internet_status", "deposit_months",
        "destination_label", "commute_minutes_oneway", "commute_mode", "commute_fare_per_trip", "source_type",
        "source_url", "posted_date", "notes_text", "risk_hits_591", "status", "status_reason"]
COSTS = ["mgmt", "water", "gas", "internet"]


def load_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def from_591(row):
    """591 刊登頁欄位 → 候選物件欄位；只取刊登上明寫的內容。"""
    c = {"rent_monthly": row.get("asking_rent"), "price_basis": "asking_591",
         "area_ping": row.get("use_area_ping"), "area_basis": "591_use_area",
         "rent_type_group": row.get("rent_type_group"), "deposit_months": row.get("deposit_months"),
         "source_type": "591", "source_url": row.get("source_url"), "posted_date": row.get("posted_date"),
         "risk_hits_591": row.get("risk_hits", ""), "city": row.get("city"), "district": row.get("district")}
    contain = row.get("price_contain_text", "") or ""
    mg = str(row.get("mgmt_fee_text") or "")
    if "管理費" in contain or "含" in mg or mg.strip() in ("無", "免") or "免管理費" in (row.get("tags") or ""):
        c["mgmt_status"] = "included"  # 含在租金內或免管理費：每月另付 0 元
    elif row.get("mgmt_fee"):
        c["mgmt_fee"], c["mgmt_status"] = row["mgmt_fee"], "stated"
    wt = row.get("water_fee_type") or ""
    wm = re.search(r"(\d+)\s*元\s*/\s*月", wt)
    if "水" in contain or "含" in wt:
        c["water_status"] = "included"
    elif row.get("water_fee") or wm:
        c["water_fee"], c["water_status"] = row.get("water_fee") or int(wm.group(1)), "stated"
    if "網路" in contain or str(row.get("net_included")) == "1":
        c["internet_status"] = "included"
    et = row.get("electric_fee_type") or ""
    m = re.search(r"([\d.]+)\s*元", et)
    if m:
        c["elec_price_per_kwh"], c["elec_status"] = float(m.group(1)), "per_kwh"
    elif "台電" in et or "臺電" in et:
        c["elec_status"] = "taipower"
    elif "含" in et or "電" in contain:
        c["elec_status"] = "included"
    c["notes_text"] = "；".join(x for x in [row.get("fee_mentions", ""), row.get("deposit_text", "")] if x)
    return {k: v for k, v in c.items() if v not in (None, "")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True); ap.add_argument("--area", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--detail591")
    a = ap.parse_args()
    items = json.loads(Path(a.input).read_text(encoding="utf-8"))
    area = json.loads(Path(a.area).read_text(encoding="utf-8"))
    d591 = {r["listing_id"]: r for r in load_csv(a.detail591)} if a.detail591 and Path(a.detail591).exists() else {}
    default = area["targets"][0] if area.get("targets") else {}
    dest = (area.get("destination") or {}).get("label")
    rows = []
    for i, it in enumerate(items, 1):
        c = {}
        if it.get("listing_591_id") and str(it["listing_591_id"]) in d591:
            c.update(from_591(d591[str(it["listing_591_id"])]))
        c.update({k: v for k, v in it.items() if v not in (None, "")})  # 使用者說的優先
        c.setdefault("listing_id", f"L{i}")
        c.setdefault("label", c["listing_id"])
        c.setdefault("city", default.get("city")); c.setdefault("district", default.get("district"))
        c["city"] = str(c["city"] or "").replace("台", "臺")
        c["area_key"] = f"{c['city']}|{c['district']}"
        match = [t for t in area.get("targets", []) if t["area_key"] == c["area_key"]]
        c.setdefault("area_source", match[0]["area_source"] if match else "user_explicit")
        c.setdefault("price_basis", "user_stated")
        c.setdefault("area_basis", "user" if c.get("area_ping") else "unstated")
        for k in COSTS:
            c.setdefault(f"{k}_status", "stated" if c.get(f"{k}_fee") not in (None, "") else "unstated")
        c.setdefault("elec_status", "per_kwh" if c.get("elec_price_per_kwh") not in (None, "") else "unstated")
        c.setdefault("destination_label", dest)
        c.setdefault("source_type", "unknown")
        c.setdefault("commute_fare_per_trip", None)
        missing = [k for k in ("rent_monthly",) if c.get(k) in (None, "")]
        c["status"] = "incomplete" if missing else "ok"
        c["status_reason"] = "缺少月租（RT10）" if missing else ""
        rows.append(c)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "01_candidates.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(json.dumps([{k: r.get(k) for k in ("listing_id", "area_key", "rent_monthly", "status")} for r in rows],
                     ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
