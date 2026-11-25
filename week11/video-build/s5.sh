source /workspace/bigdata-week11/rec/lib.sh
banner "測試 A 完整執行紀錄（V-A.jsonl）：啟動證據 E1–E3"
L=test-logs/V-A.jsonl
run "jq -r 'select(.type==\"assistant\").message.content[]|select(.type==\"tool_use\" and (.name==\"Skill\" or .name==\"Read\"))|\"\\(.name)  \\(.input.skill // (.input.file_path|split(\"/\")|.[-2:]|join(\"/\")))\"' $L" 3
run "jq -c '{agents_planned,agents_skipped}' test-logs/V-A-output/00_routing.json" 3
run "grep -o '真實每月總成本為已知項目合計 12618 元＋未提供：水費、瓦斯、網路' test-logs/V-A-output/final_report.md" 4
