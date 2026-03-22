import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import OPENWEATHER_API_KEY, CITY_LAT, CITY_LON

router = APIRouter()

class WeatherResponse(BaseModel):
    temperature: float
    humidity: int
    wind_speed: float
    description: str
    icon: str

@router.get("/weather", response_model=WeatherResponse)
async def get_live_weather():
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeatherMap API Key not configured")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={CITY_LAT}&lon={CITY_LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        r = requests.get(url)
        data = r.json()
        
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=data.get("message", "Weather API Error"))

        return WeatherResponse(
            temperature=data["main"]["temp"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"],
            description=data["weather"][0]["description"],
            icon=data["weather"][0]["icon"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
