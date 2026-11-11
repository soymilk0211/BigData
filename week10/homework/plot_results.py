"""用 matplotlib 畫圖（僅畫圖用，計算仍由 kmean.py / hierarchical.py 的標準庫程式完成）"""
import io, contextlib, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import kmean
from hierarchical import agglomerate, flatten, CUT_HEIGHT, DATA

for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [f]
        break
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 1. 樹狀圖 ----
with contextlib.redirect_stdout(io.StringIO()):
    tree, height, _ = agglomerate()
order = flatten(tree)
xs = {n: i for i, n in enumerate(order)}
fig, ax = plt.subplots(figsize=(7, 5))

def draw(n):
    if isinstance(n, str):
        return xs[n], 0.0
    (x1, h1), (x2, h2) = draw(n[0]), draw(n[1])
    h = height[tuple(sorted(flatten(n)))]
    ax.plot([x1, x1, x2, x2], [h1, h, h, h2], color="#2563eb", lw=2.5)
    ax.text(min(x1, x2) + abs(x2 - x1) * 0.25, h + 0.6, f"{h:.2f}", ha="center")
    return (x1 + x2) / 2, h

draw(tree)
ax.axhline(CUT_HEIGHT, color="#dc2626", ls="--")
ax.text(-0.4, CUT_HEIGHT + 0.8, f"切割高度 = {CUT_HEIGHT} → 2 群", color="#dc2626")
ax.set_xticks(range(len(order)))
ax.set_xticklabels([f"{n}\n{DATA[n]}" for n in order], fontsize=12)
ax.set_ylabel("Euclidean distance")
ax.set_title("階層式分群樹狀圖 (Average Linkage)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "dendrogram.png"), dpi=200)

# ---- 2. K-means 散佈圖 ----
ids, pts, truth = kmean.load(kmean.CSV_PATH)
labels, centers, _, _ = kmean.kmeans(pts, kmean.K)
acc, mapping = kmean.accuracy(labels, truth)
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True)
colors = {"A": "#2563eb", "B": "#f59e0b", "C": "#16a34a"}
for ax, title, cl in ((axes[0], "K-means 分群結果", [mapping[l] for l in labels]),
                      (axes[1], "真實群 (true_cluster)", truth)):
    for n in "ABC":
        sel = [p for p, c in zip(pts, cl) if c == n]
        ax.scatter([p[0] for p in sel], [p[1] for p in sel], s=22, c=colors[n], label=n, alpha=.8)
    ax.set_title(title); ax.set_xlabel("chinese"); ax.legend()
axes[0].set_ylabel("english")
axes[0].scatter([c[0] for c in centers], [c[1] for c in centers], marker="X", s=200,
                c="red", edgecolors="black", label="centroid", zorder=5)
# 每群畫一個圈：圓心 = 群中心，半徑 = 該群離中心最遠的學生距離（把整群圈起來）
for k, c in enumerate(centers):
    r = max(kmean.distance(p, c) for p, l in zip(pts, labels) if l == k)
    axes[0].add_patch(plt.Circle(c, r, fill=False, ls="--", lw=2,
                                 color=colors[mapping[k]], zorder=4))
for ax in axes:
    ax.set_aspect("equal", adjustable="box")
fig.suptitle(f"K=3 準確度 {acc:.2%}")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "kmeans_scatter.png"), dpi=150)
print("done")
