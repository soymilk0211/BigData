# 大數據應用 Week 10：Clustering and PCA

## 練習題目

X = 每週自學時數（hr），Y = 小測驗分數（分），共 30 筆。請算出：

- 平均值 X、平均值 Y
- 共變異數
- 標準差 X、標準差 Y
- 相關係數

> 老師還沒說明要繳交的形式，等公布後再補。

## 檔案

```
week10/
├── README.md
├── 題目照片.jpg                   課堂投影片照片（原始題目）
├── data/
│   └── study_hours_scores.csv    練習的 30 筆資料（欄位 id, x_hours, y_score，已與投影片 PDF 核對）
└── teacher/                      老師在 Teams「week10 Clustering and PCA」放的原始檔案
    ├── 03_Clustering.pdf         課堂投影片（練習題在「練習：X = 每週自學時數」那頁）
    ├── students_200.csv          分群範例資料（student_id, chinese, english, true_cluster）
    ├── students_200資料分群.txt   true_cluster 說明：A=國文高/英文較低、B=英文高/國文較低、C=兩科中上
    └── pca_300_example_dataset.csv  PCA 範例資料（Feature_A ~ Feature_F，300 筆）
```
