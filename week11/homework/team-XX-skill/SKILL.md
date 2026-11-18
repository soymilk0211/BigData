---
name: student-rental-check
description: >
  台灣各縣市學生租屋行情與避雷檢查。使用者可用縣市與區、學校名稱
  或地址指定地區（例：龜山長庚附近、台中逢甲附近、台南東區）。
  當使用者想知道套房、雅房或整層的租金合不合理、貴不貴、划不划算，
  要比較多間候選房，計算含管理費、水電、通勤時間的真實每月成本，
  或擔心訂金、押金、二房東、價格異常等踩雷風險時使用；
  使用者貼上 591 刊登或網址請你看看時也使用。
  即使沒說「實價登錄」「行情」或縣市名稱，只要是在台灣找學生租屋、
  「學校附近」找房就應啟用。資料來源為內政部實價登錄租賃開放資料與 591 租屋網刊登。
  不要用於：買房、預售屋或房貸、台灣以外的租屋、與租屋無關的學校
  校務問題、一般程式或數學問題。
---

# 學生租屋行情與避雷（student-rental-check）

> 學生指定地區與候選物件（或只問行情），由五個角色依序完成：蒐集 → 標記 → 精算 →（有風險才）踩雷檢查 → 審查重算，產出 `final_report.md`。數字一律來自腳本，判斷與文字由角色負責。

## 1. 三條底線

- **不猜**：物件事實（管理費、水電瓦斯網路、押金、通勤分鐘、坪數）沒寫就是「未提供」，寫進報告，不補預設值。地區只能來自使用者、學校查表、地址解析或使用者確認。
- **兩種租金分開**：實價登錄租金是行情依據；591 刊登租金只並列比較，永不合併進同一分組。
- **不洩漏**：輸出不含門牌、姓名、電話、LINE；591 原始網頁不保存。

## 2. 主流程（你是協調者）

`<skill>` 指本 Skill 資料夾（含本檔的目錄）。每個角色的指令一律用 **Read 工具**開啟 `<skill>/agents/<角色>.md`：log 中的 Read 紀錄就是「依分工執行」的證據，所以每個角色各讀一次。所有輸出寫在目前工作目錄的 `output/<run_id>/`（`run_id` = 台北時間 `YYYYMMDD-HHMMSS`）。每個角色開工前先讀上一個角色的**交接信封**，完工時寫自己的：`handoff_<n>_<角色>.json`，欄位 `handoff_version`（"1.0"）、`run_id`、`from`、`to`、`artifacts`（`[{"path", "rows"}]`）、`status`（ok／partial／failed）、`warnings`、`next_hint`。

### 步驟 0：建立 run 與路由

1. 建立 `output/<run_id>/`，把使用者原話存成 `request.txt`。
2. 判斷模式：訊息中有月租數字的候選物件 0 間 → `market_only`；1 間 → `single`；≥ 2 間 → `compare`。使用者貼 591 網址或刊登內容也算一間。
3. 判斷是否互動：預設為**非互動**（使用者的這一則訊息就是全部輸入，例如 `claude -p` 單次執行），此時不追問，改走第 4 節的非互動規則；只有在對話中使用者已表示可以回答追問時才算互動。
4. 寫 `00_routing.json`：`run_id`、`skill`、`mode`、`candidate_count`、`interactive`、`agents_planned`（先列四個必跑角色）、`agents_skipped: []`、`signals: []`、`warnings: []`。

完成條件：`00_routing.json` 存在且 `mode` 有值。

### 步驟 1：collector 蒐集員

用 Read 工具讀 `<skill>/agents/collector.md` 並照做。完成條件：`01_area.json` 存在；若 `area_status = resolved`，另有 `01_collected.csv`、`01_candidates.csv`、`01_collect_manifest.json` 與 591 資料（或失敗原因）。

若 `area_status = unresolved` → 直接跳到第 4 節「地區無法確定」，不讀其他角色。

### 步驟 2：fact-checker 時效驗證員

用 Read 工具讀 `<skill>/agents/fact-checker.md` 並照做。完成條件：`02_flags.csv`、`02_factcheck_summary.json` 存在且 `rows_deleted = 0`。

### 步驟 3：quant-analyst CP 值精算師

用 Read 工具讀 `<skill>/agents/quant-analyst.md` 並照做。完成條件：`03_market_stats.csv`、`03_signals.json` 存在；有候選物件時有 `03_cost_breakdown.csv`；`compare` 時有 `03_ranking.csv`。

### 步驟 4：路由 devil-advocate（條件啟動）

讀 `03_signals.json`，把 `signals` 寫回 `00_routing.json.signals`。

- `signals` 非空 → 把 `devil-advocate` 加入 `agents_planned`，用 Read 工具讀 `<skill>/agents/devil-advocate.md` 並照做。完成條件：`04_risk_report.json` 與 `04_risk_report.md` 存在。
- `signals` 為空 → 在 `agents_skipped` 加 `{"agent": "devil-advocate", "reason": "no_high_risk_signal"}`，**不要讀** `agents/devil-advocate.md`（測試以「沒有讀這個檔」作為路由證據）。

### 步驟 5：reviewer 審查員

用 Read 工具讀 `<skill>/agents/reviewer.md` 並照做。完成條件：`05_review_log.json.verdict` 為 PASS，或已重試一次後如實標示 FAIL；`final_report.md` 完成；`scripts/validate.py` 結束碼 0。

### 步驟 6：回覆使用者

用 5–8 行繁體中文回覆：分析地區與來源、一句話結論、真實每月總成本（已知項目合計與未提供項目）、是否有高風險訊號、審查結果，以及**未驗證項目**（`cost-params.json` 中 `status = 未驗證` 的參數、`03_signals.json.not_evaluated`），最後附 `final_report.md` 路徑。

## 3. 路由規則

| ID | 條件 | 動作 | 證據 |
| --- | --- | --- | --- |
| RT1 | 一律 | collector → fact-checker → quant-analyst → reviewer | Read 這四個 `agents/*.md` |
| RT2–4 | 候選物件 0／1／≥2 | `market_only`／`single`／`compare` | `00_routing.json.mode` |
| RT5 | `03_signals.json.signals` 非空 | 啟用 devil-advocate | `04_risk_report.json` |
| RT6 | 沒有訊號 | 略過 devil-advocate | `agents_skipped`；log 無 Read `devil-advocate.md` |
| RT7 | reviewer FAIL 且 `retry_count = 0` | 回到步驟 3 重算一次 | `retry_count = 1` |
| RT8 | 第二次仍 FAIL | 照常出報告，「審查紀錄」標 ❌ 並列「審查未通過項目」 | `final_report.md` |
| RT9 | 官方下載失敗 | 改用 sample-data | manifest `data_mode = offline_sample` |
| RT10 | 候選物件缺月租 | 互動：追問一次；非互動：標 incomplete 後繼續 | `01_candidates.csv.status` |
| RT11 | 只要殺價話術 | 仍跑完整流程（話術要行情數字） | 報告附錄 |
| RT12–13 | 地區唯一確定／缺少或歧義 | 照常／見第 4 節 | `01_area.json.area_status` |
| RT14 | 分組有效樣本 < 10 | 合併類型 → 全縣市 → insufficient，逐步記錄 | `03_market_stats.csv.fallback` |
| RT15 | 有 591 資料 | 刊登租金另算 `03_asking_stats.csv`，不進行情 | reviewer V13 |

## 4. 例外處理

- **地區無法確定（RT13）**：互動模式追問一次 `01_area.json.question`，使用者回覆後以 `--confirmed 縣市|區` 重跑 `resolve_area.py`。非互動模式：不下載、不計算；依 `assets/final-report-template.md` 的「追問版」寫 `final_report.md`（第一行「本次分析地區：未確定」，列出候選地區與追問句），在 `agents_skipped` 加入 fact-checker、quant-analyst、devil-advocate、reviewer（`reason = area_unresolved`），再跑 `validate.py`。
- **縣市沒有租賃資料**（連江縣）：告知沒有實價登錄租賃資料，不算行情；仍可做踩雷檢查與已知成本。
- **範圍外**：買賣、預售屋、房貸、台灣以外 → 不跑流程，一般回答並說明本 Skill 的範圍。
- 其他例外（E1–E22）見 `references/cleaning-rules.md` 末段。

## 5. 代理人分工

| 角色 | 檔案 | 只負責 | 主要產出 |
| --- | --- | --- | --- |
| ① collector 蒐集員 | `agents/collector.md` | 地區解析、實價登錄與 591 資料取得、候選物件整理 | `01_*` |
| ② fact-checker 時效驗證員 | `agents/fact-checker.md` | 逐列標記過時、重複、來源不明、未提供；不刪資料 | `02_*` |
| ③ quant-analyst CP 值精算師 | `agents/quant-analyst.md` | 行情統計、真實每月總成本、排序、刊登租金對照、訊號判定 | `03_*`、`charts/` |
| ④ devil-advocate 踩雷獵人 | `agents/devil-advocate.md` | 只在有訊號時，用唱反調的角度挑戰排名第一的物件 | `04_*` |
| ⑤ reviewer 審查員 | `agents/reviewer.md` | 獨立重算抽查、組成最終報告與殺價話術 | `05_review_log.json`、`final_report.md` |

## 6. 參考資料與腳本

| 檔案 | 何時讀 |
| --- | --- |
| `references/data-sources.md` | 下載網址、季別、591 取得方式與出處 |
| `references/field-mapping.md` | 欄位對照、候選物件欄位、單位換算 |
| `references/cleaning-rules.md` | 旗標規則 CR-01–CR-15、管理費解析、例外 E1–E22 |
| `references/risk-signals.md` | R1–R7 定義、關鍵字、風險等級 |
| `references/cost-params.json` | 使用者情境參數、門檻與查證狀態 |
| `references/negotiation-tips.md` | 殺價話術句型 |
| `assets/final-report-template.md` | 最終報告骨架 |

腳本（直接執行，不必讀進 context；`--help` 看用法）：`resolve_area.py`、`collect_lvr.py`、`crawl_591.py`、`candidates.py`（collector）；`flag.py`（fact-checker）；`analyze.py`（quant-analyst）；`recompute.py`、`validate.py`（reviewer）。需要 Python 3.10+（pandas、numpy、matplotlib、requests）與 node。
