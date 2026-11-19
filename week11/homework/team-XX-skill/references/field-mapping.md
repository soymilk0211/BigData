# 欄位對照

## 1. 實價登錄 35 欄 → `01_collected.csv`

| 原始欄名 | 正規化欄位 | 轉換 |
| --- | --- | --- |
| 鄉鎮市區 | district、area_key | 縣市由檔名代碼決定（CSV 內沒有縣市欄）；`area_key = 縣市|區` |
| 交易標的 | target_type | 原值；判斷車位綁約、非住宅 |
| 土地位置建物門牌 | addr_hash | SHA-256 前 12 碼後刪除原欄 |
| 租賃年月日 | rent_date | 民國 `yyyMMdd` → 西元；無效 → 空值＋`DATE_INVALID` |
| 租賃筆棟數 | parcel_counts_raw | 原值 |
| 租賃層次／總樓層數 | floor、floor_whole、total_floors | 「十二層」→12；「全」「整棟租賃」→ floor_whole；多層取第一個 |
| 建物型態、主要用途 | building_type、main_use | 原值 |
| 建築完成年月 | build_completed、building_age_years | 民國 7 碼 → 西元；屋齡以 rent_date 計 |
| 建物總面積平方公尺、車位面積平方公尺 | area_m2、parking_area_m2、area_ping | `area_ping = (建物 − 車位) × 0.3025`，小數 2 位 |
| 總額元、車位總額元 | rent_total、parking_rent、rent_excl_parking | 去千分位；空白 → 0 |
| 單價元平方公尺 | unit_price_m2_raw | 只用於 V3 對帳 |
| — | rent_per_ping | `rent_excl_parking / area_ping`，小數 1 位；area_ping ≤ 0 → 空值 |
| 建物現況格局-房／廳／衛／隔間 | rooms、halls、baths、partition | 數字；有／無 → True／False |
| 有無管理組織／管理員／電梯／附傢俱 | has_mgmt_org、has_manager、has_elevator、has_furniture | 有／無／空白 → True／False／空值 |
| 備註 | mgmt_fee_status、mgmt_fee_amount、mgmt_fee_with_parking、note_tags、note_raw | 見 `cleaning-rules.md` 第 2 節；note_raw 已遮蔽門牌樣式 |
| 編號 | record_id | 原值 |
| 出租型態 | rent_type、rent_type_group | 獨立套房、分租套房 → student_suite；分租雅房 → student_room；整棟(戶)出租、分層出租 → whole_unit；其他 → other；空白 → unknown |
| 租賃期間 | lease_start、lease_end、lease_months | `1150701~1160630` → 2026-07-01、2027-06-30、12 |
| 附屬設備 | equipment、equipment_count | 以「、」切分 |
| 租賃住宅服務 | rental_service、is_social_housing | 以「社會住宅」開頭或備註含「社會住宅」→ True |
| 土地面積、都市／非都市分區、主要建材、車位類別 | （不用） | — |

注意：建物總面積是登記面積，大樓含公設，所以「每坪租金」不等於室內坪數的租金。

## 2. 候選物件 `01_candidates.csv`

| 欄位 | 值 | 說明 |
| --- | --- | --- |
| listing_id、label | L1… | 依出現順序 |
| city、district、area_key、area_source | | 沒寫沿用目標地區 |
| rent_type_group | student_suite／student_room／whole_unit | |
| rent_monthly、price_basis | 元；user_stated／asking_591 | 591 來源為刊登租金 |
| area_ping、area_basis | 坪；user／591_use_area／unstated | 591 為使用坪數，不比實價登錄百分位 |
| mgmt_fee、mgmt_status | 元；stated／included／unstated | 隱藏成本：沒寫 = unstated（未提供） |
| elec_price_per_kwh、elec_status | 元／度；per_kwh／taipower／included／unstated | taipower = 台電計價（電價未驗證，不計） |
| water_fee／gas_fee／internet_fee 與 `<k>_status` | 元；stated／included／unstated | |
| deposit_months | 月 | R4 |
| destination_label、commute_minutes_oneway、commute_mode、commute_fare_per_trip | | 通勤分鐘沒寫 = 未計通勤 |
| source_type、source_url、posted_date | 591／fb／school_portal／friend／user／unknown | R6 依據 |
| notes_text、risk_hits_591 | 原文 | R3 關鍵字比對對象 |
| status、status_reason | ok／incomplete | 缺月租 → incomplete |

## 3. 591 欄位 → `591_list.csv`／`591_detail.csv`

| 591 資料 | 欄位 | 說明 |
| --- | --- | --- |
| 列表 `price`、`kind_name`、`area_name`、`address`（只取區） | asking_rent、kind_name、use_area_ping、district | kind 2、3 → student_suite；4 → student_room；1 → whole_unit |
| 列表 `role_name` | role | 只留身分（屋主／代理人／仲介），去掉姓名 |
| 刊登頁 `rent_calculation_data.deposit` | deposit_text、deposit_months | 「二個月租金」→ 2 |
| `manage_fee`、`water_fee_type`、`electric_fee_type`、`price_contain_text` | mgmt_fee、water_fee_type、electric_fee_type、price_contain_text | 「一度5元」→ 每度 5 元；「含租金內」→ included |
| `service.facility` 的 net、gas | net_included、gas_facility | |
| `tags` | tags、rent_subsidy_ok、tax_ok | 「租金補貼」「可報稅」 |
| `favData.posttime` | posted_date | 台北時間 |
| `remark`（屋況介紹） | risk_hits、fee_mentions | 只存命中的關鍵字與遮蔽後的費用片段，不存全文 |
