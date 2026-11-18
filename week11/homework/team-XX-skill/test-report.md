# 測試紀錄：student-rental-check（A／B／C 啟動測試與除錯）

> 繳交時另轉 PDF。所有 log 在 `test-logs/`，已把暫存目錄與家目錄路徑換成 `<WORK>`、`<TMP>`、`~`。

## 1. 測試方式

| 項目 | 內容 |
| --- | --- |
| 平台 | Claude Code 非互動模式 |
| 隔離 | `tests/run_test.sh`：每次建立乾淨暫存目錄，只把本 Skill 裝在 `<暫存目錄>/.claude/skills/student-rental-check/`；`--setting-sources project,local`，不載入使用者層級的其他 Skill 與外掛 |
| 指令 | `claude -p "<提示詞>" --setting-sources project,local --output-format stream-json --verbose --allowedTools Skill Read Write Edit Glob Grep Bash [--max-turns N]` |
| 分工 | **Agent 1（正向）**跑應啟動的 A、B 與 591 加測；**Agent 2（反向）**跑不應啟動的 C 與近似題。兩個 agent 都只寫 `test-logs/`，不改 Skill 本身 |
| 次數 | A、B：各 1 次完整流程＋2 次只看是否啟動（`--max-turns 3`，拿到 Skill 呼叫後即停）；C：3 次；其他各 1 次 |
| 觸發方式 | 全部是**自動觸發**：提示詞中沒有指名 Skill，也沒有使用斜線指令 |

### 怎麼判定 Skill 有啟動

| 等級 | 證據 | 判讀 |
| --- | --- | --- |
| E0 可用 | `type=system, subtype=init` 的 `skills` 含 `student-rental-check` | 只證明已安裝，**不算**啟動；反向測試用它證明「沒啟動不是因為沒裝」 |
| E1 自動選用 | `type=assistant` 中 `tool_use.name == "Skill"`、`input.skill == "student-rental-check"` | 主要證據 |
| E2 依分工執行 | 之後用 Read 讀 `agents/*.md`、用 Bash 執行 `scripts/*.py` | 證明照 SKILL.md 的角色與路由執行 |
| E3 可核對輸出 | `output/<run_id>/` 的檔案、`validate.py` 結束碼 0、`05_review_log.json.verdict` | 證明產出符合規格 |

查核指令：

```bash
# E1：Skill 是否被呼叫
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill") | .input' test-logs/A-1.jsonl
# E2：讀了哪些 agents 檔（含行號）
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Read") | .input.file_path' test-logs/B-1.jsonl | grep agents/
# 反向測試：Skill 呼叫次數應為 0
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill")' test-logs/C-1.jsonl | wc -l
```

## 2. 結果總表

| 測試 ID | 類型 | 提示詞 | 預期 | 實際 | 啟動證據位置 | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| A-1 | 應啟動（完整） | 測試 A 原文（見 3.1） | 啟動；single；略過 devil-advocate；12,618 元 | 符合 | `A-1.jsonl` E1 第 29 行；Read collector 125、fact-checker 356、quant-analyst 469、reviewer 692 行；無 devil-advocate | PASS |
| A-2 | 應啟動 | 同上 | 啟動 | 啟動 | `A-2.jsonl` E1 第 31 行 | PASS |
| A-3 | 應啟動 | 同上 | 啟動 | 啟動 | `A-3.jsonl` E1 第 28 行 | PASS |
| B-1 | 改寫後仍應啟動（完整） | 測試 B 原文（見 3.2） | 啟動；逢甲 → 臺中市西屯區；compare；啟用 devil-advocate | 符合 | `B-1.jsonl` E1 第 34 行；Read collector 134、fact-checker 393、quant-analyst 516、devil-advocate 692、reviewer 1077 行 | PASS |
| B-2 | 改寫後仍應啟動 | 同上 | 啟動 | 啟動 | `B-2.jsonl` E1 第 33 行 | PASS |
| B-3 | 改寫後仍應啟動 | 同上 | 啟動 | 啟動 | `B-3.jsonl` E1 第 35 行 | PASS |
| A591-1 | 加測（591 刊登） | 「這是我在 591 看到的，幫我看會不會踩雷：龜山區 獨立套房 7,000元/月 5坪 押金一個月租金 …」 | 啟動 | 啟動 | `A591-1.jsonl` E1 第 27 行 | PASS |
| C-1 | 不應啟動 | 「幫我寫一個 Python 函式，輸入兩個日期字串，回傳相差幾天。」 | 不啟動 | 直接給程式碼，1 回合 | `C-1.jsonl`：E0 第 3 行；Skill 呼叫 0 | PASS |
| C-2 | 不應啟動 | 同上 | 不啟動 | 同上 | `C-2.jsonl`：Skill 呼叫 0 | PASS |
| C-3 | 不應啟動 | 同上 | 不啟動 | 同上 | `C-3.jsonl`：Skill 呼叫 0 | PASS |
| C2-1 | 邊界（買賣） | 「林口預售屋現在一坪大概多少？」 | 不啟動 | 一般回答預售屋行情 | Skill 呼叫 0 | PASS |
| C3-1 | 邊界（校務） | 「長庚大學圖書館期末考週開到幾點？」 | 不啟動 | 建議查圖書館官網 | Skill 呼叫 0 | PASS |
| N1-2 | 近似（程式＋591） | 「幫我寫一個爬 591 租屋網的 Python 爬蟲」 | 不啟動 | 自行寫爬蟲，未用本 Skill 的腳本 | Skill 呼叫 0；沒有讀本 Skill 任何檔案 | PASS |
| N2-1 | 近似（國外） | 「東京學生套房一個月多少？」 | 不啟動 | 一般回答東京行情 | Skill 呼叫 0 | PASS |
| N3-1 | 近似（法規問答） | 「租屋押金法規上限是多少？」 | 不啟動 | 回答 2 個月並附條文 | Skill 呼叫 0 | PASS |
| N4-1 | 近似（房東角度） | 「我想把台中的房子出租，租金該訂多少？」 | 不啟動 | 反問物件條件 | Skill 呼叫 0 | PASS |
| N1-1 | — | 同 N1-2 | — | 執行中碰到帳號用量上限（`is_error=true`） | `N1-1.jsonl` | **無效**，以 N1-2 重跑 |
| A-4 | 應啟動（完整，SKILL.md v2 回歸） | 測試 A 原文 | 同 A-1 | 符合：12618、略過 devil-advocate、PASS | `A-4.jsonl` E1 第 27 行；Read 4 個角色檔 | PASS |
| B-4 | 改寫後仍應啟動（完整，SKILL.md v2 回歸） | 測試 B 原文 | 同 B-1 | 符合：school_lookup、L2 第 1、L1 R3＋R6 high、devil-advocate、PASS | `B-4.jsonl` E1 第 30 行；Read 5 個角色檔 | PASS |

穩定性：A 4/4、B 4/4 自動啟動（含 v2 回歸各 1 次）；C 3/3 未啟動；近似與邊界題 6/6 未啟動。每個反向 log 的 E0 都顯示 Skill 已安裝，所以「沒啟動」是模型依 description 判斷的結果。

兩個 agent 的完整明細：`test-logs/agent1-positive-results.md`（.json）、`test-logs/agent2-negative-results.md`（.json）。

## 3. 完整流程的可核對輸出（E3）

### 3.1 測試 A（桃園市龜山區，single）

提示詞：「我是長庚大學新生，在龜山區找到一間獨立套房，月租 9,500 元、權狀 8 坪，管理費另計 800 元，電費每度 5 元，騎車到學校單程約 12 分鐘，刊登在學校租屋網。請用實價登錄幫我判斷這個價格合不合理，並算出真實每月總成本。」

| 檢查 | 預期 | 實際（`test-logs/A-1-output/`） |
| --- | --- | --- |
| 地區 | 桃園市\|龜山區，user_explicit | 符合（`01_area.json`） |
| 模式與路由 | single；`agents_skipped` 有 devil-advocate | 符合（`00_routing.json`，reason = no_high_risk_signal） |
| 每坪租金 | 1,187.5 | 1187.5；行情中位數 1,188.5（n = 1,126） |
| 真實每月總成本 | 12,618（±1） | 已知項目合計 12618 = 9,500 + 800 + 750 + 1,568；未提供：水費、瓦斯、網路 |
| 高風險訊號 | 無 | 無；R5（電費上限未驗證）、R7（無評論）列為「未能判定」 |
| 審查 | PASS | `05_review_log.json` verdict = PASS，retry_count = 0 |
| 格式 | validate 結束碼 0 | 在執行目錄 `output/<run_id>/` 結束碼 0（`test-logs/` 複本刻意不含 `01_collected.csv`、`03_inclusion_log.csv`，因此只在複本上執行會因缺檔失敗） |

### 3.2 測試 B（臺中市西屯區，compare＋高風險）

提示詞：「我在逢甲附近找房，有兩間在猶豫：第一間是分租套房 7 坪，一個月 7,000，房東說要先匯訂金才能看房；第二間是雅房，一個月 5,500，管理費不知道。哪間比較划算？會不會踩雷？」

| 檢查 | 預期 | 實際（`test-logs/B-1-output/`） |
| --- | --- | --- |
| 地區 | 「逢甲」→ 臺中市\|西屯區，school_lookup；只讀 `b_lvr_land_c.csv` | 符合；報告第一行「本次分析地區：臺中市西屯區（來源：學校查表）」 |
| 模式 | compare，`03_ranking.csv` 2 列 | 符合：L2（5,500）第 1、L1（7,000）第 2；已知項目只有月租，兩間未提供項目相同 |
| 訊號 | L1 命中 R3（先匯訂金）與 R6 | 符合；L1 risk_level = high，建議「建議避開」 |
| devil-advocate | 啟用 | 讀了 `agents/devil-advocate.md`，產生 `04_risk_report.json`／`.md` |
| 提醒 | 「排名第一不等於可以租」 | `final_report.md` 第 54 行 |
| 審查 | PASS | verdict = PASS（30 項檢核），retry_count = 0 |

觀察：L2 也因 R6（使用者沒說刊登來源與日期）被標為 high，這符合規格「含 R6 → high」的規則；但對只是沒交代來源的物件，等級可能偏嚴，列為後續可調整項目（第 5 節）。

## 4. 修正紀錄（v1 → v2）

### 4.1 description（觸發條件）：首次即通過

`SKILL.md` 的 frontmatter 以規格書 2.4 節的 v1 為基礎（加上 591 一句），在第一次正式測試就全部通過：A、B 自動啟動 3/3，C 與 6 題邊界、近似題 0 誤觸發。依規格書 13.6「誠實原則」，**沒有為了製造失敗而改壞 description**，所以沒有 description 的 v2；`test-logs/SKILL.v1.md` 就是受測版本。之後 SKILL.md 本體為對齊範本而改版（4.3 節），frontmatter 前 14 行與 v1 完全相同。

最容易誤觸發的近似題是 N3（押金法規）與 N4（房東想出租），兩題都有「租屋」主題，但 description 的「學生找房」與「不要用於」讓模型改用一般回答；N3 的回答結尾只提議「可以貼刊登給我看」，沒有呼叫 Skill。

### 4.2 流程與腳本：開發階段的實際失敗與修正

正式測試前，以同樣的 `run_test.sh` 先試跑一次測試 A（開發試跑，log 未保留為證據），發現並修正：

| # | 問題（試跑時實際發生） | 原因 | 修正 | 驗證 |
| --- | --- | --- | --- | --- |
| 1 | 模型用 `cat` 讀 `agents/collector.md`，log 中沒有 Read 紀錄，E2 證據不足；其他角色檔沒讀就直接跑腳本 | SKILL.md 只寫「Read `agents/…`」，沒說明要用 Read 工具、也沒說為什麼 | SKILL.md 改為「用 Read 工具讀 `<skill>/agents/<角色>.md`：log 中的 Read 紀錄就是依分工執行的證據，每個角色各讀一次」 | A-1、B-1 都有 4／5 個 agents 檔的 Read 紀錄 |
| 2 | `claude -p` 單次執行，模型卻把 `interactive` 設成 true | SKILL.md 沒有判斷依據 | 改為「預設非互動；只有使用者已表示可回答追問時才算互動」 | A-1、B-1 都依非互動規則執行 |
| 3 | reviewer 的 V8（數字可追溯）把 run_id、檔案路徑、檢核代號當成無法追溯的數字 | 檢查範圍太寬 | V8 忽略 run_id、程式碼片段、連結與 V/R/E/CR 代號，並把 00–05 的 JSON 納入可追溯來源 | A-1、B-1 V8 PASS |
| 4 | V10（隱私）在數值欄的長串小數上誤判「手機號碼」，審查員只好標 ❌ 並人工說明 | 正則表達式掃描整個 CSV | V10 改為只掃文字欄位（備註、描述、費用片段）與報告 | — |
| 5 | 修正 #4 之後，V10 抓到**真的**個資：桃園市部分實價登錄備註含承租人姓名、身分證字號與手機號碼（官方原始資料） | 原本只遮蔽門牌樣式 | `collect_lvr.py` 新增遮蔽身分證字號（含前面的姓名）與電話；重建 `sample-data`；全桃園市備註重掃 0 筆 | A-1、B-1 V10 PASS |
| 6 | 591 的電費與水費寫法多樣（「臺電繳費」「5.5元/度」「100元/月」「免管理費」）解析不到 | 只處理了部分寫法 | `candidates.py` 補上這些寫法；「臺電／台電計價」視為電價未驗證、不計 | 單元檢查通過 |
| 7 | 測試腳本在本環境沒有 `rsync`；log 仍殘留 `/tmp/` 路徑 | 環境差異、去識別規則不足 | 改用 `tar`；sed 另外遮蔽 `/tmp/…` | 所有 `.jsonl` 掃描 `/tmp/`、`/home/`、`/root/` 皆 0 |

### 4.3 SKILL.md 本體 v1 → v2：對齊老師範本章節

正式測試後，對照老師的 `skill-template.zip`，發現 SKILL.md 的內容雖然齊全，但章節名稱與順序和範本不同、缺「範例」一節；角色檔也沒有獨立列出「輸入／處理任務／輸出／交接格式」。修正：

- SKILL.md 改為範本的九節：概述、前置條件、核心工作流程、代理人分工、輸出格式、邊界案例與限制、參考資料索引、可用腳本、範例（183 行）。
- 五個角色檔開頭加上「輸入／處理任務／輸出／交接格式／不做」表。
- **description 一字未改**（觸發條件不變）。

證據：`test-logs/SKILL.v1.md`、`test-logs/SKILL.v2.md`、`test-logs/SKILL.v1-v2.diff`（`diff -u`）。修改後以同樣提示詞重跑完整流程 A-4、B-4，結果與 A-1、B-1 一致（自動啟動、依序讀角色檔、審查 PASS、`validate.py` 結束碼 0）。

### 4.4 無效執行

第一次啟動兩個測試 agent 時，帳號碰到 5 小時用量上限，A-1、B-1、N1-1 的執行被中斷（log 結尾 `is_error = true`、「You've hit your 5-hour limit」）。A-1、B-1 的中斷 log 已刪除並重跑；N1-1 保留作為紀錄，以 N1-2 重跑。這些中斷不計入成功或失敗。

## 5. 限制與後續

- 本次全部以非互動模式測試；互動模式的「追問一次」（地區歧義、缺月租）沒有在 log 中驗證。
- 測試 B2（「東區」歧義）屬加分項，本次未列入兩個 agent 的清單；`resolve_area.py` 的單獨測試已確認會列出臺中市、臺南市、新竹市、嘉義市東區並停止計算。
- R6 對「沒交代來源與日期」的物件一律判 high，可能偏嚴；可考慮改為 medium，或只在同時有其他訊號時升為 high。
- 時間價值（基本工資時薪）與電費每度上限未能取得官方原文，報告與回覆都標「未驗證」；R5 暫停判定。
