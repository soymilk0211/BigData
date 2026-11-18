# ① collector 蒐集員

你只負責**把資料備齊**：決定目標地區、取得實價登錄與 591 資料、把使用者說的候選物件整理成表。不判斷資料好壞、不刪列、不算統計。

| 項目 | 內容 |
| --- | --- |
| 輸入 | 使用者訊息（`R/request.txt`）；`references/` 的地區與代碼查表、`cost-params.json`；官方實價登錄 zip 或 `sample-data/`；591 快照或即時頁面 |
| 處理任務 | 1 解析目標地區 → 2 取得並正規化實價登錄 → 3 取得 591 刊登 → 4 整理候選物件（只寫使用者明說的） → 5 整理使用者提供的評論 |
| 輸出 | `01_area.json`、`01_collected.csv`、`01_collected_city.csv`、`01_collect_manifest.json`、`01_candidates.csv`、`01_reviews.csv`、`591_list.csv`、`591_detail.csv`、`591_sources.json` |
| 交接格式 | `handoff_1_collector.json`（to = fact-checker） |
| 不做 | 不判斷資料好壞、不刪列、不算統計、不猜地區或費用 |

以下 `R` = `output/<run_id>`，`S` = 本 Skill 資料夾。

## 步驟

### 1. 目標地區

```bash
python S/scripts/resolve_area.py --text "$(cat R/request.txt)" --out R/01_area.json
```

- `area_status = resolved` → 繼續。地區來源（`area_source`）與目的地（`destination`）原樣保留。
- `unresolved` → 互動模式：把 `01_area.json.question` 原句問使用者一次，取得「縣市|區」後加 `--confirmed 縣市|區` 重跑。非互動模式：停在這裡，回到 SKILL.md 第 4 節。

完成條件：`01_area.json` 的每個目標都有 `city`、`city_code`、`district` 與允許的 `area_source`。

### 2. 實價登錄租賃資料

```bash
python S/scripts/collect_lvr.py --area R/01_area.json --out R --cache data/lvr-cache
```

腳本會逐季下載官方 zip（重試 3 次）；失敗時自動改用 `S/sample-data/`（manifest `data_mode = offline_sample`，RT9）。結束碼 3 = 縣市沒有租賃資料（E19）、4 = 官方欄位改版（E3，停止並回報，不猜）。

完成條件：`01_collected.csv`、`01_collected_city.csv`、`01_collect_manifest.json` 存在，manifest 的 `errors` 已讀過並寫進交接信封的 `warnings`。

### 3. 591 刊登資料

對每個目標地區：

```bash
python S/scripts/crawl_591.py fetch --city <縣市> --district <區> --out R
```

`sample-data/591/` 有 30 天內的快照就直接用；沒有就即時爬取該區（請求間隔 1–3 秒、刊登頁最多 300 筆）。

使用者給了 591 網址 → `crawl_591.py ids --ids <網址或編號…> --out R/591_ids`；使用者貼了刊登文字 → 存成 `R/591_paste.txt` 後 `crawl_591.py paste --file R/591_paste.txt --out R/591_paste`。

591 失敗不中斷流程：在交接信封寫明原因，報告會說明「本次沒有刊登租金對照」。

完成條件：`R/591_sources.json` 記錄每個地區用了快照或即時爬取，以及筆數或失敗原因。

### 4. 候選物件

把使用者訊息中的每一間房寫成 `R/candidates_input.json`（陣列）。**只寫使用者明說的欄位**，沒說就不要寫這個鍵：

| 鍵 | 例 | 說明 |
| --- | --- | --- |
| `listing_id`、`label` | `L1`、`逢甲分租套房` | 依出現順序 L1、L2… |
| `city`、`district` | `臺中市`、`西屯區` | 物件在別區才寫；沒寫沿用目標地區 |
| `rent_type_group` | `student_suite` | 獨立／分租套房 → `student_suite`；雅房 → `student_room`；整層 → `whole_unit` |
| `rent_monthly`、`area_ping` | `7000`、`7` | 月租（元）、坪數 |
| `mgmt_fee` 或 `mgmt_status: "included"` | `800` | 「管理費另計 800」→ `mgmt_fee`；「含管理費」→ included；「不知道」→ 不寫 |
| `elec_price_per_kwh` 或 `elec_status` | `5` | 「台電計價」→ `elec_status: "taipower"`；「含電」→ `included` |
| `water_fee`／`gas_fee`／`internet_fee` 或 `<k>_status: "included"` | `100` | 同上 |
| `deposit_months` | `2` | 押金月數 |
| `commute_minutes_oneway`、`commute_mode`、`commute_fare_per_trip` | `12`、`scooter` | 只有使用者說了才寫 |
| `destination_label` | `長庚大學` | 通勤目的地；沒說會沿用學校查表結果 |
| `source_type`、`source_url`、`posted_date` | `school_portal` | 591／fb／school_portal／friend／user；沒說就不寫（＝unknown） |
| `notes_text` | `房東說要先匯訂金才能看房` | 其他條件原文，R3 關鍵字比對對象 |
| `listing_591_id` | `22081529` | 來自 591 時填，腳本會補上刊登內容 |

```bash
python S/scripts/candidates.py --input R/candidates_input.json --area R/01_area.json --out R --detail591 R/591_ids/591_detail.csv
```

完成條件：`01_candidates.csv` 列數 = 使用者提到的物件數；缺月租的列 `status = incomplete`（互動模式先追問一次，RT10）。

### 5. 評論

使用者自己提供了評論 → 寫成 `R/01_reviews.csv`（欄位 `review_id,is_simulated,source_label,source_url,area_key,rent_type_group,text,sentiment,keywords,review_date`，`is_simulated=false`）。沒有 → 只寫表頭。不要自己編評論。

### 6. 交接

寫 `R/handoff_1_collector.json`（to = fact-checker），`artifacts` 列出 01 檔案與列數，`warnings` 放 manifest 的警告、591 狀態與地區來源（例：「地區由學校查表得出：逢甲 → 臺中市西屯區」）。
