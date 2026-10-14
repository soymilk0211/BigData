"""Scenario 1 test: analyze the algorithm benchmark and draw figures.

Rules followed (see AGENTS.md): pandas + matplotlib only, data/raw/ is read-only,
cleaned data goes to data/processed/, figures go to outputs/figures/.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write files only, no window

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "01_AlgorithmBenchmark_matplotlib.csv"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"


def inspect(df):
    print("shape:", df.shape)
    print("dtypes:\n", df.dtypes.to_string())
    print("missing values:\n", df.isna().sum()[lambda s: s > 0].to_string())
    print("duplicate rows:", int(df.duplicated().sum()))


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW, encoding="utf-8-sig")  # read only; raw file is never written
    inspect(df)

    clean = df.dropna(subset=["runtime_ms"]).drop_duplicates()
    clean.to_csv(PROCESSED / "algorithm_benchmark_clean.csv", index=False)
    print(f"cleaned rows: {len(clean)} (dropped {len(df) - len(clean)})")

    mean = clean.groupby(["algorithm", "input_size"], as_index=False).mean(numeric_only=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    for algo, g in mean.groupby("algorithm"):
        ax.plot(g["input_size"], g["runtime_ms"], marker="o", label=algo)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input size")
    ax.set_ylabel("Mean runtime (ms)")
    ax.set_title("Runtime vs input size")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(title="Algorithm")
    fig.tight_layout()
    fig.savefig(FIGURES / "runtime_vs_input_size.png", dpi=150)
    plt.close(fig)

    largest = clean[clean["input_size"] == clean["input_size"].max()]
    fig, ax = plt.subplots(figsize=(8, 5))
    largest.boxplot(column="memory_mb", by="algorithm", ax=ax)
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Memory (MB)")
    ax.set_title(f"Memory at input size {int(clean['input_size'].max()):,}")
    fig.suptitle("")
    fig.tight_layout()
    fig.savefig(FIGURES / "memory_by_algorithm.png", dpi=150)
    plt.close(fig)

    print("done")


if __name__ == "__main__":
    main()
