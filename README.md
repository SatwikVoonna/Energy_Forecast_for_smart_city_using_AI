# ⚡ Smart Grid AI: Energy Demand Forecasting System

A state-of-the-art, production-grade AI system designed for real-time electricity demand forecasting, anomaly detection, and grid optimization. This project leverages a hybrid approach, combining traditional Gradient Boosting with Deep Learning and Ensemble methods to ensure high accuracy and reliability in smart city environments.

---

## 📂 Project Structure

```text
smartgrid_ai/
├── app/                        # FastAPI Backend Service
│   ├── api/                    # API Route Definitions
│   │   ├── routes/             # Functional Endpoints (Forecast, Anomalies, etc.)
│   │   └── websocket.py        # Real-time WebSocket Stream
│   ├── core/                   # Core Logic (Config, Model Prep)
│   └── main.py                 # FastAPI Entry Point
├── data/                       # Dataset Storage (.csv files)
├── data_pipeline/              # Data Acquisition & Engineering
│   └── data_pipeline.py        # UCI Dataset + Weather API Integration
├── training/                   # Model Training & Evaluation
│   └── model_training.py       # Training Scripts for XGBoost, LSTM, etc.
├── models/                     # Serialized Model Artifacts (.joblib, .pt)
├── frontend/                   # Modern React/Vite/Tailwind Frontend
│   ├── src/                    # TypeScript Source Code
│   │   ├── pages/              # Dashboard & Landing Pages
│   │   ├── services/           # API Integration Logic
│   │   └── components/         # Reusable UI Blocks
│   └── package.json            # Node.js Dependencies
├── results/                    # Performance Metrics & Visualizations
└── requirements.txt            # Python Dependencies
```

---

## 🛠️ Components Used

### Backend Stack
*   **FastAPI**: High-performance Python framework for building APIs with auto-generated documentation (Swagger/OpenAPI).
*   **WebSockets**: Utilized for live telemetry and real-time anomaly alerts.
*   **Uvicorn**: ASGI server for running the FastAPI application.

### Frontend
*   **React (Vite + TypeScript)**: A premium, desktop-grade dashboard with modern transitions and high-fidelity charts.

### Modeling & Data
*   **PyTorch**: Framework for the LSTM (Long Short-Term Memory) neural network.
*   **XGBoost**: Optimized distributed gradient boosting library.
*   **Scikit-Learn**: Used for the Ridge Ensemble, Isolation Forest, and data scaling.
*   **Pandas & NumPy**: For efficient data manipulation and feature engineering.
*   **Joblib**: For persisting and loading trained models.

---

## 🤖 Models Trained

The system utilizes a multi-model approach to capture both linear and non-linear patterns in electricity consumption.

1.  **XGBoost (Extreme Gradient Boosting)**:
    *   **Role**: Primary regression model for capturing complex feature interactions (Time-of-day, Weather, Rolling Windows).
    *   **Performance**: RMSE ~0.051 on normalized test data.
2.  **LSTM (Long Short-Term Memory)**:
    *   **Role**: Recurrent Neural Network (Deep Learning) focused on long-range temporal dependencies.
    *   **Architecture**: Multi-layer LSTM units with hidden dimensions of 128.
3.  **Ensemble (Meta-Model)**:
    *   **Role**: A Ridge Regression meta-learner that weights predictions from both XGBoost and LSTM to minimize variance.
    *   **Benefit**: Provides more robust forecasts than any single model alone.
4.  **Isolation Forest**:
    *   **Role**: Unsupervised anomaly detection to identify grid failures or abnormal consumption spikes in real-time.

---

## 🌐 Backend Integration

The backend is fully integrated with the models and data pipeline, providing the following RESTful services:

*   **Forecasting Engine**: `GET /forecast` — Returns energy predictions for a configurable horizon (1-24h) with calculated confidence intervals.
*   **Anomaly Detection**: `GET /anomalies` — Audits the most recent telemetry to flag suspicious data points.
*   **Grid Optimization**: `POST /optimize` — Simulates battery storage dispatch logic based on predicted demand and renewable availability.
*   **Live Stream**: `WS /stream` — A continuous WebSocket feed broadcasting real-time forecasts every 2 seconds.
*   **Renewable Tracking**: `GET /renewables/netload` — Analyzes the impact of solar/wind generation on the total grid demand.

---

## 📊 Dataset Used

The system is trained on a heavy-duty energy dataset, enriched with real-world weather context:

*   **UCI Electricity Load Diagrams**: Contains 15-minute interval consumption data for 370 clients between 2011 and 2015.
*   **Weather Enrichment**: Integrated with the **Open-Meteo API** to include historical Temperature, Cloud Cover, Wind Speed, and Humidity—critical drivers of energy consumption.
*   **Scale**: The final processed dataset contains approximately **70,000 rows** and **31 engineered features**, including:
    *   Temporal features (Hour, Day, Month, Weekend flags).
    *   Lagged features (Previous 1h, 24h, 1-week consumption).
    *   Rolling statistics (Moving averages and std dev).

---

## 🚀 Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Running the System
1.  **Pipeline**: `python data_pipeline/data_pipeline.py` (Prepare the dataset)
2.  **Training**: `python training/model_training.py` (Train AI models)
3.  **Backend**: `uvicorn app.main:app` (Start API)
4.  **Frontend**: `cd frontend && npm run dev` (Start React Dashboard)
