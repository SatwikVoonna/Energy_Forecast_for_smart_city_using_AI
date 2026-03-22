import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.core.config import GEMINI_API_KEY

router = APIRouter()

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class InsightRequest(BaseModel):
    timestamp: str
    actual_kwh: float
    expected_kwh: float
    severity: str
    metadata: Dict[str, Any] = {}

class InsightResponse(BaseModel):
    insight: str
    recommendation: str

from app.api.routes.weather import get_live_weather


@router.post("/insights", response_model=InsightResponse)
async def get_ai_insight(req: InsightRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured")

    weather_context = ""
    try:
        weather = await get_live_weather()
        weather_context = f"Current Weather in Chennai: {weather.temperature}°C, {weather.description}, Humidity: {weather.humidity}%, Wind: {weather.wind_speed} m/s."
    except Exception:
        weather_context = "Weather data currently unavailable."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as a professional Smart Grid AI analyst. 
        Analyze the following anomaly detected in the energy grid demand:
        - Timestamp: {req.timestamp}
        - Actual Demand: {req.actual_kwh:.2f} MW
        - Predicted Demand: {req.expected_kwh:.2f} MW
        - Severity: {req.severity}
        - Context: {weather_context}
        
        Provide:
        1. A concise explanation (2-3 sentences) of why this might be happening (e.g. unexpected temperature shifts, humidity spikes, or grid faults).
        2. A clear recommendation for grid operators to mitigate this strain (e.g. peak shaving, battery discharge, or load balancing).
        
        Return the result in plain text with two fields: "Reason: " and "Recommendation: ".
        """
        
        response = model.generate_content(prompt)

        text = response.text
        
        # Simple parsing
        parts = text.split("Recommendation:")
        reason = parts[0].replace("Reason:", "").strip() if "Reason:" in parts[0] else parts[0].strip()
        rec = parts[1].strip() if len(parts) > 1 else "Monitor grid health and prepare for load shedding if necessary."
        
        return InsightResponse(insight=reason, recommendation=rec)
        
    except Exception as e:
        return InsightResponse(
            insight="AI analysis currently unavailable due to system load.",
            recommendation="Monitor grid telemetry manually and check capacity buffers."
        )
