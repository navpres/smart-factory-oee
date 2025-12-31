import os
import pandas as pd

BRONZE = "data/bronze"
SILVER = "data/silver"

FILES = [
    "oee_by_day.csv",
    "oee_by_shift.csv",
    "downtime_pareto.csv"
]

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.drop_duplicates()

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    if "day" in df.columns:
        df["day"] = pd.to_datetime(df["day"], errors="coerce").dt.date

    # Convert OEE components to 0–1 scale if they are 0–100
    for col in ["availability", "performance", "quality", "oee"]:
        if col in df.columns:
            if df[col].max() > 1.5:
                df[col] = df[col] / 100

    return df

def main():
    os.makedirs(SILVER, exist_ok=True)

    for f in FILES:
        path = os.path.join(BRONZE, f)
        df = pd.read_csv(path)
        df = clean(df)

        out = os.path.join(SILVER, f.replace(".csv", "_clean.csv"))
        df.to_csv(out, index=False)
        print("Saved:", out)

if __name__ == "__main__":
    main()

