from app.core.data_cache import get_cached_dataframe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd
from app.core.config import FORECAST_DATASET_PATH

router = APIRouter()

DROP_COLS = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}

class OptimizationRequest(BaseModel):
    battery_capacity: float = 10000.0
    peak_tariff:      float = 0.25
    offpeak_tariff:   float = 0.08

class OptimizationResponse(BaseModel):
    baseline_cost:  float
    optimized_cost: float
    savings:        float
    dispatch_plan:  Dict[str, str]

@router.post("/optimize", response_model=OptimizationResponse)
def optimize_battery(req: OptimizationRequest):
    try:
        df = get_cached_dataframe(FORECAST_DATASET_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Forecast dataset not found. No mock data allowed.")

    recent = df.tail(24)
    battery_state  = 0.0
    baseline_cost  = 0.0
    optimized_cost = 0.0
    dispatch_plan: Dict[str, str] = {}

    hour_col = "hour" if "hour" in recent.columns else None

    for idx, row in recent.iterrows():
        hour   = int(row[hour_col] * 24 + 12) % 24 if hour_col else idx.hour  # de-normalise approx
        demand = float(row['total_demand_kwh'])

        is_peak = 16 <= hour <= 21
        tariff  = req.peak_tariff if is_peak else req.offpeak_tariff

        baseline_cost += abs(demand) * tariff

        action = "Hold"
        if not is_peak and battery_state < req.battery_capacity:
            charge = min(req.battery_capacity - battery_state, abs(demand) * 0.5)
            battery_state  += charge
            optimized_cost += (abs(demand) + charge) * tariff
            action = f"Charge ({charge:.1f} kWh)"
        elif is_peak and battery_state > 0:
            discharge      = min(battery_state, abs(demand))
            battery_state -= discharge
            optimized_cost += max(0, abs(demand) - discharge) * tariff
            action = f"Discharge ({discharge:.1f} kWh)"
        else:
            optimized_cost += abs(demand) * tariff

        dispatch_plan[f"Hour~{hour:02d}"] = action

    savings = baseline_cost - optimized_cost
    return OptimizationResponse(
        baseline_cost=baseline_cost,
        optimized_cost=optimized_cost,
        savings=savings,
        dispatch_plan=dispatch_plan,
    )
