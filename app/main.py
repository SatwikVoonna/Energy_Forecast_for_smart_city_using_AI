from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.forecast import router as forecast_router
from app.api.routes.anomalies import router as anomalies_router
from app.api.routes.renewables import router as renewables_router
from app.api.routes.optimization import router as optimization_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.carbon import router as carbon_router
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

app.include_router(forecast_router, tags=["Forecast"])
app.include_router(anomalies_router, tags=["Anomalies"])
app.include_router(renewables_router, tags=["Renewables"])
app.include_router(optimization_router, tags=["Optimization"])
app.include_router(metrics_router, tags=["Metrics"])
app.include_router(carbon_router, tags=["Carbon"])
app.include_router(ws_router, tags=["WebSocket"])
