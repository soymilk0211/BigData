source /workspace/bigdata-week11/rec/lib.sh
banner "主題與資料來源｜student-rental-check：台灣學生租屋行情與避雷"
run "ls" 1.2
run "ls sample-data sample-data/591" 1.2
run "python3 -c \"import pandas as pd; d=pd.read_csv('sample-data/lvr_rent_sample_areas.csv'); print(d.groupby('鄉鎮市區').size().to_string()); print(d[['season','鄉鎮市區','建物型態','總額元']].head(3).to_string(index=False))\"" 2.5
run "grep -m2 -E '^## [12]\\.' references/data-sources.md" 2
run "grep -A2 '## 1. 一句話' test-logs/V-A-output/final_report.md | tail -1" 5
