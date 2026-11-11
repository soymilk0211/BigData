"""把 hierarchical.py 的結果畫成樹狀圖 (SVG)，只用標準庫。"""
import os
from hierarchical import agglomerate, flatten, CUT_HEIGHT
import io, contextlib

with contextlib.redirect_stdout(io.StringIO()):
    tree, height, merges = agglomerate()

W, H, L, R, T, B = 640, 460, 70, 30, 40, 60
maxh = 40.0
y = lambda h: H - B - (H - B - T) * h / maxh
order = flatten(tree)
xs = {n: L + (W - L - R) * (i + 0.5) / len(order) for i, n in enumerate(order)}
out = []

def node(n):
    """回傳 (x, h)，並畫出連線"""
    if isinstance(n, str):
        return xs[n], 0.0
    (x1, h1), (x2, h2) = node(n[0]), node(n[1])
    h = height[tuple(sorted(flatten(n)))]
    out.append(f'<path d="M{x1},{y(h1)} V{y(h)} H{x2} V{y(h2)}" fill="none" stroke="#2563eb" stroke-width="2.5"/>')
    out.append(f'<text x="{min(x1,x2)+(abs(x2-x1))*0.25}" y="{y(h)-8}" text-anchor="middle" font-size="14" fill="#333">{h:.2f}</text>')
    return (x1 + x2) / 2, h

node(tree)
for t in range(0, 41, 10):
    out.append(f'<line x1="{L-5}" x2="{L}" y1="{y(t)}" y2="{y(t)}" stroke="#555"/>'
               f'<text x="{L-10}" y="{y(t)+5}" text-anchor="end" font-size="13">{t}</text>')
out.append(f'<line x1="{L}" x2="{L}" y1="{y(0)}" y2="{y(40)}" stroke="#555"/>')
out.append(f'<line x1="{L}" x2="{W-R}" y1="{y(CUT_HEIGHT)}" y2="{y(CUT_HEIGHT)}" stroke="#dc2626" stroke-width="2" stroke-dasharray="7 5"/>')
out.append(f'<text x="{L+8}" y="{y(CUT_HEIGHT)-6}" text-anchor="start" font-size="14" fill="#dc2626">切割高度 = {CUT_HEIGHT} → 2 群</text>')
data = {"A": "(90, 60)", "B": "(85, 65)", "C": "(60, 90)", "D": "(62, 85)"}
for n, x in xs.items():
    out.append(f'<text x="{x}" y="{y(0)+24}" text-anchor="middle" font-size="20" font-weight="bold">{n}</text>'
               f'<text x="{x}" y="{y(0)+44}" text-anchor="middle" font-size="12" fill="#666">{data[n]}</text>')
out.append(f'<text x="{W/2}" y="24" text-anchor="middle" font-size="18" font-weight="bold">階層式分群樹狀圖 (Average Linkage)</text>')
out.append(f'<text x="18" y="{H/2}" font-size="13" transform="rotate(-90 18 {H/2})" text-anchor="middle">Euclidean distance</text>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="WenQuanYi Zen Hei, Noto Sans CJK TC, sans-serif"><rect width="100%" height="100%" fill="white"/>'
       + "".join(out) + "</svg>")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dendrogram.svg")
open(path, "w", encoding="utf-8").write(svg)
print("saved", path)
