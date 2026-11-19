# 第十一週：三角色 AI Skill 分組作業

本週作業是用老師提供的 Skill 範本，設計一個至少有三個角色的 AI Skill，完成 A／B／C 啟動測試，錄製約 5 分鐘含字幕的影片，並建立 AI Tutor。

本組題目：**台灣各縣市學生租屋行情與避雷 Skill**（暫定名稱 `student-rental-check`）。不限特定學校：使用者可用縣市＋區、學校名稱或地址指定地區（例：桃園市龜山區長庚大學附近、臺中市西屯區逢甲大學附近）。主要資料為內政部實價登錄租賃開放資料，涵蓋全國 21 個縣市的租賃批次檔。

## 目錄內容

| 路徑 | 說明 |
| --- | --- |
| `規格書.md` | Skill 規格書：目的、啟動條件、目標地區解析（縣市＋區／學校／地址）、五個角色與交接格式、路由規則、資料來源驗證、欄位對照、清理與例外處理、測試計畫、影片大綱、AI Tutor、匿名檢核、分工、里程碑與驗收清單 |
| `teacher/三個角色的 AI Skill 作業.docx` | 老師的作業說明（以此為準）：作業目標、三角色要求、A／B／C 測試、影片時間配置、AI Tutor、繳交目錄、評分與匿名互評規則 |
| `teacher/1_from_prompts_to_skills.pdf` | 講義一：從 Prompt 到 Skill、Agent 的概念、漸進式揭露（三層載入） |
| `teacher/2_從範本建立自己的skill.pdf` | 講義二：Skill 資料夾結構（SKILL.md、agents/、scripts/、references/、assets/），以及如何讓 AI 依範本產生 Skill 並測試 |
| `teacher/p.txt` | 講義一的文字擷取版 |
| `teacher/p2.txt` | 講義二的文字擷取版 |
| `teacher/skill-template.zip` | 老師提供的 Skill 範本（SKILL.md、三個範例 agents、validate.py、references、assets） |

## Skill 實作（`homework/team-XX-skill/`）

| 路徑 | 內容 |
| --- | --- |
| `homework/team-XX-skill/SKILL.md` | Skill 入口：frontmatter（觸發條件）、主流程、路由表、例外、代理人分工 |
| `homework/team-XX-skill/agents/` | 五個角色：collector、fact-checker、quant-analyst、devil-advocate（條件啟動）、reviewer |
| `homework/team-XX-skill/scripts/` | 8 支腳本：地區解析、實價登錄取得與正規化、591 取得、候選物件、旗標、分析、獨立重算、格式驗證 |
| `homework/team-XX-skill/references/`、`assets/` | 資料來源、欄位對照、清理規則、風險訊號、參數（含查證狀態）、話術、報告模板 |
| `homework/team-XX-skill/sample-data/` | 真實資料：實價登錄三區五季（已遮蔽）、591 三區去識別化快照 |
| `homework/team-XX-skill/test-logs/`、`test-report.md` | A／B／C 與近似題的 stream-json log、兩個測試 agent 的結果、v1→v2 紀錄 |
| `GLOSSARY.md`、`docs/adr/` | 領域用語與設計決策（591 刊登租金永不與實價登錄合併） |

規格以 `規格書.md` v1.2 為準。

## 版本控制

提交 `README.md`、`規格書.md`、`GLOSSARY.md`、`docs/`、`teacher/` 與 `homework/team-XX-skill/`。不提交：`work/`（下載的原始 zip、爬取暫存）、Skill 執行產生的 `output/`、`__pycache__/`。

## 匿名提醒

依互評規定，任何繳交檔案、影片、字幕與 AI Tutor 都不得出現組別、姓名、學號、email、帳號或絕對路徑；詳見 `規格書.md` 第 16 章。
