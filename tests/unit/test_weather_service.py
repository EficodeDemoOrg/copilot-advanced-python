"""Unit tests for WeatherService.

The OpenWeatherMap API client is mocked at the service boundary so these
tests verify business logic (unit conversion, alert evaluation) in
isolation.
"""

from unittest.mock import AsyncMock

import pytest

from tests.factories import (
    make_current_weather,
    make_forecast_day,
)
from weather_app.models import (
    AlertSeverity,
    TemperatureUnit,
)
from weather_app.services.weather_service import WeatherService

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# get_current_weather — unit conversion
# ---------------------------------------------------------------------------


class TestGetCurrentWeather:
    """Tests for WeatherService.get_current_weather()."""

    async def test_returns_celsius_by_default(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """When no unit is specified, temperatures remain in Celsius."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=20.0, feels_like=18.0
        )

        result = await weather_service.get_current_weather(51.51, -0.13)

        assert result.temperature == 20.0
        assert result.feels_like == 18.0
        assert result.units == TemperatureUnit.CELSIUS

    async def test_converts_to_fahrenheit(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temperatures are converted to Fahrenheit when requested."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=0.0, feels_like=-5.0
        )

        result = await weather_service.get_current_weather(
            51.51, -0.13, units=TemperatureUnit.FAHRENHEIT
        )

        assert result.temperature == 32.0
        assert result.feels_like == 23.0
        assert result.units == TemperatureUnit.FAHRENHEIT

    async def test_converts_to_kelvin(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temperatures are converted to Kelvin when requested."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=25.0, feels_like=23.0
        )

        result = await weather_service.get_current_weather(
            51.51, -0.13, units=TemperatureUnit.KELVIN
        )

        assert result.temperature == 298.15
        assert result.feels_like == 296.15
        assert result.units == TemperatureUnit.KELVIN

    async def test_non_temperature_fields_unchanged(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Non-temperature fields are not affected by unit conversion."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            humidity=80.0, pressure=1015.0, wind_speed=10.0
        )

        result = await weather_service.get_current_weather(
            51.51, -0.13, units=TemperatureUnit.FAHRENHEIT
        )

        assert result.humidity == 80.0
        assert result.pressure == 1015.0
        assert result.wind_speed == 10.0


# ---------------------------------------------------------------------------
# get_forecast — unit conversion
# ---------------------------------------------------------------------------


class TestGetForecast:
    """Tests for WeatherService.get_forecast()."""

    async def test_returns_forecast_with_correct_units(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Forecast temperatures are converted to the requested unit."""
        mock_owm_client.get_forecast.return_value = [
            make_forecast_day(temp_min=10.0, temp_max=25.0),
        ]

        result = await weather_service.get_forecast(
            51.51, -0.13, days=1, units=TemperatureUnit.FAHRENHEIT
        )

        assert result.units == TemperatureUnit.FAHRENHEIT
        assert result.days[0].temp_min == 50.0
        assert result.days[0].temp_max == 77.0

    async def test_forecast_preserves_non_temp_fields(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Non-temperature fields in forecast days are preserved."""
        mock_owm_client.get_forecast.return_value = [
            make_forecast_day(humidity=55.0, description="clear sky"),
        ]

        result = await weather_service.get_forecast(51.51, -0.13, days=1)

        assert result.days[0].humidity == 55.0
        assert result.days[0].description == "clear sky"

    async def test_multiple_days_all_converted(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """All days in a multi-day forecast are converted."""
        mock_owm_client.get_forecast.return_value = [
            make_forecast_day(temp_min=0.0, temp_max=10.0),
            make_forecast_day(temp_min=5.0, temp_max=15.0),
            make_forecast_day(temp_min=-5.0, temp_max=5.0),
        ]

        result = await weather_service.get_forecast(
            51.51, -0.13, days=3, units=TemperatureUnit.KELVIN
        )

        assert len(result.days) == 3
        assert result.days[0].temp_min == 273.15
        assert result.days[2].temp_min == 268.15


# ---------------------------------------------------------------------------
# get_alerts
# ---------------------------------------------------------------------------


class TestGetAlerts:
    """Tests for WeatherService.get_alerts()."""

    async def test_no_alerts_for_normal_weather(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Normal weather conditions produce no alerts."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=20.0, wind_speed=5.0, humidity=60.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        assert alerts == []

    async def test_high_wind_alert(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Wind speed at or above threshold generates a high_wind alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            wind_speed=25.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "high_wind"
        assert alerts[0].severity == AlertSeverity.MEDIUM

    async def test_very_high_wind_alert_is_high_severity(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Wind speed 1.5x the threshold is HIGH severity."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            wind_speed=30.0  # 20.0 * 1.5 = 30.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        assert alerts[0].severity == AlertSeverity.HIGH

    async def test_extreme_heat_alert(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temp at or above high threshold generates extreme_heat alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=42.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        heat_alerts = [a for a in alerts if a.alert_type == "extreme_heat"]
        assert len(heat_alerts) == 1
        assert heat_alerts[0].severity == AlertSeverity.HIGH

    async def test_extreme_heat_plus_5_is_extreme_severity(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temperature 5°C above the threshold is EXTREME severity."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=45.0  # threshold=40, +5=extreme
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        heat_alerts = [a for a in alerts if a.alert_type == "extreme_heat"]
        assert heat_alerts[0].severity == AlertSeverity.EXTREME

    async def test_extreme_cold_alert(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temperature at or below the low threshold generates an extreme_cold alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=-20.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        cold_alerts = [a for a in alerts if a.alert_type == "extreme_cold"]
        assert len(cold_alerts) == 1
        assert cold_alerts[0].severity == AlertSeverity.HIGH

    async def test_extreme_cold_minus_10_is_extreme_severity(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Temperature 10°C below the low threshold is EXTREME severity."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=-30.0  # threshold=-20, -10 below=extreme
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        cold_alerts = [a for a in alerts if a.alert_type == "extreme_cold"]
        assert cold_alerts[0].severity == AlertSeverity.EXTREME

    async def test_high_humidity_alert(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Humidity at or above threshold generates a high_humidity alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            humidity=95.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        humidity_alerts = [a for a in alerts if a.alert_type == "high_humidity"]
        assert len(humidity_alerts) == 1
        assert humidity_alerts[0].severity == AlertSeverity.LOW

    async def test_multiple_alerts_simultaneously(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Multiple thresholds exceeded produce multiple alerts."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            temperature=42.0, wind_speed=25.0, humidity=95.0
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        alert_types = {a.alert_type for a in alerts}
        assert alert_types == {"extreme_heat", "high_wind", "high_humidity"}

    async def test_wind_exactly_at_threshold(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Wind speed exactly at threshold still triggers an alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            wind_speed=20.0  # exactly at threshold
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "high_wind"

    async def test_wind_just_below_threshold_no_alert(
        self, weather_service: WeatherService, mock_owm_client: AsyncMock
    ) -> None:
        """Wind speed just below threshold does not trigger an alert."""
        mock_owm_client.get_current_weather.return_value = make_current_weather(
            wind_speed=19.99
        )

        alerts = await weather_service.get_alerts(51.51, -0.13)

        wind_alerts = [a for a in alerts if a.alert_type == "high_wind"]
        assert wind_alerts == []
