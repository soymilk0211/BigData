"""Task: "Analyze this data and make a suitable visualization." (algorithm benchmark)"""
import matplotlib

matplotlib.use("Agg")  # save files only, no window

import matplotlib.pyplot as plt

import common

NAME = "algorithm_benchmark"


def axis_label(text, unit, log):
    unit_part = f"{unit}, log scale" if unit and log else unit or ("log scale" if log else "")
    return f"{text} ({unit_part})" if unit_part else text


def main():
    df = common.load_raw("algorithm_benchmark.csv")
    common.inspect(df, NAME)

    print("\nlargest memory_mb values (reported, not removed):")
    print(df.nlargest(3, "memory_mb")[["run_id", "algorithm", "input_size", "memory_mb"]].to_string(index=False))

    # Cleaning: a run without runtime_ms cannot be plotted, so drop it and say so.
    clean = df.dropna(subset=["runtime_ms"]).drop_duplicates()
    print(f"\ncleaning: dropped {len(df) - len(clean)} row(s) with missing runtime_ms; kept {len(clean)} of {len(df)}")
    clean.to_csv(common.PROCESSED / f"{NAME}_clean.csv", index=False)

    # The data has outliers and floor values, so summarize each algorithm x input size by its median.
    summary = clean.groupby(["algorithm", "input_size"], as_index=False)[["runtime_ms", "memory_mb"]].median()
    algos = sorted(clean["algorithm"].unique())
    colors = dict(zip(algos, plt.get_cmap("Dark2").colors))  # same color per algorithm in every figure

    print("\nTool choice: matplotlib - static report figures with log axes and a labelled key point.")
    log_x = common.log_scale_check(summary["input_size"], "input_size")
    log_y = common.log_scale_check(summary["runtime_ms"], "median runtime_ms")
    common.log_scale_check(summary["memory_mb"], "median memory_mb")

    # Figure 1: runtime vs input size
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo in algos:
        g = summary[summary["algorithm"] == algo]
        ax.plot(g["input_size"], g["runtime_ms"], marker="o", color=colors[algo], label=algo)
    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(axis_label("Input size", "", log_x))
    ax.set_ylabel(axis_label("Median runtime", "ms", log_y))
    ax.set_title("Median runtime vs input size, by algorithm")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(title="Algorithm", loc="upper left")
    top = summary[summary["input_size"] == summary["input_size"].max()].nlargest(1, "runtime_ms").iloc[0]
    ax.annotate(
        f"slowest at {int(top['input_size']):,}: {top['algorithm']}, {top['runtime_ms']:.0f} ms",
        xy=(top["input_size"], top["runtime_ms"]),
        xytext=(-30, 0),
        textcoords="offset points",
        ha="right",
        va="center",
        arrowprops={"arrowstyle": "->"},
    )
    fig.tight_layout()
    runtime_png = common.FIGURES / f"{NAME}_line_runtime_by_input_size.png"
    fig.savefig(runtime_png, dpi=150)
    plt.close(fig)

    # Figure 2: memory vs input size
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo in algos:
        g = summary[summary["algorithm"] == algo]
        ax.plot(g["input_size"], g["memory_mb"], marker="o", color=colors[algo], label=algo)
    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel(axis_label("Input size", "", log_x))
    ax.set_ylabel("Median memory (MB)")
    ax.set_title("Median memory use vs input size, by algorithm")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(title="Algorithm", loc="upper left")
    fig.tight_layout()
    memory_png = common.FIGURES / f"{NAME}_line_memory_by_input_size.png"
    fig.savefig(memory_png, dpi=150)
    plt.close(fig)

    print("\nObservations (for the written summary):")
    runtime = summary.pivot(index="input_size", columns="algorithm", values="runtime_ms")
    print("median runtime growth, smallest -> largest input (x):", (runtime.iloc[-1] / runtime.iloc[0]).round(1).to_dict())
    print(f"slowest at largest input: {top['algorithm']} {top['runtime_ms']:.0f} ms; Binary_Search {runtime['Binary_Search'].iloc[-1]:.1f} ms")
    memory = summary.pivot(index="input_size", columns="algorithm", values="memory_mb")
    print("median memory at largest input (MB):", memory.iloc[-1].round(1).to_dict())
    spike = df[(df["algorithm"] == "Binary_Search") & (df["input_size"] == 10000)]["memory_mb"]
    print(f"Binary_Search at 10,000: mean {spike.mean():.1f} MB vs median {spike.median():.1f} MB (outlier-driven)")

    ok = common.self_check([common.PROCESSED / f"{NAME}_clean.csv", runtime_png, memory_png])
    print("self-check:", "all output files exist" if ok else "FAILED")


if __name__ == "__main__":
    main()
