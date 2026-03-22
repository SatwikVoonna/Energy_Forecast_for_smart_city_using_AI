from app.core.data_cache import get_cached_dataframe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from app.core.config import FORECAST_DATASET_PATH

router = APIRouter()

DROP_COLS = {"is_anomaly", "anomaly_type", "minute", "split", "total_demand_kwh"}

class RenewableResponse(BaseModel):
    timestamp: str
    demand: float
    solar: float
    wind: float
    net_load: float
    renewable_utilization_pct: float

@router.get("/renewables/netload", response_model=RenewableResponse)
def get_renewables_netload():
    try:
        df = get_cached_dataframe(FORECAST_DATASET_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Dataset not found. No mock data allowed.")

    latest    = df.iloc[-1]
    timestamp = str(df.index[-1])

    # The demand in the CSV is scaled; use the raw row value (scaled)
    demand_scaled = float(latest['total_demand_kwh'])

    # Use temperature & wind columns actually in the dataset
    temp_col  = 'temperature_2m'       if 'temperature_2m'       in df.columns else None
    wind_col  = 'windspeed_10m'        if 'windspeed_10m'        in df.columns else None
    solar_col = 'shortwave_radiation'  if 'shortwave_radiation'  in df.columns else None

    hour = float(latest['hour']) if 'hour' in df.columns else 12.0

    # Solar: daylight curve × radiation proxy (scaled value, normalised to capacity)
    solar_factor = max(0.0, np.sin(np.pi * max(0.0, (hour + 1.660811) / 24.0 * 24.0 - 6.0) / 12.0))
    if solar_col:
        solar_raw = float(latest[solar_col])  # scaled
        solar     = max(0.0, solar_factor * (1 + solar_raw) * 2000.0)
    else:
        solar = solar_factor * 2000.0

    # Wind: proportional to wind speed proxy
    if wind_col:
        wind_raw = float(latest[wind_col])
        wind     = max(0.0, (1 + wind_raw) * 1500.0)
    else:
        wind = 1000.0

    # Scale demand back to approximate kWh range for display
    demand_for_display = (1 + demand_scaled) * 5000.0
    demand_for_display = max(100.0, demand_for_display)
    solar = min(solar, demand_for_display)
    wind  = min(wind,  demand_for_display)

    net_load    = demand_for_display - solar - wind
    utilization = ((solar + wind) / demand_for_display) * 100.0

    return RenewableResponse(
        timestamp=timestamp,
        demand=demand_for_display,
        solar=solar,
        wind=wind,
        net_load=max(0.0, net_load),
        renewable_utilization_pct=min(100.0, max(0.0, utilization)),
    )
