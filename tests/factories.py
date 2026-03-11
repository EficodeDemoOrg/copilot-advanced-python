"""Test data factories for weather app models.

Each factory function returns a valid model instance with sensible defaults.
All parameters can be overridden via keyword arguments, making it easy to
create variations for specific test scenarios.
"""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from weather_app.models import (
    AlertSeverity,
    Coordinates,
    CurrentWeather,
    Forecast,
    ForecastDay,
    Location,
    LocationCreate,
    LocationUpdate,
    TemperatureUnit,
    WeatherAlert,
)


def make_coordinates(
    *,
    lat: float = 51.51,
    lon: float = -0.13,
) -> Coordinates:
    """Create a ``Coordinates`` instance (default: London)."""
    return Coordinates(lat=lat, lon=lon)


def make_location(
    *,
    id: UUID | None = None,
    name: str = "London",
    lat: float = 51.51,
    lon: float = -0.13,
    created_at: datetime | None = None,
) -> Location:
    """Create a ``Location`` instance with sensible defaults."""
    return Location(
        id=id or uuid4(),
        name=name,
        coordinates=Coordinates(lat=lat, lon=lon),
        created_at=created_at or datetime(2025, 1, 15, 12, 0, 0),
    )


def make_location_create(
    *,
    name: str = "London",
    lat: float = 51.51,
    lon: float = -0.13,
) -> LocationCreate:
    """Create a ``LocationCreate`` request body."""
    return LocationCreate(name=name, lat=lat, lon=lon)


def make_location_update(
    *,
    name: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> LocationUpdate:
    """Create a ``LocationUpdate`` request body."""
    return LocationUpdate(name=name, lat=lat, lon=lon)


def make_current_weather(
    *,
    temperature: float = 15.0,
    feels_like: float = 13.5,
    humidity: float = 72.0,
    pressure: float = 1013.0,
    wind_speed: float = 5.5,
    wind_direction: int = 220,
    description: str = "scattered clouds",
    icon: str = "03d",
    timestamp: datetime | None = None,
    location_name: str = "London",
    units: TemperatureUnit = TemperatureUnit.CELSIUS,
) -> CurrentWeather:
    """Create a ``CurrentWeather`` instance with typical London weather."""
    return CurrentWeather(
        temperature=temperature,
        feels_like=feels_like,
        humidity=humidity,
        pressure=pressure,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        description=description,
        icon=icon,
        timestamp=timestamp or datetime(2025, 6, 15, 14, 0, 0, tzinfo=UTC),
        location_name=location_name,
        units=units,
    )


def make_forecast_day(
    *,
    forecast_date: date | None = None,
    temp_min: float = 10.0,
    temp_max: float = 20.0,
    humidity: float = 65.0,
    description: str = "light rain",
    icon: str = "10d",
) -> ForecastDay:
    """Create a ``ForecastDay`` instance."""
    return ForecastDay(
        forecast_date=forecast_date or date(2025, 6, 16),
        temp_min=temp_min,
        temp_max=temp_max,
        humidity=humidity,
        description=description,
        icon=icon,
    )


def make_forecast(
    *,
    location_name: str = "Forecast",
    units: TemperatureUnit = TemperatureUnit.CELSIUS,
    days: list[ForecastDay] | None = None,
) -> Forecast:
    """Create a ``Forecast`` instance with a default 3-day forecast."""
    if days is None:
        days = [
            make_forecast_day(forecast_date=date(2025, 6, 16)),
            make_forecast_day(
                forecast_date=date(2025, 6, 17),
                temp_min=12.0,
                temp_max=22.0,
            ),
            make_forecast_day(
                forecast_date=date(2025, 6, 18),
                temp_min=8.0,
                temp_max=18.0,
            ),
        ]
    return Forecast(location_name=location_name, units=units, days=days)


def make_weather_alert(
    *,
    alert_type: str = "high_wind",
    message: str = "High wind speed: 25.0 m/s (threshold: 20.0 m/s)",
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    value: float = 25.0,
    threshold: float = 20.0,
) -> WeatherAlert:
    """Create a ``WeatherAlert`` instance."""
    return WeatherAlert(
        alert_type=alert_type,
        message=message,
        severity=severity,
        value=value,
        threshold=threshold,
    )


def make_owm_current_weather_response(
    *,
    temp: float = 15.0,
    feels_like: float = 13.5,
    humidity: float = 72.0,
    pressure: float = 1013.0,
    wind_speed: float = 5.5,
    wind_deg: int = 220,
    description: str = "scattered clouds",
    icon: str = "03d",
    dt: int = 1718452800,
    name: str = "London",
) -> dict:
    """Create a raw OpenWeatherMap ``/weather`` API response dict."""
    return {
        "coord": {"lon": -0.13, "lat": 51.51},
        "weather": [
            {
                "id": 802,
                "main": "Clouds",
                "description": description,
                "icon": icon,
            }
        ],
        "main": {
            "temp": temp,
            "feels_like": feels_like,
            "temp_min": temp - 2,
            "temp_max": temp + 2,
            "pressure": pressure,
            "humidity": humidity,
        },
        "wind": {"speed": wind_speed, "deg": wind_deg},
        "dt": dt,
        "name": name,
    }


def make_owm_forecast_response(
    *,
    base_temp: float = 15.0,
    num_entries: int = 8,
    base_dt: int = 1718452800,
) -> dict:
    """Create a raw OpenWeatherMap ``/forecast`` API response dict.

    Generates *num_entries* 3-hour interval entries starting from *base_dt*.
    """
    entries = []
    for i in range(num_entries):
        dt = base_dt + i * 10800  # 3-hour intervals
        temp = base_temp + (i % 4) - 1  # slight variation
        entries.append(
            {
                "dt": dt,
                "main": {
                    "temp": temp,
                    "feels_like": temp - 1.5,
                    "temp_min": temp - 1,
                    "temp_max": temp + 1,
                    "pressure": 1013,
                    "humidity": 65 + i,
                },
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain",
                        "icon": "10d",
                    }
                ],
                "dt_txt": f"2025-06-15 {(i * 3) % 24:02d}:00:00",
            }
        )
    return {
        "cod": "200",
        "message": 0,
        "cnt": num_entries,
        "list": entries,
        "city": {
            "id": 2643743,
            "name": "London",
            "coord": {"lat": 51.51, "lon": -0.13},
            "country": "GB",
        },
    }
