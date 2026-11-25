#!/usr/bin/env python3
"""resolve_area.py — 由使用者訊息決定目標地區，寫出 01_area.json（collector 使用）。

用法：
  python scripts/resolve_area.py --text "<使用者訊息>" --out <run>/01_area.json [--confirmed 臺中市|東區 ...]

規則（第一個得到唯一結果的步驟就採用；不呼叫地圖、不猜）：
  1 縣市＋區       → user_explicit
  2 只有區名       → 只有一個縣市有就 user_explicit，否則有歧義
  3 學校名稱／簡稱 → references/school-districts.csv 唯一命中就 school_lookup；多校區＝有歧義
  4 地址字串       → 抓得出「縣市＋區」且存在才 address_parse
  5 都沒有         → 缺少
--confirmed 用於互動模式追問後，使用者確認的地區（user_confirmed）。
"""
import argparse, csv, json, re, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SUFFIX = ("區", "鄉", "鎮", "市")


def load_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def norm(text):
    return re.sub(r"\s+", "", text.replace("台", "臺"))


def city_aliases(city):
    base = city[:-1]
    return {city, base} if len(base) >= 2 else {city}


def district_aliases(d):
    base = d[:-1] if d.endswith(SUFFIX) else d
    return {d, base} if len(base) >= 2 else {d}


def longest_matches(text, alias_map):
    """回傳不重疊、取最長的命中：[(alias, key)]。"""
    hits = []
    for alias, keys in alias_map.items():
        for m in re.finditer(re.escape(alias), text):
            hits.append((m.start(), m.end(), alias, keys))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, end = [], -1
    for s, e, alias, keys in sorted(hits, key=lambda h: -(h[1] - h[0])):
        if all(e <= s2 or s >= e2 for s2, e2, *_ in out):
            out.append((s, e, alias, keys))
    return sorted(out)


def target(row, source, matched):
    return {"city": row["city"], "city_code": row["city_code"], "district": row["district"],
            "area_key": f"{row['city']}|{row['district']}", "area_source": source, "matched_text": matched,
            "in_rent_data": row["in_rent_data"] == "true"}


def resolve(text, confirmed):
    districts = load_csv(SKILL / "references/districts.csv")
    schools = load_csv(SKILL / "references/school-districts.csv")
    t = norm(text)
    res = {"area_status": "unresolved", "targets": [], "destination": None, "ambiguities": [], "missing": [],
           "question": None, "district_quirk": None}
    by_key = {(d["city"], d["district"]): d for d in districts}

    if confirmed:
        for c in confirmed:
            city, _, dist = norm(c).partition("|")
            if (city, dist) in by_key:
                res["targets"].append(target(by_key[(city, dist)], "user_confirmed", c))

    # 學校（同時決定通勤目的地）
    school_alias = {}
    for s in schools:
        for a in [s["school_name"]] + [x for x in s["aliases"].split(";") if x]:
            school_alias.setdefault(norm(a), set()).add(s["school_name"])
    school_hits = longest_matches(t, school_alias)
    school_rows = []
    for _, _, alias, names in school_hits:
        rows = [s for s in schools if s["school_name"] in names]
        school_rows.append((alias, rows))
    if school_rows:
        alias, rows = school_rows[0]
        if len(rows) == 1:
            r = rows[0]
            res["destination"] = {"label": r["school_name"], "city": r["city"], "district": r["district"],
                                  "source": "school_lookup"}

    if not res["targets"]:
        # 步驟 1、2：縣市＋區、只有區名
        d_alias = {}
        for d in districts:
            if d["district"] == d["city"]:
                continue  # 新竹市、嘉義市不分區的資料列
            for a in district_aliases(d["district"]):
                d_alias.setdefault(a, []).append(d)
        cities = {d["city"] for d in districts}
        c_alias = {a: c for c in cities for a in city_aliases(c)}
        city_hits = {c_alias[a] for _, _, a, _ in longest_matches(t, {a: a for a in c_alias})}
        for s, e, alias, rows in longest_matches(t, d_alias):
            # 排除縣市名的一部分被當成區名（例：「臺中市」中的「中市」不存在，但「新竹市」≠「竹市」）
            cands = [r for r in rows if not city_hits or r["city"] in city_hits] or rows
            if len(cands) == 1:
                src = "user_explicit"
                res["targets"].append(target(cands[0], src, alias))
            else:
                res["ambiguities"].append({"matched_text": alias,
                                           "candidates": [f"{r['city']}{r['district']}" for r in cands]})

    if not res["targets"] and not res["ambiguities"]:
        # 步驟 3：學校
        if school_rows:
            alias, rows = school_rows[0]
            if len(rows) == 1:
                r = rows[0]
                row = by_key.get((r["city"], r["district"]))
                if row:
                    res["targets"].append(target(row, "school_lookup", alias))
            else:
                res["ambiguities"].append({"matched_text": alias,
                                           "candidates": [f"{r['school_name']}{r['campus']}（{r['city']}{r['district']}）" for r in rows]})
        else:
            # 步驟 4：地址
            m = re.search(r"(\S{2}[市縣])(\S{1,3}?[區鄉鎮市])", t)
            if m and (m.group(1), m.group(2)) in by_key:
                res["targets"].append(target(by_key[(m.group(1), m.group(2))], "address_parse", m.group(0)))

    # 去重
    seen, uniq = set(), []
    for x in res["targets"]:
        if x["area_key"] not in seen:
            seen.add(x["area_key"]); uniq.append(x)
    res["targets"] = uniq

    if res["targets"] and not res["ambiguities"]:
        res["area_status"] = "resolved"
        if not res["destination"] and len(res["targets"]) == 1 and school_rows == []:
            res["destination"] = None
        for x in res["targets"]:
            if x["city"] in ("新竹市", "嘉義市"):
                res["district_quirk"] = f"{x['city']} 的實價登錄租賃資料不分區，行情以全市計算（E20）"
            if not x["in_rent_data"]:
                x["note"] = "E17 該區五季內沒有租賃案件，行情改用全縣市（city_wide）"
    elif res["ambiguities"]:
        opts = "、".join(c for a in res["ambiguities"] for c in a["candidates"])
        res["question"] = f"你說的「{res['ambiguities'][0]['matched_text']}」是指哪一個？可選：{opts}。請補上縣市與區。"
    else:
        res["missing"] = ["city", "district"]
        res["question"] = "請告訴我要分析的地區（縣市＋區，例如「臺中市西屯區」），或學校名稱。"
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--confirmed", nargs="*", default=[])
    a = ap.parse_args()
    res = resolve(a.text, a.confirmed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"area_status": res["area_status"], "targets": [x["area_key"] for x in res["targets"]],
                      "destination": res["destination"], "question": res["question"]}, ensure_ascii=False))
    if res["area_status"] == "unresolved" and res.get("question"):
        print("地區還不能確定：" + res["question"], file=sys.stderr)
    elif res["area_status"] == "resolved" and res["targets"]:
        names = "、".join(x["area_key"].replace("|", "") for x in res["targets"])
        print("分析地區：" + names, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
