import os
import sys
import pandas as pd
from datetime import datetime

BRONZE_DIR = "data/bronze"
SILVER_DIR = "data/silver"

FILES = {
    "oee_by_day": "oee_by_day.csv",
    "oee_by_shift": "oee_by_shift.csv",
    "downtime_pareto": "downtime_pareto.csv",
}

def read_csv_safe(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def try_parse_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df

def is_numeric_series(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)

def make_quality_report(tables: dict) -> pd.DataFrame:
    rows = []
    run_ts = datetime.utcnow().isoformat()

    for name, df in tables.items():
        df = df.copy()

        # Common expectations
        df = normalize_columns(df)

        # Candidate key + required columns (best-effort based on typical schema)
        required = []
        key_cols = []

        if name == "oee_by_day":
            required = ["day", "machine"]
            key_cols = ["day", "machine"]
        elif name == "oee_by_shift":
            required = ["day", "machine", "shift"]
            key_cols = ["day", "machine", "shift"]
        elif name == "downtime_pareto":
            required = ["day", "machine", "cause"]
            key_cols = ["day", "machine", "cause"]

        # Date parse
        df = try_parse_date(df, "day")

        # Basic checks
        total_rows = len(df)
        null_day = int(df["day"].isna().sum()) if "day" in df.columns else None
        null_machine = int(df["machine"].isna().sum()) if "machine" in df.columns else None

        missing_required = [c for c in required if c not in df.columns]

        # Duplicate keys
        dup_keys = None
        if all(c in df.columns for c in key_cols) and len(key_cols) > 0:
            dup_keys = int(df.duplicated(subset=key_cols).sum())

        # Negative numeric values (scan numeric cols)
        neg_violations = 0
        for col in df.columns:
            if is_numeric_series(df[col]):
                neg_violations += int((df[col] < 0).sum())

        # OEE component bounds checks if present
        bound_cols = [c for c in ["availability", "performance", "quality", "oee"] if c in df.columns]
        out_of_bounds = 0
        for c in bound_cols:
            # accept 0-1 OR 0-100 (detect)
            series = df[c].dropna()
            if series.empty:
                continue
            maxv = series.max()
            if maxv <= 1.5:
                out_of_bounds += int(((df[c] < 0) | (df[c] > 1)).sum())
            else:
                out_of_bounds += int(((df[c] < 0) | (df[c] > 100)).sum())

        rows.append({
            "run_utc": run_ts,
            "table": name,
            "rows": total_rows,
            "missing_required_columns": ", ".join(missing_required) if missing_required else "",
            "null_day": null_day if null_day is not None else "",
            "null_machine": null_machine if null_machine is not None else "",
            "duplicate_key_rows": dup_keys if dup_keys is not None else "",
            "negative_numeric_cells": neg_violations,
            "oee_out_of_bounds_cells": out_of_bounds,
        })

    return pd.DataFrame(rows)

def main():
    os.makedirs(SILVER_DIR, exist_ok=True)

    tables = {}
    for name, fname in FILES.items():
        path = os.path.join(BRONZE_DIR, fname)
        df = read_csv_safe(path)
        tables[name] = df

    report = make_quality_report(tables)
    out_path = os.path.join(SILVER_DIR, "data_quality_report.csv")
    report.to_csv(out_path, index=False)

    print("✅ Data quality report saved to:", out_path)
    print(report.to_string(index=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ ETL failed:", e)
        sys.exit(1)

