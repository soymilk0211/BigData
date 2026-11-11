"""Week10 作業：K-means (K=3) 學生成績分群
只使用標準庫 (csv, math, random, itertools)，不使用 numpy / scikit-learn。
"""
import csv
import math
import os
import random
from itertools import permutations

K = 3
MAX_ITER = 100
SEED = 42
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "teacher", "students_200.csv")


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = [r["student_id"] for r in rows]
    pts = [(float(r["chinese"]), float(r["english"])) for r in rows]
    truth = [r["true_cluster"] for r in rows]
    return ids, pts, truth


def distance(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


def mean_point(points):
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


def assign(points, centers):
    return [min(range(len(centers)), key=lambda k: distance(p, centers[k]))
            for p in points]


def sse(points, labels, centers):
    return sum(distance(p, centers[l]) ** 2 for p, l in zip(points, labels))


def kmeans_once(points, k, rng):
    centers = rng.sample(points, k)                # Step 1: 隨機選 K 個中心
    labels = assign(points, centers)
    for it in range(1, MAX_ITER + 1):
        new_centers = []
        for c in range(k):                         # Step 2: 重新計算中心
            members = [p for p, l in zip(points, labels) if l == c]
            new_centers.append(mean_point(members) if members else centers[c])
        new_labels = assign(points, new_centers)   # Step 3: 重新分配
        if new_labels == labels:                   # Step 4: 收斂
            return labels, new_centers, it
        labels, centers = new_labels, new_centers
    return labels, centers, MAX_ITER


def kmeans(points, k, seed=SEED, n_init=10):
    """K-means 結果依初始值而異，跑多次取 SSE 最小者。"""
    rng = random.Random(seed)
    best = None
    for _ in range(n_init):
        labels, centers, it = kmeans_once(points, k, rng)
        err = sse(points, labels, centers)
        if best is None or err < best[0]:
            best = (err, labels, centers, it)
    return best[1], best[2], best[3], best[0]


def accuracy(labels, truth):
    """群編號與 A/B/C 沒有固定對應，嘗試所有排列取最高準確度。"""
    names = sorted(set(truth))
    best_acc, best_map = -1, None
    for perm in permutations(names):
        mapping = dict(enumerate(perm))
        acc = sum(mapping[l] == t for l, t in zip(labels, truth)) / len(truth)
        if acc > best_acc:
            best_acc, best_map = acc, mapping
    return best_acc, best_map


def main():
    ids, pts, truth = load(CSV_PATH)
    print(f"讀入 {len(pts)} 筆學生資料")
    labels, centers, iters, err = kmeans(pts, K)
    acc, mapping = accuracy(labels, truth)
    print(f"K={K}, 收斂迭代 {iters} 次, SSE={err:.2f}\n")

    print("student_id  chinese  english  群標籤  對應類別  true_cluster")
    for sid, p, l, t in zip(ids, pts, labels, truth):
        print(f"{sid:<10}  {p[0]:7.1f}  {p[1]:7.1f}  {l:^6}  {mapping[l]:^8}  {t}")

    print("\n每群成績平均：")
    for c in range(K):
        members = [p for p, l in zip(pts, labels) if l == c]
        m = mean_point(members)
        print(f"  群 {c} (對應 {mapping[c]}): {len(members):3d} 人, "
              f"國文平均 {m[0]:.2f}, 英文平均 {m[1]:.2f}")

    print("\n與真實群對照 (列=true_cluster, 欄=K-means 對應類別)：")
    names = sorted(set(truth))
    print("      " + "".join(f"{n:>5}" for n in names))
    for t in names:
        row = [sum(1 for l, tt in zip(labels, truth) if tt == t and mapping[l] == n)
               for n in names]
        print(f"  {t:>3} " + "".join(f"{v:>5}" for v in row))
    correct = round(acc * len(truth))
    print(f"\n分群準確度 Accuracy = {correct}/{len(truth)} = {acc:.2%}")


if __name__ == "__main__":
    main()
