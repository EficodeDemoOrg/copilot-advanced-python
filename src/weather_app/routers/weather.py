"""API routes for weather data retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from weather_app.dependencies import get_weather_service
from weather_app.models import CurrentWeather, Forecast, TemperatureUnit, WeatherAlert
from weather_app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current", response_model=CurrentWeather)
async def get_current_weather(
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    units: Annotated[
        TemperatureUnit, Query(description="Temperature unit")
    ] = TemperatureUnit.CELSIUS,
    service: WeatherService = Depends(get_weather_service),
) -> CurrentWeather:
    """Get current weather conditions for the given coordinates."""
    return await service.get_current_weather(lat, lon, units=units)


@router.get("/forecast", response_model=Forecast)
async def get_forecast(
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    days: Annotated[int, Query(ge=1, le=5, description="Number of days")] = 5,
    units: Annotated[
        TemperatureUnit, Query(description="Temperature unit")
    ] = TemperatureUnit.CELSIUS,
    service: WeatherService = Depends(get_weather_service),
) -> Forecast:
    """Get a multi-day weather forecast for the given coordinates."""
    return await service.get_forecast(lat, lon, days=days, units=units)


@router.get("/alerts", response_model=list[WeatherAlert])
async def get_alerts(
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    service: WeatherService = Depends(get_weather_service),
) -> list[WeatherAlert]:
    """Check for weather alerts at the given coordinates."""
    return await service.get_alerts(lat, lon)
