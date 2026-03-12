export interface ForecastResponse {
  horizon: number;
  model: string;
  history_kwh: number[];
  forecast_kwh: number[];
  lower_bound_kwh: number[];
  upper_bound_kwh: number[];
}

export interface RenewableResponse {
  timestamp: string;
  temperature: number;
  cloud_cover: number;
  wind_speed: number;
  demand_kwh: number;
  solar_generation_kwh: number;
  wind_generation_kwh: number;
  net_load_kwh: number;
  renewable_utilization_pct: number;
}

export interface AnomalyResponse {
  timestamp: string;
  actual_kwh: number;
  expected_kwh: number;
  difference_pct: number;
}

export interface MetricsResponse {
  [model: string]: {
    MAE: number;
    RMSE: number;
    MAPE: number;
    SMAPE: number;
    R2: number;
  };
}

export interface LiveStreamData {
  timestamp: string;
  actual_kwh: number;
  is_anomaly: boolean;
  forecast_kwh: number;
}
