# YouTube 上傳資料

- 已上傳：https://youtu.be/HTNxGOs2UcE （4:45，1080p，已燒錄中文字幕、Google 語音旁白）。公開 repo 不保留 mp4。
- 可見度：**不公開（Unlisted）**，不可設「私人」
- 字幕：上傳 `student-rental-check.zh-TW.srt`，語言「中文（台灣）」
- 「為兒童打造」：否
- 頻道名稱／頭像會出現在影片頁：依匿名規定，請用不含姓名、組別的頻道（或確認頻道名稱不會暴露身分）

## 標題

```
student-rental-check｜台灣學生租屋行情與避雷 AI Skill（三角色以上、A/B/C 啟動測試）
```

## 說明欄

```
以 Claude Code Skill 實作的學生租屋行情與避雷檢查：使用內政部實價登錄租賃開放資料（主）與 591 刊登（對照），由五個 Agent 分工：collector → fact-checker → quant-analyst →（有風險訊號才啟動）devil-advocate → reviewer（獨立重算抽查），產出 final_report.md。

影片展示 SKILL.md 的 Trigger（name／description）、測試 A／B／C 的實際執行與啟動證據（stream-json log 中的 Skill tool_use、Read 角色檔紀錄），以及 reviewer V8 FAIL → 修正 → 回歸測試 PASS 的除錯過程。旁白為 Google 語音合成。

章節：
0:00 主題與資料來源
0:40 Skill 架構與五個 Agent
1:24 測試 A：應啟動（即時執行）
2:04 完整流程：各角色腳本
2:31 測試 A 啟動證據
2:51 測試 B：換說法仍應啟動
3:33 測試 C：不應啟動
3:44 失敗分析與修正
4:18 限制與 AI Tutor
```
