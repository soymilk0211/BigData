# 大數據應用 Week 9：離群值偵測（Z-score vs IQR）
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

def plot(name, data, z_out, iqr_out):
    # 左：直方圖、右：Boxplot；兩種方法的離群值用不同顏色/形狀標記
    fig = make_subplots(1, 2, subplot_titles=(f"dataset{name} 直方圖", f"dataset{name} Boxplot 離群值偵測"))
    fig.add_trace(go.Histogram(x=data, nbinsx=30, name="資料", marker_color="#4C78A8", showlegend=False), 1, 1)
    fig.add_trace(go.Box(y=data, name="value", boxpoints="outliers", marker=dict(color="#BBBBBB", size=4), line_color="#4C78A8", showlegend=False), 1, 2)
    for out, label, color, symbol in [(z_out, f"Z-score 離群值（{len(z_out)}）", "#E45756", "x"),
                                      (iqr_out, f"IQR 離群值（{len(iqr_out)}）", "#F58518", "circle-open")]:
        mk = dict(color=color, symbol=symbol, size=11, line=dict(width=2))
        fig.add_trace(go.Scatter(x=out, y=[0] * len(out), mode="markers", marker=mk, name=label, legendgroup=label), 1, 1)
        fig.add_trace(go.Scatter(x=["value"] * len(out), y=out, mode="markers", marker=mk, name=label,
                                 legendgroup=label, showlegend=False), 1, 2)
    fig.update_layout(width=1000, height=420, font_family="Noto Sans CJK TC, Noto Sans CJK JP, sans-serif",
                      legend=dict(orientation="h", y=-0.15))
    fig.write_html(f"figures/dataset{name}.html", include_plotlyjs="cdn")
    fig.write_image(f"figures/dataset{name}.png")
    return fig

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
    plot(name, data, z_out, iqr_out)

summary = pd.DataFrame(rows).set_index("dataset")
summary.round(4).to_csv("summary.csv")
pd.set_option("display.width", 200)
print(summary.round(3))
