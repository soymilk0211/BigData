"""產生繳交用 PowerPoint：二個程式的執行畫面截圖與分群準確度。
截圖 (k.png / h.png / s.png) 為程式輸出的終端機畫面。"""
import os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = sys.argv[1]
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]

def text(s, x, y, w, h, lines, size=18, bold=False, color="222222"):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, l in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = l; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = RGBColor.from_string(color); p.space_after = Pt(6)

def title(s, t):
    text(s, .5, .25, 12.3, .7, [t], 28, True, "1d4ed8")

def fit(s, path, x, y, maxw, maxh):
    from PIL import Image
    w, h = Image.open(path).size; r = min(maxw / w, maxh / h)
    s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w * r), Inches(h * r))

s = prs.slides.add_slide(blank)
text(s, 1, 2.3, 11.3, 1, ["Week10：K-means 與階層式分群"], 40, True, "1d4ed8")
text(s, 1, 3.6, 11.3, 2, ["程式 1：kmean.py（K-means, K=3, 200 位學生）", "程式 2：hierarchical.py（階層式分群, Average Linkage）", "分群準確度：168 / 200 = 84.00%"], 22)

s = prs.slides.add_slide(blank); title(s, "程式 1：kmean.py 執行畫面")
fit(s, f"{SHOTS}/k.png", .5, 1.1, 7.3, 6.2)
text(s, 8.2, 1.4, 4.7, 5, ["只用標準庫 csv / math / random", "隨機選 3 個中心 → 分配 → 更新中心，重複直到收斂（11 次）", "固定亂數種子、跑 10 次取 SSE 最小", "群編號與 A/B/C 無固定對應，取 6 種對應中最高者", "", "分群準確度 = 168 / 200 = 84.00%"], 17)

s = prs.slides.add_slide(blank); title(s, "K-means 分群結果 vs 真實群（準確度 84.00%）")
fit(s, os.path.join(HERE, "kmeans_scatter.png"), .5, 1.2, 12.3, 6)

s = prs.slides.add_slide(blank); title(s, "程式 2：hierarchical.py 執行畫面")
fit(s, f"{SHOTS}/h.png", .5, 1.1, 5.3, 6.2)
text(s, 6.2, 1.4, 6.7, 5, ["Agglomerative，距離：Euclidean，連結：Average Linkage", "", "合併順序：", "1. C + D（距離 5.39）", "2. A + B（距離 7.07）", "3. CD + AB（距離 36.45）", "", "切割高度 = 30 → 2 群：(A, B)、(C, D)", "", "註：依表格資料實際計算，C–D 距離為 5.39，與投影片的 7.07 略有出入，最終樹形與分群相同"], 17)

s = prs.slides.add_slide(blank); title(s, "樹狀結構 (Dendrogram)")
fit(s, os.path.join(HERE, "dendrogram.png"), 2.2, 1.1, 9, 6.2)

s = prs.slides.add_slide(blank); title(s, "練習題：stats_practice.py 執行畫面")
fit(s, f"{SHOTS}/s.png", .5, 1.3, 7, 5)
text(s, 8, 1.5, 4.9, 4, ["X = 每週自學時數，Y = 小測驗分數（30 筆）", "相關係數 0.9657：強正相關", "共變異數與標準差同時列出樣本 (n-1) 與母體 (n) 版本"], 17)

out = os.path.join(HERE, "week10_作業.pptx"); prs.save(out); print(out)
