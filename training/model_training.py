import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import IsolationForest
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
MODELS_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")

os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

TARGET = "total_demand_kwh"
SEQ_LEN = 96
BATCH_SIZE = 128
EPOCHS = 5

# ── LSTM ─────────────────────────────────────────────────────────────────────
class DemandLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128):
        super().__init__()
        self.lstm   = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        return self.linear(hn[-1])

def create_sequences(features, target, seq_len=96):
    xs, ys = [], []
    for i in range(len(features) - seq_len):
        xs.append(features[i : i + seq_len])
        ys.append(target[i + seq_len])
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)

# ── Load Data ─────────────────────────────────────────────────────────────────
def load_data():
    csv_path = os.path.join(DATA_DIR, "forecast_dataset.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    log.info("Loading forecast_dataset.csv ...")
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    # Automatically get numerical feature columns
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in [TARGET, "is_anomaly", "minute"]]
    
    n = len(df)
    train_end = int(n * 0.7)
    val_end   = int(n * 0.85)

    df_train = df.iloc[:train_end]
    df_val   = df.iloc[train_end:val_end]
    df_test  = df.iloc[val_end:]

    X_train = df_train[feature_cols].values
    y_train = df_train[TARGET].values
    X_val   = df_val[feature_cols].values
    y_val   = df_val[TARGET].values
    X_test  = df_test[feature_cols].values
    y_test  = df_test[TARGET].values

    log.info(f"Train:{len(X_train)}  Val:{len(X_val)}  Test:{len(X_test)}  Features:{len(feature_cols)}")
    return X_train, y_train, X_val, y_val, X_test, y_test, df[feature_cols], df[TARGET], len(feature_cols)

# ── Model 1: XGBoost ─────────────────────────────────────────────────────────
def train_xgboost(X_train, y_train, X_val, y_val, X_test):
    log.info("Training XGBoost with early stopping ...")
    model = XGBRegressor(
        n_estimators=1500,
        max_depth=8,
        learning_rate=0.02,
        subsample=0.9,
        colsample_bytree=0.9,
        tree_method="hist",
        random_state=42,
        eval_metric="rmse",
        early_stopping_rounds=50,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    log.info(f"XGBoost best iteration: {model.best_iteration}, best RMSE: {model.best_score:.5f}")
    joblib.dump(model, os.path.join(MODELS_DIR, "xgboost_model.pkl"))
    log.info("XGBoost saved.")
    return model, model.predict(X_test)

# ── Model 2: LSTM ─────────────────────────────────────────────────────────────
def train_lstm(X_train, y_train, X_val, y_val, X_test, n_features, seq_len=96, epochs=10, batch_size=128):
    log.info("Training LSTM ...")
    X_tr_seq, y_tr_seq = create_sequences(X_train, y_train, seq_len)
    X_va_seq, y_va_seq = create_sequences(X_val,   y_val,   seq_len)
    X_te_seq, _        = create_sequences(X_test,  np.zeros(len(X_test)), seq_len)

    ds     = TensorDataset(torch.from_numpy(X_tr_seq), torch.from_numpy(y_tr_seq).unsqueeze(1))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = DemandLSTM(n_features, hidden_size=128).to(device)
    opt    = optim.Adam(model.parameters(), lr=1e-3)
    crit   = nn.MSELoss()
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=3, factor=0.5)

    best_val_loss = float("inf")
    best_state    = None
    
    model.train()
    for ep in range(1, epochs + 1):
        train_loss = 0
        for bx, by in loader:
            bx, by = bx.to(device), by.to(device)
            opt.zero_grad()
            loss = crit(model(bx), by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_loss += loss.item()

        model.eval()
        val_ds     = TensorDataset(torch.from_numpy(X_va_seq), torch.from_numpy(y_va_seq).unsqueeze(1))
        val_loader = DataLoader(val_ds, batch_size=batch_size)
        val_loss   = 0.0
        with torch.no_grad():
            for vx, vy in val_loader:
                val_loss += crit(model(vx.to(device)), vy.to(device)).item()
        val_loss /= len(val_loader)
        model.train()
        
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state    = {k: v.clone() for k, v in model.state_dict().items()}

        log.info(f"LSTM Epoch {ep}/{epochs}  train_loss={train_loss/len(loader):.5f}  val_loss={val_loss:.5f}")

    model.load_state_dict(best_state)
    torch.save(model.state_dict(), os.path.join(MODELS_DIR, "lstm_model.pt"))
    log.info(f"LSTM saved (best val_loss={best_val_loss:.5f}).")

    model.eval()
    te_ds     = TensorDataset(torch.from_numpy(X_te_seq))
    te_loader = DataLoader(te_ds, batch_size=batch_size)
    preds_list = []
    with torch.no_grad():
        for (bx,) in te_loader:
            preds_list.append(model(bx.to(device)).cpu().numpy().flatten())
    preds = np.concatenate(preds_list)

    pad = np.full(seq_len, np.nan)
    return model, np.concatenate([pad, preds])

# ── Model 3: Ensemble ─────────────────────────────────────────────────────────
def train_ensemble(xgb_preds, lstm_preds, y_test):
    log.info("Training Ridge ensemble ...")
    valid = ~np.isnan(lstm_preds)
    X_ens = np.column_stack([xgb_preds[valid], lstm_preds[valid]])
    y_ens = y_test[valid]
    ens   = Ridge(alpha=1.0)
    ens.fit(X_ens, y_ens)
    joblib.dump(ens, os.path.join(MODELS_DIR, "ensemble_model.pkl"))
    log.info("Ensemble saved.")
    return ens, y_ens, ens.predict(X_ens), valid

# ── Model 4: Isolation Forest ─────────────────────────────────────────────────
def train_anomaly_detector(xgb_preds_all, y_all):
    log.info("Training Isolation Forest ...")
    
    anom_file = os.path.join(DATA_DIR, "anomaly_dataset.csv")
    if os.path.exists(anom_file):
        df_anom = pd.read_csv(anom_file)
        residuals = df_anom[TARGET].diff().fillna(0).values.reshape(-1, 1)
        isf = IsolationForest(contamination=0.03)
        isf.fit(residuals)
        joblib.dump(isf, os.path.join(MODELS_DIR, "anomaly_detector.pkl"))
        log.info("Isolation Forest saved.")

# ── Metrics (with DE-SCALING) ──────────────────────────────────────────────────
def calc_metrics(y_true, y_pred, scaler, name="Model"):
    # REVERSE TRANSFORM values for true interpretation!
    y_true_real = scaler.inverse_transform(y_true.reshape(-1, 1)).flatten()
    y_pred_real = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()

    mae  = float(mean_absolute_error(y_true_real, y_pred_real))
    rmse = float(np.sqrt(mean_squared_error(y_true_real, y_pred_real)))
    r2   = float(r2_score(y_true_real, y_pred_real))

    # SMAPE on real values
    smape = float(np.mean(
        2 * np.abs(y_pred_real - y_true_real) / (np.abs(y_true_real) + np.abs(y_pred_real) + 1e-10)
    ) * 100)

    threshold = 0.01 * np.std(y_true_real)
    mask = np.abs(y_true_real) > threshold
    if mask.sum() > 0:
        mape = float(np.mean(np.abs((y_true_real[mask] - y_pred_real[mask]) / y_true_real[mask])) * 100)
    else:
        mape = smape

    log.info(f"{name:15s}  MAE={mae:.2f}  RMSE={rmse:.2f}  SMAPE={smape:.2f}%  MAPE={mape:.2f}%  R²={r2:.4f}")
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape, "SMAPE": smape, "R2": r2}

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    X_train, y_train, X_val, y_val, X_test, y_test, df_features, df_target, n_features = load_data()
    
    scaler_path = os.path.join(MODELS_DIR, "target_scaler.pkl")
    target_scaler = joblib.load(scaler_path)

    # 1. XGBoost
    xgb_model, xgb_test_preds = train_xgboost(X_train, y_train, X_val, y_val, X_test)

    # 2. LSTM
    _, lstm_test_preds = train_lstm(X_train, y_train, X_val, y_val, X_test, n_features)

    # 3. Ensemble
    _, y_ens, ens_preds, valid_idx = train_ensemble(xgb_test_preds, lstm_test_preds, y_test)

    # 4. Anomaly Detector
    xgb_all = xgb_model.predict(df_features.values)
    train_anomaly_detector(xgb_all, df_target.values)

    # 5. Metrics per model (INVERSE SCALED!)
    log.info("\n--- FINAL METRICS (Actual kWh) ---")
    xgb_metrics  = calc_metrics(y_test, xgb_test_preds, target_scaler, name="XGBoost")
    
    lstm_src     = lstm_test_preds[~np.isnan(lstm_test_preds)]
    lstm_metrics = calc_metrics(y_test[valid_idx], lstm_src, target_scaler, name="LSTM")
    
    ens_metrics  = calc_metrics(y_ens, ens_preds, target_scaler, name="Ensemble")

    results = {
        "XGBoost":  xgb_metrics,
        "LSTM":     lstm_metrics,
        "Ensemble": ens_metrics,
    }

    with open(os.path.join(RESULTS_DIR, "model_results.json"), "w") as f:
        json.dump(results, f, indent=4)

    log.info("Training complete. Results saved to results/model_results.json")

if __name__ == "__main__":
    main()
