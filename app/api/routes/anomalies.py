from app.core.data_cache import get_cached_dataframe
from fastapi import APIRouter, HTTPException
import pandas as pd
from pydantic import BaseModel
from typing import List
from app.core.config import ANOMALY_DATASET_PATH
from app.core.model_loader import model_manager

router = APIRouter()

DROP_COLS = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}

class AnomalyResponse(BaseModel):
    timestamp: str
    severity: str
    score: float
    expected_kwh: float
    actual_kwh: float

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies():
    if not model_manager.anomaly_detector or not model_manager.xgb_model:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        df = get_cached_dataframe(ANOMALY_DATASET_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Anomaly dataset missing. No mock data allowed.")

    df_recent    = df.tail(500)
    feature_cols = [c for c in df_recent.columns if c not in DROP_COLS]

    actual     = df_recent['total_demand_kwh'].values
    timestamps = df_recent.index.astype(str).tolist()

    preds_scaled = model_manager.xgb_model.predict(df_recent[feature_cols])
    preds        = model_manager.target_scaler.inverse_transform(
                       preds_scaled.reshape(-1, 1)
                   ).flatten()
    actual_orig  = model_manager.target_scaler.inverse_transform(
                       actual.reshape(-1, 1)
                   ).flatten()

    residuals   = (actual - preds_scaled).reshape(-1, 1)
    predictions = model_manager.anomaly_detector.predict(residuals)
    scores      = model_manager.anomaly_detector.decision_function(residuals)

    results = []
    for t, is_anom, score, expected, act in zip(timestamps, predictions, scores, preds, actual_orig):
        if is_anom == -1:
            severity = "High" if abs(score) > 0.1 else "Medium"
            results.append(AnomalyResponse(
                timestamp=t,
                severity=severity,
                score=float(score),
                expected_kwh=float(expected),
                actual_kwh=float(act),
            ))

    return results
