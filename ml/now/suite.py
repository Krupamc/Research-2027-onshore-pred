import pandas as pd
import numpy as np
from tensorflow import keras # type: ignore
from sklearn.preprocessing import StandardScaler

# X: 24 completed hours of weather y: wind_u_ms and wind_v_ms for the following hour

FEATURES = [
    "temp_c",
    "humidity_pct",
    "pressure_hpa",
    "wind_u_ms",
    "wind_v_ms",
]

TARGETS = [
    "wind_u_ms",
    "wind_v_ms",
]
LOOKBACK = 24 # window of hours how much to look back

df = pd.read_csv("ml/now/KMJOCEAN178_scraped_data.csv")

if "station_id" in df.columns:
    stations = df["station_id"].dropna().unique()
    if len(stations) != 1:
        raise ValueError(f"Use one station for this first model. Found: {stations}")

time_col = "observed_at_local"

df[time_col] = pd.to_datetime(df[time_col], errors="raise")
df = df.sort_values(time_col).set_index(time_col)

if df.index.has_duplicates:
    raise ValueError( "Duplicate timestamps found. Check reruns and daylight-saving transitions before training.")

numeric_columns = [
    "temp_c",
    "humidity_pct",
    "pressure_hpa",
    "wind_speed_ms",
    "wind_from_deg",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Reject invalid wind values.
df.loc[df["wind_speed_ms"] < 0, "wind_speed_ms"] = np.nan

df.loc[~df["wind_from_deg"].between(0, 360), "wind_from_deg"] = np.nan

theta = np.deg2rad(df["wind_from_deg"])

df["wind_u_ms"] = -df["wind_speed_ms"] * np.sin(theta)
df["wind_v_ms"] = -df["wind_speed_ms"] * np.cos(theta)

calm = df["wind_speed_ms"].eq(0)
df.loc[calm, ["wind_u_ms", "wind_v_ms"]] = 0.0

df[FEATURES] = df[FEATURES].replace([np.inf, -np.inf], np.nan)

print(df[FEATURES].head())
print("\nMissing values:")
print(df[FEATURES].isna().sum())

# -- Model prep --
X = []
y = []
target_times = []

feature_values = df[FEATURES].to_numpy(dtype=np.float32)
target_values = df[TARGETS].to_numpy(dtype=np.float32)

for i in range(LOOKBACK, len(df)):
    # Includes 24 input timestamps plus the target timestamp.
    times = df.index[i - LOOKBACK:i + 1]

    if not np.all(
        (times[1:] - times[:-1]) == pd.Timedelta(hours=1)
    ):
        continue

    x_window = feature_values[i - LOOKBACK:i]
    y_next = target_values[i]

    if not np.isfinite(x_window).all():
        continue

    if not np.isfinite(y_next).all():
        continue

    X.append(x_window)
    y.append(y_next)
    target_times.append(df.index[i])

if not X:
    raise ValueError("X not valid")

X = np.asarray(X, dtype=np.float32)
y = np.asarray(y, dtype=np.float32)
target_times = pd.DatetimeIndex(target_times)

# shapes
print("X shape:", X.shape) 
print("y shape:", y.shape)

# Model train
n = len(X)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

X_train = X[:train_end]
X_val = X[train_end:val_end]
X_test = X[val_end:]

y_train = y[:train_end]
y_val = y[train_end:val_end]
y_test = y[val_end:]

scaler_x = StandardScaler()
scaler_y = StandardScaler()

scaler_x.fit(X_train.reshape(-1, len(FEATURES)))
scaler_y.fit(y_train)

def scale_x(values):
    return scaler_x.transform(values.reshape(-1, len(FEATURES))).reshape(values.shape).astype(np.float32)

X_train_scaled = scale_x(X_train)