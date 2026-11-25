source /workspace/bigdata-week11/rec/lib.sh
banner "測試 B｜換個說法仍應啟動（即時執行）＋ 高風險 → devil-advocate"
P="$(cat test-logs/V-B-output/request.txt)"
note "提示詞：${P:0:62}…" 0.5
type_cmd "claude -p \"\$(cat test-logs/V-B-output/request.txt)\" --output-format stream-json --max-turns 6 | 過濾工具事件"
/workspace/bigdata-week11/rec/claude_live.sh LIVE-B 6 "$P"
run "python3 scripts/resolve_area.py --text \"\$(cat test-logs/V-B-output/request.txt)\" --out ../b_area.json" 2
note "完整執行紀錄 V-B：R3 先匯訂金 → 路由加入 devil-advocate" 0.3
run "jq -c '.signals[0]' test-logs/V-B-output/03_signals.json; jq -c '.agents_planned' test-logs/V-B-output/00_routing.json" 2
run "grep -m2 -E '風險等級|建議' test-logs/V-B-output/04_risk_report.md | cut -c1-105" 4
