source /workspace/bigdata-week11/rec/lib.sh
banner "完整流程：每個角色呼叫的腳本（離線 sample-data，直接執行）"
R=../run/live; rm -rf ../run/live; mkdir -p $R; cp test-logs/V-A-output/{request.txt,candidates_input.json} $R/
note "① collector：地區解析、實價登錄、591 快照、候選物件" 0.3
run "python3 scripts/resolve_area.py --text \"\$(cat $R/request.txt)\" --out $R/01_area.json" 0.8
run "python3 scripts/collect_lvr.py --area $R/01_area.json --out $R --offline" 0.8
run "python3 scripts/candidates.py --input $R/candidates_input.json --area $R/01_area.json --out $R" 1
note "② fact-checker：逐列加旗標，不刪資料" 0.3
run "python3 scripts/flag.py --run $R" 1.5
note "③ quant-analyst：行情、真實每月總成本、R1–R7 訊號" 0.3
run "python3 scripts/analyze.py --run $R --asking $R" 1.5
note "④ devil-advocate：signals 為空 → 不啟動" 1
note "⑤ reviewer：獨立重算（不 import analyze.py）" 0.3
run "python3 scripts/recompute.py --run $R --stage data" 4
