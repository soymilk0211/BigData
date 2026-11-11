"""Week10 練習：X=每週自學時數, Y=小測驗分數 的平均、共變異數、標準差、相關係數
只使用標準庫 (csv, math)。同時列出樣本(n-1)與母體(n)兩種版本。
"""
import csv
import math
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "study_hours_scores.csv")

with open(PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
x = [float(r["x_hours"]) for r in rows]
y = [float(r["y_score"]) for r in rows]
n = len(x)

mx, my = sum(x) / n, sum(y) / n
sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
sxx = sum((a - mx) ** 2 for a in x)
syy = sum((b - my) ** 2 for b in y)

print(f"資料筆數 n = {n}")
print(f"平均值X：{mx:.4f}")
print(f"平均值Y：{my:.4f}")
print(f"{'':<8}{'樣本(n-1)':>12}{'母體(n)':>12}")
print(f"共變異數：{sxy/(n-1):>10.4f}{sxy/n:>12.4f}")
print(f"標準差X：{math.sqrt(sxx/(n-1)):>11.4f}{math.sqrt(sxx/n):>12.4f}")
print(f"標準差Y：{math.sqrt(syy/(n-1)):>11.4f}{math.sqrt(syy/n):>12.4f}")
print(f"相關係數：{sxy/math.sqrt(sxx*syy):.4f}  (與 n 或 n-1 無關)")
