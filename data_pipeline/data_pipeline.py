import os
import io
import zipfile
import urllib.request
import numpy as np
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sklearn.preprocessing import RobustScaler, StandardScaler
import joblib

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

TARGET = "total_demand_kwh"
CITY_LAT = 13.0827
CITY_LON = 80.2707

# ------------------------------------------------
# DOWNLOAD DATASET
# ------------------------------------------------
def download_dataset():
    zip_path = os.path.join(DATA_DIR, "LD2011_2014.txt.zip")
    if not os.path.exists(zip_path):
        print("[→] Downloading UCI Electricity dataset...")
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100.0, downloaded * 100 / total_size)
                print(f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB ({percent:.1f}%)", end="")
            else:
                print(f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB", end="")
        urllib.request.urlretrieve("https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip", zip_path, reporthook=show_progress)
        print("\n[✓] Dataset downloaded")
    else:
        print("[✓] Dataset zip exists")

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
def load_energy_data(n_clients=100):
    print("[→] Loading energy dataset")
    zip_path = os.path.join(DATA_DIR, "LD2011_2014.txt.zip")
    with zipfile.ZipFile(zip_path) as z:
        filename = [n for n in z.namelist() if n.endswith('.txt')][0]
        with z.open(filename) as f:
            df = pd.read_csv(
                f,
                sep=";",
                index_col=0,
                parse_dates=True,
                decimal=",",
                usecols=range(n_clients + 1)
            )

    df[TARGET] = df.sum(axis=1)
    df = df[[TARGET]]
    df.index.name = "timestamp"
    print(f"[✓] Rows: {len(df)}")
    return df

# ------------------------------------------------
# WEATHER DATA
# ------------------------------------------------
def fetch_weather(start_date, end_date):
    print("[→] Fetching weather data")
    import requests
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": CITY_LAT,
        "longitude": CITY_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m",
        "timezone": "auto",
    }
    r = requests.get(url, params=params)
    data = r.json()
    hourly = data["hourly"]

    weather = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "temperature": hourly["temperature_2m"],
        "humidity": hourly["relativehumidity_2m"],
        "wind_speed": hourly["windspeed_10m"],
    })
    weather = weather.set_index("timestamp")
    if weather.index.tz is not None:
        weather.index = weather.index.tz_localize(None)

    weather = weather.resample("15min").interpolate()
    print("[✓] Weather loaded")
    return weather

# ------------------------------------------------
# FEATURE ENGINEERING
# ------------------------------------------------
def engineer_features(df):
    print("[→] Engineering features")
    ts = df.index
    df["hour"] = ts.hour
    df["dayofweek"] = ts.dayofweek
    df["month"] = ts.month
    df["is_weekend"] = (ts.dayofweek >= 5).astype(int)

    df["sin_hour"] = np.sin(2 * np.pi * ts.hour / 24)
    df["cos_hour"] = np.cos(2 * np.pi * ts.hour / 24)
    df["sin_day"] = np.sin(2 * np.pi * ts.dayofweek / 7)
    df["cos_day"] = np.cos(2 * np.pi * ts.dayofweek / 7)

    # lag features (15min intervals)
    df["lag_1h"] = df[TARGET].shift(4)
    df["lag_3h"] = df[TARGET].shift(12)
    df["lag_24h"] = df[TARGET].shift(96)
    df["lag_168h"] = df[TARGET].shift(672)

    df["rolling_mean_3h"] = df[TARGET].shift(1).rolling(12).mean()
    df["rolling_std_3h"] = df[TARGET].shift(1).rolling(12).std()
    df["rolling_mean_24h"] = df[TARGET].shift(1).rolling(96).mean()

    if "temperature" in df.columns:
        df["temp_lag_1h"] = df["temperature"].shift(4)
        df["temp_lag_24h"] = df["temperature"].shift(96)
        df["temp_change"] = df["temperature"].diff()

    print(f"[✓] Features created: {df.shape[1]}")
    return df

# ------------------------------------------------
# ANOMALY INJECTION
# ------------------------------------------------
def inject_anomalies(df, rate=0.02):
    print("[→] Injecting anomalies")
    df = df.copy()
    n = len(df)
    k = int(n * rate)
    idx = np.random.choice(n, k, replace=False)
    df["is_anomaly"] = 0

    for i in idx:
        multiplier = np.random.uniform(3, 6)
        df.iloc[i, df.columns.get_loc(TARGET)] *= multiplier
        df.iloc[i, df.columns.get_loc("is_anomaly")] = 1

    print(f"[✓] Injected {k} anomalies")
    return df

# ------------------------------------------------
# SCALING
# ------------------------------------------------
def scale_data(df, is_train=True):
    print("[→] Scaling data")
    df = df.dropna()

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in [TARGET, "is_anomaly"]]
    
    target_scaler = RobustScaler()
    feature_scaler = StandardScaler()

    train_end = int(len(df) * 0.7)
    train = df.iloc[:train_end]

    # Fit only on training portion
    target_scaler.fit(train[[TARGET]])
    feature_scaler.fit(train[feature_cols])

    # Transform everything
    df = df.copy()
    df[TARGET] = target_scaler.transform(df[[TARGET]])
    df[feature_cols] = feature_scaler.transform(df[feature_cols])

    if is_train:
        joblib.dump(target_scaler, f"{MODEL_DIR}/target_scaler.pkl")
        joblib.dump(feature_scaler, f"{MODEL_DIR}/feature_scaler.pkl")

    print("[✓] Scaling complete")
    return df

# ------------------------------------------------
# PIPELINE
# ------------------------------------------------
def run_pipeline():
    print("\n==============================")
    print("ENERGY DEMAND DATA PIPELINE")
    print("==============================\n")

    download_dataset()
    energy = load_energy_data()

    start = energy.index.min().strftime("%Y-%m-%d")
    end = energy.index.max().strftime("%Y-%m-%d")
    weather = fetch_weather(start, end)

    df = energy.join(weather)
    df = df.ffill().bfill()
    df = engineer_features(df)

    forecast_df = df.copy()
    anomaly_df = inject_anomalies(df)

    forecast_df = scale_data(forecast_df, is_train=True)
    anomaly_df = scale_data(anomaly_df, is_train=False)

    forecast_df.to_csv(f"{DATA_DIR}/forecast_dataset.csv")
    anomaly_df.to_csv(f"{DATA_DIR}/anomaly_dataset.csv")

    print("\n[✓] Pipeline complete")

if __name__ == "__main__":
    run_pipeline()
