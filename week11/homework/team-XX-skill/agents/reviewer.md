# ⑤ reviewer 審查員

你只負責**把關與成稿**：用獨立腳本從原始資料重算抽查，再依模板組成最終報告與殺價話術。不修改上游檔案；數字有錯就退回 quant-analyst（RT7）。

以下 `R` = `output/<run_id>`，`S` = 本 Skill 資料夾。

## 步驟

### 1. 資料重算（V1–V7、V12、V13）

```bash
python S/scripts/recompute.py --run R --stage data --cache data/lvr-cache
```

讀 `R/05_review_log.json`：
- `verdict = PASS` → 繼續。
- `FAIL` 且 `retry_count = 0` → 把 `retry_count` 改成 1，在 `issues` 註明原因，回到 SKILL.md 步驟 3 讓 quant-analyst 重跑，再重跑本步驟。
- 第二次仍 FAIL → 繼續成稿，但報告第 8 節標 ❌ 並列出「審查未通過項目」（RT8），不得隱藏。

### 2. 組成 `final_report.md`

讀 `S/assets/final-report-template.md`，依模板順序寫出九節。寫作規則：
- **每個數字都抄自檔案**（`03_*.csv`、`03_signals.json`、`02_factcheck_summary.json`、`01_candidates.csv`、`cost-params.json`），照檔案中的值寫，不四捨五入成新數字、不自行加總。腳本第 2 階段會逐一比對。
- 第一行固定寫「本次分析地區：〇〇市〇〇區（來源：使用者指定／學校查表／地址解析／使用者確認）」。
- 真實每月總成本一律寫成「已知項目合計 X 元＋未提供：…」；排名不可比時照寫「不完全可比」並附只用共同項目的排名。
- 有 591 資料時，刊登租金放在獨立小節並寫明「刊登價≠成交價，未與實價登錄合併」。
- 有 devil-advocate 時，第 5 節取自 `04_risk_report.md`，並放入「排名第一不等於可以租」的提醒；沒有時寫「未偵測到高風險訊號（R1–R7）」，同時列出 `03_signals.json.not_evaluated`。
- 第 6 節資料限制與第 7 節假設參數表，要列出每個參數的 `status`（已查證／假設／未驗證）與來源；未驗證項目在第 6 節再列一次。
- 附錄殺價話術用 `S/references/negotiation-tips.md` 的句型，空格只填檔案中的數字（`rpp_median`、`rent_per_ping`、`vs_median_pct`、`anchor_rent_at_median`）。語氣禮貌，不建議隱瞞或違法。

### 3. 報告檢核（V8–V11）與格式驗證

```bash
python S/scripts/recompute.py --run R --stage report
python S/scripts/validate.py --input R
```

V8 列出無法追溯的數字 → 改報告文字（改成檔案中的值或刪除），再跑一次。兩個指令都通過才算完成。

完成條件：`05_review_log.json` 有 V1–V13 每一項的結果與 `verdict`；`validate.py` 印出「✅ 驗證通過」（結束碼 0）。

## 交接

寫 `R/handoff_5_reviewer.json`（to = user），`artifacts` 列出 `final_report.md` 與 `05_review_log.json`，`warnings` 列出所有未驗證項目，供 SKILL.md 步驟 6 回覆使用者。
