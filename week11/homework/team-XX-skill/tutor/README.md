# AI Tutor（ClassTutor）製作與使用說明

本資料夾是影片的 AI Tutor 材料，用 [ClassTutor](https://educatres.github.io/ClassTutor/) 製作課程包。

| 檔案 | 用途（ClassTutor 中的欄位） |
| --- | --- |
| `subtitles.zh-TW.srt` | 影片燒錄字幕的 SRT 版（共 95 段，5:43，精確 5:43.67；影片 https://youtu.be/pKZa5sm2O5o ，edge-tts Yunjian 旁白；公開 repo 不保留 mp4）；上傳到「字幕檔案（VTT／SRT／SBV）」，也上傳到 YouTube 當字幕 |
| `tutor-material.md` | 講義（Skill 功能、五個 Agent、E0–E3、測試 A／B／C 與時間點、除錯、限制）；上傳到「教材／講義（可多選）」 |
| `vocabulary.txt` | 專有名詞，一行一個；貼到「確認詞彙／專有名詞」 |
| `course-intro.md` | 課程簡介（≤150 字）；貼到「摘要內容（可自由修改）」 |
| `chapters.md` | 影片章節時間表；也可貼到 YouTube 說明欄當章節 |
| `student-rental-check_v8.classtutor` | 已用 v8 影片與字幕重建的課程包；雲端硬碟連結（知道連結的任何人可檢視）見 `../submission.md` |
| `screenshots/tutor-v8-q1.webp`、`screenshots/tutor-v8-q2.webp` | 學生頁 v8 課程包 Q1、Q2 實測截圖（已裁切瀏覽器列與工作列，畫面中沒有 API Key） |

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
8. 分享方式（＝本作業的 AI Tutor 存取方式）：把 `.classtutor` 檔上傳到雲端硬碟，設成「知道連結的任何人可檢視」，用**不含個人姓名的檔名**（例：`student-rental-check_v8.classtutor`），把連結填入 `submission.md` 的「AI Tutor」欄。課程包不是加密檔，請勿放入敏感資料（本課程包只含字幕、講義、詞彙與影片網址）。

## 二、學生端：使用 AI Tutor

1. 下載老師分享的 `.classtutor` 檔。
2. 開啟 <https://educatres.github.io/ClassTutor/> →「**載入課程包**」→ 選擇 `.classtutor` 檔；影片與字幕自動載入。
3. 在 API Key 設定中「貼上你的 API Key」（**自己的** Gemini API Key；金鑰只存在本機瀏覽器）→「測試連線」。
4. 提問。問整支影片的問題時請切到「**全課複習**」；「跟著進度」模式只會用目前播放位置之前的字幕回答。回答附有影片時間點，可點擊「跳到影片 …」。

## 三、測試題（YouTube 上傳、課程包製作後實測）

| # | 問題 | 預期回答重點 | 預期時間點 |
| --- | --- | --- | --- |
| Q1 | 哪一段測試證明 Skill 有自動啟動？ | 測試 A：提示詞沒指名 Skill、沒用斜線指令；log 中有 `name = Skill` 的 tool_use（E1），接著依序讀 collector、fact-checker、quant-analyst、reviewer 四個角色檔（E2），輸出已知項目合計 12,618 元可核對（E3） | 1:11–1:56 |
| Q2 | reviewer（審查員）如何檢查資料？ | 從原始資料獨立重算抽查（V1–V13），例如資料階段 23 項檢查全部 PASS、總成本重算一致；也檢查報告數字可追溯（V8），V-A 完整執行那次 V8 判 FAIL，修正後 A-5 PASS | 1:02–1:04、3:56–4:09（亦可 4:55–5:11） |
| Q3 | 什麼情況才會啟動 devil-advocate？ | 條件啟動：只有出現高風險訊號才啟動；測試 B 第一間「房東要先匯訂金才能看房」命中 R3，路由啟動 devil-advocate，判為高風險、建議避開；測試 A 沒有訊號就沒有讀 devil-advocate | 3:35–3:55（亦可 0:58–1:01、1:40–1:44） |
| Q4 | 不限長庚嗎？ | 不限；測試 B 用逢甲，經學校對照表對應到臺中市西屯區，證明全台各縣市都能用（限制：學校對照表只收錄少數學校） | 2:07–2:11（測試 B 段 1:56–4:27） |
| Q5 | 測試 C 為什麼沒有啟動？ | 一般程式問題（影片中即時執行）；init 顯示 Skill 已安裝但 Skill 呼叫 0，是模型依 description 判斷 | 4:27–4:41 |

### 實測結果（2026-11-25，學生頁，v8 課程包）

模型：`gemini-flash-lite-latest`。課程包 `student-rental-check_v8.classtutor`。兩題都在影片播到 5:43（片尾）後提問。截圖（已裁切瀏覽器列與工作列，畫面中沒有 API Key）在 `screenshots/tutor-v8-q1.webp`、`screenshots/tutor-v8-q2.webp`。

Q1 前兩次嘗試（觀看進度 1:08、5:41）回傳「Google AI Studio 暫時無法服務，請稍後重試」；第三次（5:43）成功。Q2 一次成功。下面記錄的是成功的那一次回答。實際問句與上表預定問句略有不同，以實測為準。

| # | 實際問句 | 實際回答（摘要） | 引用時間點 | 是否指到正確時間點 |
| --- | --- | --- | --- | --- |
| Q1 | 哪一段測試證明 Skill 有啟動？ | 內容正確：要判定 Skill 是否有啟動，可看 stream-json 的工具呼叫紀錄，第一個 tool_use 就是 Skill（參數 student-rental-check）；測試 A 與 B 都有正確啟動，測試 C 呼叫次數為 0、沒有誤啟動。截圖 `screenshots/tutor-v8-q1.webp`。 | 04:50、以及原始標記 `[chunk0002]` | 部分符合。內容對，但 04:50 對到的字幕是「log 沒有 Read 證據」（4:50–4:51，除錯段），不是啟動證據；`[chunk0002]` 不是影片時間點。啟動證據在 1:18–1:32（怎麼判定、第一個 tool_use 就是 Skill）、1:34–1:39（E1–E3 完整 log）、2:02–2:05（測試 B 同樣第一個 tool_use 是 Skill）。總結「A、B 正確啟動，C 沒有誤啟動」在 5:13–5:17。 |
| Q2 | 審查員做了什麼？ | 內容正確：reviewer 會從原始資料獨立重算；測試 A 完整執行時判 V8 FAIL，報告數字在舊排除規則下無法追溯；修正規則後再跑回歸測試 A-5 判 PASS；最後五個角色完整交接並由 reviewer 判 PASS。截圖 `screenshots/tutor-v8-q2.webp`。 | 00:00、04:50 | 部分符合。內容對，但 00:00 是片頭標題，不是審查員說明，引用偏弱。04:50 同樣對到「log 沒有 Read 證據」，比 V8 FAIL（4:55–5:11）和總結「reviewer 判 PASS」（5:18–5:21）都早。審查員職責說明在 1:02–1:04（「reviewer 從原始資料獨立重算」），測試 B 的審查結果在 3:57–4:01。 |

