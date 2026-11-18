#!/usr/bin/env python3
"""crawl_591.py — 取得 591 租屋網的刊登資料（刊登租金與物件細節），只保存去識別化欄位。

取得方式參考 Rent591Watcher（https://github.com/ryk001/Rent591Watcher，無授權條款，
本檔只參考其「先取 session、再讀列表頁與刊登頁」的流程，程式碼為獨立撰寫）。

用法：
  python scripts/crawl_591.py area --city 桃園市 --district 龜山區 --out <dir> [--detail-cap 300]
  python scripts/crawl_591.py ids  --ids 22081529 22354664 --out <dir>
  python scripts/crawl_591.py paste --file listing.txt --out <dir>
  python scripts/crawl_591.py fetch --city 桃園市 --district 龜山區 --out <run>
      （collector 用：sample-data/591/ 有 30 天內的快照就複製，否則即時爬取；結果附加到 <run>/591_*.csv）

輸出（UTF-8 with BOM CSV）：
  591_list.csv    列表層級：每筆刊登的刊登租金、類型、使用坪數、區、標籤、刊登身分
  591_detail.csv  刊登頁層級：押金、管理費、水電瓦斯網路計價、踩雷關鍵字命中
  591_manifest.json  取得時間、請求數、筆數、略過原因

隱私：姓名、電話、LINE、Email、門牌、經緯度、原始網頁一律不寫入任何檔案。
需要 node（解析頁面內嵌的 __NUXT__ 資料）。
"""
import argparse, csv, datetime as dt, json, random, re, subprocess, sys, time
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
BASE = "https://rent.591.com.tw"
SKILL = Path(__file__).resolve().parent.parent
TZ = dt.timezone(dt.timedelta(hours=8))
KIND_GROUP = {2: "student_suite", 3: "student_suite", 4: "student_room", 1: "whole_unit"}
STUDENT_KINDS = (2, 3, 4)

NUXT_JS = r"""
const fs=require('fs'),vm=require('vm');
const t=fs.readFileSync(0,'utf8');
const m=t.match(/<script>window\.__NUXT__=([\s\S]*?)<\/script>/);
if(!m){process.stdout.write('null');process.exit(0);}
const ctx={window:{}};vm.createContext(ctx);
vm.runInContext('window.__NUXT__='+m[1],ctx);
process.stdout.write(JSON.stringify(ctx.window.__NUXT__));
"""

# 踩雷關鍵字（與 references/risk-signals.md R3 同步）
RISK_WORDS = ["先匯訂金", "先轉帳", "未看房先付", "不能看房", "不可看房", "不給收據", "不能報稅", "不可報稅",
              "不能入籍", "不可入籍", "不能申請租金補貼", "不可租補", "不可申請租補", "頂樓加蓋", "頂加",
              "鐵皮", "違建", "二房東", "轉租"]
FEE_RE = re.compile(r"[^。！!；;\n<>]{0,25}(水費|電費|每度|台電|網路|瓦斯|管理費|清潔費)[^。！!；;\n<>]{0,25}")
MASK_RES = [re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}"), re.compile(r"0\d{1,2}[-\s]?\d{6,8}"),
            re.compile(r"(?i)line\s*(id)?\s*[:：]?\s*@?[\w.\-]+"), re.compile(r"@[\w.\-]{3,}"),
            re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
            re.compile(r"[^\s，,。]{1,8}(路|街|大道)[^\s，,。]{0,6}(段|巷|弄|號)")]
CN_NUM = {"半": 0.5, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6}


class Polite:
    """單一 session、每次請求間隔隨機 1–3 秒、請求數上限。"""

    def __init__(self, max_requests):
        self.s = requests.Session()
        self.s.headers["user-agent"] = UA
        self.n = 0
        self.max = max_requests

    def get(self, url):
        if self.n >= self.max:
            raise RuntimeError(f"已達請求上限 {self.max}")
        if self.n:
            time.sleep(random.uniform(1, 3))
        self.n += 1
        r = self.s.get(url, timeout=30)
        r.raise_for_status()
        return r.text


def nuxt(html):
    out = subprocess.run(["node", "-e", NUXT_JS], input=html, capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout or "null")


def mask(text):
    for rx in MASK_RES:
        text = rx.sub("〔已遮蔽〕", text)
    return text


def ping(s):
    m = re.search(r"([\d.]+)\s*坪", str(s or ""))
    return float(m.group(1)) if m else None


def money(s):
    m = re.search(r"(\d[\d,]*)", str(s or ""))
    return int(m.group(1).replace(",", "")) if m else None


def role_only(role_name):
    """「代理人李先生」→「代理人」：只保留身分，去掉姓名。"""
    for r in ("屋主", "代理人", "仲介", "房東", "二房東", "經紀人"):
        if str(role_name or "").startswith(r):
            return r
    return "其他" if role_name else ""


def deposit_months(text, rent):
    t = str(text or "")
    m = re.search(r"([半一二兩三四五六\d.]+)\s*個?月", t)
    if m:
        v = m.group(1)
        return float(v) if re.match(r"^[\d.]+$", v) else CN_NUM.get(v)
    amt = money(t)
    if amt and rent:
        return round(amt / rent, 2)
    return None


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, cols):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


LIST_COLS = ["listing_id", "city", "district", "area_key", "kind", "kind_name", "rent_type_group", "asking_rent",
             "use_area_ping", "floor_name", "role", "tags", "social_house", "refresh_time", "source_url", "crawled_at"]
DETAIL_COLS = ["listing_id", "city", "district", "area_key", "kind_name", "rent_type_group", "asking_rent",
               "use_area_ping", "floor", "shape", "role", "deposit_text", "deposit_months", "service_fee",
               "mgmt_fee_text", "mgmt_fee", "water_fee_type", "water_fee", "electric_fee_type", "electric_fee",
               "price_contain_text", "extra_fee_text", "net_included", "gas_facility", "has_certificate", "tags",
               "rent_subsidy_ok", "tax_ok", "posted_date", "end_date", "status", "risk_hits", "fee_mentions",
               "price_basis", "source_url", "crawled_at"]


def list_row(it, city, district, now):
    kind = it.get("kind")
    tags = it.get("tags") or []
    tags = [t["name"] if isinstance(t, dict) else str(t) for t in tags]
    return {"listing_id": it["id"], "city": city, "district": district, "area_key": f"{city}|{district}",
            "kind": kind, "kind_name": it.get("kind_name", ""), "rent_type_group": KIND_GROUP.get(kind, "other"),
            "asking_rent": money(it.get("price")), "use_area_ping": ping(it.get("area_name") or it.get("area")),
            "floor_name": it.get("floor_name", ""), "role": role_only(it.get("role_name")),
            "tags": ";".join(tags), "social_house": it.get("social_house", ""),
            "refresh_time": it.get("refresh_time", ""), "source_url": f"{BASE}/{it['id']}", "crawled_at": now}


def detail_row(lid, d, now):
    info = {x.get("key"): x.get("value") for x in d.get("info", [])}
    cost = {x.get("key"): x.get("value") for x in (d.get("costData") or {}).get("data", [])}
    rc = d.get("rent_calculation_data") or {}
    fac = {x.get("key"): x.get("active") for x in (d.get("service") or {}).get("facility", [])}
    infod = {x.get("key"): x.get("value") for x in (d.get("infoData") or {}).get("data", [])}
    crumbs = d.get("breadcrumb") or []
    city = (crumbs[0]["name"] if crumbs else "").replace("台", "臺")
    district = crumbs[1]["name"] if len(crumbs) > 1 else ""
    tags = [t.get("value", "") for t in d.get("tags", [])]
    remark = re.sub(r"<[^>]+>|&nbsp;", " ", (d.get("remark") or {}).get("content", ""))
    rent = rc.get("rent_price") or money(d.get("price"))
    fav = d.get("favData") or {}
    posted = dt.datetime.fromtimestamp(fav["posttime"], TZ).date().isoformat() if fav.get("posttime") else ""
    hits = sorted({w for w in RISK_WORDS if w in remark})
    fees = [mask(m.group(0).strip()) for m in FEE_RE.finditer(remark)][:5]
    kind = d.get("kind")
    return {"listing_id": lid, "city": city, "district": district, "area_key": f"{city}|{district}",
            "kind_name": info.get("kind", ""), "rent_type_group": KIND_GROUP.get(kind, "other"),
            "asking_rent": rent, "use_area_ping": ping(info.get("area")), "floor": info.get("floor", ""),
            "shape": info.get("shape", ""), "role": role_only((d.get("linkInfo") or {}).get("roleName")),
            "deposit_text": rc.get("deposit") or d.get("deposit", ""),
            "deposit_months": deposit_months(rc.get("deposit") or d.get("deposit"), rent),
            "service_fee": rc.get("service_fee", ""), "mgmt_fee_text": rc.get("manage_fee_text") or cost.get("manageprice", ""),
            "mgmt_fee": rc.get("manage_fee") if rc.get("manage_fee") else None,
            "water_fee_type": rc.get("water_fee_type", ""), "water_fee": rc.get("water_fee") or None,
            "electric_fee_type": rc.get("electric_fee_type", ""), "electric_fee": rc.get("electric_fee") or None,
            "price_contain_text": rc.get("price_contain_text") or cost.get("priceContainText", ""),
            "extra_fee_text": d.get("extra_fee_text", ""), "net_included": fac.get("net", ""),
            "gas_facility": fac.get("gas", ""), "has_certificate": infod.get("hasCertificate", ""),
            "tags": ";".join(tags), "rent_subsidy_ok": int("租金補貼" in tags), "tax_ok": int("可報稅" in tags),
            "posted_date": posted, "end_date": d.get("endTime", ""), "status": d.get("status", ""),
            "risk_hits": ";".join(hits), "fee_mentions": " | ".join(fees), "price_basis": "asking",
            "source_url": f"{BASE}/{lid}", "crawled_at": now}


def find_section(client, region, district, max_pages=20):
    for page in range(1, max_pages + 1):
        data = nuxt(client.get(f"{BASE}/list?region={region}&sort=posttime_desc&page={page}"))
        for it in data["pinia"]["rent-list"]["dataList"]:
            if str(it.get("address", "")).split("-")[0] == district and it.get("sectionid"):
                return it["sectionid"]
    return None


def fetch_detail(client, lid):
    data = nuxt(client.get(f"{BASE}/{lid}"))
    for v in (data or {}).get("data", {}).values():
        if isinstance(v, dict) and isinstance(v.get("data"), dict) and "rent_calculation_data" in v["data"]:
            return v["data"]
    return None


def cmd_area(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(TZ).isoformat(timespec="seconds")
    regions = {r["city"]: r["region_id"] for r in load_csv(SKILL / "references/591-regions.csv")}
    sections = {(r["city"], r["district"]): r["section_id"] for r in load_csv(SKILL / "references/591-sections.csv")}
    city = a.city.replace("台", "臺")
    man = {"mode": "area", "city": city, "district": a.district, "started_at": now, "errors": [],
           "source": "591 租屋網（刊登租金，非成交價）", "reference": "https://github.com/ryk001/Rent591Watcher"}
    client = Polite(a.max_requests)
    rows, details = [], []
    try:
        if city not in regions:
            raise RuntimeError(f"591 沒有 {city} 的地區代碼")
        client.get(BASE + "/")  # 先取 session cookie（同 Rent591Watcher 的作法）
        sec = sections.get((city, a.district)) or find_section(client, regions[city], a.district)
        if not sec:
            raise RuntimeError(f"在 591 找不到 {city}{a.district} 的 section")
        man["region_id"], man["section_id"] = regions[city], sec
        page, total = 1, None
        while True:
            data = nuxt(client.get(f"{BASE}/list?region={regions[city]}&section={sec}&sort=posttime_desc&page={page}"))
            store = data["pinia"]["rent-list"]
            total = store.get("total", 0)
            items = store.get("dataList") or []
            rows += [list_row(it, city, a.district, now) for it in items
                     if str(it.get("address", "")).split("-")[0] == a.district]
            if not items or page * 30 >= total or page >= a.max_pages:
                break
            page += 1
        man["listing_total_on_site"] = total
        seen, uniq = set(), []
        for r in rows:
            if r["listing_id"] not in seen:
                seen.add(r["listing_id"]); uniq.append(r)
        rows = uniq
        pick = [r for r in rows if r["kind"] in STUDENT_KINDS][: a.detail_cap]
        for r in pick:
            try:
                d = fetch_detail(client, r["listing_id"])
                if d:
                    details.append(detail_row(r["listing_id"], d, now))
            except Exception as e:  # 單筆失敗不中斷
                man["errors"].append(f"{r['listing_id']}: {type(e).__name__}")
    except Exception as e:
        man["errors"].append(f"{type(e).__name__}: {e}")
    man.update({"requests": client.n, "list_rows": len(rows), "detail_rows": len(details),
                "finished_at": dt.datetime.now(TZ).isoformat(timespec="seconds"),
                "status": "ok" if rows else "failed"})
    write_csv(out / "591_list.csv", rows, LIST_COLS)
    write_csv(out / "591_detail.csv", details, DETAIL_COLS)
    (out / "591_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: man[k] for k in ("status", "requests", "list_rows", "detail_rows", "errors")}, ensure_ascii=False))
    return 0 if rows else 2


def cmd_ids(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(TZ).isoformat(timespec="seconds")
    client = Polite(a.max_requests)
    details, errors = [], []
    ids = [re.sub(r"\D", "", x.rstrip("/").split("/")[-1]) for x in a.ids]
    try:
        client.get(BASE + "/")
        for lid in ids:
            try:
                d = fetch_detail(client, lid)
                if d:
                    details.append(detail_row(lid, d, now))
                else:
                    errors.append(f"{lid}: 頁面沒有刊登資料（可能已下架）")
            except Exception as e:
                errors.append(f"{lid}: {type(e).__name__}")
    except Exception as e:
        errors.append(f"{type(e).__name__}: {e}")
    write_csv(out / "591_detail.csv", details, DETAIL_COLS)
    man = {"mode": "ids", "requests": client.n, "detail_rows": len(details), "errors": errors, "crawled_at": now}
    (out / "591_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False))
    return 0 if details else 2


def cmd_paste(a):
    """使用者貼上的刊登文字 → 591_detail.csv 一列（抓不到的欄位留空＝未提供）。"""
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    text = Path(a.file).read_text(encoding="utf-8")
    now = dt.datetime.now(TZ).isoformat(timespec="seconds")
    rent = money(re.search(r"(\d[\d,]{2,})\s*元\s*/\s*月", text).group(1)) if re.search(r"(\d[\d,]{2,})\s*元\s*/\s*月", text) else None
    dep = re.search(r"押金[：:\s]*([^\n，,。]{1,12})", text)
    mg = re.search(r"管理費[：:\s]*([^\n，,。]{1,12})", text)
    row = {"listing_id": "PASTE1", "asking_rent": rent, "use_area_ping": ping(text),
           "deposit_text": dep.group(1) if dep else "", "deposit_months": deposit_months(dep.group(1), rent) if dep else None,
           "mgmt_fee_text": mg.group(1) if mg else "", "mgmt_fee": money(mg.group(1)) if mg else None,
           "risk_hits": ";".join(sorted({w for w in RISK_WORDS if w in text})),
           "fee_mentions": " | ".join(mask(m.group(0).strip()) for m in FEE_RE.finditer(text)),
           "price_basis": "asking", "crawled_at": now}
    write_csv(out / "591_detail.csv", [row], DETAIL_COLS)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def append_csv(src, dst):
    rows = load_csv(src) if Path(src).exists() else []
    old = load_csv(dst) if Path(dst).exists() else []
    cols = DETAIL_COLS if Path(dst).name == "591_detail.csv" else LIST_COLS
    write_csv(dst, old + rows, cols)
    return len(rows)


def cmd_fetch(a):
    """有新鮮快照用快照（測試不依賴即時 591），否則即時爬取；兩者都記錄在 <run>/591_sources.json。"""
    run = Path(a.out); run.mkdir(parents=True, exist_ok=True)
    city = a.city.replace("台", "臺")
    params = json.loads((SKILL / "references/cost-params.json").read_text(encoding="utf-8"))
    max_age = params["snapshot_max_age_days"]["value"]
    snap = SKILL / "sample-data/591" / f"{city}_{a.district}"
    src = {"area_key": f"{city}|{a.district}"}
    man = snap / "591_manifest.json"
    age = None
    if man.exists():
        crawled = dt.datetime.fromisoformat(json.loads(man.read_text(encoding="utf-8"))["started_at"])
        age = (dt.datetime.now(TZ) - crawled).days
    if age is not None and age <= max_age and not a.live:
        src.update({"mode": "snapshot", "path": f"sample-data/591/{snap.name}", "age_days": age})
        folder = snap
    else:
        folder = run / "591_live" / f"{city}_{a.district}"
        ns = argparse.Namespace(city=city, district=a.district, out=str(folder), detail_cap=a.detail_cap,
                                max_pages=200, max_requests=a.detail_cap + 250)
        rc = cmd_area(ns)
        src.update({"mode": "live", "path": str(folder.relative_to(run)), "status": "ok" if rc == 0 else "failed"})
    src["list_rows"] = append_csv(folder / "591_list.csv", run / "591_list.csv")
    src["detail_rows"] = append_csv(folder / "591_detail.csv", run / "591_detail.csv")
    sp = run / "591_sources.json"
    allsrc = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else []
    sp.write_text(json.dumps(allsrc + [src], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(src, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("area"); s.add_argument("--city", required=True); s.add_argument("--district", required=True)
    s.add_argument("--detail-cap", type=int, default=300); s.add_argument("--max-pages", type=int, default=200)
    s.add_argument("--max-requests", type=int, default=600); s.add_argument("--out", required=True)
    s = sub.add_parser("ids"); s.add_argument("--ids", nargs="+", required=True)
    s.add_argument("--max-requests", type=int, default=20); s.add_argument("--out", required=True)
    s = sub.add_parser("paste"); s.add_argument("--file", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("fetch"); s.add_argument("--city", required=True); s.add_argument("--district", required=True)
    s.add_argument("--out", required=True); s.add_argument("--detail-cap", type=int, default=300)
    s.add_argument("--live", action="store_true", help="忽略快照，強制即時爬取")
    a = p.parse_args()
    sys.exit({"area": cmd_area, "ids": cmd_ids, "paste": cmd_paste, "fetch": cmd_fetch}[a.cmd](a))


if __name__ == "__main__":
    main()
