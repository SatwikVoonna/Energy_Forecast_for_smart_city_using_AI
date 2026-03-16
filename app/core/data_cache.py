import pandas as pd
from functools import lru_cache
from .config import FORECAST_DATASET_PATH, ANOMALY_DATASET_PATH

@lru_cache(maxsize=2)
def get_cached_dataframe(path: str) -> pd.DataFrame:
    """Read the CSV once and keep it in memory for instant API responses."""
    return pd.read_csv(path, index_col=0, parse_dates=True)
