# AI Tutor（ClassTutor）製作與使用說明

本資料夾是影片的 AI Tutor 材料，用 [ClassTutor](https://educatres.github.io/ClassTutor/) 製作課程包。

| 檔案 | 用途（ClassTutor 中的欄位） |
| --- | --- |
| `subtitles.zh-TW.srt` | 影片燒錄字幕的 SRT 版（共 65 段，4:45；影片 https://youtu.be/HTNxGOs2UcE ，Google TTS 旁白；公開 repo 不保留 mp4）；上傳到「字幕檔案（VTT／SRT／SBV）」，也上傳到 YouTube 當字幕 |
| `tutor-material.md` | 講義（Skill 功能、五個 Agent、E0–E3、測試 A／B／C 與時間點、除錯、限制）；上傳到「教材／講義（可多選）」 |
| `vocabulary.txt` | 專有名詞，一行一個；貼到「確認詞彙／專有名詞」 |
| `course-intro.md` | 課程簡介（≤150 字）；貼到「摘要內容（可自由修改）」 |
| `chapters.md` | 影片章節時間表；也可貼到 YouTube 說明欄當章節 |
| `student-rental-check.classtutor` | 已產生的課程包（約 10 KB）；雲端硬碟連結見 `../submission.md` |
| `screenshots/q1.webp`、`q2.webp`、`q3.webp` | 學生頁 Q1–Q3 實測截圖（已裁切，無 API Key） |

字幕已校對關鍵詞（SKILL.md、Agent、Trigger、collector、fact-checker、quant-analyst、devil-advocate、reviewer、實價登錄、龜山、逢甲、西屯）：與燒錄字幕一致、沒有錯字，因此未修改任何文字與時間軸。

## 一、老師端：產生 `.classtutor` 課程包

1. 先把影片上傳 YouTube，可見度設「**不公開**」（有連結的人才能看，不是「私人」），字幕上傳 `subtitles.zh-TW.srt`（語言：中文（台灣））。複製影片網址。
2. 開啟 <https://educatres.github.io/ClassTutor/teacher.html>（老師課程工作台）。
3. 「匯入字幕與教材」：
   - 「字幕檔案（VTT／SRT／SBV）」→ 拖放或選擇 `tutor/subtitles.zh-TW.srt`。
   - 「教材／講義（可多選）」→ 選擇 `tutor/tutor-material.md`。
   - 「確認詞彙／專有名詞」→ 把 `tutor/vocabulary.txt` 的內容貼上 →「加入詞彙」。
4. 字幕逐段編修（**可選**）：
   - 「修正字幕」／「逐行修正字幕」需要在「AI 設定」貼上**自己的** Gemini API Key（Google AI Studio 免費申請）；只修文字、時間軸不變。
   - 字幕已校對過，可以直接跳過 AI 修正（不需要 API Key）。
5. 課程摘要：在「摘要內容（可自由修改）」貼上 `tutor/course-intro.md`（或留白）。不按「產生摘要」就不消耗 token。
6. 「影片網址」→ 貼上 YouTube 不公開影片網址，等待出現「已辨識 YouTube 影片」。
7. 按「**產生並下載 .classtutor 課程包**」，得到 `.classtutor` 檔。
8. 分享方式（＝本作業的 AI Tutor 存取方式）：把 `.classtutor` 檔上傳到雲端硬碟，設成「知道連結的任何人可檢視」，用**不含個人姓名的檔名**（例：`student-rental-check.classtutor`），把連結填入 `submission.md` 的「AI Tutor」欄。課程包不是加密檔，請勿放入敏感資料（本課程包只含字幕、講義、詞彙與影片網址）。

## 二、學生端：使用 AI Tutor

1. 下載老師分享的 `.classtutor` 檔。
2. 開啟 <https://educatres.github.io/ClassTutor/> →「**載入課程包**」→ 選擇 `.classtutor` 檔；影片與字幕自動載入。
3. 在 API Key 設定中「貼上你的 API Key」（**自己的** Gemini API Key；金鑰只存在本機瀏覽器）→「測試連線」。
4. 提問。問整支影片的問題時請切到「**全課複習**」；「跟著進度」模式只會用目前播放位置之前的字幕回答。回答附有影片時間點，可點擊「跳到影片 …」。

## 三、測試題（YouTube 上傳、課程包製作後實測）

| # | 問題 | 預期回答重點 | 預期時間點 |
| --- | --- | --- | --- |
| Q1 | 哪一段測試證明 Skill 有自動啟動？ | 測試 A：提示詞沒指名 Skill、沒用斜線指令；log 中有 `name = Skill` 的 tool_use（E1），接著依序讀 collector、fact-checker、quant-analyst、reviewer 四個角色檔（E2），輸出已知項目合計 12,618 元可核對（E3） | 1:24–2:51 |
| Q2 | reviewer（審查員）如何檢查資料？ | 從原始資料獨立重算抽查（V1–V13），例如資料階段 23 項檢查全部 PASS、總成本重算一致；也檢查報告數字可追溯（V8），V-A 完整執行那次 V8 判 FAIL，修正後 A-5 PASS | 1:15–1:19、2:24–2:31（亦可 4:00–4:18） |
| Q3 | 什麼情況才會啟動 devil-advocate？ | 條件啟動：只有出現高風險訊號才啟動；測試 B 第一間「房東要先匯訂金才能看房」命中 R3，路由啟動 devil-advocate，判為高風險、建議避開；測試 A 沒有訊號就沒有讀 devil-advocate | 2:51–3:33（亦可 1:11–1:15） |
| Q4 | 不限長庚嗎？ | 不限；測試 B 用逢甲，經學校對照表對應到臺中市西屯區，證明全台各縣市都能用（限制：學校對照表只收錄少數學校） | 3:00–3:08（測試 B 段 2:51–3:33） |
| Q5 | 測試 C 為什麼沒有啟動？ | 一般程式問題（影片中即時執行）；init 顯示 Skill 已安裝但 Skill 呼叫 0，是模型依 description 判斷 | 3:33–3:44 |

### 實測結果（2026-11-25，學生頁）

模型：`gemini-flash-lite-latest`（「測試連線」成功）。課程包 `student-rental-check.classtutor` 載入後有出現正確的影片與課程簡介，但沒有另外的成功提示。實測時用「跟著進度」：在 0:00 提問會被拒答（「目前播放進度以前尚無足夠的字幕證據」），因此先把影片拉到約 3:41 之後再問。點擊回答裡的 01:11 可正確跳到該時間。三次回答都只引用 01:11 與 02:24，後面段落（測試 B 的 devil-advocate、測試 C）沒有被引用，這是 ClassTutor 對時間點對應偏弱，不是課程內容本身寫錯。截圖（已裁切瀏覽器列與工作列，畫面中沒有 API Key、姓名或信箱）在 `screenshots/q1.webp`、`q2.webp`、`q3.webp`。

| # | 模式（全課複習／跟著進度） | 實際回答（摘要） | 引用時間點 | 是否指到正確時間點 |
| --- | --- | --- | --- | --- |
| Q1 | 跟著進度（提問時間 3:55；0:00 時曾拒答） | 內容正確：測試 A 提示詞沒指名 Skill、沒用斜線指令，第一個工具呼叫就是 Skill，參數是 student-rental-check，代表模型依 description 自動選用；並提到測試 B 即時執行時同樣第一步就呼叫 Skill。截圖 `screenshots/q1.webp`（點 01:11 後播放器停在 1:11/4:44） | 01:11、02:24 | 部分符合。預期 1:24–2:51；02:24 在範圍內，01:11 略早（落在架構段，講 Trigger／Agent）。點擊 01:11 可正確跳轉 |
| Q2 | 跟著進度（提問時間 3:51） | 內容正確：reviewer 從原始資料獨立重算抽查，並用另一支程式獨立重算，資料階段二十三項檢查全部 PASS。截圖 `screenshots/q2.webp` | 01:11、02:24 | 部分符合。預期 1:15–1:19 與 2:24–2:31；02:24 對上後段，01:11 略早 |
| Q3 | 跟著進度（提問時間 4:05）。實際問句是「devil-advocate 在影片裡做了什麼？」（與上表預定問句相近） | 內容正確：只在出現高風險訊號時加入；測試 A 沒有高風險訊號所以沒啟動；測試 B 因「先匯訂金才能看房」命中 R3，devil-advocate 加入、五個角色都出現，並建議避開要先匯訂金的那間。截圖 `screenshots/q3.webp` | 01:11、02:24 | 不符合預期時間點。預期 2:51–3:33，實際仍只引用 01:11、02:24 |
| Q4 | 未測 | — | — | — |
| Q5 | 未測 | — | — | — |
