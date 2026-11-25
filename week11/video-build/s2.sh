source /workspace/bigdata-week11/rec/lib.sh
banner "Skill 架構：SKILL.md（Trigger）與五個 Agent"
run "ls agents scripts" 2
run "sed -n 1,14p SKILL.md" 7
run "grep -h -m1 -A7 '^| 輸入' agents/fact-checker.md | cut -c1-105" 4
run "jq -c '{from,to,status,artifacts:[.artifacts[].path]}' test-logs/V-B-output/handoff_2_fact-checker.json" 5
