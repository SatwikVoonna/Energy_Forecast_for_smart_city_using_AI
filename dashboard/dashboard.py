import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import asyncio
import websockets
import json
import time

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/stream"

# Must be the very first Streamlit command
st.set_page_config(
    page_title="AI Energy Forecasting Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Dark Theme Colors explicitly via CSS if needed, 
# but Streamlit has a native dark theme we will leverage via config (or in .streamlit/config.toml)
st.markdown("""
<style>
    .stApp {
        background-color: #060d16;
        color: #e2e8f0;
    }
    .css-1d391kg {
        background-color: #0d1b2a;
    }
    .stMetric {
        background-color: #0d1b2a;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #1e3a5f;
    }
    h1, h2, h3 {
        color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Smart City AI Energy Demand Forecasting")
st.markdown("Real-time ML pipeline powered by XGBoost, LSTM, and Isolation Forest.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Forecast", "☀️ Renewables", "🚨 Anomalies", "📊 Models", "🔴 Live Stream"])

def fetch_data(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", params=params)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error ({endpoint}): {e}")
        return None

def fetch_post(endpoint, json_data):
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=json_data)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error ({endpoint}): {e}")
        return None

with tab1:
    st.header("Demand Forecast")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        horizon = st.slider("Forecast Horizon (hours)", 12, 168, 24)
        model_choice = st.selectbox("Model", ["ensemble", "xgboost"])
        
    with col1:
        data = fetch_data("forecast", params={"horizon": horizon, "model": model_choice})
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            fig = go.Figure()
            
            # Confidence bounds
            fig.add_trace(go.Scatter(
                x=df['timestamp'].tolist() + df['timestamp'].tolist()[::-1],
                y=df['upper_bound'].tolist() + df['lower_bound'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(56, 189, 248, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                name='95% Confidence Interval'
            ))
            
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=df['timestamp'], y=df['forecast_kwh'],
                line=dict(color='#38bdf8', width=3),
                mode='lines', name='Forecast (kWh)'
            ))
            
            fig.update_layout(
                paper_bgcolor='#060d16',
                plot_bgcolor='#060d16',
                font=dict(color='#e2e8f0'),
                title="Energy Demand Forecast",
                xaxis_title="Time",
                yaxis_title="Demand (kWh)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            m1, m2 = st.columns(2)
            m1.metric("Peak Demand (kWh)", f"{df['forecast_kwh'].max():.2f}")
            m2.metric("Average Demand (kWh)", f"{df['forecast_kwh'].mean():.2f}")

with tab2:
    st.header("Renewables Integration & Battery Optimization")
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Current Net Load")
        renew_data = fetch_data("renewables/netload")
        if renew_data:
            st.metric("Total Demand", f"{renew_data['demand']:,.2f} kWh")
            st.metric("Solar Generation", f"{renew_data['solar']:,.2f} kWh")
            st.metric("Wind Generation", f"{renew_data['wind']:,.2f} kWh")
            st.metric("Net Load", f"{renew_data['net_load']:,.2f} kWh")
            st.progress(renew_data['renewable_utilization_pct'] / 100.0, text=f"{renew_data['renewable_utilization_pct']:.1f}% Renewable Utilization")

    with colB:
        st.subheader("Battery Dispatch Optimization")
        batt_cap = st.number_input("Battery Capacity (kWh)", value=10000.0)
        p_tariff = st.number_input("Peak Tariff ($/kWh)", value=0.25)
        op_tariff = st.number_input("Off-Peak Tariff ($/kWh)", value=0.08)
        
        if st.button("Run Simulation"):
            opt_data = fetch_post("optimize", {
                "battery_capacity": batt_cap,
                "peak_tariff": p_tariff,
                "offpeak_tariff": op_tariff
            })
            if opt_data:
                st.metric("Baseline Cost", f"${opt_data['baseline_cost']:,.2f}")
                st.metric("Optimized Cost", f"${opt_data['optimized_cost']:,.2f}")
                st.metric("Savings", f"${opt_data['savings']:,.2f}", delta=f"${opt_data['savings']:,.2f}")

with tab3:
    st.header("Anomaly Detection (Isolation Forest)")
    anom_data = fetch_data("anomalies")
    if anom_data:
        df_anom = pd.DataFrame(anom_data)
        if not df_anom.empty:
            df_anom['timestamp'] = pd.to_datetime(df_anom['timestamp'])
            st.dataframe(df_anom.style.map(lambda x: 'color: #ff4b4b' if x == 'High' else 'color: #ffa500', subset=['severity']), use_container_width=True)
        else:
            st.success("No recent anomalies detected.")

with tab4:
    st.header("Model Evaluation Metrics")
    metrics_data = fetch_data("metrics")
    if metrics_data:
        # Handle both flat (old) and nested per-model (new) format
        if any(isinstance(v, dict) for v in metrics_data.values()):
            # New format: {"XGBoost": {...}, "LSTM": {...}, "Ensemble": {...}}
            for model_name, m in metrics_data.items():
                st.subheader(f"🤖 {model_name}")
                cols = st.columns(5)
                cols[0].metric("MAE",   f"{m['MAE']:.5f}")
                cols[1].metric("RMSE",  f"{m['RMSE']:.5f}")
                cols[2].metric("MAPE",  f"{m['MAPE']:.2f}%")
                cols[3].metric("SMAPE", f"{m.get('SMAPE', m['MAPE']):.2f}%")
                cols[4].metric("R²",    f"{m['R2']:.4f}")
                st.divider()
        else:
            # Legacy flat format
            m_cols = st.columns(len(metrics_data))
            for i, (key, val) in enumerate(metrics_data.items()):
                if isinstance(val, float):
                    m_cols[i].metric(key, f"{val:.4f}")


with tab5:
    st.header("🔴 Live Stream (WebSocket)")
    st.markdown("Listening for live predictions and anomaly alerts...")
    
    placeholder = st.empty()
    
    # We use a button to start the stream to prevent blocking the entire app randomly
    if st.button("Start Live Stream"):
        async def listen_ws():
            chart_data = pd.DataFrame(columns=['timestamp', 'forecast_kwh', 'actual_kwh'])
            try:
                async with websockets.connect(WS_URL) as ws:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        
                        # Show alerts
                        if data['is_anomaly']:
                            st.toast(f"🚨 Anomaly Detected! Severity: {data['anomaly_type']} at {data['timestamp']}", icon="🚨")
                        
                        # Update chart
                        new_row = pd.DataFrame([data])
                        chart_data = pd.concat([chart_data, new_row]).tail(50)
                        
                        with placeholder.container():
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=chart_data['timestamp'], y=chart_data['actual_kwh'], name="Actual", line=dict(color='#e2e8f0')))
                            fig.add_trace(go.Scatter(x=chart_data['timestamp'], y=chart_data['forecast_kwh'], name="Forecast", line=dict(color='#38bdf8', dash='dot')))
                            
                            fig.update_layout(paper_bgcolor='#060d16', plot_bgcolor='#060d16', font=dict(color='#e2e8f0'))
                            st.plotly_chart(fig, use_container_width=True, key=f"live_chart_{data['timestamp']}")
                            
            except Exception as e:
                st.error(f"WebSocket Error: {e}")
                
        asyncio.run(listen_ws())
