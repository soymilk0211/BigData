# 影片章節（https://youtu.be/QIAtzRLjpL8 ，總長 4:45）

| 時間 | 段落 | 畫面 |
| --- | --- | --- |
| 0:00–0:09 | 標題 | 標題卡 |
| 0:09–0:40 | 主題、資料來源、預期成果 | 終端機：資料夾、sample-data（三區筆數）、data-sources、final_report 一句話結論 |
| 0:40–1:24 | Skill 架構：SKILL.md（Trigger）與五個 Agent | 終端機：SKILL.md frontmatter（name、description）、agents/ 五個角色檔、fact-checker 的輸入／輸出／交接表、handoff_2 交接檔 |
| 1:24–2:04 | 測試 A（應啟動）：Claude Code 即時執行 | 終端機：claude -p 測試 A 即時執行（init、tool_use Skill、Read collector.md），加速 1.5 倍；最後 jq 從 log 取出 Skill 名稱 |
| 2:04–2:31 | 完整流程：各角色腳本直接執行 | 終端機：resolve_area → collect_lvr → candidates → flag → analyze → recompute（data）實際輸出 |
| 2:31–2:51 | 測試 A 完整執行紀錄：啟動證據 E1–E3 | 終端機：jq 列出 V-A.jsonl 的 Skill 與四個 Read 角色檔、00_routing.json（略過 devil-advocate）、12618 元 |
| 2:51–3:33 | 測試 B（換說法仍應啟動）＋ devil-advocate | 終端機：claude -p 測試 B 即時執行（tool_use Skill）、resolve_area 逢甲→臺中市西屯區、V-B 的 R3 訊號、agents_planned 五角色、04_risk_report 風險等級 high |
| 3:33–3:44 | 測試 C（不應啟動）：即時執行 | 終端機：claude -p 測試 C 即時執行、Skill 呼叫次數 = 0 |
| 3:44–4:18 | 失敗分析與修正：V8 FAIL → A-5 PASS | 終端機：SKILL v1/v2 description 相同、V-A 05_review_log V8 FAIL、A-5 PASS、validate 通過 |
| 4:18–4:45 | 限制、AI Tutor 使用方式 | 限制與 AI Tutor 說明卡（含 ClassTutor 老師頁截圖） |
