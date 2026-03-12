from app.core.data_cache import get_cached_dataframe
from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
import torch
from pydantic import BaseModel
from typing import List
from app.core.config import FORECAST_DATASET_PATH
from app.core.model_loader import model_manager

router = APIRouter()

# Columns to drop when building the feature matrix
DROP_COLS = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}

class ForecastResponse(BaseModel):
    timestamp: str
    forecast_kwh: float
    lower_bound: float
    upper_bound: float

@router.get("/forecast", response_model=List[ForecastResponse])
async def get_forecast(horizon: int = 24, model: str = "ensemble"):
    if not model_manager.xgb_model:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        df = get_cached_dataframe(FORECAST_DATASET_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Forecast dataset not found. No mock data allowed.")

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    recent       = df.tail(horizon)
    timestamps   = recent.index.astype(str).tolist()
    X_recent     = recent[feature_cols].values

    if model.lower() == "xgboost":
        preds_scaled = model_manager.xgb_model.predict(X_recent)

    elif model.lower() == "ensemble":
        xgb_preds = model_manager.xgb_model.predict(X_recent)

        # LSTM needs seq_len rows of context
        seq_len = 96
        if len(df) < seq_len + horizon:
            raise HTTPException(status_code=500, detail="Not enough historical data for LSTM.")

        features_all = df[feature_cols].values
        lstm_preds   = []
        for i in range(len(features_all) - horizon, len(features_all)):
            seq    = features_all[i - seq_len : i]
            tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0).to(model_manager.device)
            with torch.no_grad():
                lstm_preds.append(model_manager.lstm_model(tensor).item())

        X_ens        = np.column_stack([xgb_preds, np.array(lstm_preds)])
        preds_scaled = model_manager.ensemble_model.predict(X_ens)

    else:
        raise HTTPException(status_code=400, detail="Unknown model. Choose 'ensemble' or 'xgboost'.")

    preds_orig = model_manager.target_scaler.inverse_transform(
        preds_scaled.reshape(-1, 1)
    ).flatten()

    return [
        ForecastResponse(
            timestamp=t,
            forecast_kwh=float(p),
            lower_bound=float(p * 0.95),
            upper_bound=float(p * 1.05),
        )
        for t, p in zip(timestamps, preds_orig)
    ]
