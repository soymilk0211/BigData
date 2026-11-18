# 資料來源與驗證紀錄

## 1. 主要資料：內政部實價登錄「不動產租賃」批次資料（實價登錄租金）

| 項目 | 內容 | 驗證（2026-11-18） |
| --- | --- | --- |
| 下載頁 | https://plvr.land.moi.gov.tw/DownloadOpenData | HTTP 200 |
| 季別下載 | `https://plvr.land.moi.gov.tw/DownloadSeason?season=<季別>&type=zip&fileName=lvr_landcsv.zip` | 112S4、114S4、115S1、115S2、115S3 皆 HTTP 200、檔頭 `PK`；115S3 為 16,508,126 bytes |
| zip 內容 | `manifest.csv`、`schema-main-rent.csv`、21 個縣市租賃主檔 `<代碼>_lvr_land_c.csv` | 代碼對照見 `county-codes.csv`（取自 115S3 manifest）；連江縣只有買賣檔 |
| 檔案格式 | UTF-8 with BOM；第 1 列中文欄名、第 2 列英文欄名；35 欄 | 五季欄名完全相同 |
| 授權 | 政府資料開放授權條款 | 引用時註明來源 |

採用季別：114S4–115S3（目前行情，約 12 個月）、112S4（兩年前對照）。參數在 `cost-params.json` 的 `seasons_current`、`season_trend`。

`sample-data/lvr_rent_sample_areas.csv` 是五季中桃園市龜山區、新北市林口區、臺中市西屯區的全部租賃列（10,429 列），門牌欄已改為 `addr_hash`（SHA-256 前 12 碼）、備註中的門牌樣式已遮蔽。重建方式見 `sample-data/HOW_TO_DOWNLOAD.md`。

## 2. 補充資料：591 租屋網（刊登租金）

| 項目 | 內容 |
| --- | --- |
| 列表頁 | `https://rent.591.com.tw/list?region=<地區代碼>&section=<區代碼>&sort=posttime_desc&page=<n>`（每頁 30 筆） |
| 刊登頁 | `https://rent.591.com.tw/<刊登編號>` |
| 解析方式 | 頁面內嵌的 `window.__NUXT__` 資料（以 node 執行後讀取）；刊登頁的 `rent_calculation_data`、`costData` 提供押金、管理費、水電計價、租金包含項目 |
| 地區代碼 | `591-regions.csv`（22 個縣市，2026-11-18 以列表頁 seoData 標題驗證）、`591-sections.csv`（已驗證的區；其他區由列表資料自動找出） |
| 取得流程 | 參考 Rent591Watcher（https://github.com/ryk001/Rent591Watcher）：先取得 session cookie，再讀列表頁與刊登頁。該專案沒有授權條款，本 Skill **只參考流程、未複製程式碼** |
| 禮貌限制 | 單一 session、每次請求間隔隨機 1–3 秒、每次執行刊登頁最多 300 筆（`crawl_591_detail_cap`）、請求總數上限 |
| 去識別化 | 只保存租金、坪數、類型、樓層、押金與費用文字、刊登身分（屋主／代理人／仲介）、標籤、刊登日期、區與刊登編號；姓名、電話、LINE、Email、門牌、經緯度、原始網頁一律不存 |
| 快照 | `sample-data/591/<縣市>_<區>/`：測試地區的去識別化快照，30 天內有效（`snapshot_max_age_days`），讓測試不依賴即時連線 |

刊登租金是開價，偏誤方向與實價登錄不同，因此只另做 `03_asking_stats.csv` 並列比較，永不合併進行情分組（reviewer V13 檢查）。591 坪數為使用坪數，與實價登錄的登記坪數（含公設）基準不同，不比每坪百分位。

## 3. 參數來源

| 參數 | 狀態 | 來源 |
| --- | --- | --- |
| 押金上限 2 個月 | 已查證 | 租賃住宅市場發展及管理條例第 7 條（全國法規資料庫，2026-11-18） |
| 時間價值 196 元／小時 | 未驗證 | 2026 年基本工資時薪；勞動部公告未能於本環境取得 |
| 電費每度上限 | 未驗證 | 住宅租賃定型化契約應記載事項（台電夏月最高級距）；原文未取得，R5 暫停判定 |
| 學校所在區 | 未於線上查證 | `school-districts.csv` 各列註記；教育部大專校院名錄網站在本環境無法連線 |

## 4. 痛點背景（不作為資料）

- Dcard〈中興大學租屋看房注意事項懶人包〉https://www.dcard.tw/f/nchu/p/238630083
- PTT home-sale〈已經有租屋實價登錄？〉https://www.ptt.cc/bbs/home-sale/M.1723345067.A.C1F.html
