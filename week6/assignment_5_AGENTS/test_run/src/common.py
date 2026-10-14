"""Shared helpers: paths, data inspection (AGENTS.md rule 1), self-check (rule 5)."""
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
HTML = ROOT / "outputs" / "html"

for _folder in (PROCESSED, FIGURES, HTML):
    _folder.mkdir(parents=True, exist_ok=True)


def load_raw(filename):
    """Read a raw CSV. Files in data/raw/ are only read, never written."""
    return pd.read_csv(RAW / filename, encoding="utf-8-sig")


def inspect(df, name):
    """Print columns, dtypes, missing values, duplicates and implausible values."""
    print(f"=== Data inspection: {name} ===")
    print(f"rows x columns: {df.shape[0]} x {df.shape[1]}")
    print("\ncolumns and dtypes:")
    print(df.dtypes.to_string())

    missing = df.isna().sum()
    print("\nmissing values per column:", missing[missing > 0].to_dict() or "none")
    print("fully duplicated rows:", int(df.duplicated().sum()))
    for col in df.columns:
        if col.endswith("_id"):
            print(f"repeated values in {col}:", int(df[col].duplicated().sum()))

    numeric = df.select_dtypes("number")
    print("\nnumeric summary (min / median / max):")
    print(numeric.describe().T[["min", "50%", "max"]].round(2).to_string())

    flags = []
    for col in numeric.columns:
        s = numeric[col].dropna()
        if (s < 0).any():
            flags.append(f"{col}: {int((s < 0).sum())} negative value(s)")
        if col.endswith("_pct") and ((s < 0) | (s > 100)).any():
            flags.append(f"{col}: value(s) outside 0-100")
        q1, q3 = s.quantile([0.25, 0.75])
        spread = q3 - q1
        outliers = int(((s < q1 - 1.5 * spread) | (s > q3 + 1.5 * spread)).sum())
        if outliers:
            flags.append(f"{col}: {outliers} value(s) outside 1.5 x IQR (kept, not removed)")
        if pd.api.types.is_float_dtype(s) and (s == 0).any():
            flags.append(f"{col}: {int((s == 0).sum())} zero value(s)")
        if pd.api.types.is_float_dtype(s):
            top_value, top_count = s.value_counts().index[0], int(s.value_counts().iloc[0])
            if top_count / len(s) > 0.05:
                flags.append(
                    f"{col}: value {top_value} repeats {top_count} times "
                    f"({top_count / len(s):.0%}), possibly a floor or cap"
                )
    print("\nimplausible or suspicious values:")
    print("\n".join(f"  - {f}" for f in flags) if flags else "  none")


def log_scale_check(series, label):
    """Rule: use a log axis only when positive values span 2 or more orders of magnitude."""
    if (series <= 0).any():
        print(f"log-scale check {label}: contains zero or negative values -> linear axis")
        return False
    orders = math.log10(series.max() / series.min())
    use_log = orders >= 2
    print(
        f"log-scale check {label}: max/min = {series.max() / series.min():,.0f}x "
        f"({orders:.1f} orders of magnitude) -> {'log' if use_log else 'linear'} axis"
    )
    return use_log


def self_check(paths):
    """List the expected output files and report whether each exists."""
    print("\nOutput files:")
    all_ok = True
    for path in paths:
        ok = path.exists() and path.stat().st_size > 0
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else 'MISSING'}] {path.relative_to(ROOT)}")
    return all_ok
