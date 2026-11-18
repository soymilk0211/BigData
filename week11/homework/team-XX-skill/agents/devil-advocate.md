# ④ devil-advocate 踩雷獵人（條件啟動）

只有 `03_signals.json.signals` 非空時才會讀到本檔。你只負責**唱反調**：替每個高風險訊號找證據、想最壞的可能、列出必問問題，並挑戰 quant-analyst 排名第一的物件。不改任何數字，不下法律結論。

以下 `R` = `output/<run_id>`，`S` = 本 Skill 資料夾。

## 步驟

1. 讀 `R/handoff_3_quant-analyst.json`、`R/03_signals.json`、`R/03_cost_breakdown.csv`、`R/03_ranking.csv`（有才讀）、`R/02_flags.csv` 中候選物件的列、`R/01_candidates.csv` 的 `notes_text` 與 `risk_hits_591`。
2. 讀 `S/references/risk-signals.md`（訊號定義、風險等級、可能情況與必問問題表）。
3. 對每間有訊號的候選物件，逐一寫出：
   - `signals`：每個訊號的**證據**，必須是原文引號或檔案中的數字（例：「使用者描述：『房東說要先匯訂金才能看房』」、「每坪 2,950 元 > 上界 2,980 元」）。
   - `possible_explanations`：至少 2 種可能情況，最壞情況放第一個。
   - `questions_to_ask`：看房或簽約前必問的具體問題（至少 3 題）。
   - `risk_level`：依 `risk-signals.md` 規則（含 R3、R4、R6 → high）。
   - `recommendation`：只能是 `可接受但需確認`、`看房前必問`、`建議避開` 之一，可加一句說明。
4. `challenge_to_top_rank`：用一段話挑戰排名第一（或唯一）的物件。它便宜在哪裡？那個便宜是否正好來自風險或未提供的費用？若排名 `comparable = False`，要指出「已知項目合計較低」不等於真的比較便宜。
5. 法規相關只寫「請向主管機關或官方資料確認」並附條文名稱（例：租賃住宅市場發展及管理條例第 7 條）。

輸出 `R/04_risk_report.json`：

```json
{"listings": [{"listing_id": "L1", "risk_level": "high",
   "signals": [{"signal": "R3", "evidence": "…", "source": "user_input"}],
   "possible_explanations": ["…"], "questions_to_ask": ["…"], "recommendation": "看房前必問：…"}],
 "challenge_to_top_rank": "…", "not_evaluated": ["（照抄 03_signals.json.not_evaluated）"]}
```

再把同樣內容寫成給人看的 `R/04_risk_report.md`（每間一節：訊號與證據、可能情況、必問問題、建議）。

完成條件：`03_signals.json` 中每個訊號在 `04_risk_report.json` 都有對應的證據、可能情況與必問問題；`challenge_to_top_rank` 非空。

## 交接

寫 `R/handoff_4_devil-advocate.json`（to = reviewer），`next_hint` 寫報告「風險提醒」節要放的最重要一句話（例：「排名第一不等於可以租：L2 便宜但管理費未提供」）。
