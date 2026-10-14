"""Week 6 data-analysis assignment.

Reads the raw CSVs in data/raw/, writes cleaned copies to data/processed/,
and saves figures to outputs/figures/.

    01 AlgorithmBenchmark -> matplotlib
    02 SoftwareQuality    -> seaborn
    03 WebServiceLogs     -> plotly (interactive HTML)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: write files only, never open a window

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"


def read_raw(name):
    return pd.read_csv(RAW / name, encoding="utf-8-sig")


def save_matplotlib(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=150)
    plt.close(fig)


# --- 01 Algorithm benchmark (matplotlib) -------------------------------------

def analyze_algorithms():
    df = read_raw("01_AlgorithmBenchmark_matplotlib.csv")
    df = df.dropna(subset=["runtime_ms"])  # one row has no runtime
    df.to_csv(PROCESSED / "01_algorithm_benchmark_clean.csv", index=False)

    mean = df.groupby(["algorithm", "input_size"], as_index=False).mean(numeric_only=True)

    # Mean runtime vs input size, log-log so all four algorithms are readable.
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo, g in mean.groupby("algorithm"):
        ax.plot(g["input_size"], g["runtime_ms"], marker="o", label=algo)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input size")
    ax.set_ylabel("Mean runtime (ms)")
    ax.set_title("Runtime vs input size")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    save_matplotlib(fig, "01_runtime_vs_input_size.png")

    # Mean comparisons vs input size.
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo, g in mean.groupby("algorithm"):
        ax.plot(g["input_size"], g["comparisons"], marker="s", label=algo)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input size")
    ax.set_ylabel("Mean comparisons")
    ax.set_title("Comparisons vs input size")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    save_matplotlib(fig, "01_comparisons_vs_input_size.png")

    # Memory use per algorithm at the largest input size.
    largest = df[df["input_size"] == df["input_size"].max()]
    fig, ax = plt.subplots(figsize=(8, 5))
    largest.boxplot(column="memory_mb", by="algorithm", ax=ax)
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Memory (MB)")
    ax.set_title(f"Memory at input size {int(df['input_size'].max()):,}")
    fig.suptitle("")
    save_matplotlib(fig, "01_memory_by_algorithm.png")


# --- 02 Software quality (seaborn) -------------------------------------------

def analyze_quality():
    df = read_raw("02_SoftwareQuality_seaborn.csv")
    df.to_csv(PROCESSED / "02_software_quality_clean.csv", index=False)
    sns.set_theme(style="whitegrid")

    # Correlation between the numeric metrics.
    numeric = df.select_dtypes("number")
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(numeric.corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation of module metrics")
    save_matplotlib(fig, "02_correlation_heatmap.png")

    # Complexity vs defects, split by language.
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=df, x="cyclomatic_complexity", y="defect_count",
        hue="language", alpha=0.7, ax=ax,
    )
    ax.set_title("Cyclomatic complexity vs defect count")
    save_matplotlib(fig, "02_complexity_vs_defects.png")

    # Test coverage distribution per language.
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x="language", y="test_coverage_pct", ax=ax)
    ax.set_title("Test coverage by language")
    save_matplotlib(fig, "02_coverage_by_language.png")

    # Defects per module type and language.
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=df, x="module_type", y="defect_count", hue="language", ax=ax)
    ax.set_title("Mean defects by module type")
    save_matplotlib(fig, "02_defects_by_module_type.png")


# --- 03 Web service logs (plotly) --------------------------------------------

def analyze_logs():
    df = read_raw("03_WebServiceLogs_plotly.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["cache_hit"] = df["cache_hit"].astype(str).str.lower() == "true"
    df.to_csv(PROCESSED / "03_web_service_logs_clean.csv", index=False)

    def write(fig, name):
        fig.write_html(FIGURES / name, include_plotlyjs="cdn")

    write(
        px.box(df, x="endpoint", y="latency_ms", color="endpoint",
               title="Latency by endpoint (ms)"),
        "03_latency_by_endpoint.html",
    )

    status = df.groupby(["endpoint", "status_code"], as_index=False).size()
    status["status_code"] = status["status_code"].astype(str)
    write(
        px.bar(status, x="endpoint", y="size", color="status_code",
               title="Requests by endpoint and status code",
               labels={"size": "requests"}),
        "03_status_by_endpoint.html",
    )

    hourly = df.set_index("timestamp").resample("h").size().reset_index(name="requests")
    write(
        px.line(hourly, x="timestamp", y="requests", title="Requests per hour"),
        "03_requests_per_hour.html",
    )

    write(
        px.box(df, x="region", y="latency_ms", color="cache_hit",
               title="Latency by region and cache hit"),
        "03_latency_by_region_cache.html",
    )

    write(
        px.scatter(df, x="response_kb", y="latency_ms", color="device",
                   opacity=0.5, title="Response size vs latency"),
        "03_response_size_vs_latency.html",
    )


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    analyze_algorithms()
    analyze_quality()
    analyze_logs()
    print(f"Cleaned data -> {PROCESSED}")
    print(f"Figures      -> {FIGURES}")


if __name__ == "__main__":
    main()
