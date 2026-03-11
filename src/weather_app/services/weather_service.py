"""High-level weather service that orchestrates the API client.

This service sits between the routers and the raw API client.  It handles
temperature-unit conversion, forecast trimming, and weather-alert generation.
"""

from weather_app.config import Settings
from weather_app.models import (
    AlertSeverity,
    CurrentWeather,
    Forecast,
    ForecastDay,
    TemperatureUnit,
    WeatherAlert,
)
from weather_app.services.openweathermap import OpenWeatherMapClient
from weather_app.utils.converters import celsius_to_fahrenheit, celsius_to_kelvin


class WeatherService:
    """Orchestrates weather data retrieval and business logic.

    Args:
        client: An ``OpenWeatherMapClient`` instance for API communication.
        settings: Application settings (used for alert thresholds).
    """

    def __init__(self, client: OpenWeatherMapClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        units: TemperatureUnit = TemperatureUnit.CELSIUS,
    ) -> CurrentWeather:
        """Fetch current weather and convert temperatures to the requested unit.

        Args:
            lat: Latitude.
            lon: Longitude.
            units: Desired temperature unit (default: Celsius).

        Returns:
            ``CurrentWeather`` with temperatures in the requested unit.
        """
        weather = await self._client.get_current_weather(lat, lon)
        return self._convert_current_weather(weather, units)

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 5,
        units: TemperatureUnit = TemperatureUnit.CELSIUS,
    ) -> Forecast:
        """Fetch a multi-day forecast and convert temperatures.

        Args:
            lat: Latitude.
            lon: Longitude.
            days: Number of forecast days (1–5, default 5).
            units: Desired temperature unit.

        Returns:
            A ``Forecast`` model with daily forecasts in the requested unit.
        """
        forecast_days = await self._client.get_forecast(lat, lon, days=days)
        converted = [self._convert_forecast_day(d, units) for d in forecast_days]
        return Forecast(
            location_name="Forecast",
            units=units,
            days=converted,
        )

    async def get_alerts(self, lat: float, lon: float) -> list[WeatherAlert]:
        """Check current conditions and return any weather alerts.

        Alerts are generated when measured values exceed the thresholds
        defined in ``Settings``.

        Args:
            lat: Latitude.
            lon: Longitude.

        Returns:
            A (possibly empty) list of ``WeatherAlert`` objects.
        """
        weather = await self._client.get_current_weather(lat, lon)
        return self._evaluate_alerts(weather)

    # ------------------------------------------------------------------
    # Temperature conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_temperature(celsius: float, units: TemperatureUnit) -> float:
        """Convert a Celsius value to the target unit."""
        if units == TemperatureUnit.FAHRENHEIT:
            return celsius_to_fahrenheit(celsius)
        if units == TemperatureUnit.KELVIN:
            return celsius_to_kelvin(celsius)
        return round(celsius, 2)

    def _convert_current_weather(
        self, weather: CurrentWeather, units: TemperatureUnit
    ) -> CurrentWeather:
        """Return a new ``CurrentWeather`` with converted temperature fields."""
        return weather.model_copy(
            update={
                "temperature": self._convert_temperature(weather.temperature, units),
                "feels_like": self._convert_temperature(weather.feels_like, units),
                "units": units,
            }
        )

    def _convert_forecast_day(
        self, day: ForecastDay, units: TemperatureUnit
    ) -> ForecastDay:
        """Return a new ``ForecastDay`` with converted temperature fields."""
        return day.model_copy(
            update={
                "temp_min": self._convert_temperature(day.temp_min, units),
                "temp_max": self._convert_temperature(day.temp_max, units),
            }
        )

    # ------------------------------------------------------------------
    # Alert evaluation
    # ------------------------------------------------------------------

    def _evaluate_alerts(self, weather: CurrentWeather) -> list[WeatherAlert]:
        """Evaluate current weather against configured thresholds."""
        alerts: list[WeatherAlert] = []

        if weather.wind_speed >= self._settings.alert_wind_speed_threshold:
            alerts.append(
                WeatherAlert(
                    alert_type="high_wind",
                    message=(
                        f"High wind speed: {weather.wind_speed} m/s "
                        f"(threshold: {self._settings.alert_wind_speed_threshold} m/s)"
                    ),
                    severity=(
                        AlertSeverity.HIGH
                        if weather.wind_speed
                        >= self._settings.alert_wind_speed_threshold * 1.5
                        else AlertSeverity.MEDIUM
                    ),
                    value=weather.wind_speed,
                    threshold=self._settings.alert_wind_speed_threshold,
                )
            )

        if weather.temperature >= self._settings.alert_temp_high_threshold:
            alerts.append(
                WeatherAlert(
                    alert_type="extreme_heat",
                    message=(
                        f"Extreme heat: {weather.temperature}°C "
                        f"(threshold: {self._settings.alert_temp_high_threshold}°C)"
                    ),
                    severity=(
                        AlertSeverity.EXTREME
                        if weather.temperature
                        >= self._settings.alert_temp_high_threshold + 5
                        else AlertSeverity.HIGH
                    ),
                    value=weather.temperature,
                    threshold=self._settings.alert_temp_high_threshold,
                )
            )

        if weather.temperature <= self._settings.alert_temp_low_threshold:
            alerts.append(
                WeatherAlert(
                    alert_type="extreme_cold",
                    message=(
                        f"Extreme cold: {weather.temperature}°C "
                        f"(threshold: {self._settings.alert_temp_low_threshold}°C)"
                    ),
                    severity=(
                        AlertSeverity.EXTREME
                        if weather.temperature
                        <= self._settings.alert_temp_low_threshold - 10
                        else AlertSeverity.HIGH
                    ),
                    value=weather.temperature,
                    threshold=self._settings.alert_temp_low_threshold,
                )
            )

        if weather.humidity >= self._settings.alert_humidity_threshold:
            alerts.append(
                WeatherAlert(
                    alert_type="high_humidity",
                    message=(
                        f"High humidity: {weather.humidity}% "
                        f"(threshold: {self._settings.alert_humidity_threshold}%)"
                    ),
                    severity=AlertSeverity.LOW,
                    value=weather.humidity,
                    threshold=self._settings.alert_humidity_threshold,
                )
            )

        return alerts
