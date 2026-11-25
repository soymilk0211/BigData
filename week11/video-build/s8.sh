source /workspace/bigdata-week11/rec/lib.sh
banner "失敗分析與修正：V8 FAIL → 修正 → 回歸測試 PASS"
run "grep -c '^[-+][^-+]' test-logs/SKILL.v1-v2.diff; diff <(sed -n 2,14p test-logs/SKILL.v1.md) <(sed -n 2,14p test-logs/SKILL.v2.md) && echo 'description 一字未改'" 2.5
run "jq -c '{verdict, issues}' test-logs/V-A-output/05_review_log.json" 3
run "jq -c '{verdict, report_retry, issues}' test-logs/A-5-output/05_review_log.json" 3
run "python3 scripts/validate.py --input test-logs/A-5-output --evidence-copy | tail -2" 4
