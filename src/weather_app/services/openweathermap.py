"""Async client for the OpenWeatherMap API.

This module handles all HTTP communication with the OpenWeatherMap API,
parsing raw JSON responses into typed Pydantic models.  It uses
``httpx.AsyncClient`` for non-blocking HTTP requests.
"""

from datetime import UTC, date, datetime

import httpx

from weather_app.config import Settings
from weather_app.models import CurrentWeather, ForecastDay, TemperatureUnit
from weather_app.services.exceptions import (
    WeatherAPIConnectionError,
    WeatherAPIError,
    WeatherAPINotFoundError,
)


class OpenWeatherMapClient:
    """Async wrapper around the OpenWeatherMap REST API.

    Args:
        settings: Application settings containing the API key and base URL.
    """

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.openweathermap_api_key
        self._base_url = settings.openweathermap_base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(10.0),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_current_weather(self, lat: float, lon: float) -> CurrentWeather:
        """Fetch current weather conditions for the given coordinates.

        The API is called with ``units=metric`` so temperatures are in
        Celsius and wind speed is in m/s.

        Args:
            lat: Latitude of the location.
            lon: Longitude of the location.

        Returns:
            Parsed ``CurrentWeather`` model with data in metric units.

        Raises:
            WeatherAPINotFoundError: If the location is not found.
            WeatherAPIError: For other API-level errors.
            WeatherAPIConnectionError: On network failures.
        """
        data = await self._request(
            "/weather",
            params={"lat": lat, "lon": lon, "units": "metric"},
        )
        return self._parse_current_weather(data)

    async def get_forecast(
        self, lat: float, lon: float, days: int = 5
    ) -> list[ForecastDay]:
        """Fetch a multi-day weather forecast for the given coordinates.

        The OpenWeatherMap free-tier ``/forecast`` endpoint returns data in
        3-hour intervals.  This method aggregates them into daily summaries.

        Args:
            lat: Latitude of the location.
            lon: Longitude of the location.
            days: Number of forecast days to return (max 5).

        Returns:
            A list of ``ForecastDay`` models (one per day, up to *days*).

        Raises:
            WeatherAPINotFoundError: If the location is not found.
            WeatherAPIError: For other API-level errors.
            WeatherAPIConnectionError: On network failures.
        """
        data = await self._request(
            "/forecast",
            params={"lat": lat, "lon": lon, "units": "metric"},
        )
        return self._parse_forecast(data, days)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _request(self, path: str, *, params: dict[str, object]) -> dict:
        """Send a GET request and return the parsed JSON body.

        Adds the API key to query parameters automatically.
        """
        params["appid"] = self._api_key
        try:
            response = await self._client.get(path, params=params)
        except httpx.ConnectError as exc:
            raise WeatherAPIConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise WeatherAPIConnectionError(f"Request to {path} timed out") from exc

        if response.status_code == 404:
            raise WeatherAPINotFoundError()
        if response.status_code != 200:
            content_type = response.headers.get("content-type", "")
            body = (
                response.json() if content_type.startswith("application/json") else {}
            )
            message = body.get("message", response.text)
            raise WeatherAPIError(
                status_code=response.status_code,
                message=str(message),
            )
        return response.json()

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_current_weather(data: dict) -> CurrentWeather:
        """Map the raw ``/weather`` JSON response to a ``CurrentWeather`` model."""
        weather_block = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})

        return CurrentWeather(
            temperature=main.get("temp", 0.0),
            feels_like=main.get("feels_like", 0.0),
            humidity=main.get("humidity", 0.0),
            pressure=main.get("pressure", 0.0),
            wind_speed=wind.get("speed", 0.0),
            wind_direction=wind.get("deg", 0),
            description=weather_block.get("description", ""),
            icon=weather_block.get("icon", ""),
            timestamp=datetime.fromtimestamp(data.get("dt", 0), tz=UTC),
            location_name=data.get("name", "Unknown"),
            units=TemperatureUnit.CELSIUS,
        )

    @staticmethod
    def _parse_forecast(data: dict, days: int) -> list[ForecastDay]:
        """Aggregate 3-hour forecast intervals into daily summaries."""
        daily: dict[date, list[dict]] = {}
        for entry in data.get("list", []):
            dt = datetime.fromtimestamp(entry["dt"], tz=UTC)
            day = dt.date()
            daily.setdefault(day, []).append(entry)

        result: list[ForecastDay] = []
        for day_date in sorted(daily.keys())[:days]:
            entries = daily[day_date]
            temps = [e["main"]["temp"] for e in entries]
            humidities = [e["main"]["humidity"] for e in entries]
            # Use the most common weather description for the day
            descriptions = [e["weather"][0]["description"] for e in entries]
            icons = [e["weather"][0]["icon"] for e in entries]

            result.append(
                ForecastDay(
                    forecast_date=day_date,
                    temp_min=round(min(temps), 2),
                    temp_max=round(max(temps), 2),
                    humidity=round(sum(humidities) / len(humidities), 1),
                    description=max(set(descriptions), key=descriptions.count),
                    icon=max(set(icons), key=icons.count),
                )
            )

        return result
