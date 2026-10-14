"""Task: "Analyze the important trends in the data and present them with suitable charts." (web logs)"""
import datetime

import pandas as pd
import plotly.express as px

import common

NAME = "web_service_logs"


def save_html(fig, suffix):
    fig.update_layout(width=900, height=550)
    path = common.HTML / f"{NAME}_{suffix}.html"
    fig.write_html(path, include_plotlyjs="cdn")
    return path


def main():
    df = common.load_raw("web_service_logs.csv")
    common.inspect(df, NAME)

    # Transformation: timestamp is stored as text.
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    first, last = df["timestamp"].min(), df["timestamp"].max()
    print(f"\ntransformation: timestamp converted from text to datetime ({first} -> {last})")
    if first.time() > datetime.time(1) or last.time() < datetime.time(23):
        print("note: the first and last calendar days are partial, so per-day request counts are not comparable; per-day means are still valid.")

    needs_cleaning = df.isna().any().any() or df.duplicated().any()
    print("cleaning:", "needed" if needs_cleaning else "not needed (no missing values, no duplicates); nothing written to data/processed/")

    print("\nTool choice: plotly - time series plus 2,500 points that benefit from hover and zoom, so interactive HTML.")
    colors = dict(zip(sorted(df["endpoint"].unique()), px.colors.qualitative.Set2))  # same color per endpoint in every figure
    order = df.groupby("endpoint")["latency_ms"].median().sort_values(ascending=False).index.tolist()

    # Figure 1: daily mean latency per endpoint (trend over time)
    daily = (
        df.assign(day=df["timestamp"].dt.date)
        .groupby(["day", "endpoint"], as_index=False)["latency_ms"].mean()
        .rename(columns={"latency_ms": "mean_latency_ms"})
    )
    common.log_scale_check(daily["mean_latency_ms"], "daily mean latency")
    fig = px.line(
        daily, x="day", y="mean_latency_ms", color="endpoint", markers=True,
        color_discrete_map=colors, category_orders={"endpoint": order},
        title="Mean latency per day, by endpoint",
        labels={"day": "Date", "mean_latency_ms": "Mean latency (ms)", "endpoint": "Endpoint"},
    )
    line_html = save_html(fig, "line_latency_by_day_endpoint")

    # Figure 2: latency distribution per endpoint
    common.log_scale_check(df["latency_ms"], "latency_ms")
    fig = px.box(
        df, x="endpoint", y="latency_ms", color="endpoint",
        color_discrete_map=colors, category_orders={"endpoint": order},
        title="Latency distribution by endpoint",
        labels={"endpoint": "Endpoint", "latency_ms": "Latency (ms)"},
    )
    box_html = save_html(fig, "box_latency_by_endpoint")

    # Figure 3: response size vs latency
    log_x = common.log_scale_check(df["response_kb"], "response_kb")
    fig = px.scatter(
        df, x="response_kb", y="latency_ms", color="endpoint", opacity=0.5, log_x=log_x,
        hover_name="request_id", hover_data=["timestamp", "status_code", "region", "device", "cache_hit"],
        color_discrete_map=colors, category_orders={"endpoint": order},
        title="Response size vs latency, by endpoint",
        labels={
            "response_kb": "Response size (KB" + (", log scale)" if log_x else ")"),
            "latency_ms": "Latency (ms)",
            "endpoint": "Endpoint",
        },
    )
    scatter_html = save_html(fig, "scatter_latency_by_response_size")

    print("\nObservations (for the written summary):")
    day_mean = df.groupby(df["timestamp"].dt.date)["latency_ms"].mean()
    print(f"daily mean latency across all endpoints: min {day_mean.min():.0f} ms, max {day_mean.max():.0f} ms")
    print("mean latency by endpoint (ms):", df.groupby("endpoint")["latency_ms"].mean().sort_values(ascending=False).round(0).to_dict())
    # Spearman correlation = Pearson correlation of the ranks. scipy is not installed and must not be added.
    rho = df["response_kb"].rank().corr(df["latency_ms"].rank())
    print(f"spearman correlation, response_kb vs latency_ms: {rho:.2f}")
    print(f"requests with status >= 400: {(df['status_code'] >= 400).mean():.1%}")

    ok = common.self_check([line_html, box_html, scatter_html])
    print("self-check:", "all output files exist" if ok else "FAILED")


if __name__ == "__main__":
    main()
