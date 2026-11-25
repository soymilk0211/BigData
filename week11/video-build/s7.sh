source /workspace/bigdata-week11/rec/lib.sh
banner "測試 C｜不應啟動（即時執行）：一般程式問題"
P="請幫我寫一個 Python 函式，把字串反轉並回傳。"
note "提示詞：$P" 0.5
type_cmd "claude -p \"$P\" --output-format stream-json | 過濾工具事件"
/workspace/bigdata-week11/rec/claude_live.sh LIVE-C 0 "$P"
run "jq -s '[.[]|select(.type==\"assistant\").message.content[]|select(.type==\"tool_use\" and .name==\"Skill\")]|length' ../live-logs/LIVE-C.jsonl | sed 's/^/Skill 呼叫次數 = /'" 4
