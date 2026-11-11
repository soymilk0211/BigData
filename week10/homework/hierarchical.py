"""Week10：階層式分群 (Agglomerative, Average Linkage) + 樹狀結構
只使用標準庫 (math)。資料為投影片的 A/B/C/D 四位學生 (中文, 英文)。
"""
import math

DATA = {"A": (90, 60), "B": (85, 65), "C": (60, 90), "D": (62, 85)}
CUT_HEIGHT = 30  # 投影片：切割高度 = 30 → 2 群


def distance(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


def avg_linkage(c1, c2):
    """兩群間所有點對距離的平均 (Average Linkage)"""
    ds = [distance(DATA[a], DATA[b]) for a in c1 for b in c2]
    return sum(ds) / len(ds)


def show_matrix(clusters):
    names = ["".join(c) for c in clusters]
    print("        " + "".join(f"{n:>8}" for n in names))
    for a, na in zip(clusters, names):
        row = [0.0 if a == b else avg_linkage(a, b) for b in clusters]
        print(f"{na:>8}" + "".join(f"{v:8.2f}" for v in row))


def agglomerate():
    clusters = [(k,) for k in DATA]
    tree = {c: c[0] for c in clusters}          # 群 -> 巢狀 tuple 樹
    height = {c: 0.0 for c in clusters}
    merges = []
    print("Step 0：初始距離矩陣 (Euclidean distance)")
    show_matrix(clusters)
    step = 0
    while len(clusters) > 1:
        step += 1
        pairs = [(avg_linkage(a, b), a, b)
                 for i, a in enumerate(clusters) for b in clusters[i + 1:]]
        d, a, b = min(pairs)
        new = tuple(sorted(a + b))
        tree[new] = (tree[a], tree[b])
        height[new] = d
        merges.append((a, b, d))
        clusters = [c for c in clusters if c not in (a, b)] + [new]
        print(f"\nStep {step}：最小距離 = {d:.2f} → 合併 "
              f"{''.join(a)} + {''.join(b)} → 新群 {''.join(new)}")
        if len(clusters) > 1:
            show_matrix(clusters)
    return tree[clusters[0]], height, merges


def print_tree(node, height, prefix="", last=True):
    """文字樹狀圖，括號內為合併高度"""
    leaves = tuple(sorted(flatten(node)))
    if isinstance(node, str):
        print(prefix + ("└── " if last else "├── ") + node)
        return
    print(prefix + ("└── " if last else "├── ") +
          f"{''.join(leaves)}  (距離 {height[leaves]:.2f})")
    ext = prefix + ("    " if last else "│   ")
    print_tree(node[0], height, ext, False)
    print_tree(node[1], height, ext, True)


def flatten(node):
    return [node] if isinstance(node, str) else flatten(node[0]) + flatten(node[1])


def cut(merges, h):
    """切割高度 h：只做距離 <= h 的合併"""
    groups = [{k} for k in DATA]
    for a, b, d in merges:
        if d <= h:
            ga = next(g for g in groups if g == set(a))
            gb = next(g for g in groups if g == set(b))
            groups = [g for g in groups if g not in (ga, gb)] + [ga | gb]
    return groups


def main():
    tree, height, merges = agglomerate()
    print("\n樹狀結構 (巢狀表示)：", tree)
    print("\n樹狀圖 (Dendrogram，文字版)：")
    print_tree(tree, height)
    groups = cut(merges, CUT_HEIGHT)
    print(f"\n切割高度 = {CUT_HEIGHT} → {len(groups)} 群：",
          [sorted(g) for g in sorted(groups, key=sorted)])


if __name__ == "__main__":
    main()
