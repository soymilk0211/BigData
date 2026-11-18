# ② fact-checker 時效驗證員

你只負責**標記**：每一列資料與每一間候選物件有什麼要注意的地方。不刪列、不算行情、不下「能不能租」的結論。

| 項目 | 內容 |
| --- | --- |
| 輸入 | `handoff_1_collector.json`、`01_collected.csv`、`01_candidates.csv`、`01_reviews.csv`、`01_area.json`、`references/cleaning-rules.md` |
| 處理任務 | 逐列加旗標（過時、遲延申報、重複、非住宅、社宅、面積無效、來源不明、刊登過期、刊登租金、未提供），並核對候選物件旗標與使用者原話一致 |
| 輸出 | `02_flags.csv`（一列一旗標，含規則 ID）、`02_factcheck_summary.json`（`rows_deleted` 恆為 0） |
| 交接格式 | `handoff_2_fact-checker.json`（to = quant-analyst） |
| 不做 | 不刪列、不算行情、不下「能不能租」的結論 |

以下 `R` = `output/<run_id>`，`S` = 本 Skill 資料夾。

## 步驟

1. 讀 `R/handoff_1_collector.json`，把它的 `warnings` 記下來。
2. 執行：

   ```bash
   python S/scripts/flag.py --run R
   ```

3. 讀 `R/02_factcheck_summary.json`，逐項確認：
   - `rows_deleted` 必須是 0；不是 0 就停止並回報。
   - `candidate_flags`：每間候選物件的旗標都對得上使用者的原話。例：使用者沒說刊登來源 → 應有 `UNKNOWN_SOURCE`；沒說刊登日期 → `STALE_LISTING`；有任何隱藏成本未提供 → `COST_UNSTATED`；月租來自 591 → `ASKING_PRICE`。對不上就回到 collector 修 `candidates_input.json`，不要手改 CSV。
   - `notes`：社會住宅比例高的地區要轉告 quant-analyst（行情會被拉低）。
4. 旗標代碼、嚴重度與規則 ID 的定義在 `S/references/cleaning-rules.md`；遇到不認得的旗標才去讀。

完成條件：`02_flags.csv`、`02_factcheck_summary.json` 存在，`rows_deleted = 0`，每間候選物件的旗標都已核對過原話。

## 交接

寫 `R/handoff_2_fact-checker.json`（to = quant-analyst）。`warnings` 寫：社宅比例、各候選物件的 warn 級旗標、未提供的隱藏成本；`next_hint` 寫需要特別注意的分組（例：「龜山雅房有效樣本少，可能需要退回」）。
