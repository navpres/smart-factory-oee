import os
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SILVER = os.path.join(BASE_DIR, "data", "silver")
GOLD = os.path.join(BASE_DIR, "data", "gold")

os.makedirs(GOLD, exist_ok=True)

# Load cleaned silver data
oee_day = pd.read_csv(os.path.join(SILVER, "oee_by_day_clean.csv"))
oee_shift = pd.read_csv(os.path.join(SILVER, "oee_by_shift_clean.csv"))
downtime = pd.read_csv(os.path.join(SILVER, "downtime_pareto_clean.csv"))

print("Downtime columns:", list(downtime.columns))

# 1. KPI summary
kpi_summary = pd.DataFrame({
    "metric": ["Avg OEE", "Avg Availability", "Avg Performance", "Avg Quality"],
    "value": [
        oee_day["oee"].mean(),
        oee_day["availability"].mean(),
        oee_day["performance"].mean(),
        oee_day["quality"].mean(),
    ]
})

kpi_summary.to_csv(os.path.join(GOLD, "kpi_summary.csv"), index=False)

# 2. Worst shift
worst_shift = (
    oee_shift.groupby("shift")["oee"]
    .mean()
    .reset_index()
    .sort_values("oee")
    .head(1)
)

worst_shift.to_csv(os.path.join(GOLD, "worst_shift.csv"), index=False)

# 3. Top downtime cause (auto-detect numeric column)
numeric_cols = downtime.select_dtypes(include="number").columns.tolist()

if not numeric_cols:
    raise ValueError("No numeric columns found in downtime_pareto_clean.csv")

downtime_metric = numeric_cols[0]

top_downtime = downtime.sort_values(downtime_metric, ascending=False).head(1)
top_downtime.to_csv(os.path.join(GOLD, "top_downtime_cause.csv"), index=False)

# 4. Optimisation actions
cause_col = "cause" if "cause" in downtime.columns else downtime.columns[0]

actions = pd.DataFrame({
    "issue": ["Low OEE", "Worst shift", "Top downtime cause"],
    "recommended_action": [
        "Review maintenance and process stability",
        f"Investigate shift: {worst_shift.iloc[0]['shift']}",
        f"Reduce downtime from: {top_downtime.iloc[0][cause_col]}",
    ]
})

actions.to_csv(os.path.join(GOLD, "optimisation_actions.csv"), index=False)

print("✅ Gold layer built successfully.")
print("Files created in data/gold:")
print(os.listdir(GOLD))

