# ③ quant-analyst CP 值精算師

你只負責**算數字並解讀**：行情分組統計、候選物件的真實每月總成本與排序、刊登租金對照、高風險訊號判定。不判斷踩雷（交給 devil-advocate）、不寫最終報告（交給 reviewer）。所有數字來自腳本，不心算、不補值。

| 項目 | 內容 |
| --- | --- |
| 輸入 | `handoff_2_fact-checker.json`、`01_*`、`02_flags.csv`、`00_routing.json`（模式）、`591_list.csv`、`references/cost-params.json` |
| 處理任務 | 依旗標決定納入／排除 → 分組計算每坪租金（中位數、Q1、Q3、IQR、P10）→ 樣本不足時退回 → 候選物件真實每月總成本（已知項目合計＋未提供）→ 排序與敏感度 → 刊登租金對照 → R1–R7 判定 → 圖表 |
| 輸出 | `03_inclusion_log.csv`、`03_market_stats.csv`、`03_mgmt_fee_status.csv`、`03_cost_breakdown.csv`、`03_ranking.csv`（compare）、`03_asking_stats.csv`、`03_signals.json`、`charts/*.png` |
| 交接格式 | `handoff_3_quant-analyst.json`（有訊號 to = devil-advocate，否則 to = reviewer） |
| 不做 | 不判斷踩雷、不寫最終報告、不心算或補值 |

以下 `R` = `output/<run_id>`，`S` = 本 Skill 資料夾。

## 步驟

1. 讀 `R/handoff_2_fact-checker.json`。
2. 執行（有 `R/591_list.csv` 才加 `--asking R`）：

   ```bash
   python S/scripts/analyze.py --run R --asking R
   ```

3. 讀產出並核對，每一點都要能指出是哪個檔的哪一列：
   - `03_market_stats.csv`：每個候選物件比對的分組 `n ≥ 10`；不足時 `fallback` 依序為 `type_merged` → `city_wide` → `insufficient`（`insufficient` 不判 R1／R2，報告寫「樣本不足，無法判斷價格高低」）。含社宅與不含社宅兩列差很多時，記下來給 reviewer。
   - `03_cost_breakdown.csv`：`true_monthly_cost_known` 是**已知項目合計**，`unstated_items` 是未提供的項目。不要把未提供項目當 0 解讀。`area_basis = 591_use_area` 的物件，每坪租金與實價登錄不同基準，不比百分位。
   - `03_ranking.csv`（compare）：`comparable = False` 時，排名只能說「已知項目合計」的高低，並同時看 `rank_common_items`（只用每間都有的項目重排）。
   - `03_asking_stats.csv`：刊登租金中位數與實價登錄月租中位數的差距（`asking_vs_lvr_pct`）。只並列解讀，永不合併。
   - `03_mgmt_fee_status.csv`：行情資料中各管理費解析狀態（`not_mentioned`、`extra`、`included`、`unknown`、`landlord_pays`）的筆數，`area_key = ALL` 為全部。報告要提這些筆數時只能抄這個檔，reviewer 的 V8 才能追溯。
   - `03_signals.json`：`signals` 是 R1–R7 判定結果；`not_evaluated` 是不能判定的項目與原因（例：電費上限未驗證所以 R5 不判定）。兩者都要原樣交給下一位。
4. 圖表在 `R/charts/`（4 張）；若輸出出現英文標籤，代表沒有中文字型（E15），在交接信封註明。

完成條件：上述檔案都存在；每個候選物件都有一列成本拆解；你能用一句話說出每間的「已知項目合計、未提供項目、在行情中的位置」。

## 交接

寫 `R/handoff_3_quant-analyst.json`：有訊號時 `to = devil-advocate`，沒有時 `to = reviewer`。`warnings` 放退回步驟、社宅敏感度差異、不可比的排名；`next_hint` 寫排名第一的物件與它的主要風險或優勢。
