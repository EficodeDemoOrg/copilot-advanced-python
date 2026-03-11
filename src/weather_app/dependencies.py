"""FastAPI dependency-injection wiring.

Provides factory functions that create and cache shared instances of
services, repositories, and configuration objects.  These are used as
FastAPI ``Depends()`` parameters in route handlers.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from weather_app.config import Settings
from weather_app.repositories.location_repo import LocationRepository
from weather_app.services.openweathermap import OpenWeatherMapClient
from weather_app.services.weather_service import WeatherService


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application settings (cached singleton)."""
    return Settings()


def get_openweathermap_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OpenWeatherMapClient:
    """Create an ``OpenWeatherMapClient`` bound to the current settings."""
    return OpenWeatherMapClient(settings)


def get_weather_service(
    client: Annotated[OpenWeatherMapClient, Depends(get_openweathermap_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> WeatherService:
    """Create a ``WeatherService`` with the injected API client and settings."""
    return WeatherService(client=client, settings=settings)


# The location repository is a singleton (in-memory state must persist
# across requests for the lifetime of the process).
_location_repo = LocationRepository()


def get_location_repository() -> LocationRepository:
    """Return the shared in-memory ``LocationRepository``."""
    return _location_repo
