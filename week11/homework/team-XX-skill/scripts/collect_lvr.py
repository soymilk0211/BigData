#!/usr/bin/env python3
"""collect_lvr.py — 取得並正規化內政部實價登錄「不動產租賃」資料（collector 使用）。

用法：
  python scripts/collect_lvr.py --area <run>/01_area.json --out <run> [--offline] [--cache data/lvr-cache]
  python scripts/collect_lvr.py --build-sample --cache <dir> --out sample-data/lvr_rent_sample_areas.csv

流程：依 01_area.json 的目標縣市代碼，逐季下載官方 zip（重試 3 次、TLS 1.2），只取
<代碼>_lvr_land_c.csv；下載失敗就改用 sample-data（data_mode = offline_sample）。
正規化規則見 references/field-mapping.md 與 references/cleaning-rules.md。
輸出：01_collected.csv（目標區）、01_collected_city.csv（整個縣市，供 city_wide 退回）、
01_collect_manifest.json。門牌欄只取雜湊後刪除；備註中的門牌樣式先遮蔽。
"""
import argparse, csv, datetime as dt, hashlib, io, json, re, ssl, sys, time, urllib.request, zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TZ = dt.timezone(dt.timedelta(hours=8))
URL = "https://plvr.land.moi.gov.tw/DownloadSeason?season={s}&type=zip&fileName=lvr_landcsv.zip"
EN_ROW2 = "The villages and towns urban district"
SCHEMA = ["鄉鎮市區", "交易標的", "土地位置建物門牌", "土地面積平方公尺", "都市土地使用分區", "非都市土地使用分區",
          "非都市土地使用編定", "租賃年月日", "租賃筆棟數", "租賃層次", "總樓層數", "建物型態", "主要用途", "主要建材",
          "建築完成年月", "建物總面積平方公尺", "建物現況格局-房", "建物現況格局-廳", "建物現況格局-衛",
          "建物現況格局-隔間", "有無管理組織", "有無附傢俱", "總額元", "單價元平方公尺", "車位類別",
          "車位面積平方公尺", "車位總額元", "備註", "編號", "出租型態", "有無管理員", "租賃期間", "有無電梯",
          "附屬設備", "租賃住宅服務"]
ADDR = "土地位置建物門牌"
TYPE_GROUP = {"獨立套房": "student_suite", "分租套房": "student_suite", "分租雅房": "student_room",
              "整棟(戶)出租": "whole_unit", "分層出租": "whole_unit"}
CN = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
PII_MASK = re.compile(r"[\u4e00-\u9fff]{0,3}\s*[A-Z][12]\d{8}|(?<![\d.])0\d{1,3}-?\d{3,4}-?\d{3,4}(?![\d.])")  # 身分證字號（含前面姓名）、電話
ADDR_MASK = re.compile(r"[^\s，,。；;]{0,10}(路|街|大道)[^\s，,。；;]{0,8}?(段|巷|弄|號)[^\s，,。；;]{0,6}|"
                       r"[^\s，,。；;]{0,8}\d+\s*號[^\s，,。；;]{0,4}|車位編號\s*[\w-]+")

OUT_COLS = ["record_id", "season", "city_code", "city", "district", "area_key", "target_type", "rent_date",
            "building_type", "main_use", "rent_type", "rent_type_group", "floor", "floor_whole", "total_floors",
            "area_m2", "parking_area_m2", "area_ping", "rent_total", "parking_rent", "rent_excl_parking",
            "unit_price_m2_raw", "rent_per_ping", "rooms", "halls", "baths", "partition", "has_mgmt_org",
            "has_manager", "has_elevator", "has_furniture", "build_completed", "building_age_years", "lease_start",
            "lease_end", "lease_months", "equipment", "equipment_count", "rental_service", "is_social_housing",
            "mgmt_fee_status", "mgmt_fee_amount", "mgmt_fee_with_parking", "note_tags", "note_raw",
            "parcel_counts_raw", "addr_hash", "date_invalid"]


def load_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(p, rows, cols):
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def num(s):
    s = str(s or "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def roc_date(s):
    s = str(s or "").strip()
    if not re.fullmatch(r"\d{6,7}", s):
        return None
    s = s.zfill(7)
    try:
        return dt.date(int(s[:3]) + 1911, int(s[3:5]), int(s[5:7]))
    except ValueError:
        return None


def cn_int(s):
    """「十二層」→12；「二十一層」→21；「全」「整棟租賃」→None。"""
    s = str(s or "").split("、")[0].replace("層", "").strip()
    if not s or "地下" in s:
        return None
    if s.isdigit():
        return int(s)
    if "十" in s:
        a, _, b = s.partition("十")
        return (CN.get(a, 1) if a else 1) * 10 + (CN.get(b, 0) if b else 0)
    return CN.get(s)


def yesno(s):
    return {"有": True, "無": False}.get(str(s or "").strip())


def parse_mgmt(note):
    """references/cleaning-rules.md 8.2：依序比對，命中即停。"""
    if "管理費" not in note:
        return "not_mentioned", None, False
    if re.search(r"(?<!不)含管理費", note):
        return "included", 0, False
    m = re.search(r"管理費[^。；;]{0,20}?由出租人負擔", note)
    if m:
        return "landlord_pays", 0, False
    m = re.search(r"管理費\D{0,8}(\d[\d,]{2,5})\s*元?", note)
    if m and re.search(r"承租人負擔|承租人自付|不包含在租金|未計入租金|另有|另計", note):
        return "extra", int(m.group(1).replace(",", "")), "停車位管理費" in note
    return "unknown", None, False


def note_tags(note):
    tags = []
    for word, tag in [("續租案件", "RENEWAL"), ("多人共同承租", "MULTI_TENANT"), ("含稅", "TAX_INCLUDED"),
                      ("約定不同租金", "STEP_RENT"), ("免租", "RENT_FREE_PERIOD")]:
        if word in note:
            tags.append(tag)
    return ";".join(tags)


def normalize(raw, season, code, city):
    rd = roc_date(raw["租賃年月日"])
    area_m2 = num(raw["建物總面積平方公尺"]) or 0.0
    park_m2 = num(raw["車位面積平方公尺"]) or 0.0
    area_ping = round((area_m2 - park_m2) * 0.3025, 2)
    total = int(num(raw["總額元"]) or 0)
    park = int(num(raw["車位總額元"]) or 0)
    excl = total - park
    bc = roc_date(raw["建築完成年月"])
    lease = str(raw["租賃期間"] or "").split("~")
    ls, le = (roc_date(lease[0]), roc_date(lease[1])) if len(lease) == 2 else (None, None)
    note = ADDR_MASK.sub("〔遮蔽〕", PII_MASK.sub("〔遮蔽〕", raw["備註"] or ""))
    status, amount, with_park = parse_mgmt(raw["備註"] or "")
    service = raw["租賃住宅服務"] or ""
    addr_hash = raw.get("addr_hash") or hashlib.sha256((raw.get(ADDR) or "").encode()).hexdigest()[:12]
    floor_raw = raw["租賃層次"] or ""
    eq = [x for x in (raw["附屬設備"] or "").split("、") if x]
    return {
        "record_id": raw["編號"], "season": season, "city_code": code, "city": city, "district": raw["鄉鎮市區"],
        "area_key": f"{city}|{raw['鄉鎮市區']}", "target_type": raw["交易標的"],
        "rent_date": rd.isoformat() if rd else "", "building_type": raw["建物型態"], "main_use": raw["主要用途"],
        "rent_type": raw["出租型態"], "rent_type_group": TYPE_GROUP.get(raw["出租型態"], "other" if raw["出租型態"] else "unknown"),
        "floor": cn_int(floor_raw), "floor_whole": floor_raw in ("全", "整棟租賃"), "total_floors": cn_int(raw["總樓層數"]),
        "area_m2": area_m2, "parking_area_m2": park_m2, "area_ping": area_ping, "rent_total": total,
        "parking_rent": park, "rent_excl_parking": excl, "unit_price_m2_raw": num(raw["單價元平方公尺"]),
        "rent_per_ping": round(excl / area_ping, 1) if area_ping > 0 else "",
        "rooms": num(raw["建物現況格局-房"]), "halls": num(raw["建物現況格局-廳"]), "baths": num(raw["建物現況格局-衛"]),
        "partition": yesno(raw["建物現況格局-隔間"]), "has_mgmt_org": yesno(raw["有無管理組織"]),
        "has_manager": yesno(raw["有無管理員"]), "has_elevator": yesno(raw["有無電梯"]),
        "has_furniture": yesno(raw["有無附傢俱"]), "build_completed": bc.isoformat() if bc else "",
        "building_age_years": round((rd - bc).days / 365.25, 1) if rd and bc else "",
        "lease_start": ls.isoformat() if ls else "", "lease_end": le.isoformat() if le else "",
        "lease_months": round((le - ls).days / 30.44) if ls and le else "",
        "equipment": "、".join(eq), "equipment_count": len(eq), "rental_service": service,
        "is_social_housing": service.startswith("社會住宅") or "社會住宅" in (raw["備註"] or ""),
        "mgmt_fee_status": status, "mgmt_fee_amount": amount if amount is not None else "",
        "mgmt_fee_with_parking": with_park, "note_tags": note_tags(raw["備註"] or ""), "note_raw": note,
        "parcel_counts_raw": raw["租賃筆棟數"], "addr_hash": addr_hash, "date_invalid": rd is None,
    }


def read_county_csv(text):
    """CR-01、CR-02：跳過第 2 列英文表頭；欄名不符就停止（E3）。"""
    rows = list(csv.reader(io.StringIO(text)))
    header, warn = rows[0], []
    if header != SCHEMA:
        missing = [c for c in SCHEMA if c not in header]
        extra = [c for c in header if c not in SCHEMA]
        raise ValueError(f"E3 欄名與 schema 不符：缺 {missing}，多 {extra}")
    body = rows[1:]
    if body and body[0] and body[0][0] == EN_ROW2:
        body = body[1:]
    else:
        warn.append("E4 第 2 列不是英文表頭，未跳列")
    return [dict(zip(header, r)) for r in body if len(r) == len(header)], warn


def download(season, cache):
    """E1／E2：重試 3 次、指數退避、TLS 1.2；檢查檔頭 PK。"""
    path = cache / f"{season}.zip"
    if path.exists() and path.read_bytes()[:2] == b"PK":
        return path, "cache"
    ctx = ssl.create_default_context()
    ctx.minimum_version = ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(URL.format(s=season), timeout=300, context=ctx) as r:
                if r.status != 200:
                    raise IOError(f"HTTP {r.status}")
                data = r.read()
            if data[:2] != b"PK":
                raise IOError("下載內容不是 zip")
            cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return path, "downloaded"
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * 2 ** i)
    raise IOError(f"{season} 下載失敗：{last}")


def load_online(seasons, codes, cache, man):
    out = {}
    for s in seasons:
        path, how = download(s, cache)
        raw = path.read_bytes()
        man["downloads"].append({"season": s, "url": URL.format(s=s), "bytes": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest(), "how": how,
                                 "fetched_at": dt.datetime.now(TZ).isoformat(timespec="seconds")})
        with zipfile.ZipFile(path) as z:
            mf = list(csv.DictReader(io.StringIO(z.read("manifest.csv").decode("utf-8-sig"))))
            have = {m["name"][0] for m in mf if m["name"].endswith("_lvr_land_c.csv")}
            for c in codes:
                if c not in have:
                    raise ValueError(f"E19 {s} 沒有代碼 {c} 的租賃檔")
                text = z.read(f"{c}_lvr_land_c.csv").decode("utf-8-sig")
                rows, warn = read_county_csv(text)
                man["warnings"] += [f"{s}/{c}: {w}" for w in warn]
                out[(s, c)] = rows
    return out


def load_offline(seasons, codes, man):
    sample = SKILL / "sample-data/lvr_rent_sample_areas.csv"
    out = {}
    for r in load_csv(sample):
        if r["season"] in seasons and r["city_code"] in codes:
            out.setdefault((r["season"], r["city_code"]), []).append(r)
    man["downloads"].append({"source": "sample-data/lvr_rent_sample_areas.csv",
                             "sha256": hashlib.sha256(sample.read_bytes()).hexdigest()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--area"); ap.add_argument("--out", required=True)
    ap.add_argument("--offline", action="store_true"); ap.add_argument("--cache", default="data/lvr-cache")
    ap.add_argument("--build-sample", action="store_true")
    a = ap.parse_args()
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    seasons = params["seasons_current"]["value"] + [params["season_trend"]["value"]]
    counties = {r["city_code"]: r["city"] for r in load_csv(SKILL / "references/county-codes.csv") if r["rent_file"]}

    if a.build_sample:  # 維護者用：從快取 zip 產生離線樣本（已刪門牌、備註遮蔽）
        targets = [("h", "龜山區"), ("f", "林口區"), ("b", "西屯區")]
        man = {"downloads": [], "warnings": []}
        data = load_online(seasons, sorted({c for c, _ in targets}), Path(a.cache), man)
        rows = []
        for (s, c), recs in data.items():
            for r in recs:
                if (c, r["鄉鎮市區"]) in targets:
                    r = dict(r)
                    r["addr_hash"] = hashlib.sha256(r[ADDR].encode()).hexdigest()[:12]
                    r[ADDR] = ""
                    r["備註"] = ADDR_MASK.sub("〔遮蔽〕", PII_MASK.sub("〔遮蔽〕", r["備註"]))
                    rows.append({"season": s, "city_code": c, **r})
        write_csv(a.out, rows, ["season", "city_code"] + SCHEMA + ["addr_hash"])
        print(json.dumps({"rows": len(rows), "downloads": man["downloads"]}, ensure_ascii=False))
        return 0

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    area = json.loads(Path(a.area).read_text(encoding="utf-8"))
    targets = area["targets"]
    codes = sorted({t["city_code"] for t in targets})
    man = {"data_mode": "offline_sample" if a.offline else "online", "seasons": seasons,
           "county_files": [{"city_code": c, "city": counties.get(c), "file": f"{c}_lvr_land_c.csv"} for c in codes],
           "downloads": [], "row_counts": {}, "dropped_columns": [ADDR], "warnings": [], "errors": []}
    missing = [c for c in codes if c not in counties]
    if missing:
        man["errors"].append(f"E19 實價登錄沒有這些縣市的租賃批次資料：{missing}")
        (out / "01_collect_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "no_rent_data", "errors": man["errors"]}, ensure_ascii=False))
        return 3
    try:
        data = load_offline(seasons, codes, man) if a.offline else load_online(seasons, codes, Path(a.cache), man)
    except ValueError as e:  # E3：schema 改版，不猜
        man["errors"].append(str(e))
        (out / "01_collect_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "schema_error", "errors": man["errors"]}, ensure_ascii=False))
        return 4
    except Exception as e:  # noqa: BLE001  RT9：改用 sample-data
        man["warnings"].append(f"RT9 官方下載失敗，改用 sample-data：{e}")
        man["data_mode"] = "offline_sample"
        man["downloads"] = []
        data = load_offline(seasons, codes, man)

    keys = {t["area_key"] for t in targets}
    collected, city_rows = [], []
    for (s, c), recs in sorted(data.items()):
        for r in recs:
            n = normalize(r, s, c, counties[c])
            city_rows.append(n)
            if n["area_key"] in keys:
                collected.append(n)
            man["row_counts"].setdefault(s, {}).setdefault(n["area_key"], 0)
            man["row_counts"][s][n["area_key"]] += 1
        man["row_counts"].setdefault(s, {})[f"{counties[c]}|(全市)"] = len(recs)
    for k in keys:
        if not any(r["area_key"] == k for r in collected):
            man["errors" if man["data_mode"] == "offline_sample" else "warnings"].append(
                f"{'E21 離線樣本沒有' if man['data_mode'] == 'offline_sample' else 'E17 五季內沒有'} {k} 的租賃案件")
    write_csv(out / "01_collected.csv", collected, OUT_COLS)
    write_csv(out / "01_collected_city.csv", city_rows, OUT_COLS)
    man["rows_collected"], man["rows_city"] = len(collected), len(city_rows)
    (out / "01_collect_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "data_mode": man["data_mode"], "rows_collected": len(collected),
                      "rows_city": len(city_rows), "warnings": man["warnings"], "errors": man["errors"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
