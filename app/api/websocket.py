from app.core.data_cache import get_cached_dataframe
import asyncio
import json
import pandas as pd
import torch
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import FORECAST_DATASET_PATH
from app.core.model_loader import model_manager

router = APIRouter()

DROP_COLS = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    if not model_manager.xgb_model or not model_manager.anomaly_detector:
        await websocket.close(code=1011, reason="Models not loaded")
        return

    try:
        df = get_cached_dataframe(FORECAST_DATASET_PATH)
        feature_cols = [c for c in df.columns if c not in DROP_COLS]
        recent_df    = df.tail(500)
    except FileNotFoundError:
        await websocket.close(code=1011, reason="Forecast dataset not found. No mock data allowed.")
        return

    try:
        for idx, row in recent_df.iterrows():
            timestamp = str(idx)
            features  = row[feature_cols].to_frame().T
            actual    = float(row['total_demand_kwh'])

            pred_scaled = model_manager.xgb_model.predict(features)[0]
            pred_orig   = float(model_manager.target_scaler.inverse_transform(
                              [[pred_scaled]]
                          )[0][0])

            residual        = [[actual - pred_scaled]]
            is_anomaly_pred = model_manager.anomaly_detector.predict(residual)[0]
            is_anomaly      = bool(is_anomaly_pred == -1)

            payload = {
                "timestamp":    timestamp,
                "forecast_kwh": pred_orig,
                "actual_kwh":   float(model_manager.target_scaler.inverse_transform([[actual]])[0][0]),
                "is_anomaly":   is_anomaly,
                "anomaly_type": "High" if is_anomaly else "Normal",
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")
