"""Domain models for the Weather App."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TemperatureUnit(StrEnum):
    """Supported temperature units."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


class AlertSeverity(StrEnum):
    """Severity levels for weather alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class Coordinates(BaseModel):
    """Geographic coordinates with validation."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude")


class Location(BaseModel):
    """A saved geographic location."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Location name")
    coordinates: Coordinates
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the location was saved"
    )


class LocationCreate(BaseModel):
    """Request body for creating a new location."""

    name: str = Field(..., min_length=1, max_length=200, description="Location name")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude")


class LocationUpdate(BaseModel):
    """Request body for updating an existing location."""

    name: str | None = Field(None, min_length=1, max_length=200, description="New name")
    lat: float | None = Field(None, ge=-90.0, le=90.0, description="New latitude")
    lon: float | None = Field(None, ge=-180.0, le=180.0, description="New longitude")


class CurrentWeather(BaseModel):
    """Current weather conditions at a location."""

    temperature: float = Field(..., description="Temperature in the requested unit")
    feels_like: float = Field(
        ..., description="Feels-like temperature in the requested unit"
    )
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    wind_direction: int = Field(
        ..., ge=0, le=360, description="Wind direction in degrees"
    )
    description: str = Field(..., description="Human-readable weather description")
    icon: str = Field(..., description="OpenWeatherMap icon code")
    timestamp: datetime = Field(..., description="Observation timestamp")
    location_name: str = Field(..., description="Name of the location")
    units: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS, description="Temperature unit used"
    )


class ForecastDay(BaseModel):
    """Weather forecast for a single day."""

    forecast_date: date = Field(..., description="Forecast date")
    temp_min: float = Field(..., description="Minimum temperature")
    temp_max: float = Field(..., description="Maximum temperature")
    humidity: float = Field(
        ..., ge=0, le=100, description="Average humidity percentage"
    )
    description: str = Field(..., description="Weather description")
    icon: str = Field(..., description="OpenWeatherMap icon code")


class Forecast(BaseModel):
    """Multi-day weather forecast."""

    location_name: str = Field(..., description="Name of the location")
    units: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS, description="Temperature unit used"
    )
    days: list[ForecastDay] = Field(..., description="Daily forecasts")


class WeatherAlert(BaseModel):
    """A weather alert based on current conditions exceeding thresholds."""

    alert_type: str = Field(..., description="Type of alert, e.g. 'high_wind'")
    message: str = Field(..., description="Human-readable alert message")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    value: float = Field(..., description="The measured value that triggered the alert")
    threshold: float = Field(..., description="The threshold that was exceeded")
