"""Task: "Analyze this data and make a suitable visualization." (software quality)"""
import matplotlib

matplotlib.use("Agg")  # save files only, no window

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import common

NAME = "software_quality"


def main():
    df = common.load_raw("software_quality.csv")
    common.inspect(df, NAME)

    needs_cleaning = df.isna().any().any() or df.duplicated().any()
    print("\ncleaning:", "needed" if needs_cleaning else "not needed (no missing values, no duplicates); nothing written to data/processed/")

    print("\nTool choice: seaborn - correlation and group comparison are statistical views.")
    sns.set_theme(style="whitegrid")

    # Figure 1: correlation between all numeric metrics
    corr = df.select_dtypes("number").corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax,
                cbar_kws={"label": "Pearson correlation"})
    ax.set_title("Correlation between module metrics")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Metric")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    heatmap_png = common.FIGURES / f"{NAME}_heatmap_correlation_all_metrics.png"
    fig.savefig(heatmap_png, dpi=150)
    plt.close(fig)

    # Figure 2: mean defects per module type (bars start at 0)
    order = df.groupby("module_type")["defect_count"].mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df, x="module_type", y="defect_count", order=order, errorbar=("ci", 95),
                color="#4c72b0", ax=ax)
    ax.set_title("Mean defect count by module type (95% confidence interval)")
    ax.set_xlabel("Module type")
    ax.set_ylabel("Mean defects per module")
    fig.tight_layout()
    bar_png = common.FIGURES / f"{NAME}_bar_defects_by_module_type.png"
    fig.savefig(bar_png, dpi=150)
    plt.close(fig)

    # Figure 3: the most strongly related pair of metrics (task: relationship between variables)
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    pair = upper.abs().unstack().dropna().idxmax()
    x_col, y_col = sorted(pair, key=list(df.columns).index)  # the earlier column goes on the x axis
    r = corr.loc[y_col, x_col]
    names = {"LOC": "Lines of code (LOC)", "code_churn_lines": "Code churn (lines changed)"}
    short = {"LOC": "lines of code", "code_churn_lines": "code churn"}
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.regplot(data=df, x=x_col, y=y_col, scatter_kws={"alpha": 0.5}, line_kws={"color": "#d62728"}, ax=ax)
    ax.set_title(f"{short.get(y_col, y_col)} vs {short.get(x_col, x_col)} (r = {r:.2f})".capitalize())
    ax.set_xlabel(names.get(x_col, x_col))
    ax.set_ylabel(names.get(y_col, y_col))
    fig.tight_layout()
    scatter_png = common.FIGURES / f"{NAME}_scatter_{x_col.lower()}_vs_{y_col.lower()}.png"
    fig.savefig(scatter_png, dpi=150)
    plt.close(fig)

    print("\nObservations (for the written summary):")
    print("correlation with defect_count:", corr["defect_count"].drop("defect_count").sort_values(ascending=False).round(2).to_dict())
    print("mean defects by module type:", df.groupby("module_type")["defect_count"].mean().sort_values(ascending=False).round(2).to_dict())
    print(f"modules with zero defects: {(df['defect_count'] == 0).mean():.0%}")
    print(f"test_coverage_pct equal to 100: {int((df['test_coverage_pct'] == 100).sum())} of {len(df)} (a natural cap, not an error)")

    print(f"strongest pair of metrics: {x_col} and {y_col}, r = {r:.2f}")

    ok = common.self_check([heatmap_png, bar_png, scatter_png])
    print("self-check:", "all output files exist" if ok else "FAILED")


if __name__ == "__main__":
    main()
