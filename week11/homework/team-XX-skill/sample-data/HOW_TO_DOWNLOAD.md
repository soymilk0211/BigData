# 範例資料與重建方式

## 內容

| 檔案 | 內容 | 來源 |
| --- | --- | --- |
| `lvr_rent_sample_areas.csv` | 112S4、114S4、115S1、115S2、115S3 五季中，桃園市龜山區、新北市林口區、臺中市西屯區的全部租賃案件（10,429 列）。門牌欄清空並改存 `addr_hash`（SHA-256 前 12 碼），備註中的門牌樣式已遮蔽 | 內政部實價登錄「不動產租賃」批次資料（政府資料開放授權條款） |
| `591/<縣市>_<區>/591_list.csv` | 該區 591 全部刊登的列表層級資料：刊登租金、類型、使用坪數、標籤、刊登身分（屋主／代理人／仲介） | 591 租屋網（刊登價，非成交價） |
| `591/<縣市>_<區>/591_detail.csv` | 學生型刊登（獨立套房、分租套房、雅房）的刊登頁資料：押金、管理費、水電計價、租金包含項目、踩雷關鍵字命中、費用片段（已遮蔽） | 同上 |
| `591/<縣市>_<區>/591_manifest.json` | 取得時間、請求數、筆數、錯誤 | — |

全部是真實資料，沒有模擬資料。591 快照不含姓名、電話、LINE、Email、門牌、經緯度與原始網頁。

## 自行下載實價登錄

1. 到 https://plvr.land.moi.gov.tw/DownloadOpenData，或直接下載各季：
   `https://plvr.land.moi.gov.tw/DownloadSeason?season=115S3&type=zip&fileName=lvr_landcsv.zip`（季別換成 112S4、114S4、115S1、115S2）。
2. 存成 `<季別>.zip`，放在同一個資料夾（例：`data/lvr-cache/`）。
3. 重建本範例檔：

   ```bash
   python scripts/collect_lvr.py --build-sample --cache data/lvr-cache --out sample-data/lvr_rent_sample_areas.csv
   ```

連線不穩時（曾遇過 TLS 中斷），腳本會以 TLS 1.2 重試 3 次。

## 自行更新 591 快照

```bash
python scripts/crawl_591.py area --city 桃園市 --district 龜山區 --out sample-data/591/桃園市_龜山區
```

請求間隔隨機 1–3 秒，學生型刊登頁每次最多 300 筆（`--detail-cap`）。取得流程參考 Rent591Watcher（https://github.com/ryk001/Rent591Watcher，無授權條款，只參考流程、未複製程式碼）。快照超過 30 天，Skill 會改為即時爬取。
