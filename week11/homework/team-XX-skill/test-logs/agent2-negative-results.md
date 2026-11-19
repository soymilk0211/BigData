# Agent 2：反向測試結果（student-rental-check 不該啟動的情境）

- 日期：2026-11-18
- 執行方式：`tests/run_test.sh <ID> "<提示詞>" 8`（乾淨暫存目錄安裝 Skill，`claude -p --setting-sources project,local --output-format stream-json --verbose --max-turns 8`）
- 機器可讀版：`test-logs/agent2-negative-results.json`
- 結論：**7 組全部 PASS，沒有誤觸發。** 每個 log 的 `system/init` 事件（第 3 行）都列出 `student-rental-check`，代表 Skill 已安裝而且可以選用；所有 log 的 Skill 呼叫都是 0，也沒有任何 tool_use 讀取本 Skill 的檔案。
- 例外：N1-1 在第 3 回合因 API 用量上限中斷（`is_error=true`，`api_error=usage_limit_reached`），標為**無效（用量上限）**，不算 PASS 或 FAIL，已用同一提示詞重跑一次，存成 N1-2。

## 總表

| 測試 ID | 提示詞 | 預期 | E0 行號（init 含本 Skill） | Skill 呼叫次數 | 讀本 Skill 檔案 | result（行號／subtype／turns／USD） | 回答摘要 | 判定 | 原因 |
|---|---|---|---|---|---|---|---|---|---|
| C-1 | 幫我寫一個 Python 函式，輸入兩個日期字串，回傳相差幾天。 | 不啟動（一般程式） | 3 ✔ | 0 | 否（0 筆） | 95／success／1／0.0593 | 直接給 `days_between()`（`datetime.strptime` 相減後取絕對值），沒有呼叫任何工具 | PASS | E0 有安裝，Skill 呼叫 0 |
| C-2 | 同上 | 不啟動 | 3 ✔ | 0 | 否 | 122／success／1／0.0643 | 同上，附參數說明，沒有呼叫任何工具 | PASS | 同上 |
| C-3 | 同上 | 不啟動 | 3 ✔ | 0 | 否 | 106／success／1／0.0615 | 同上，沒有呼叫任何工具 | PASS | 同上 |
| C2-1 | 林口預售屋現在一坪大概多少？ | 不啟動（預售屋） | 3 ✔ | 0 | 否 | 247／success／3／0.0924 | 試用 WebSearch（不在允許清單，被拒），改用既有知識列出林口各區預售單價（約 55～68 萬／坪），並說明不是即時數字 | PASS | Skill 呼叫 0 |
| C3-1 | 長庚大學圖書館期末考週開到幾點？ | 不啟動（校務） | 3 ✔ | 0 | 否 | 163／success／4／0.0980 | 試用 WebSearch／WebFetch（被拒），說無法確認，建議查圖書館官網與公告 | PASS | Skill 呼叫 0 |
| N1-1 | 幫我寫一個爬 591 租屋網的 Python 爬蟲 | 不啟動（一般程式） | 3 ✔ | 0 | 否 | 111／success（`is_error=true`）／3／0.0752 | 中斷前用 Bash 抓 591 頁面分析；result 文字為「You've hit your 5-hour limit」 | **無效（用量上限）** | 429 `usage_limit_reached`，依規則以 N1-2 重跑 |
| N1-2 | 幫我寫一個爬 591 租屋網的 Python 爬蟲 | 不啟動（一般程式） | 3 ✔ | 0 | 否 | 1182／success／9／0.3558 | 用 curl 和 BeautifulSoup 分析 591 後寫出 `<WORK>/rent591.py` 並實測（台北套房 60 筆、新北整層輸出 CSV），沒有用到本 Skill 的 scripts/ | PASS | Skill 呼叫 0；8 筆 tool_use（Bash/Write/Edit）都沒有提到 student-rental-check |
| N2-1 | 東京學生套房一個月多少？ | 不啟動（台灣以外） | 3 ✔ | 0 | 否 | 206／success／1／0.0831 | 用一般知識列出東京各區套房月租（日圓與台幣對照）、學生會館、初期費用，建議查 SUUMO、HOME'S | PASS | Skill 呼叫 0 |
| N3-1 | 租屋押金法規上限是多少？ | 不啟動（近似題：法規） | 3 ✔ | 0 | 否 | 158／success／1／0.0747 | 押金上限 2 個月（租賃住宅條例第 7 條、土地法第 99 條），並說明訂金與押金的差別；結尾說「如果你是學生在找房，也可以把刊登資訊或網址貼給我」，這只是提議 | PASS | 近似題，Skill 呼叫 0 |
| N4-1 | 我想把台中的房子出租，租金該訂多少？ | 不啟動（近似題：房東角度） | 3 ✔ | 0 | 否 | 176／success／1／0.0749 | 反問地點、類型、坪數等條件，建議參考實價登錄與 591，並說提供資訊後可以估租金範圍 | PASS | 近似題，Skill 呼叫 0 |

### 各組判定

| 組別 | 依據 | 判定 |
|---|---|---|
| C（同一提示跑 3 次） | C-1、C-2、C-3 的 Skill 呼叫都是 0，都沒有讀本 Skill 檔案（3 次都沒有任何 tool_use） | PASS |
| C2 預售屋 | C2-1 | PASS |
| C3 校務 | C3-1 | PASS |
| N1 爬蟲程式 | N1-2（N1-1 無效） | PASS |
| N2 東京 | N2-1 | PASS |
| N3 押金法規（近似題） | N3-1 | PASS |
| N4 房東定價（近似題） | N4-1 | PASS |

**誤觸發：無。** 每個 log 裡 `student-rental-check` 都只出現 1 次，就是第 3 行 init 事件的 `skills` 清單。

## 其他說明

1. **路徑去識別化**：腳本已把暫存目錄換成 `<WORK>`、家目錄換成 `~/`，但 log 裡仍留有 `/tmp/` 開頭的路徑：init 事件的 `scratchpad_path` 和 `messaging_socket_path`（10 個 log 各 1 行），以及 N1-1、N1-2 的 Bash 指令和工具輸出（N1-1 有 3 行，N1-2 有 13 行）。處理方式如下：先用 `sed -E 's#/tmp/claude-0/[^"\\ ]*/scratchpad#<WORK>/scratchpad#g; s#/tmp/#<WORK>/#g; s#/home/[^/"]+/#~/#g; s#/root/#~/#g'` 替換，再逐行用 `json.loads` 確認仍是合法 JSON。處理後，本 Agent 產生的 10 個 .jsonl 中 `/tmp/`、`/home/`、`/root/` 都是 0 筆。A-*、B-* 是其他 Agent 的檔案，沒有動。
2. **N1-1 無效**：result 事件的 `api_error_status=429`、`api_error_type=rate_limit_error`、`terminal_reason=api_error`。原始檔 N1-1.jsonl 沒有刪除，留作紀錄。中斷前的 3 個回合裡，Skill 呼叫也是 0，但這只當參考，不計入判定。
3. **N1-2 的 num_turns=9**：比設定的 max_turns=8 多 1，但 `subtype=success`、`terminal_reason=completed`，是正常結束，不影響判定。
4. **C2-1、C3-1 的網路工具被拒**：WebSearch／WebFetch 不在 `--allowedTools` 裡，所以被拒絕，跟 Skill 是否觸發無關。
5. **並行數**：第 1 批（C-1～C-3）和第 2 批（C2-1、C3-1、N1-1）的執行時間有重疊，最多同時跑 6 個，超過「一次最多 3 個」的上限。N1-1 碰到用量上限可能跟這有關。第 3 批（N2-1、N3-1、N4-1）和重跑的 N1-2 都在上限內。
6. **N3-1 的結尾提議**：模型知道有學生租屋的能力，所以順口提了一句，但沒有呼叫 Skill。依任務規則，這題算 PASS。

## 查核指令

### jq（在 test-logs/ 執行）

```bash
for f in C-1 C-2 C-3 C2-1 C3-1 N1-1 N1-2 N2-1 N3-1 N4-1; do
  # E0：init 行號，以及 skills 是否含本 Skill
  jq -r 'select(.type=="system" and .subtype=="init")
         | [input_line_number, (.skills|index("student-rental-check")!=null)] | @tsv' $f.jsonl
  # Skill 呼叫次數（每行一個數字，加總）
  jq '[select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill")] | length' $f.jsonl | paste -sd+ | bc
  # input 含 student-rental-check 的 tool_use 數
  jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use")
         | .input | tostring | select(contains("student-rental-check"))' $f.jsonl | wc -l
  # result：行號、subtype、is_error、num_turns、total_cost_usd、前 200 字
  jq -c 'select(.type=="result") | [input_line_number,.subtype,.is_error,.num_turns,.total_cost_usd,(.result[:200])]' $f.jsonl
done
# 本 Skill 名稱在每個 log 出現的行數（預期都是 1，即 init 行）
grep -c 'student-rental-check' C-*.jsonl C2-1.jsonl C3-1.jsonl N*.jsonl
# 確認沒有殘留絕對路徑（預期輸出 0）
grep -lE '/tmp/|/home/|/root/' C-*.jsonl C2-1.jsonl C3-1.jsonl N*.jsonl | wc -l
```

jq 跑出來的結果（與上表一致）：

```
C-1 E0=3 true skill=0 ref=0 res=[95,"success",false,1,0.0593046]
C-2 E0=3 true skill=0 ref=0 res=[122,"success",false,1,0.0642806]
C-3 E0=3 true skill=0 ref=0 res=[106,"success",false,1,0.0614886]
C2-1 E0=3 true skill=0 ref=0 res=[247,"success",false,3,0.0923724]
C3-1 E0=3 true skill=0 ref=0 res=[163,"success",false,4,0.097999]
N1-1 E0=3 true skill=0 ref=0 res=[111,"success",true,3,0.0751796]
N1-2 E0=3 true skill=0 ref=0 res=[1182,"success",false,9,0.3558048]
N2-1 E0=3 true skill=0 ref=0 res=[206,"success",false,1,0.0830578]
N3-1 E0=3 true skill=0 ref=0 res=[158,"success",false,1,0.0747138]
N4-1 E0=3 true skill=0 ref=0 res=[176,"success",false,1,0.0748618]
```

### Python（與 jq 交叉比對，產生 JSON 用的同一套邏輯）

```python
import json
SK = "student-rental-check"
def analyze(path):
    r = {"E0_line": None, "E0_skill_installed": False, "skill_calls": [], "refs": [], "result": None}
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        ev = json.loads(line)
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            r["E0_line"], r["E0_skill_installed"] = ln, SK in (ev.get("skills") or [])
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content") or []:
                if c.get("type") == "tool_use":
                    s = json.dumps(c.get("input", {}), ensure_ascii=False)
                    if c.get("name") == "Skill": r["skill_calls"].append(ln)
                    if SK in s: r["refs"].append((ln, c.get("name")))
        if ev.get("type") == "result":
            r["result"] = dict(line=ln, subtype=ev.get("subtype"), is_error=ev.get("is_error"),
                               num_turns=ev.get("num_turns"), cost=ev.get("total_cost_usd"),
                               head=(ev.get("result") or "")[:200])
    return r
```
