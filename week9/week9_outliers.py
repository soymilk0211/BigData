# 大數據應用 Week 9：離群值偵測（Z-score vs IQR）
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

def percentile(data_sorted, p):
    # 與講義相同的分位數算法（線性內插）
    n = len(data_sorted)
    k = (n - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < n:
        return data_sorted[f] + c * (data_sorted[f + 1] - data_sorted[f])
    return data_sorted[f]

rows = []
for name in "ABCDE":
    data = pd.read_csv(f"data/dataset{name}.csv")["value"].tolist()
    s = pd.Series(data)
    # Z-score
    mean = np.mean(data); std = np.std(data)
    z_out = [x for x in data if abs((x - mean) / std) > 3]
    # IQR
    data_sorted = sorted(data)
    Q1 = percentile(data_sorted, 25); Q3 = percentile(data_sorted, 75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR; upper = Q3 + 1.5 * IQR
    iqr_out = [x for x in data if x < lower or x > upper]
    sh_p = stats.shapiro(data).pvalue
    rows.append(dict(dataset=name, n=len(data), mean=mean, median=s.median(), std=std,
                     min=s.min(), max=s.max(), skew=stats.skew(data), kurtosis=stats.kurtosis(data),
                     shapiro_p=sh_p, Q1=Q1, Q3=Q3, IQR=IQR,
                     z_outliers=len(z_out), iqr_outliers=len(iqr_out)))
    print(f"=== dataset{name} ===")
    print(s.describe().round(3).to_string())
    print("Z-score離群值：", [round(x, 2) for x in z_out])
    print("IQR離群值：", [round(x, 2) for x in iqr_out])
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].hist(data, bins=30); ax[0].set_title(f"dataset{name} 直方圖")
    ax[1].boxplot(data); ax[1].set_title(f"dataset{name} Boxplot 離群值偵測")
    plt.tight_layout(); plt.savefig(f"figures/dataset{name}.png", dpi=100); plt.close()

summary = pd.DataFrame(rows).set_index("dataset")
summary.round(4).to_csv("summary.csv")
pd.set_option("display.width", 200)
print(summary.round(3))
