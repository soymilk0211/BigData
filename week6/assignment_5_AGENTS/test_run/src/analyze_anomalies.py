"""Task C: find unusually high or low values (memory, defect density, latency)."""
import matplotlib

matplotlib.use("Agg")  # save files only, no window

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns

import common


def iqr_outliers(series):
    """True where a value lies outside 1.5 x IQR of the series."""
    q1, q3 = series.quantile([0.25, 0.75])
    spread = q3 - q1
    return (series < q1 - 1.5 * spread) | (series > q3 + 1.5 * spread)


def benchmark_memory():
    df = common.load_raw("algorithm_benchmark.csv")
    # Outliers are judged inside each algorithm x input size group, because memory depends on both.
    df["is_outlier"] = df.groupby(["algorithm", "input_size"])["memory_mb"].transform(iqr_outliers)
    algos = sorted(df["algorithm"].unique())
    colors = dict(zip(algos, plt.get_cmap("Dark2").colors))  # same colors as the other benchmark figures
    shift = {a: 10 ** (0.04 * (i - (len(algos) - 1) / 2)) for i, a in enumerate(algos)}  # sideways offset

    print("=== algorithm_benchmark: memory outliers ===")
    print("Tool choice: matplotlib - labelled key points (the outliers) on a static figure.")
    log_x = common.log_scale_check(df["input_size"], "input_size")

    fig, ax = plt.subplots(figsize=(8, 5))
    for algo in algos:
        g = df[df["algorithm"] == algo]
        ax.scatter(g["input_size"] * shift[algo], g["memory_mb"], s=18, alpha=0.7, color=colors[algo], label=algo)
    out = df[df["is_outlier"]]
    ax.scatter(out["input_size"] * out["algorithm"].map(shift), out["memory_mb"], s=100,
               facecolors="none", edgecolors="black", linewidths=1.2, label="outlier (1.5 x IQR in its group)")
    for _, row in out.nlargest(1, "memory_mb").iterrows():  # label only the key point; other outliers stay circled
        ax.annotate(f"{row['run_id']}: {row['memory_mb']:.0f} MB",
                    xy=(row["input_size"] * shift[row["algorithm"]], row["memory_mb"]),
                    xytext=(10, 0), textcoords="offset points", va="center", fontsize=10)
    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel("Input size" + (" (log scale, points offset slightly by algorithm)" if log_x else ""))
    ax.set_ylabel("Memory (MB)")
    ax.set_title("Memory per run, outliers marked")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    path = common.FIGURES / "algorithm_benchmark_scatter_memory_outliers.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    print(f"memory outliers: {len(out)} of {len(df)} runs; per algorithm: {out['algorithm'].value_counts().to_dict()}")
    print("highest memory runs:")
    print(out.nlargest(3, "memory_mb")[["run_id", "algorithm", "input_size", "memory_mb"]].to_string(index=False))
    print("lowest runtime runs:")
    print(df.nsmallest(2, "runtime_ms")[["run_id", "algorithm", "input_size", "runtime_ms"]].to_string(index=False))
    return path


def quality_defect_density():
    df = common.load_raw("software_quality.csv")
    # Transformation: defects per 1,000 lines of code, so large and small modules are comparable.
    df["defects_per_kloc"] = df["defect_count"] / (df["LOC"] / 1000)

    print("\n=== software_quality: defect density ===")
    print("transformation: added defects_per_kloc = defect_count / (LOC / 1000)")
    print("Tool choice: seaborn - grouped scatter by module type, top modules labelled.")
    sns.set_theme(style="whitegrid")
    log_x = common.log_scale_check(df["LOC"], "LOC")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=df, x="LOC", y="defects_per_kloc", hue="module_type", palette="Dark2", alpha=0.7, ax=ax)
    if log_x:
        ax.set_xscale("log")
    top = df.nlargest(3, "defects_per_kloc")
    offsets = [(8, 4), (10, 10), (10, -12)]  # stagger the labels so neighbouring points do not overlap
    for (_, row), offset in zip(top.iterrows(), offsets):
        ax.annotate(row["module_id"], xy=(row["LOC"], row["defects_per_kloc"]),
                    xytext=offset, textcoords="offset points", fontsize=10)
    ax.set_title("Defect density vs module size, by module type")
    ax.set_xlabel("Lines of code (LOC" + (", log scale)" if log_x else ")"))
    ax.set_ylabel("Defects per 1,000 lines of code")
    ax.legend(title="Module type")
    fig.tight_layout()
    path = common.FIGURES / "software_quality_scatter_defect_density_by_loc.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    print("highest defect density modules:")
    print(top[["module_id", "module_type", "LOC", "defect_count", "defects_per_kloc"]].round(2).to_string(index=False))
    print("modules with 3 or more defects:", df[df["defect_count"] >= 3]["module_id"].tolist())
    return path


def web_latency():
    df = common.load_raw("web_service_logs.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Latency depends on the endpoint, so outliers are judged per endpoint.
    df["is_outlier"] = df.groupby("endpoint")["latency_ms"].transform(iqr_outliers)
    colors = dict(zip(sorted(df["endpoint"].unique()), px.colors.qualitative.Set2))

    print("\n=== web_service_logs: latency outliers ===")
    print("Tool choice: plotly - each outlier is a single request the reader will want to hover over and inspect.")
    common.log_scale_check(df["latency_ms"], "latency_ms")

    fig = px.scatter(
        df, x="timestamp", y="latency_ms", color="endpoint", opacity=0.45,
        color_discrete_map=colors, hover_name="request_id",
        hover_data=["status_code", "region", "device", "cache_hit"],
        title="Latency over time, outliers marked per endpoint",
        labels={"timestamp": "Time", "latency_ms": "Latency (ms)", "endpoint": "Endpoint"},
    )
    out = df[df["is_outlier"]]
    fig.add_scatter(
        x=out["timestamp"], y=out["latency_ms"], mode="markers",
        marker={"symbol": "x", "size": 9, "color": "black"},
        name="outlier (1.5 x IQR per endpoint)",
        text=out["request_id"] + " " + out["endpoint"],
        hovertemplate="%{text}<br>%{y:.0f} ms<br>%{x}<extra></extra>",
    )
    fig.update_layout(width=900, height=550)
    path = common.HTML / "web_service_logs_scatter_latency_outliers_over_time.html"
    fig.write_html(path, include_plotlyjs="cdn")

    print(f"latency outliers: {len(out)} of {len(df)} requests ({len(out) / len(df):.1%}); per endpoint: {out['endpoint'].value_counts().to_dict()}")
    print("slowest requests:")
    print(df.nlargest(3, "latency_ms")[["request_id", "endpoint", "latency_ms", "status_code"]].to_string(index=False))
    return path


def main():
    paths = [benchmark_memory(), quality_defect_density(), web_latency()]
    ok = common.self_check(paths)
    print("self-check:", "all output files exist" if ok else "FAILED")


if __name__ == "__main__":
    main()
