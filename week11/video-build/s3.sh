source /workspace/bigdata-week11/rec/lib.sh
banner "測試 A｜應啟動（Claude Code 即時執行，自動觸發，未指名 Skill）"
P="$(cat test-logs/V-A-output/request.txt)"
note "提示詞：${P:0:60}…" 0.5
type_cmd "claude -p \"\$(cat test-logs/V-A-output/request.txt)\" --output-format stream-json --max-turns 8 | 過濾工具事件"
/workspace/bigdata-week11/rec/claude_live.sh LIVE-A 8 "$P"
sleep 1
run "jq -c 'select(.type==\"assistant\").message.content[]|select(.type==\"tool_use\" and .name==\"Skill\").input.skill' ../live-logs/LIVE-A.jsonl" 4
