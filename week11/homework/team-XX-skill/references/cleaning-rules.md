# 清理規則、旗標與例外處理

只標記、不刪除：每個旗標都對應到一條規則 ID；是否納入統計由 quant-analyst 決定並寫在 `03_inclusion_log.csv`。

## 1. 通用規則與旗標

| 規則 | 內容 | 旗標（嚴重度） | 對統計的影響 |
| --- | --- | --- | --- |
| CR-01 | `utf-8-sig` 讀檔；第 2 列第 1 欄為 `The villages and towns urban district` 才跳過 | — | E4 |
| CR-02 | 欄名須與 35 欄 schema 完全相同 | — | 不符即停止（E3） |
| CR-03 | 只讀目標縣市的 `<代碼>_lvr_land_c.csv`；`01_collected.csv` 只留目標區，`01_collected_city.csv` 留全縣市 | — | — |
| CR-04 | 數值去千分位與空白；非數字 → 空值 | — | — |
| CR-05 | 日期換算；分析窗 = 最新季最大租賃日往前 12 個月 | DATE_INVALID（warn）、STALE（info）、LATE_FILING（info，比該季中位日早 180 天以上） | 不進目前行情 |
| CR-06 | 刪門牌前先算 `addr_hash` | — | — |
| CR-07 | 重複 | DUP_ID（warn）、DUP_CROSS_SEASON（warn，同 `addr_hash+rent_date+rent_total` 在不同季） | 只保留一列／最新季 |
| CR-08 | 非住宅、含稅、類型空白、管理費不明、分段租金 | NON_RESIDENTIAL、TAX_INCLUDED、TYPE_MISSING、MGMT_FEE_UNKNOWN、STEP_RENT（info） | 前兩者排除；類型空白不進學生組 |
| CR-09 | 面積 ≤ 0 或 > 200 坪；車位綁約；全區粗分組 IQR 外 | AREA_INVALID（warn）、PARKING_BUNDLED、OUTLIER_PRELIM（info） | 面積無效排除；車位用 `rent_excl_parking` |
| CR-10 | 社會住宅 | SOCIAL_HOUSING（info） | 主分析保留，另算不含社宅版本 |
| CR-11 | 候選物件來源與刊登日期 | UNKNOWN_SOURCE（warn）、STALE_LISTING（warn，無日期或超過 30 天）、INCOMPLETE（warn） | R6 依據 |
| CR-12 | 地名正規化（台→臺）；地區來源 | AREA_FROM_LOOKUP（info）、AREA_NO_DISTRICT_DATA（warn） | 報告第一行寫地區來源 |
| CR-13 | 月租來自 591 | ASKING_PRICE（info） | 刊登租金，不進行情 |
| CR-14 | 隱藏成本或通勤未提供 | COST_UNSTATED、COMMUTE_UNSTATED（info） | 不補值；報告列「未提供」 |
| CR-15 | 評論為模擬資料 | SIMULATED（info） | 本 Skill 不使用模擬評論 |

## 2. 備註欄管理費解析（依序比對，命中即停）

| 順序 | 條件 | 結果 |
| --- | --- | --- |
| 1 | 「含管理費」且前面不是「不」 | `included`，0 |
| 2 | 「管理費…由出租人負擔」 | `landlord_pays`，0 |
| 3 | `管理費\D{0,8}(\d[\d,]{2,5})元?`，且有「承租人負擔／承租人自付／不包含在租金／未計入租金／另有／另計」 | `extra`，取金額；含「停車位管理費」→ `mgmt_fee_with_parking` |
| 4 | 有「管理費」但不符合以上 | `unknown`＋MGMT_FEE_UNKNOWN |
| 5 | 沒提到 | `not_mentioned` |

其他標籤：續租案件 → RENEWAL；多人共同承租 → MULTI_TENANT；含稅 → TAX_INCLUDED；約定不同租金 → STEP_RENT；免租 → RENT_FREE_PERIOD。

## 3. 隱私

輸出不含門牌欄；備註與 591 費用片段先遮蔽「路／街／段／巷／弄／號」門牌樣式、車位編號、電話、LINE、Email。

## 4. 例外處理（E1–E22）

| 代號 | 情況 | 處理 |
| --- | --- | --- |
| E1／E2 | 官方網站 TLS 中斷、逾時、非 200、不是 zip | 重試 3 次（指數退避、TLS 1.2）→ 改用 sample-data（RT9） |
| E3 | 欄名與 schema 不符 | 停止並回報缺少／多出的欄位，不猜 |
| E4 | 第 2 列不是英文表頭 | 不跳列，manifest 警告 |
| E5 | 編碼錯誤 | 停止並回報 |
| E6／E7／E8 | 日期無效、面積 0、類型空白 | 對應旗標 |
| E9／E18 | 分組有效樣本 < 10 | 合併類型 → 全縣市 → insufficient（不判 R1／R2）；`window_8q` 本版未下載，記為 `window_8q_unavailable` |
| E10 | 管理費（實價登錄）抽不出 | 標記；候選物件的管理費只看使用者或刊登內容，不用行情推估 |
| E11 | 候選物件缺月租 | RT10 |
| E12 | 候選物件不在目標區 | 加入該區，各自比對行情 |
| E13 | 沒給通勤時間 | 未計通勤（不套預設分鐘） |
| E14 | reviewer 檢核失敗 | RT7／RT8 |
| E15 | 圖表沒有中文字型 | 改英文標籤並註明 |
| E16 | 地區缺少或有歧義 | 互動追問一次；非互動不猜（RT13） |
| E17 | 區名不在資料中 | 打錯字：列候選請確認；確定存在但沒資料：全縣市＋AREA_NO_DISTRICT_DATA |
| E19 | 縣市沒有租賃檔（連江縣） | 告知無資料，不算行情 |
| E20 | 新竹市、嘉義市資料不分區 | 以全市計算並標記 |
| E21 | 離線模式但樣本沒有該地區 | 告知需連線，不以其他地區代替 |
| E22 | 跨縣市 | 分別讀各縣市檔，不跨縣市合併 |
| E23 | 591 連線失敗或被擋 | 不中斷；報告寫「本次沒有刊登租金對照」，可請使用者貼上刊登內容 |
