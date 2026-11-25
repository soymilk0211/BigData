# 測試紀錄：student-rental-check（A／B／C 啟動測試與除錯）

> 繳交時另轉 PDF。所有 log 在 `test-logs/`，已把暫存目錄與家目錄路徑換成 `<WORK>`、`<TMP>`、`~`。
>
> **log 的事後處理（如實揭露）**：
> 1. 路徑：A-4、B-4 是在 `run_test.sh` 加入 `/tmp/` 規則之後跑的，執行時就直接產生 `<TMP>`（A-4 有 15 處、B-4 有 10 處）。A-1–A-3、A591-1、B-1–B-3、C、C2、C3、N 系列則在那之前跑，是兩個測試 agent **事後**用 `sed` 補清的（取代為 `<WORK>/scratchpad`、`<WORK>/cc-socks` 等，指令見 `test-logs/agent1-positive-results.md`、`agent2-negative-results.md`），所以這些 log 中 `<TMP>` 為 0 次。
> 2. 第三方個資：繳交前發現 N1-1、N1-2 的 tool_result 含 591 原始網頁與刊登列表（含仲介／屋主姓名與路段，見 4.5 節），已把這幾行的 tool_result 內容換成「[591 原始內容已移除]」。
>
> 3. 11/18 為早期影片草稿錄製的 V-A、V-B（`test-logs/V-A.jsonl`、`V-B.jsonl`；新版影片拿來當完整流程證據）由錄影腳本執行，執行後即以與 `run_test.sh` 相同的 sed 規則去除路徑；A-5 由 `run_test.sh` 直接產生。繳交前對這三份 log 與輸出複本掃描第三方個資（591 原始 HTML、「○先生／小姐／太太」、手機與市話、門牌）與路徑，**皆 0 筆**，因此沒有再修改內容（行數：V-A 108、V-B 92、A-5 92）。
>
> 所有事後處理都是逐行取代，**每份 log 的行數不變**，本報告引用的行號仍然有效。
>
> 影片已上傳 YouTube（不公開）：https://youtu.be/pKZa5sm2O5o （5:43，精確 5:43.67，edge-tts Yunjian 旁白＋燒錄字幕；公開 repo 不保留 mp4）。章節表見 `tutor/chapters.md`，字幕見 `tutor/subtitles.zh-TW.srt`（95 段）；總表最後一欄「影片時間點」依 v8 章節表填寫。AI Tutor（ClassTutor）材料見 `tutor/README.md`。

## 1. 測試方式

| 項目 | 內容 |
| --- | --- |
| 平台 | Claude Code 非互動模式 |
| 隔離 | `tests/run_test.sh`：每次建立乾淨暫存目錄，只把本 Skill 裝在 `<暫存目錄>/.claude/skills/student-rental-check/`；`--setting-sources project,local`，不載入**使用者層級**的 Skill 與設定。但環境並非只剩本 Skill：正式測試的 19 份 log 的 init 事件都相同，列出 23 個 skill（本 Skill＋22 個 Claude Code 內建 skill，例如 `dataviz`、`code-review`、`simplify`）與 4 個內建 plugin（`source` 都是 `…@builtin`），沒有任何使用者層級的 skill 或 plugin。之後的 V-A、V-B、A-5 換了 Claude Code 版本（init 的 `claude_code_version` 2.1.322），內建 skill 變少，init 列出 18 個 skill（含本 Skill）與 4 個內建 plugin，同樣沒有使用者層級的 skill |
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
# 隔離：init 事件載入的 skill 數、plugin 數與 plugin 來源（正式測試 19 份是 23、4、["builtin"]；V-A、V-B、A-5 是 18、4、["builtin"]）
jq -c 'select(.type=="system" and .subtype=="init") | [(.skills|length), (.plugins|length), (.plugins|map(.path)|unique)]' test-logs/A-1.jsonl
# 工具權限被拒（C2-1、C3-1 不是 0）
jq -c 'select(.type=="result") | .permission_denials | map(.tool_name)' test-logs/C3-1.jsonl
```

## 2. 結果總表

| 測試 ID | 類型 | 提示詞 | 觸發方式 | 預期 | 實際 | 啟動證據位置 | 判定 | 影片時間點 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | 應啟動（完整） | 測試 A 原文（見 3.1） | 自動 | 啟動；single；略過 devil-advocate；12,618 元 | 符合 | `A-1.jsonl` E1 第 29 行；Read collector 125、fact-checker 356、quant-analyst 469、reviewer 692 行；無 devil-advocate | PASS | 1:11–1:56 |
| A-2 | 應啟動 | 同上 | 自動 | 啟動 | 啟動 | `A-2.jsonl` E1 第 31 行 | PASS | 1:11–1:56 |
| A-3 | 應啟動 | 同上 | 自動 | 啟動 | 啟動 | `A-3.jsonl` E1 第 28 行 | PASS | 1:11–1:56 |
| B-1 | 改寫後仍應啟動（完整） | 測試 B 原文（見 3.2） | 自動 | 啟動；逢甲 → 臺中市西屯區；compare；啟用 devil-advocate | 符合 | `B-1.jsonl` E1 第 34 行；Read collector 134、fact-checker 393、quant-analyst 516、devil-advocate 692、reviewer 1077 行 | PASS | 1:56–4:27 |
| B-2 | 改寫後仍應啟動 | 同上 | 自動 | 啟動 | 啟動 | `B-2.jsonl` E1 第 33 行 | PASS | 1:56–4:27 |
| B-3 | 改寫後仍應啟動 | 同上 | 自動 | 啟動 | 啟動 | `B-3.jsonl` E1 第 35 行 | PASS | 1:56–4:27 |
| A591-1 | 加測（591 刊登） | 「這是我在 591 看到的，幫我看會不會踩雷：龜山區 獨立套房 7,000元/月 5坪 押金一個月租金 …」 | 自動 | 啟動 | 啟動 | `A591-1.jsonl` E1 第 27 行 | PASS | 未入鏡 |
| C-1 | 不應啟動 | 「幫我寫一個 Python 函式，輸入兩個日期字串，回傳相差幾天。」 | 自動 | 不啟動 | 直接給程式碼，1 回合 | `C-1.jsonl`：E0 第 3 行；Skill 呼叫 0 | PASS | 4:27–4:41（影片即時執行的是 LIVE-C，見 4.8 節） |
| C-2 | 不應啟動 | 同上 | 自動 | 不啟動 | 同上 | `C-2.jsonl`：Skill 呼叫 0 | PASS | 4:27–4:41 |
| C-3 | 不應啟動 | 同上 | 自動 | 不啟動 | 同上 | `C-3.jsonl`：Skill 呼叫 0 | PASS | 4:27–4:41 |
| C2-1 | 邊界（買賣） | 「林口預售屋現在一坪大概多少？」 | 自動 | 不啟動 | 一般回答預售屋行情；WebSearch 權限被拒（`permission_denials` 1 筆），回答註明不是即時資料 | Skill 呼叫 0；權限被拒見 `type=result` 事件（第 247 行） | PASS | 未入鏡 |
| C3-1 | 邊界（校務） | 「長庚大學圖書館期末考週開到幾點？」 | 自動 | 不啟動 | WebSearch、WebFetch 權限被拒（`permission_denials` 2 筆），回答「沒查到」，建議查圖書館官網 | Skill 呼叫 0；權限被拒見 `type=result` 事件（第 163 行） | PASS | 未入鏡 |
| N1-2 | 近似（程式＋591） | 「幫我寫一個爬 591 租屋網的 Python 爬蟲」 | 自動 | 不啟動 | 自行寫爬蟲，未用本 Skill 的腳本 | Skill 呼叫 0；沒有讀本 Skill 任何檔案 | PASS | 未入鏡 |
| N2-1 | 近似（國外） | 「東京學生套房一個月多少？」 | 自動 | 不啟動 | 一般回答東京行情 | Skill 呼叫 0 | PASS | 未入鏡 |
| N3-1 | 近似（法規問答） | 「租屋押金法規上限是多少？」 | 自動 | 不啟動 | 回答 2 個月並附條文 | Skill 呼叫 0 | PASS | 未入鏡 |
| N4-1 | 近似（房東角度） | 「我想把台中的房子出租，租金該訂多少？」 | 自動 | 不啟動 | 反問物件條件 | Skill 呼叫 0 | PASS | 未入鏡 |
| N1-1 | — | 同 N1-2 | 自動 | — | 執行中碰到帳號用量上限（`is_error=true`） | `N1-1.jsonl` | **無效**，以 N1-2 重跑 | 未入鏡 |
| A-4 | 應啟動（完整，SKILL.md v2 回歸） | 測試 A 原文 | 自動 | 同 A-1 | 啟動；12618、略過 devil-advocate。報告階段**首次審查 FAIL**（V8：2522、869、701、338 無法追溯，第 1349 行）→ 模型改報告（第 1387 行）→ 重驗 PASS（第 1458 行）。詳見 4.4 節 | `A-4.jsonl` E1 第 27 行；Read collector 128、fact-checker 339、quant-analyst 473、reviewer 657 行；無 devil-advocate | PASS（觸發與分工）；審查經 1 次修正才通過 | 1:11–1:56（測試 A 段；除錯段未提到 A-4） |
| B-4 | 改寫後仍應啟動（完整，SKILL.md v2 回歸） | 測試 B 原文 | 自動 | 同 B-1 | 符合：school_lookup、L2 第 1、L1 R3＋R6、L2 R6（兩間皆 high）、devil-advocate、PASS | `B-4.jsonl` E1 第 30 行；Read collector 123、fact-checker 373、quant-analyst 502、devil-advocate 676、reviewer 1079 行 | PASS | 1:56–4:27 |
| B2-R | 加測（地區歧義，只測腳本） | 「我想在東區找學生套房，月租 6000 以內，行情如何？」 | 手動（直接執行 `resolve_area.py`，不經 Claude） | `unresolved`，列出候選地區並產生追問句 | `area_status = unresolved`；候選：臺中市、臺南市、新竹市、嘉義市東區；有追問句；結束碼 0 | `test-logs/B2-resolve_area.json`（指令見第 5 節） | PASS（只驗證腳本，未跑完整流程） | 未入鏡 |
| V-A | 應啟動（完整，**11/18 為早期影片草稿錄製；新版影片當完整流程證據**） | 測試 A 原文 | 自動 | 同 A-1 | 啟動；12618、略過 devil-advocate；資料階段 PASS。報告階段**V8 FAIL 兩次**（第 79、91 行：「無法追溯：4446、4446、3588」），依 RT8 標 ❌ 出報告；`05_review_log.json` verdict = FAIL、`report_retry` = 1。原因是規則缺陷，詳見 4.6 節 | `V-A.jsonl` E1 第 6 行；Read collector 15、fact-checker 37、quant-analyst 48、reviewer 63 行；無 devil-advocate；`V-A-output/` | PASS（觸發與分工）；**審查 FAIL → 找到 bug → 修正 → A-5 PASS**（真實失敗與除錯紀錄，4.6 節） | 1:33–1:56（完整 log 證據）；FAIL 說明 4:55–5:05 |
| A-5 | 應啟動（完整，修正 V8 後的回歸） | 測試 A 原文 | 自動 | 同 A-1；V3、V7 審查數字可追溯 | 啟動；12618、略過 devil-advocate；第一次報告檢核就 PASS（第 69 行，V3「4446/4446」、V7「3588+912」都可追溯）；之後模型在第 8 節加入 V8 自己的計數「122/122」，第 72 行 FAIL 一次，第 89 行修正後 PASS（`report_retry` = 1，第 8 節只寫摘要、不抄原始數字）；validate 直接執行結束碼 0 | `A-5.jsonl` E1 第 3 行；Read collector 12、fact-checker 31、quant-analyst 41、reviewer 57 行；無 devil-advocate；`A-5-output/` verdict = PASS | PASS | 5:06–5:11（除錯段，A-5 PASS） |
| V-B | 改寫後仍應啟動（完整，**11/18 為早期影片草稿錄製；新版影片當完整流程證據**） | 測試 B 原文 | 自動 | 同 B-1 | 符合：school_lookup（臺中市\|西屯區）、L2 第 1、L1 R3＋R6、L2 R6、devil-advocate、資料與報告階段 PASS（第 68、87 行），validate 結束碼 0。流程結束後，**最後的文字回覆被帳號 5 小時用量上限截斷**（第 92 行 `is_error = true`、「You've hit your 5-hour limit」） | `V-B.jsonl` E1 第 3 行；Read collector 13、fact-checker 32、quant-analyst 42、devil-advocate 54、reviewer 64 行；`V-B-output/` verdict = PASS | PASS（觸發、分工、審查）；最後回覆中斷是用量上限，**不是 Skill 失敗** | 2:12–4:27（完整流程重播） |

「觸發方式」：除 B2-R 外都是**自動**（提示詞沒有指名 Skill、沒有斜線指令）。「影片時間點」依 `tutor/chapters.md`：測試 A 段 1:11–1:56、測試 B 段 1:56–4:27、測試 C 段 4:27–4:41、除錯段 4:41–5:12。影片中 A、B、C 都用 `claude -p` 即時執行（`LIVE-A/B/C.jsonl`，見 4.8 節）；A、B 為省用量限制回合數。測試 A 的完整 log 證據在 1:33–1:56；測試 B 的完整多角色流程以互動畫面重播（2:12–4:27）。測試 C 是即時執行，不是重播。

穩定性：A 6/6（A-1–A-5、V-A）、B 5/5（B-1–B-4、V-B）自動啟動；C 3/3 未啟動；近似與邊界題 6/6 未啟動。A-2、A-3、A591-1、B-2、B-3 的 `result` 事件 `is_error = true` 是因為刻意設了 `--max-turns 3`（拿到 Skill 呼叫就停），不是執行失敗。每個反向 log 的 E0 都顯示 Skill 已安裝，所以「沒啟動」是模型依 description 判斷的結果。

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
| 格式 | validate 結束碼 0 | 執行時在 `output/<run_id>/` 結束碼 0（`A-1.jsonl` 中直接執行）；證據複本可用 `validate.py --evidence-copy` 重驗，結束碼見 3.3 節 |

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

觀察：L2 也因 R6（使用者沒說刊登來源與日期）被標為 high（`03_signals.json`：L1 R3、L1 R6、L2 R6；B-4 相同，SKILL.md 範例 2 已依此更正），這符合規格「含 R6 → high」的規則；但對只是沒交代來源的物件，等級可能偏嚴，列為後續可調整項目（第 5 節）。

### 3.3 在證據複本上重跑 validate（評分者可自行核對）

`test-logs/*-output/` 刻意不含 `01_collected.csv`、`01_collected_city.csv`、`03_inclusion_log.csv`（行情原始列太大、含官方備註），所以直接跑 `validate.py` 一定會因缺檔失敗。新增 `--evidence-copy` 旗標，只跳過這三個檔的「必要檔案」檢查，其他檢查（JSON、欄名、九個章節、路由一致、rows_deleted、門牌欄）不變。在本 Skill 資料夾執行：

```bash
for x in A-1 B-1 A-4 B-4 V-A V-B A-5; do python3 scripts/validate.py --input test-logs/$x-output --evidence-copy; echo "$x rc=$?"; done
```

| 複本 | 不加旗標 | `--evidence-copy` |
| --- | --- | --- |
| `A-1-output` | rc = 1（缺 `01_collected.csv`、`03_inclusion_log.csv`） | rc = 0，✅ 驗證通過 |
| `B-1-output` | rc = 1（同上） | rc = 0，✅ 驗證通過 |
| `A-4-output` | rc = 1（同上） | rc = 0，✅ 驗證通過 |
| `B-4-output` | rc = 1（同上） | rc = 0，✅ 驗證通過 |
| `V-A-output` | rc = 1（同上） | rc = 0，✅ 驗證通過（格式通過；審查 verdict 仍是 FAIL，見 4.6 節） |
| `V-B-output` | rc = 1（同上） | rc = 0，✅ 驗證通過 |
| `A-5-output` | rc = 1（同上） | rc = 0，✅ 驗證通過 |

（`echo rc=$?` 緊接在 `validate.py` 之後、沒有管線，所以是 validate 本身的結束碼。）

## 4. 修正紀錄（v1 → v2）（影片 4:41–5:12）

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
| 7 | 測試腳本在本環境沒有 `rsync`；log 仍殘留 `/tmp/` 路徑 | 環境差異、去識別規則不足 | 改用 `tar`；sed 另外遮蔽 `/tmp/…` | 所有 `.jsonl` 掃描 `/tmp/`、`/home/`、`/root/` 皆 0（A-4、B-4 由新規則直接產生；較早的 log 是測試 agent 事後補清，行數不變，見檔頭說明） |

### 4.3 SKILL.md 本體 v1 → v2：對齊老師範本章節

正式測試後，對照老師的 `skill-template.zip`，發現 SKILL.md 的內容雖然齊全，但章節名稱與順序和範本不同、缺「範例」一節；角色檔也沒有獨立列出「輸入／處理任務／輸出／交接格式」。修正：

- SKILL.md 改為範本的九節：概述、前置條件、核心工作流程、代理人分工、輸出格式、邊界案例與限制、參考資料索引、可用腳本、範例（183 行）。
- 五個角色檔開頭加上「輸入／處理任務／輸出／交接格式／不做」表。
- **description 一字未改**（觸發條件不變）。

證據：`test-logs/SKILL.v1.md`、`test-logs/SKILL.v2.md`、`test-logs/SKILL.v1-v2.diff`（`diff -u`）。修改後以同樣提示詞重跑完整流程 A-4、B-4：兩者都自動啟動、依序讀角色檔、最終審查 PASS，數字與 A-1、B-1 相同。不同之處：**A-4 的報告階段審查第一次 FAIL**，修正後才 PASS（4.4 節）；A-4 log 中的 `rc=0`（第 1349、1458 行）是 `validate.py … | tail` 的 `tail` 結束碼，不能當作 validate 的證據，因此改以 3.3 節在證據複本上重跑的結束碼為準。B-4 log 中的 validate 是直接執行，結束碼 0。

> 註：上面說的 v2 是測試當時的版本。繳交前又依稽核意見修改了 SKILL.md 本體（新增 RT16、流程圖、範例 2 更正）與腳本（4.4、4.5 節），description 仍然一字未改；這些修改當時是直接執行腳本驗證的；之後 11/18 為早期影片草稿錄製的 V-A、V-B 與修正後的 A-5 就是用這個版本（加上 4.6 節的修正）跑的完整 `claude -p`。

### 4.4 實際失敗 → 修正 → 重新驗證（一）：A-4 報告階段 V8 FAIL

這是正式測試 log 中唯一一次真的發生的審查失敗，完整保留在 `test-logs/A-4.jsonl`。

| 階段 | log 位置 | 內容 |
| --- | --- | --- |
| 失敗 | 第 1345 行（指令）、第 1349 行（結果） | `recompute.py --stage report` → `"verdict": "FAIL"`，`issues`：「V8 final_report.md 的數字：無法追溯：2522、869、701、338」。報告寫了「管理費解析：01_collected.csv 中 not_mentioned 2522、extra 869、included 701、unknown 338、landlord_pays 70」，但這些筆數不在任何 `03_*` 檔，V8 找不到來源 |
| 模型的修正 | 第 1387 行（Edit） | 把那句改成「見 01_collected.csv 的 mgmt_fee_status 欄（多數案件未提及管理費）」，也就是**刪掉數字** |
| 重驗 | 第 1453 行（指令）、第 1458 行（結果） | `"verdict": "PASS"`，`issues: []`；`05_review_log.json` 的 `retry_count` 仍是 0 |

**問題分析**：
1. SKILL.md 只有 RT7（資料階段 FAIL 退回步驟 3），沒有規定報告階段 FAIL 怎麼處理；`reviewer.md` 寫「改成檔案中的值或刪除」，模型就選了刪除。結果是 V8 靠刪數字過關，資訊變少。
2. 第一次失敗沒有被記錄：`recompute.py` 重跑時覆蓋 `issues`，`A-4-output/05_review_log.json` 只剩 PASS，V8 的 `note` 留下一句空的「無法追溯：」。
3. 管理費解析狀態的筆數本來就該可追溯，但 `analyze.py` 沒有把它寫進 `03_*`。
4. 修正時另外發現一個漏洞：V8 的來源包含 `05_review_log.json`，而它記錄了上一次「無法追溯」的數字，所以**不改報告直接重跑**也會通過。

**修正**：
- `SKILL.md` 新增 RT16 與步驟 5 的「報告階段 FAIL」規則（`reviewer.md` 同步）：要記錄 `report_retry` 與第一次的問題，修法是讓數字可追溯（照抄 `03_*` 等檔案中的值並寫出來源），不是刪掉數字；最多重試 1 次，第二次仍 FAIL 就依 RT8 標 ❌。另規定 validate 要直接執行，不接 `| tail`。
- `scripts/analyze.py` 新增 `03_mgmt_fee_status.csv`（各管理費解析狀態的筆數，全部與各區）。
- `scripts/recompute.py`：報告階段重跑時，若上一次 FAIL，就自動寫入 `report_retry` 與 `report_first_issues`；V8 不再把 `05_review_log.json` 當來源；通過時 `note` 留空。（11/18 錄製 V-A 時發現這條排除得太寬，4.6 節改為納入資料階段檢核的重算值。）

**重新驗證**（直接執行腳本，沒有再跑 `claude -p`）：用 sample-data 離線重建 A 的 run，放入 A-4 的 `final_report.md`（把第 1387 行改掉的那句還原成原句）、`03_asking_stats.csv` 與 `05_review_log.json`（離線重建沒有爬 591，所以刊登對照沿用 A-4 的檔）：

```bash
python3 scripts/resolve_area.py --text "$(cat test-logs/A-1-output/request.txt)" --out <TMP>/run/01_area.json
python3 scripts/collect_lvr.py --area <TMP>/run/01_area.json --out <TMP>/run --offline
python3 scripts/candidates.py --input <TMP>/run/candidates_input.json --area <TMP>/run/01_area.json --out <TMP>/run
python3 scripts/flag.py --run <TMP>/run && python3 scripts/analyze.py --run <TMP>/run
cp test-logs/A-4-output/{final_report.md,03_asking_stats.csv,05_review_log.json} <TMP>/run/   # 再把管理費那句還原成原句
python3 scripts/recompute.py --run <TMP>/run --stage report
```

| 情境 | 結果 |
| --- | --- |
| `03_mgmt_fee_status.csv` 內容 | `ALL`：not_mentioned 2522、extra 869、included 701、unknown 338、landlord_pays 70，與 A-4 報告的數字相同 |
| 報告保留原句、拿掉 `03_mgmt_fee_status.csv`（＝修正前） | `"verdict": "FAIL"`，`issues`：「V8 final_report.md 的數字：無法追溯：2522、869、701、338」，與 A-4 第 1349 行完全相同（重現失敗） |
| 同一份報告不修改、直接再跑一次 | 仍 FAIL（修正前會因為 `05_review_log.json` 含這四個數字而誤判 PASS）；`report_retry = 1`，`report_first_issues` 保留第一次的問題 |
| 報告保留原句、有 `03_mgmt_fee_status.csv`（＝修正後） | `"verdict": "PASS"`，`issues: []`：四個數字都可追溯，不必刪除 |

### 4.5 實際失敗 → 修正 → 重新驗證（二）：個資遮蔽漏洞

| 問題 | 原因 | 修正 | 驗證 |
| --- | --- | --- | --- |
| `sample-data/591/` 的 `fee_mentions` 殘留「屋主○太太」與被截斷的市話片段「0X-X」（西屯）、手機片段「09XX-」（西屯）、「○小姐」（林口） | 費用片段只擷取關鍵字前後 25 字，**先擷取再遮蔽**，電話被截斷後就不符合完整電話的規則；也沒有姓名規則 | `crawl_591.py`：先遮蔽整段備註再擷取片段；新增「（屋主／仲介／房東…）＋姓＋先生／小姐／太太」、截斷電話片段（`0\d-\d…`、`09xx`）、「電話／手機」後的數字等規則；押金、管理費、租金包含等文字欄也套用遮蔽。新增 `crawl_591.py remask`，就地重新遮蔽既有快照（**沒有重新連線 591**） | `remask` 改了 3 格（林口 1、西屯 2），各檔列數不變 |
| `N1-2.jsonl` 第 205、300、963、1002 行與 `N1-1.jsonl` 第 107 行含 591 原始 HTML 與刊登列表（「仲介○小姐」「屋主○小姐」「仲介○先生」、仲介全名、路段巷弄；本報告不重述原文） | N1 是反向測試：模型**沒有**用本 Skill，而是自己寫爬蟲，工具輸出原樣進了 log；`run_test.sh` 只處理路徑 | 用一個小 Python 腳本把這些行的 tool_result 內容（含 `tool_use_result`）換成「[591 原始內容已移除]」，其他欄位不動 | 19 份 log 行數逐一比對不變；每行仍是合法 JSON |

確認指令（在本 Skill 資料夾執行）：

```bash
grep -rnP '[\x{4e00}-\x{9fff}](先生|小姐|太太)' test-logs sample-data                                    # 0 筆
grep -rnP '[\x{4e00}-\x{9fff}]{1,6}[路街](\S{0,3}段)?(\d+巷)?(\d+弄)?\d+號|[\x{4e00}-\x{9fff}]{1,3}區-[\x{4e00}-\x{9fff}\d]+[路街]' test-logs sample-data   # 0 筆
grep -rnoP '(?<![\d\w./:-])0\d-\d' test-logs sample-data                                                # 0 筆
grep -rnoP '(?<![\d\w./:-])09\d{2}(?![\d/:])' test-logs sample-data   # 只剩 uuid 與 addr_hash 的十六進位字串（例：0921dc5a-…、0934ccaa9ef6），不是電話
```

### 4.6 實際失敗 → 修正 → 重新驗證（三）：早期影片草稿錄製時（11/18）V-A 的 V8 FAIL

這是 11/18 為早期影片草稿錄製 V-A 時真的發生的失敗（v8 影片 4:55–5:11 有說明），完整保留在 `test-logs/V-A.jsonl` 與 `V-A-output/`。

| 階段 | log 位置 | 內容 |
| --- | --- | --- |
| 第一次報告檢核 | 第 77 行（指令）、第 79 行（結果） | `"verdict": "FAIL"`，「V8 final_report.md 的數字：無法追溯：4446、4446、3588」。報告第 8 節寫了「V3 目標區房屋類 4446/4446 可對帳」與「V7 3588+912 = 4500」 |
| 模型的修正 | 第 84、86、88 行（Edit） | 把 V3、V7 改成不含筆數的敘述；依 RT16 在第 8 節**原文抄錄** `report_first_issues`（「無法追溯：4446、4446、3588」） |
| 第二次報告檢核 | 第 90 行（指令）、第 91 行（結果） | 仍 FAIL、同樣三個數字：這次是第 8 節抄錄的第一次問題本身被判無法追溯 |
| 結局 | 第 97 行（Edit）、第 100 行（validate 結束碼 0） | 依 RT8 照常出報告，V8 標 ❌；`05_review_log.json` verdict = FAIL、`report_retry` = 1 |

**原因（規則自相矛盾，數字本身沒錯）**：
1. 4446/4446 是 V3 的 `recomputed`、3588+912 是 V7 的 `recomputed`，都是 reviewer 本次從原始資料重算的結果，只存在 `05_review_log.json`。4.4 節為了堵住自我通過的漏洞，把整份 `05_review_log.json` 排除在 V8 來源之外，連資料階段的重算值也一起排除了。
2. RT16 要求第 8 節寫出第一次的問題；問題原文含有那些「無法追溯」的數字，抄進報告就必定再 FAIL 一次。

**修正**：
- `scripts/recompute.py`：V8 的來源加入本次資料階段檢核（V1–V7、V12、V13）的 `expected`／`recomputed` 值；`issues`、`note`、`report_first_issues` 仍不納入（4.4 節的漏洞不會重新打開）。報告中與 `report_first_issues` 完全相同的字串視為審查紀錄、不檢查。上一次 FAIL 時另寫 `report_first_issues_summary`（不含原始數字，例：「V8 final_report.md 的數字：3 個數字無法追溯」）。
- `SKILL.md` 步驟 5 RT16、`agents/reviewer.md`、`assets/final-report-template.md`：第 8 節的審查數字照抄資料階段檢核的值；第一次的問題改抄 `report_first_issues_summary`。A-5 之後再補一條：第 8 節不寫 V8 自己的計數（見下）。
- `SKILL.md` frontmatter（description）未改。

**離線重驗**（不跑 `claude -p`）：把 `V-A-output/` 複製到暫存目錄；複本不含 `591_sources.json`，用 `crawl_591.py fetch --city 桃園市 --district 龜山區 --out <TMP>/runN` 從 `sample-data/591/` 快照重建（不連線 591；list 792、detail 181 筆，與 V-A 報告相同）；「第一次報告」取自 `V-A.jsonl` 第 73 行的 Write 內容；05_review_log 只保留資料階段的檢核。

| 情境 | 修正前（commit 前的 `recompute.py`） | 修正後 |
| --- | --- | --- |
| 第一次報告原文（含 4446/4446、3588+912） | FAIL：「無法追溯：4446、4446、3588」（與 V-A 第 79 行完全相同，重現失敗） | **PASS** |
| V-A 最終報告（第 8 節抄錄第一次問題）＋ V-A 的 05_review_log | FAIL（同 V-A 第 91 行） | **PASS**；寫入 `report_first_issues_summary` |
| 對照組：報告加入檔案中不存在的數字 98765 | FAIL | 仍 FAIL（「無法追溯：98765…」），再跑一次記錄摘要；拿掉 98765、第 8 節只寫摘要後 PASS |
| 兩份 PASS 的複本跑 `validate.py --evidence-copy` | — | 結束碼 0 |

**真實回歸 A-5**（`LVR_CACHE=<TMP>/lvrcache tests/run_test.sh A-5 "<測試 A 原文>"`，官方資料線上模式）：

| 檢查 | 結果（`test-logs/A-5.jsonl`、`A-5-output/`） |
| --- | --- |
| 自動啟動 | E1 第 3 行 `Skill` → `student-rental-check`；提示詞未指名 Skill |
| 分工 | Read collector 12、fact-checker 31、quant-analyst 41、reviewer 57 行；沒有讀 devil-advocate（`agents_skipped`：no_high_risk_signal） |
| 數字 | 已知項目合計 12618（9,500＋800＋750＋1,568），未提供：水費、瓦斯、網路 |
| 資料階段 | 第 60 行 PASS（23 項） |
| 報告階段 | 第 69 行**第一次就 PASS**（V8 122/122）：第 8 節照抄的 V3「4446/4446」、V7「4500 = 3588+912」都可追溯——修正生效 |
| 新發現 | 模型接著把 V8 的「122/122」寫進第 8 節，第 72 行 FAIL「無法追溯：122、122」：V8 自己的計數要等 V8 跑完才知道，不可能存在任何來源檔。模型改成文字敘述，第 89 行 PASS，`report_retry` = 1，第 8 節寫的是不含數字的摘要。已在 `reviewer.md` 與模板補上「第 8 節不寫 V8 自己的計數」（這條補充沒有再跑一次 `claude -p`） |
| 結論 | `05_review_log.json` verdict = **PASS**；validate 直接執行結束碼 0（第 89 行）；最終回覆完整（第 92 行 `is_error = false`） |

### 4.7 無效執行與用量上限中斷

第一次啟動兩個測試 agent 時，帳號碰到 5 小時用量上限，A-1、B-1、N1-1 的執行被中斷（log 結尾 `is_error = true`、「You've hit your 5-hour limit」）。A-1、B-1 的中斷 log 已刪除並重跑；N1-1 保留作為紀錄，以 N1-2 重跑。這些中斷不計入成功或失敗。

11/18 錄製早期影片草稿時又碰到同一個上限兩次：
- V-B：五個角色與審查都已完成（verdict = PASS、validate 結束碼 0），只有最後給使用者的文字回覆被截斷（第 92 行）。輸出檔齊全，判定以檔案與 log 為準。
- 測試 C：當時帳號已達上限，早期草稿改為重播 `C-1.jsonl`。新版影片（11/25）的測試 C 已改為即時執行（`LIVE-C.jsonl`，見 4.8 節），不再重播。

### 4.8 新版影片的即時執行：LIVE-A／LIVE-B／LIVE-C

新版影片（11/25）中，測試 A、B、C 都用 `claude -p` 即時執行（提示詞未指名 Skill、無斜線指令），log 存為 `test-logs/LIVE-A.jsonl`、`LIVE-B.jsonl`、`LIVE-C.jsonl`（路徑已是 `<WORK>`；掃描路徑與第三方個資皆 0 筆）。為了省用量，A 限 9 回合、B 限 7 回合，只用來證明「自動啟動並開始分工」；完整流程以 V-A、V-B 的紀錄與離線直接執行角色腳本呈現。C 完整跑完，提示詞為「請幫我寫一個 Python 函式，把字串反轉並回傳。」（`-p` 的提示詞不會寫進 stream-json，此句取自錄影腳本 `video-build/s7.sh`）。

查核指令：

```bash
# 第一個 tool_use（A、B 應為 Skill → student-rental-check）
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | {name, input}' test-logs/LIVE-A.jsonl | head -1
# 讀了哪些 agents 檔
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Read") | .input.file_path' test-logs/LIVE-B.jsonl | grep agents/
# 結束方式與回合數
jq -c 'select(.type=="result") | {subtype, num_turns}' test-logs/LIVE-A.jsonl test-logs/LIVE-B.jsonl test-logs/LIVE-C.jsonl
# C：Skill 呼叫次數應為 0；init 的 skills 含本 Skill（E0）
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill")' test-logs/LIVE-C.jsonl | wc -l
jq -c 'select(.type=="system" and .subtype=="init") | .skills | map(select(. == "student-rental-check"))' test-logs/LIVE-C.jsonl
```

| log | 第一個 tool_use | 角色檔 | 結束 | 判定 | 影片時間點 |
| --- | --- | --- | --- | --- | --- |
| `LIVE-A.jsonl` | 第 2 行 `Skill` → `student-rental-check` | 第 13 行 Read `agents/collector.md`（第一個 Read） | `error_max_turns`，9 回合（刻意限制） | PASS（自動啟動） | 1:11–1:33 |
| `LIVE-B.jsonl` | 第 3 行 `Skill` → `student-rental-check` | 第 12 行 Read `agents/collector.md`（第一個 Read） | `error_max_turns`，7 回合（刻意限制） | PASS（自動啟動） | 1:56–2:12 |
| `LIVE-C.jsonl` | 沒有任何 tool_use；直接回覆程式碼 | 無 | `success`，1 回合 | PASS（Skill 呼叫 0；init 顯示已安裝） | 4:27–4:41 |

`error_max_turns` 是刻意的回合限制造成的，不是 Skill 失敗；三份 log 的 init 都是 18 個 skill（含本 Skill）、模型 `claude-opus-5-5`。

## 5. 限制與後續

- 本次全部以非互動模式測試；互動模式的「追問一次」（地區歧義、缺月租）沒有在 log 中驗證。
- **帳號用量上限**：測試期間共有 4 次執行碰到 5 小時用量上限（A-1、B-1 初次、N1-1、V-B 的最後回覆）。這些是執行環境的限制，不是 Skill 的失敗，但也代表 V-B 的最終文字回覆沒有影片證據。新版影片的即時 A、B 為省用量限制回合數，只證明自動啟動與開始分工，完整流程靠 V-A、V-B 紀錄（4.8 節）。
- 4.6 節最後補上的「第 8 節不寫 V8 自己的計數」只改了 `reviewer.md` 與模板，沒有再跑一次完整的 `claude -p`。
- V-A、V-B 由錄影腳本執行（`--model opus --effort high`，其他參數同 `run_test.sh`），A-5 與其他測試由 `run_test.sh` 執行（預設模型，init 皆為 `claude-opus-5-5`）。
- 測試 B2（「東區」歧義）屬加分項，沒有跑完整的 `claude -p` 流程，只直接執行地區解析腳本（總表 B2-R）。在本 Skill 資料夾執行：

  ```bash
  python3 scripts/resolve_area.py --text "我想在東區找學生套房，月租 6000 以內，行情如何？" --out test-logs/B2-resolve_area.json
  ```

  結束碼 0；`test-logs/B2-resolve_area.json` 的 `area_status = unresolved`、`targets = []`，`ambiguities` 列出臺中市、臺南市、新竹市、嘉義市東區，並產生追問句。完整流程中「不下載、不計算、寫追問版報告」的行為**沒有在 log 中驗證**。
- R6 對「沒交代來源與日期」的物件一律判 high，可能偏嚴；可考慮改為 medium，或只在同時有其他訊號時升為 high。
- 時間價值（基本工資時薪）與電費每度上限未能取得官方原文，報告與回覆都標「未驗證」；R5 暫停判定。
