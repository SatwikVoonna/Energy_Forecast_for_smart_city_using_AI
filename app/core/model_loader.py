import os
import joblib
import torch
import torch.nn as nn
from app.core.config import (
    XGBOOST_MODEL_PATH, LSTM_MODEL_PATH, ENSEMBLE_MODEL_PATH,
    ANOMALY_DETECTOR_PATH, TARGET_SCALER_PATH, FEATURE_SCALER_PATH,
    FORECAST_DATASET_PATH
)
import pandas as pd

class DemandLSTM(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(DemandLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        return self.linear(hn[-1])

class ModelManager:
    def __init__(self):
        self.xgb_model = None
        self.lstm_model = None
        self.ensemble_model = None
        self.anomaly_detector = None
        self.target_scaler = None
        self.feature_scaler = None
        self.feature_cols = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def load_models(self):
        paths = [XGBOOST_MODEL_PATH, LSTM_MODEL_PATH, ENSEMBLE_MODEL_PATH,
                 ANOMALY_DETECTOR_PATH, TARGET_SCALER_PATH, FEATURE_SCALER_PATH]

        for p in paths:
            if not os.path.exists(p):
                raise RuntimeError(
                    f"Missing required model/scaler at {p}. "
                    "Run model training first. No mock data allowed."
                )

        self.xgb_model        = joblib.load(XGBOOST_MODEL_PATH)
        self.ensemble_model   = joblib.load(ENSEMBLE_MODEL_PATH)
        self.anomaly_detector = joblib.load(ANOMALY_DETECTOR_PATH)
        self.target_scaler    = joblib.load(TARGET_SCALER_PATH)
        self.feature_scaler   = joblib.load(FEATURE_SCALER_PATH)

        # Determine feature columns from the dataset FIRST (before loading LSTM)
        drop_cols = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}
        if not os.path.exists(FORECAST_DATASET_PATH):
            raise RuntimeError(f"Forecast dataset not found at {FORECAST_DATASET_PATH}.")
        df_sample = pd.read_csv(FORECAST_DATASET_PATH, nrows=2, index_col=0)
        self.feature_cols = [c for c in df_sample.columns if c not in drop_cols]

        # Now instantiate LSTM with the CORRECT input size
        n_features = len(self.feature_cols)
        self.lstm_model = DemandLSTM(input_size=n_features, hidden_size=128).to(self.device)
        self.lstm_model.load_state_dict(
            torch.load(LSTM_MODEL_PATH, map_location=self.device, weights_only=True)
        )
        self.lstm_model.eval()

model_manager = ModelManager()
