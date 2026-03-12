from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import forecast, anomalies, renewables, optimization, metrics, carbon
from app.api.websocket import router as ws_router
from app.core.model_loader import model_manager

app = FastAPI(title="Smart Grid AI Demand Forecasting System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Pre-loading trained ML models...")
    model_manager.load_models()
    print("Models loaded successfully.")

@app.get("/")
def root():
    return {"status": "ok", "message": "Smart Grid AI Endpoint is running"}

app.include_router(forecast.router, tags=["Forecast"])
app.include_router(anomalies.router, tags=["Anomalies"])
app.include_router(renewables.router, tags=["Renewables"])
app.include_router(optimization.router, tags=["Optimization"])
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(carbon.router, tags=["Carbon"])
app.include_router(ws_router, tags=["WebSocket"])
