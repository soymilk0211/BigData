"""產生繳交用 PowerPoint：kmean.py 的執行畫面截圖與分群準確度。
執行畫面為 run_screenshot.png（終端機實際執行 kmean.py 的螢幕截圖）。"""
import os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
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
text(s, 1, 2.3, 11.3, 1, ["Week10：K-means 分群作業"], 40, True, "1d4ed8")
text(s, 1, 3.6, 11.3, 2, ["程式：kmean.py（K-means, K=3, 200 位學生）", "分群準確度：168 / 200 = 84.00%", "第4組：廖晢勛（B1229009）、姚睿、林敬棠、黃柏瑞"], 22)

s = prs.slides.add_slide(blank); title(s, "kmean.py 執行畫面（終端機實際執行截圖）")
fit(s, os.path.join(HERE, "run_screenshot.png"), .5, 1.05, 12.3, 5.6)
text(s, .5, 6.75, 12.3, .6, ["python3 kmean.py：只用標準庫 csv / math / random，K=3；分群準確度 Accuracy = 168 / 200 = 84.00%"], 18, True)

s = prs.slides.add_slide(blank); title(s, "K-means 分群結果 vs 真實群（準確度 84.00%）")
fit(s, os.path.join(HERE, "kmeans_scatter.png"), .5, 1.2, 12.3, 6)

out = os.path.join(HERE, "week10_作業.pptx"); prs.save(out); print(out)
