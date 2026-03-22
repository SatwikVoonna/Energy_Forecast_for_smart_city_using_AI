from fastapi import APIRouter, HTTPException
import json
import os
from app.core.config import METRICS_PATH

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    if not os.path.exists(METRICS_PATH):
        raise HTTPException(status_code=404, detail="Metrics file not found. Run model training first. No mock data allowed.")
        
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
        
    return metrics
