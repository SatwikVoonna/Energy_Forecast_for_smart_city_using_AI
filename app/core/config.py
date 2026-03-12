import os

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Expected Model Paths
XGBOOST_MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_model.pkl")
LSTM_MODEL_PATH = os.path.join(MODELS_DIR, "lstm_model.pt")
ENSEMBLE_MODEL_PATH = os.path.join(MODELS_DIR, "ensemble_model.pkl")
ANOMALY_DETECTOR_PATH = os.path.join(MODELS_DIR, "anomaly_detector.pkl")
TARGET_SCALER_PATH = os.path.join(MODELS_DIR, "target_scaler.pkl")
FEATURE_SCALER_PATH = os.path.join(MODELS_DIR, "feature_scaler.pkl")
FORECAST_DATASET_PATH = os.path.join(DATA_DIR, "forecast_dataset.csv")
ANOMALY_DATASET_PATH = os.path.join(DATA_DIR, "anomaly_dataset.csv")
METRICS_PATH = os.path.join(RESULTS_DIR, "model_results.json")
