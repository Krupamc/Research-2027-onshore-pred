import pandas as pd
import numpy as np
from tensorflow import keras # type: ignore
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import Ridge
import joblib
from pathlib import Path


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

df = pd.read_csv("ml/now/KNJWARET3_scraped_data.csv")

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

# Average columns from 15mins to 1 hr
df = df[FEATURES].resample(
    "h",
    closed="left",
    label="left",
).mean()

print("\nHourly data:")
print(df.head())

print("\nHourly spacing:")
print(df.index.to_series().diff().value_counts())

print("\nMissing values after resampling:")
print(df[FEATURES].isna().sum())

print(df[FEATURES].head())
print("\nMissing values:")
print(df[FEATURES].isna().sum())

#
missing_rows = df[FEATURES].isna().any(axis=1)

print("\nMissing rows by hour of day:")
print(df.loc[missing_rows].groupby(df.loc[missing_rows].index.hour).size())

# -- Model prep --
X = []
y = []
target_times = []

# Fill short input gaps using past observations. Y stay unchanged
input_df = df[FEATURES].ffill(limit=2)

feature_values = input_df.to_numpy(dtype=np.float32)
target_values = df[TARGETS].to_numpy(dtype=np.float32)

print("\nMissing inputs before filling:")
print(df[FEATURES].isna().sum())

print("\nMissing inputs after filling:")
print(input_df.isna().sum())

bad_time = 0
bad_input = 0
bad_target = 0

for i in range(LOOKBACK, len(df)):
    times = df.index[i - LOOKBACK:i + 1]

    # 24 input hours + the following target hour
    spacing = times[1:] - times[:-1]

    if not (spacing == pd.Timedelta(hours=1)).all():
        bad_time += 1
        continue

    x_window = feature_values[i - LOOKBACK:i]
    y_next = target_values[i]

    if not np.isfinite(x_window).all():
        bad_input += 1
        continue

    if not np.isfinite(y_next).all():
        bad_target += 1
        continue

    X.append(x_window)
    y.append(y_next)
    target_times.append(df.index[i])

# Check longest stretch with all features available
valid_hours = np.isfinite(feature_values).all(axis=1)

longest_run = 0
current_run = 0

for valid in valid_hours:
    if valid:
        current_run += 1
        longest_run = max(longest_run, current_run)
    else:
        current_run = 0

print("\nWindow checks:")
print("Possible windows:", max(0, len(df) - LOOKBACK))
print("Rejected for time spacing:", bad_time)
print("Rejected for missing inputs:", bad_input)
print("Rejected for missing target:", bad_target)
print("Valid windows:", len(X))
print("Longest complete stretch:", longest_run, "hours")

if not X:
    raise ValueError(
        "No valid 24-hour windows. See window checks above."
    )

X = np.asarray(X, dtype=np.float32)
y = np.asarray(y, dtype=np.float32)
target_times = pd.DatetimeIndex(target_times)

# Model train
n = len(X)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

if train_end == 0 or val_end <= train_end or val_end >= n:
    raise ValueError("Not enough valid windows for training, validation, and testing.")

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
X_val_scaled = scale_x(X_val)
X_test_scaled = scale_x(X_test)

y_train_scaled = scaler_y.transform(y_train)
y_val_scaled = scaler_y.transform(y_val)

print("Training samples:", len(X_train))
print("Validation samples:", len(X_val))
print("Test samples:", len(X_test))

# -- Ridge (like lr) --
X_train_flat = X_train_scaled.reshape(len(X_train_scaled), -1)
X_val_flat = X_val_scaled.reshape(len(X_val_scaled), -1)
X_test_flat = X_test_scaled.reshape(len(X_test_scaled), -1)

# Pick regularization using validation data, not test data.
best_ridge = None
best_alpha = None
best_val_mae = float("inf")

for alpha in [0.1, 1.0, 10.0, 100.0]:
    ridge = Ridge(alpha=alpha)
    ridge.fit(X_train_flat, y_train)

    val_prediction = ridge.predict(X_val_flat)
    val_mae = mean_absolute_error(y_val, val_prediction)

    print(f"Ridge alpha={alpha}: validation component MAE={val_mae:.4f}")

    if val_mae < best_val_mae:
        best_val_mae = val_mae
        best_alpha = alpha
        best_ridge = ridge

ridge_prediction = best_ridge.predict(X_test_flat)

print("Selected Ridge alpha:", best_alpha)

# LSTM
keras.utils.set_random_seed(42)

model = keras.Sequential([
    keras.layers.Input(shape=(LOOKBACK, len(FEATURES))),
    keras.layers.LSTM(32),
    keras.layers.Dense(2),
])

#optimizers 
model.compile(optimizer="adam", loss="mse",)

history = model.fit(
    X_train_scaled,
    y_train_scaled,
    validation_data=(X_val_scaled, y_val_scaled),
    epochs=50,
    batch_size=32,
    shuffle=False,
    callbacks=[
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
        )
    ],
    verbose=1,
)

prediction_scaled = model.predict(
    X_test_scaled,
    verbose=0,
)

prediction = scaler_y.inverse_transform(prediction_scaled)
print("\nPrediction checks:")
print("Test samples:", len(y_test))
print("Prediction shape:", prediction.shape)
print("Actual shape:", y_test.shape)

print("\nFirst 5 actual targets:")
print(y_test[:5])

print("\nFirst 5 model predictions:")
print(prediction[:5])

print("\nFirst 5 differences:")
print(prediction[:5] - y_test[:5])

print("\nTest target timestamps:")
u_index = FEATURES.index("wind_u_ms")
v_index = FEATURES.index("wind_v_ms")

# Naive persistence
persistence = X_test[:, -1, [u_index, v_index]]

actual_speed = np.hypot(y_test[:, 0], y_test[:, 1])
lstm_speed = np.hypot(prediction[:, 0], prediction[:, 1])
persistence_speed = np.hypot(persistence[:, 0], persistence[:, 1])
ridge_speed = np.hypot(ridge_prediction[:, 0],ridge_prediction[:, 1])

# metrics
metrics = pd.DataFrame([
    {
        "model": "Persistence",
        "u_mae_ms": mean_absolute_error(
            y_test[:, 0], persistence[:, 0]
        ),
        "v_mae_ms": mean_absolute_error(
            y_test[:, 1], persistence[:, 1]
        ),
        "vector_speed_mae_ms": mean_absolute_error(
            actual_speed, persistence_speed
        ),
    },
    {
        "model": "LSTM",
        "u_mae_ms": mean_absolute_error(
            y_test[:, 0], prediction[:, 0]
        ),
        "v_mae_ms": mean_absolute_error(
            y_test[:, 1], prediction[:, 1]
        ),
        "vector_speed_mae_ms": mean_absolute_error(
            actual_speed, lstm_speed
        ),
    },
    {
        "model": "Ridge",
        "u_mae_ms": mean_absolute_error(
            y_test[:, 0], ridge_prediction[:, 0]
        ),
        "v_mae_ms": mean_absolute_error(
            y_test[:, 1], ridge_prediction[:, 1]
        ),
        "vector_speed_mae_ms": mean_absolute_error(
            actual_speed, ridge_speed
        ),
    },
])

print(metrics.to_string(index=False))

print("\nPrediction check:")
print("First 5 predictions:")
print(prediction[:5])

print("Prediction std, u and v:")
print(prediction.std(axis=0))

print("Actual std, u and v:")
print(y_test.std(axis=0))


# output
output_dir = Path("ml/now/results")
output_dir.mkdir(exist_ok=True)

results = pd.DataFrame({
    "target_timestamp": target_times[val_end:],
    "actual_u_ms": y_test[:, 0],
    "actual_v_ms": y_test[:, 1],
    "actual_vector_speed_ms": actual_speed,
    "lstm_u_ms": prediction[:, 0],
    "lstm_v_ms": prediction[:, 1],
    "lstm_vector_speed_ms": lstm_speed,
    "persistence_u_ms": persistence[:, 0],
    "persistence_v_ms": persistence[:, 1],
    "ridge_u_ms": ridge_prediction[:, 0],
    "ridge_v_ms": ridge_prediction[:, 1],
    "ridge_vector_speed_ms": ridge_speed,
})

results.to_csv(output_dir / "test_predictions.csv", index=False)
metrics.to_csv(output_dir / "model_metrics.csv", index=False)

model.save(output_dir / "wind_lstm.keras")

joblib.dump(
    {
        "scaler_x": scaler_x,
        "scaler_y": scaler_y,
        "features": FEATURES,
        "targets": TARGETS,
        "lookback": LOOKBACK,
    },
    output_dir / "preprocessing.joblib",
)
joblib.dump(
    best_ridge,
    output_dir / "wind_ridge.joblib",
)

