import pandas as pd
import numpy as np
from direction_score import rank_headings

df = pd.read_csv("ml/now/results/test_predictions.csv")

# Look for all co,umns
required = [
    "target_timestamp",
    "actual_u_ms",
    "actual_v_ms",
    "ridge_u_ms",
    "ridge_v_ms",
    "persistence_u_ms",
    "persistence_v_ms",
]

missing = [
    column for column in required
    if column not in df.columns
]

if missing:
    raise ValueError(f"Prediction CSV is missing columns: {missing}. Rerun suite.py after adding Ridge.")
if df.empty:
    raise ValueError("Prediction CSV has no observations.")
print("Historical test rows:", len(df))

# Wind moving east at 5 m/s
ranking = rank_headings(
    u=5.0,
    v=0.0,
    headings=[0, 90, 180, 270],
)

print("\nEastward wind ranking:")
print(ranking)

scores = {
    row["heading_deg"]: row["headwind_ms"]
    for row in ranking
}

print("Scores:", scores)

assert np.isclose(scores[90], 0.0)
assert np.isclose(scores[270], 5.0)
assert np.isclose(scores[0], 0.0)
assert np.isclose(scores[180], 0.0)

print("[PASS] Eastward wind test")

# Wind moving south at 4 m/s.
# Travelling north should face 4 m/s of opposing wind.
ranking = rank_headings(
    u=0.0,
    v=-4.0,
    headings=[0, 180],
)

scores = {
    row["heading_deg"]: row["headwind_ms"]
    for row in ranking
}

assert np.isclose(scores[0], 4.0)
assert np.isclose(scores[180], 0.0)

# No wind: every heading should have zero opposing wind.
ranking = rank_headings(
    u=0.0,
    v=0.0,
    headings=[0, 90, 180, 270],
)

assert all(
    np.isclose(row["headwind_ms"], 0.0)
    for row in ranking
)

print("[PASS] Basic heading-score tests")

# Example choices only. Replace these with headings toward locations.
headings = [0, 90, 180, 270]

row = df.iloc[0]

ranking = rank_headings(
    row["ridge_u_ms"],
    row["ridge_v_ms"],
    headings,
)

print("Historical target hour:", row["target_timestamp"])

print("\nExperimental heading ranking:")

for option in ranking:
    print(
        f"Heading: {option['heading_deg']:.0f} degrees | "
        f"Opposing wind: {option['headwind_ms']:.2f} m/s"
    )

comparison = []

for _, row in df.iterrows():
    ridge_choice = rank_headings(
        row["ridge_u_ms"],
        row["ridge_v_ms"],
        headings,
    )[0]

    persistence_choice = rank_headings(
        row["persistence_u_ms"],
        row["persistence_v_ms"],
        headings,
    )[0]

    # Score each chosen heading against observed wind,
    # not the forecast that selected it.
    ridge_actual = rank_headings(
        row["actual_u_ms"],
        row["actual_v_ms"],
        [ridge_choice["heading_deg"]],
    )[0]

    persistence_actual = rank_headings(
        row["actual_u_ms"],
        row["actual_v_ms"],
        [persistence_choice["heading_deg"]],
    )[0]

    comparison.append({
        "target_timestamp": row["target_timestamp"],
        "ridge_heading_deg": ridge_choice["heading_deg"],
        "persistence_heading_deg": persistence_choice["heading_deg"],
        "ridge_observed_headwind_ms": ridge_actual["headwind_ms"],
        "persistence_observed_headwind_ms": (
            persistence_actual["headwind_ms"]
        ),
    })

comparison = pd.DataFrame(comparison)

print("\nMean observed opposing wind:")
print(
    comparison[[
        "ridge_observed_headwind_ms",
        "persistence_observed_headwind_ms",
    ]].mean()
)

comparison.to_csv(
    "ml/now/results/heading_comparison.csv",
    index=False,
)