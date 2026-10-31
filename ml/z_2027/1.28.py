import pandas as pd
import numpy as np
from tensorflow import keras # type: ignore
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error


df = pd.read_csv("CLEAN.csv")

df["Date"] = pd.to_datetime(df["Date"]) + pd.to_timedelta(df["Hr"], unit="h")
df = df[df["Date"].dt.month.isin([6, 7, 8])].reset_index(drop=True)

features = [
    "Mainland Air Temp",
    "Direction (A)",
    "Wind Speed (A)",
    "Gusting",
    "Atmospheric Pressure (IN)",
    "Precipitation Rate",
    "Bay Temp",
    "Salinity",
    "LBI Air Temp",
    "Ocean Temp",
    "Onshore",
    "upwelling_flag"
]

target_col = "Wind Speed (A)"   # predict next-hour wind speed

# next hour target
df["target"] = df[target_col].shift(-1)

df = df.dropna().reset_index(drop=True)

X = df[features].values
y = df["target"].values.reshape(-1, 1)

# ----------------------------
# 2. Train/test split FIRST
# ----------------------------
split = int(len(df) * 0.9)

X_train_raw, X_test_raw = X[:split], X[split:]
y_train_raw, y_test_raw = y[:split], y[split:]

# ----------------------------
# 3. Scale using train only
# ----------------------------
scaler_x = StandardScaler()
scaler_y = StandardScaler()

X_train_scaled = scaler_x.fit_transform(X_train_raw)
X_test_scaled = scaler_x.transform(X_test_raw)

y_train_scaled = scaler_y.fit_transform(y_train_raw)
y_test_scaled = scaler_y.transform(y_test_raw)

# ----------------------------
# 4. Make sequences
# ----------------------------
seq_len = 24

def make_sequences(X, y, seq_len):
    X_seq, y_seq = [], []
    for i in range(seq_len, len(X)):
        X_seq.append(X[i-seq_len:i])
        y_seq.append(y[i])
    return np.array(X_seq), np.array(y_seq)

X_train, y_train = make_sequences(X_train_scaled, y_train_scaled, seq_len)
X_test, y_test = make_sequences(X_test_scaled, y_test_scaled, seq_len)

# ----------------------------
# 5. Build simple LSTM
# ----------------------------
model = keras.Sequential([
    keras.layers.Input(shape=(seq_len, X_train.shape[2])),
    keras.layers.LSTM(32),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(1)
])

model.compile(optimizer="adam", loss="mae")

early_stop = keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=16,
    validation_split=0.1,
    shuffle=False,
    callbacks=[early_stop],
    verbose=1
)

# ----------------------------
# 6. Predict and unscale
# ----------------------------
pred_scaled = model.predict(X_test)
pred = scaler_y.inverse_transform(pred_scaled)
y_test_true = scaler_y.inverse_transform(y_test)

mae = mean_absolute_error(y_test_true.ravel(), pred.ravel())
print("Test MAE:", mae)

# optional results dataframe
results = df.iloc[split + seq_len:].copy()
results["actual_next_hour"] = y_test_true.ravel()
results["pred_next_hour"] = pred.ravel()

print(results[["Date", "actual_next_hour", "pred_next_hour"]].head())



