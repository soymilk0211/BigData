# Agent 1 正向測試結果（student-rental-check）

- 測試日期：2026-11-18
- 執行方式：`tests/run_test.sh <ID> "<提示詞>" [max_turns]`（`claude -p --setting-sources project,local --output-format stream-json --verbose`），執行前 `export LVR_CACHE=~/BigData/week11/work/rent-raw`
- 觸發方式：全部為**自動**觸發，提示詞一字未改，也沒有指名 Skill
- 機器可讀版本：`test-logs/agent1-positive-results.json`
- 無效執行：A-1、B-1 的第一次執行被 API 用量上限中斷（result `is_error=true`，訊息為 5-hour limit）。協調者已刪除那兩份 log，本報告用的是重跑結果，那兩次不算 FAIL。重跑後 7 份 log 都沒有用量上限訊息。A-2、A-3、B-2、B-3、A591-1 的 `is_error=true` 是 `subtype=error_max_turns`，代表照設計在第 3 回合停止，不是錯誤。

## 總表

| 測試 ID | 類型 | 觸發方式 | 預期 | 實際 | E0（init skills） | E1 行號 | E2 讀到的 agents 檔（行號） | 判定 | 原因 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | 完整流程 | 自動 | 觸發 Skill；single；讀 4 個必跑 agent；不讀 devil-advocate；成本 12618 | 觸發；single；讀 4 個 agent；沒讀 devil-advocate；12618 | 有 | 29 | collector(125)、fact-checker(356)、quant-analyst(469)、reviewer(692) | PASS | 每項完整流程檢查都符合預期（見下方） |
| A-2 | 只看啟動（max_turns 3） | 自動 | 觸發 Skill | 觸發 | 有 | 31 | collector(132) | PASS | 有 E1 |
| A-3 | 只看啟動（max_turns 3） | 自動 | 觸發 Skill | 觸發 | 有 | 28 | collector(124) | PASS | 有 E1 |
| B-1 | 完整流程 | 自動 | 觸發；compare；臺中市\|西屯區／school_lookup；L1 有 R3、風險 high；讀 devil-advocate | 全部符合 | 有 | 34 | collector(134)、fact-checker(393)、quant-analyst(516)、devil-advocate(692)、reviewer(1077) | PASS | 每項完整流程檢查都符合預期（見下方） |
| B-2 | 只看啟動（max_turns 3） | 自動 | 觸發 Skill | 觸發 | 有 | 33 | collector(120) | PASS | 有 E1 |
| B-3 | 只看啟動（max_turns 3） | 自動 | 觸發 Skill | 觸發 | 有 | 35 | collector(133) | PASS | 有 E1 |
| A591-1（加測） | 只看啟動（max_turns 3） | 自動 | 觸發 Skill | 觸發 | 有 | 27 | collector(120) | PASS | 有 E1 |

**群組判定**
- **A：PASS**（規則是 A-1..A-3 三次都要有 E1，且 A-1 符合完整流程預期。結果 3/3 有 E1，A-1 全部符合）
- **B：PASS**（規則是 B-1..B-3 至少 2 次有 E1，且 B-1 符合完整流程預期。結果 3/3 有 E1，B-1 全部符合）
- **A591：PASS**（加測，有 E1）

只看啟動的測試都是第 1 個 assistant 回合就呼叫 `Skill(student-rental-check)`。之後的回合是兩次 Bash（建立 run 資料夾、寫 request/routing）和一次 Read `agents/collector.md`，然後在 max_turns 停下，所以沒有執行任何 scripts/*.py。

## result 事件

| 測試 ID | subtype | num_turns | total_cost_usd | duration_ms | result 行號 |
| --- | --- | --- | --- | --- | --- |
| A-1 | success | 21 | 0.6732 | 109423 | 1520 |
| A-2 | error_max_turns | 4 | 0.1152 | 9938 | 137 |
| A-3 | error_max_turns | 4 | 0.1141 | 8879 | 129 |
| B-1 | success | 25 | 0.7900 | 130154 | 2028 |
| B-2 | error_max_turns | 4 | 0.1136 | 8875 | 126 |
| B-3 | error_max_turns | 4 | 0.1144 | 9510 | 138 |
| A591-1 | error_max_turns | 4 | 0.1181 | 8991 | 125 |

## E2：執行過的腳本（Bash 指令中的 scripts/*.py，含行號）

- A-1：resolve_area.py、collect_lvr.py(165)；crawl_591.py、candidates.py(245)；flag.py(382)；analyze.py(501)；recompute.py(729)；recompute.py、validate.py(1293)
- B-1：resolve_area.py(163)；collect_lvr.py(192)；crawl_591.py(223)；candidates.py(287)；flag.py(419)；analyze.py(552)；recompute.py(1119)；recompute.py、validate.py(1785)
- A-2、A-3、B-2、B-3、A591-1：沒有（在 max_turns 3 停下）

## 完整流程關鍵數字

### A-1（龜山區獨立套房，single）

| 項目 | 預期 | 實際 | 結果 |
| --- | --- | --- | --- |
| `validate.py --input test-logs/A-1-output` | 只因刻意未複製的檔案失敗 | 結束碼 1：缺少必要檔案 `01_collected.csv`、`03_inclusion_log.csv`（run_test.sh 刻意排除這兩個檔） | 符合 |
| `validate.py --input <WORK>/output/20261118-220902` | 0 | 結束碼 0：「✅ 驗證通過」 | 符合 |
| 00_routing.mode | single | single | 符合 |
| 00_routing.agents_skipped | devil-advocate／no_high_risk_signal | `[{"agent":"devil-advocate","reason":"no_high_risk_signal"}]` | 符合 |
| 01_area.targets | — | 桃園市\|龜山區，area_source=user_explicit（destination 長庚大學，source=school_lookup） | 符合 |
| 05_review_log | — | verdict=PASS、retry_count=0、issues=[] | 符合 |
| true_monthly_cost_known | 12618 ±1 | 12618（= 月租 9500 + 管理費 800 + 電費 750〔5 元/度 × 150 度〕+ 通勤時間成本 1568） | 符合 |
| rent_per_ping | 1187.5 | 1187.5（true_cost_per_ping 1577.2） | 符合 |
| unstated_items | 列出未提供項目 | water;gas;internet | 符合 |
| 行情位置 | — | 分組 桃園市\|龜山區\|student_suite\|114S4-115S3，百分位 49.9，與中位數差 -0.1%，outlier=none | — |
| 03_signals | 無訊號 | signals=[]；not_evaluated 有 R5（電費上限未驗證）、R7（無評論） | 符合 |
| 04_risk_report.json | 不存在 | 不存在 | 符合 |
| Read devil-advocate.md | 沒有 | 沒有（log 中 Read 只出現 4 個必跑 agent） | 符合 |
| 資料 | — | data_mode=online（使用 LVR_CACHE），county_files 只有 h（桃園市），季別 114S4–115S3、112S4 | — |
| final_report.md 第一行 | 寫分析地區 | 「本次分析地區：桃園市龜山區（來源：使用者指定）」 | 符合 |

### B-1（逢甲兩間候選，compare）

| 項目 | 預期 | 實際 | 結果 |
| --- | --- | --- | --- |
| `validate.py --input test-logs/B-1-output` | 只因刻意未複製的檔案失敗 | 結束碼 1：缺少必要檔案 `01_collected.csv`、`03_inclusion_log.csv` | 符合 |
| `validate.py --input <WORK>/output/20261118-220902` | 0 | 結束碼 0：「✅ 驗證通過」 | 符合 |
| 00_routing.mode | compare | compare（candidate_count=2） | 符合 |
| 00_routing.agents_planned／skipped | 加入 devil-advocate | planned 有 5 個，含 devil-advocate；skipped=[] | 符合 |
| 01_area.targets | 臺中市\|西屯區／school_lookup | 臺中市\|西屯區，area_source=school_lookup（matched_text=逢甲） | 符合 |
| 01_collect_manifest.county_files | 只有 b | `[{"city_code":"b","city":"臺中市","file":"b_lvr_land_c.csv"}]` | 符合 |
| 03_ranking.csv | 2 列 | 2 列：第 1 名 L2（5500）、第 2 名 L1（7000，delta 1500）；兩間的 unstated 都是 mgmt;water;gas;internet;elec;commute | 符合 |
| 03_signals：L1 有 R3 | 有 | L1：R3（命中「先匯訂金」，來源 user_input）、R6；L2：R6 | 符合 |
| 04_risk_report：L1 risk_level | high | L1=high（建議避開）；L2=high（因為 R6） | 符合 |
| final_report 提醒排名第一不等於可以租 | 有 | 第 54 行：「**排名第一不等於可以租**：L2 便宜只是因為目前只知道月租……」 | 符合 |
| Read devil-advocate.md | 有 | 有（第 692 行） | 符合 |
| 05_review_log | — | verdict=PASS、retry_count=0、issues=[] | 符合 |
| 成本 | — | L1：7000，rent_per_ping 1000.0，百分位 55.2；L2：5500，缺坪數，無法算百分位 | — |

**觀察（不影響判定）**：B-1 的 L2（雅房）也被判成 risk_level=high，依據只有 R6（STALE_LISTING＋UNKNOWN_SOURCE），因為使用者沒有給刊登日期和來源。這個結果符合 Skill 規則，但每次使用者沒寫來源時都會出現 R6，可能讓所有候選物件都被標成 high，交給其他 Agent 參考。另外，A-1 與 B-1 同時啟動，run_id 同為 20261118-220902。兩者在不同暫存目錄，所以沒有互相影響。

## 絕對路徑清理

run_test.sh 的 sed 只會取代完整的暫存目錄字串。取代後的 log 仍殘留這幾種路徑：init 事件的 `scratchpad_path`（`/tmp/claude-0/...`）、`messaging_socket_path`（`/tmp/cc-socks/...`），以及 stream_event 分段送出的 `/tmp/t`、`/tmp/tmp` 片段。各檔殘留數：A-1 7、A-2 2、A-3 1、A591-1 1、B-1 7、B-2 2、B-3 2。我用下列指令清理了 A-1、A-2、A-3、B-1、B-2、B-3、A591-1 這 7 份 .jsonl：

```bash
sed -i -E 's#/tmp/claude-0/[^"]*#<WORK>/scratchpad#g; s#/tmp/cc-socks/#<WORK>/cc-socks/#g; s#/tmp/#<WORK>/#g; s#/home/[^/"]+/#~/#g; s#/root/#~/#g' <ID>.jsonl
```

清理後確認：test-logs 下所有 `.jsonl` 都沒有 `/root/`、`/home/`、`/tmp/`。每行仍可被 `json.loads` 解析，行數不變，所以上面記錄的行號仍然有效。C-*、N-* 等其他 Agent 的 log 我沒有動，檢查時本來就是 0。`*-output/` 資料夾內也沒有絕對路徑。暫存目錄路徑與輔助檔（`.workdir`）都放在 `/tmp/claude-0/` 底下的 scratchpad，沒有寫進 test-logs。

## 查核指令

E0／E1／E2／result 的抽取（Python，逐行解析 stream-json）：

```python
import json, re
for ln, line in enumerate(open("test-logs/A-1.jsonl", encoding="utf-8"), 1):
    ev = json.loads(line)
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        print("E0", ln, "student-rental-check" in ev.get("skills", []))
    if ev.get("type") == "assistant":
        for c in ev["message"]["content"]:
            if c.get("type") != "tool_use": continue
            if c["name"] == "Skill" and c["input"].get("skill") == "student-rental-check": print("E1", ln)
            if c["name"] == "Read": print("READ", ln, c["input"]["file_path"])
            if c["name"] == "Bash": print("PY", ln, re.findall(r"scripts/(\w+\.py)", c["input"]["command"]))
    if ev.get("type") == "result":
        print("RESULT", ln, ev["subtype"], ev["num_turns"], ev["total_cost_usd"], ev["duration_ms"])
```

等價的 jq 指令：

```bash
# E1 行號
jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill" and .input.skill=="student-rental-check")' test-logs/A-1.jsonl   # 內容
grep -n '"name":"Skill"' test-logs/A-1.jsonl | grep student-rental-check | cut -d: -f1                                                                         # 行號
# E0
jq -c 'select(.type=="system" and .subtype=="init") | (.skills | index("student-rental-check") != null)' test-logs/A-1.jsonl
# E2 Read 路徑
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Read") | .input.file_path' test-logs/B-1.jsonl
# result
jq -c 'select(.type=="result") | {subtype, num_turns, total_cost_usd, duration_ms}' test-logs/B-1.jsonl
```

輸出檢查：

```bash
python3 scripts/validate.py --input test-logs/A-1-output; echo $?
python3 scripts/validate.py --input <WORK>/output/<run_id>; echo $?      # 暫存目錄（run_test.sh 最後印出）
jq '{mode, agents_skipped}' test-logs/A-1-output/00_routing.json
jq '.targets[] | {area_key, area_source}' test-logs/B-1-output/01_area.json
jq '{verdict, retry_count, issues}' test-logs/B-1-output/05_review_log.json
jq '[.county_files[].city_code]' test-logs/B-1-output/01_collect_manifest.json
jq '.signals[] | select(.listing_id=="L1") | .signal' test-logs/B-1-output/03_signals.json
jq '.listings[] | {listing_id, risk_level}' test-logs/B-1-output/04_risk_report.json
grep -n '排名第一不等於可以租' test-logs/B-1-output/final_report.md
grep -c -E '/root/|/home/|/tmp/' test-logs/*.jsonl
```
