# YouTube 上傳資料

- 已上傳：https://youtu.be/pKZa5sm2O5o （長度 5:43.67，1920×1080，30 fps，已燒錄中文字幕、edge-tts Yunjian 旁白）。公開 repo 不保留 mp4。
- 可見度：**不公開（Unlisted）**，不可設「私人」
- 字幕：上傳 `student-rental-check_final_v8.zh-TW.srt`（共 95 段），語言「中文（台灣）」
- 「為兒童打造」：否
- 頻道名稱／頭像會出現在影片頁：依匿名規定，請用不含姓名、組別的頻道（或確認頻道名稱不會暴露身分）

## 標題

```
student-rental-check｜台灣學生租屋行情與避雷 AI Skill（三角色以上、A/B/C 啟動測試）
```

## 說明欄

```
以 Claude Code Skill 實作的學生租屋行情與避雷檢查：使用內政部實價登錄租賃開放資料（主）與 591 刊登（對照），由五個 Agent 分工：collector → fact-checker → quant-analyst →（有風險訊號才啟動）devil-advocate → reviewer（獨立重算抽查），產出 final_report.md。

影片展示 SKILL.md 的 Trigger（name／description）、測試 A／B／C 的實際執行與啟動證據（stream-json log 中的 Skill tool_use、Read 角色檔紀錄），測試 B 的完整多角色流程，以及 reviewer V8 FAIL → 修正 → 回歸測試 A-5 PASS 的除錯過程。旁白為 edge-tts zh-CN-YunjianNeural。

章節：
0:00 主題、來源資料、預期成果
0:32 Skill 架構與角色分工；展示 SKILL.md
1:11 測試 A：應啟動（即時執行）
1:33 測試 A：啟動證據 E1–E3
1:56 測試 B：換說法仍應啟動（即時執行）
2:12 測試 B：重播完整流程
2:27 collector 蒐集員
2:50 fact-checker 時效驗證員
3:07 quant-analyst 精算師
3:35 devil-advocate 踩雷獵人
3:56 reviewer 審查員與最終報告
4:27 測試 C：不應啟動
4:41 失敗原因、修正與驗證
5:12 成果總結與限制
5:31 AI Tutor 使用方式
```
