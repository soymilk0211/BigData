<!-- reviewer 依此骨架撰寫 final_report.md。{…} 一律換成檔案中的值；整節不適用時保留標題並寫明原因。 -->

本次分析地區：{city}{district}（來源：{使用者指定／學校查表／地址解析／使用者確認}）　｜　run：{run_id}

# 學生租屋行情與避雷報告

## 1. 一句話結論

{一句話：價格在行情中的位置＋已知項目合計＋最重要的風險或「未偵測到高風險訊號」。}

## 2. 你問的問題、分析地區與模式

- 你的問題：{request.txt 摘要}
- 分析地區：{area_key}（{area_source}）；通勤目的地：{destination 或「未提供」}
- 模式：{market_only／single／compare}；候選物件 {n} 間
- 資料：實價登錄 {seasons}（{data_mode}）；591 刊登 {快照日期或即時爬取時間，或「本次沒有」}

## 3. 行情摘要

| 分組 | 含社宅 | n | 退回 | 月租中位數 | 每坪 Q1／中位數／Q3 | P10 | 上界 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {group_key} | {include_social_housing} | {n} | {fallback 或 —} | {rent_median} | {rpp_q1}／{rpp_median}／{rpp_q3} | {rpp_p10} | {upper_fence} |

![每坪租金箱型圖](charts/rpp_box_by_group.png)

### 3.1 591 刊登租金對照（刊登價≠成交價，未與實價登錄合併）

| 地區 | 類型 | 刊登筆數 | 刊登月租中位數 | 實價登錄月租中位數 | 刊登比實價登錄高 |
| --- | --- | --- | --- | --- | --- |
| {area_key} | {rent_type_group} | {n_listings} | {asking_rent_median} | {lvr_rent_median} | {asking_vs_lvr_pct}% |

註：591 坪數為使用坪數，實價登錄為登記坪數（含公設），兩者每坪租金不可直接比較。

## 4. 候選物件真實每月總成本

| 物件 | 月租（基準） | 管理費 | 電費 | 水費 | 瓦斯 | 網路 | 通勤時間成本 | 已知項目合計 | 未提供 | 每坪 | 行情百分位 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {listing_id} | {rent}（{price_basis}） | {mgmt_fee 或「未提供」} | {elec_cost} | … | … | … | {commute_time_cost} | {true_monthly_cost_known} | {unstated_items} | {rent_per_ping} | {market_percentile} |

![真實成本堆疊圖](charts/true_cost_stacked.png)

排名（compare）：{依 03_ranking.csv；comparable = False 時寫「不完全可比」並附 rank_common_items}

## 5. 風險提醒

{有 devil-advocate：取自 04_risk_report.md，含「排名第一不等於可以租」。沒有：「未偵測到高風險訊號（R1–R7）」。}

未能判定：{03_signals.json.not_evaluated 逐條}

## 6. 資料限制

- 實價登錄只含已申報的租賃案件，並非全部成交；申請租金補貼者較常登錄。
- 社會住宅相關案件比例：{02_factcheck_summary.json.notes}
- 實價登錄坪數為登記面積（含公設），每坪租金不等於室內坪數的租金。
- 管理費解析：{mgmt_fee_status 分布或「見 01_collected.csv」}
- 樣本不足的退回：{fallback 或「無」}
- 591 為刊登租金，可能高於成交價，也可能已下架。
- 未驗證項目：{cost-params.json 中 status = 未驗證 的參數}
- 本 Skill 不使用模擬資料；評論只採用使用者提供的內容（本次：{有／無}）。

## 7. 假設參數表

| 參數 | 值 | 類別 | 狀態 | 來源 |
| --- | --- | --- | --- | --- |
| {kwh_per_month 等每個 kind ≠ 分析設定 的參數} | {value} | {kind} | {status} | {source} |

物件事實（管理費、水電瓦斯網路、押金、通勤分鐘）沒有預設值：未提供就不計入。

## 8. 審查紀錄

| 檢核 | 結果 | 說明 |
| --- | --- | --- |
| V1 筆數與地區 … V13 刊登租金未混入行情 | ✅／❌ | {05_review_log.json} |

審查結論：{verdict}；重試次數：{retry_count}。{FAIL 時：審查未通過項目：…}

## 9. 附錄：看房殺價話術

{依 references/negotiation-tips.md，至少四句；空格只填檔案中的數字。}

<!-- ===== 追問版（area_status = unresolved 時改用以下內容，九節標題保留，內容寫「地區未確定，未計算」） =====
本次分析地區：未確定（需要你補充）
## 1. 一句話結論：地區無法唯一確定，尚未計算行情。
## 2. 你問的問題…：{question}；可選地區：{ambiguities}
## 3–8：地區未確定，未計算。
## 9. 附錄：補上縣市與區後即可產生話術。
-->
