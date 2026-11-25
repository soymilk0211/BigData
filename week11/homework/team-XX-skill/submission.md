# 繳交資訊

| 項目 | 內容 |
| --- | --- |
| 組別 | 依匿名互評規定不列出 |
| YouTube 影片 | https://youtu.be/pKZa5sm2O5o ；可見度「不公開」（非私人）；長度 5:43（精確 5:43.67）；字幕已上傳 `tutor/subtitles.zh-TW.srt`（中文（台灣），95 段）；章節見 `tutor/chapters.md` |
| 影片 Drive 備份 | https://drive.google.com/file/d/1CJLdnihYP16584XdWuF-ryBQE3Lkod-A/view?usp=sharing （檔名 `student-rental-check_final_v8.mp4`；知道連結的任何人可檢視） |
| 字幕 Drive 備份 | https://drive.google.com/file/d/1r63ynn51-j2KMkBb9tPanU19tTNps5v2/view?usp=sharing （檔名 `student-rental-check_final_v8.zh-TW.srt`；知道連結的任何人可檢視） |
| AI Tutor 課程包 | `tutor/student-rental-check_v8.classtutor`（檔名不含個人資訊） |
| AI Tutor 雲端連結 | https://drive.google.com/file/d/1QgwV-tgN19m_y3_yUeV_NSTXo7wgndOw/view?usp=sharing （知道連結的任何人可檢視） |
| AI Tutor 使用方式 | 學生開啟 https://educatres.github.io/ClassTutor/ →「載入課程包」→ 輸入**自己的** Gemini API Key → 提問。問整支影片的問題請切到「全課複習」；「跟著進度」模式只會用目前播放位置之前的字幕，在 0:00 時會因字幕不足而拒答。詳細步驟見 `tutor/README.md`。 |
| AI Tutor 測試題 | 已用 v8 課程包、模型 `gemini-flash-lite-latest`，在播到 5:43 後實測 2 題（見下表）。內容大致正確，時間點引用偏弱。完整說明與截圖見 `tutor/README.md` 第三節。 |

已測問題與簡短結果：

| # | 問題 | 簡短結果 | 引用時間點 | 備註 |
| --- | --- | --- | --- | --- |
| Q1 | 哪一段測試證明 Skill 有啟動？ | 內容正確：應看 stream-json，第一個 tool_use 就是 Skill（參數 student-rental-check）；測試 A、B 都有啟動，測試 C 呼叫 0 次、沒有誤啟動。 | 回答附上 04:50 與原始標記 `[chunk0002]` | 前兩次（觀看進度 1:08、5:41）遇到 Google AI Studio 暫時無法服務，第三次（5:43）成功。04:50 對到的字幕是「log 沒有 Read 證據」（除錯段），不是啟動證據；`[chunk0002]` 不是影片時間點。啟動證據實際在 1:18–1:32（第一個 tool_use 就是 Skill）、1:34–1:39（E1–E3）、2:02–2:05（測試 B 同樣呼叫 Skill）。 |
| Q2 | 審查員做了什麼？ | 內容正確：reviewer 從原始資料獨立重算；測試 A 完整執行時判 V8 FAIL（舊規則下數字無法追溯），修正後回歸測試 A-5 判 PASS，最後五個角色完整交接並由 reviewer 判 PASS。 | 00:00、04:50 | 00:00 是片頭，不是審查員說明，引用偏弱。04:50 同樣對到「log 沒有 Read 證據」，比 V8 FAIL（4:55–5:11）和總結（5:18–5:21）都早。審查員說明實際在 1:02–1:04、測試 B 重算結果在 3:57–4:01。 |
