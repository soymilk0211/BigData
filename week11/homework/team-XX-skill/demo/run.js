/* 重播資料來自一次真實的 Claude Code CLI 執行（test-logs/B-4），不是模擬。 */
window.DEMO_RUN = {
  source: {
    id: "B-4",
    run_id: "20261118-230656",
    recorded_at: "2026-11-18 23:06（臺北時間）",
    tool: "Claude Code CLI",
    log: "test-logs/B-4.jsonl",
    output: "test-logs/B-4-output/",
    turns: 23,
    duration_sec: 135,
    review: "PASS"
  },
  question: "我在逢甲附近找房，有兩間在猶豫：第一間是分租套房 7 坪，一個月 7,000，房東說要先匯訂金才能看房；第二間是雅房，一個月 5,500，管理費不知道。哪間比較划算？會不會踩雷？",
  skill: {
    name: "student-rental-check",
    title: "學生租屋行情與避雷",
    invoked_with: "台中逢甲附近，比較兩間：(1) 分租套房 7 坪，月租 7,000，房東要求先匯訂金才能看房；(2) 雅房，月租 5,500，管理費未知。哪間划算？有無踩雷風險？"
  },
  agents: [
    {
      id: "collector",
      no: "①",
      name: "蒐集員",
      name_en: "collector",
      brief: "找出地區、把資料與物件收齊",
      wait: "待命",
      did: [
        "把「逢甲」對到臺中市西屯區（學校查表），目的地是逢甲大學。",
        "下載內政部實價登錄近四季，西屯區留下 4,782 筆租賃資料（全市 30,596 筆）。",
        "對照 591 房屋交易網刊登快照：清單 3,881 筆。",
        "整理兩間候選物件：分租套房月租 7,000 元／7 坪；雅房月租 5,500 元（沒寫坪數）。"
      ],
      outputs: ["01_area.json", "01_candidates.csv", "實價登錄與 591 資料表"]
    },
    {
      id: "fact-checker",
      no: "②",
      name: "時效驗證員",
      name_en: "fact-checker",
      brief: "只標記問題，不刪資料",
      wait: "待命",
      did: [
        "4,782 筆裡標記了 4,062 筆有狀況的資料，一筆都沒刪。",
        "西屯行情窗內約 55% 與社會住宅有關（2,296／4,137），行情可能被拉低，後面要分開看。",
        "兩間都沒寫刊登來源與日期，也沒寫管理費、水電、瓦斯、網路和通勤。",
        "第二間沒有坪數，之後沒辦法算每坪租金。"
      ],
      outputs: ["02_flags.csv", "02_factcheck_summary.json"]
    },
    {
      id: "quant-analyst",
      no: "③",
      name: "精算師",
      name_en: "quant-analyst",
      brief: "算行情與已知花費，標出風險",
      wait: "待命",
      did: [
        "西屯套房月租中位數 8,000 元（扣掉社宅後是 10,500 元）；雅房中位數 6,400 元。",
        "第一間每坪 1,000 元，落在套房行情第 55.2 百分位，價格本身合理；若不含社宅，其實偏便宜。",
        "已知花費目前只能算月租：第一間 7,000 元、第二間 5,500 元，差 1,500 元。其他費用都標「未提供」，沒有隨便補數字。",
        "第一間命中「先匯訂金」高風險訊號（R3），兩間來源都不清楚（R6），因此要叫出踩雷獵人。"
      ],
      outputs: ["03_market_stats.csv", "03_cost_breakdown.csv", "03_signals.json", "圖表"]
    },
    {
      id: "devil-advocate",
      no: "④",
      name: "踩雷獵人",
      name_en: "devil-advocate",
      brief: "有高風險訊號才出場",
      wait: "沒訊號就不出場",
      optional: true,
      did: [
        "因為第一間提到「先匯訂金才能看房」，這個角色被啟動。",
        "第一間列為高風險：最壞情況是假房東收了訂金就失聯；「分租」也可能是二房東，不一定有屋主同意。建議：對方不肯先看房，就不要匯任何錢。",
        "第二間是提醒：來源與日期不明，要先問還能不能租、對方是誰、管理費和電費怎麼算、幾坪、衛浴幾人共用。",
        "提醒「排名第一不等於可以租」：現在只比了月租，雜費一加，名次就可能反过来。"
      ],
      outputs: ["04_risk_report.md"]
    },
    {
      id: "reviewer",
      no: "⑤",
      name: "審查員",
      name_en: "reviewer",
      brief: "把數字重新計算一遍，再寫報告",
      wait: "待命",
      did: [
        "從原始資料獨立把行情、成本和訊號重新計算一次。",
        "審查結果：全部通過（PASS），沒有需要重跑。",
        "寫成 final report，並用白話回覆同學。"
      ],
      outputs: ["final_report.md", "05_review_log.json"]
    }
  ],
  report: {
    title: "學生租屋行情與避雷報告",
    summary: [
      { label: "地區", text: "臺中市西屯區（由「逢甲」查表得出）" },
      { label: "價格", text: "兩間月租都算合理。第一間每坪 1,000 元，約在套房行情第 55.2 百分位。" },
      { label: "已知花費", text: "目前只能比月租：第一間 7,000 元、第二間 5,500 元。管理費、水電、網路、通勤都還不知道。" },
      { label: "風險", text: "第一間「先匯訂金才能看房」，是高風險，建議先別碰。" },
      { label: "建議", text: "第二間可以繼續問清楚再比；現在還不能確定哪間比較划算。" }
    ],
    conclusion: "第一間（分租套房 7,000）先別碰；第二間（雅房 5,500）可以繼續問，但現在還不能確定它比較划算。",
    reply_path: "test-logs/B-4.jsonl 的最終回覆",
    report_path: "test-logs/B-4-output/final_report.md",
    charts: [
      { src: "assets/rpp_box_by_group.png", alt: "西屯各類型每坪租金箱型圖" },
      { src: "assets/true_cost_stacked.png", alt: "兩間已知花費對照（目前只有月租）" }
    ]
  }
};
