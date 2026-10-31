import pandas as pd
import numpy as np
import itertools
from tensorflow import keras # type: ignore
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

# ----------------------------
# 1. Load and clean data
# ----------------------------
df = pd.read_csv("CLEAN.csv")

df["Date"] = pd.to_datetime(df["Date"]) + pd.to_timedelta(df["Hr"], unit="h")
df = df[df["Date"].dt.month.isin([6, 7, 8])].reset_index(drop=True)

all_vars = [
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

# ----------------------------
# 2. Hyperparameter options
# ----------------------------
seq_lens = [6, 12, 24]
batch_sizes = [8, 16, 32]
validation_splits = [0.1, 0.2]
epochs_list = [30, 60]
lstm_units_list = [16, 32]
dense_units_list = [0, 16]
dropout_list = [0.0, 0.2]

# ----------------------------
# 3. Sequence maker
# ----------------------------
def make_sequences(X, y, seq_len):
    X_seq, y_seq = [], []
    for i in range(seq_len, len(X)):
        X_seq.append(X[i-seq_len:i])
        y_seq.append(y[i])
    return np.array(X_seq), np.array(y_seq)

# ----------------------------
# 4. Train one model
# ----------------------------
def run_lstm_for_target(df, target_col, seq_len, batch_size, validation_split,
                        epochs, lstm_units, dense_units, dropout):

    feature_cols = [c for c in all_vars if c != target_col]

    temp = df[feature_cols + [target_col]].copy()
    temp["target"] = temp[target_col].shift(-1)
    temp = temp.dropna().reset_index(drop=True)

    X = temp[feature_cols].values
    y = temp["target"].values.reshape(-1, 1)

    split = int(len(temp) * 0.9)
    X_train_raw, X_test_raw = X[:split], X[split:]
    y_train_raw, y_test_raw = y[:split], y[split:]

    if len(X_train_raw) <= seq_len or len(X_test_raw) <= seq_len:
        return None

    scaler_x = StandardScaler()
    scaler_y = StandardScaler()

    X_train_scaled = scaler_x.fit_transform(X_train_raw)
    X_test_scaled = scaler_x.transform(X_test_raw)

    y_train_scaled = scaler_y.fit_transform(y_train_raw)
    y_test_scaled = scaler_y.transform(y_test_raw)

    X_train, y_train = make_sequences(X_train_scaled, y_train_scaled, seq_len)
    X_test, y_test = make_sequences(X_test_scaled, y_test_scaled, seq_len)

    if len(X_train) == 0 or len(X_test) == 0:
        return None

    model = keras.Sequential()
    model.add(keras.layers.Input(shape=(seq_len, X_train.shape[2])))
    model.add(keras.layers.LSTM(lstm_units))

    if dropout > 0:
        model.add(keras.layers.Dropout(dropout))

    if dense_units > 0:
        model.add(keras.layers.Dense(dense_units, activation="relu"))

    model.add(keras.layers.Dense(1))
    model.compile(optimizer="adam", loss="mae")

    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True
    )

    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        shuffle=False,
        callbacks=[early_stop],
        verbose=0
    )

    pred_scaled = model.predict(X_test, verbose=0)
    pred = scaler_y.inverse_transform(pred_scaled)
    y_true = scaler_y.inverse_transform(y_test)

    mae = mean_absolute_error(y_true.ravel(), pred.ravel())

    best_val_loss = min(history.history["val_loss"])
    epochs_ran = len(history.history["loss"])

    return {
        "target": target_col,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "validation_split": validation_split,
        "epochs_requested": epochs,
        "epochs_ran": epochs_ran,
        "lstm_units": lstm_units,
        "dense_units": dense_units,
        "dropout": dropout,
        "mae": mae,
        "best_val_loss": best_val_loss
    }

# ----------------------------
# 5. Loop through everything
# ----------------------------
results = []

param_grid = list(itertools.product(
    seq_lens,
    batch_sizes,
    validation_splits,
    epochs_list,
    lstm_units_list,
    dense_units_list,
    dropout_list
))

for target_col in all_vars:
    print(f"\nRunning target: {target_col}")
    for i, (seq_len, batch_size, validation_split, epochs,
            lstm_units, dense_units, dropout) in enumerate(param_grid, start=1):

        print(f"  Combo {i}/{len(param_grid)} | seq={seq_len}, batch={batch_size}, "
              f"val={validation_split}, epochs={epochs}, lstm={lstm_units}, "
              f"dense={dense_units}, dropout={dropout}")

        try:
            result = run_lstm_for_target(
                df=df,
                target_col=target_col,
                seq_len=seq_len,
                batch_size=batch_size,
                validation_split=validation_split,
                epochs=epochs,
                lstm_units=lstm_units,
                dense_units=dense_units,
                dropout=dropout
            )

            if result is not None:
                results.append(result)

        except Exception as e:
            results.append({
                "target": target_col,
                "seq_len": seq_len,
                "batch_size": batch_size,
                "validation_split": validation_split,
                "epochs_requested": epochs,
                "epochs_ran": None,
                "lstm_units": lstm_units,
                "dense_units": dense_units,
                "dropout": dropout,
                "mae": None,
                "best_val_loss": None,
                "error": str(e)
            })

# ----------------------------
# 6. Save results
# ----------------------------
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(["target", "mae"], na_position="last")

results_df.to_csv("lstm_hyperparameter_results.csv", index=False)

# Best row per target
best_per_target = results_df.dropna(subset=["mae"]).groupby("target", as_index=False).first()
best_per_target.to_csv("lstm_best_per_target.csv", index=False)

print("\nBest per target:")
print(best_per_target[["target", "mae", "seq_len", "batch_size", "validation_split",
                       "epochs_requested", "lstm_units", "dense_units", "dropout"]])