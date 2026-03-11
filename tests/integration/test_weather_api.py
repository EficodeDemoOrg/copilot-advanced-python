"""Integration tests for the weather API endpoints.

These tests exercise the full FastAPI request/response cycle with mocked
external HTTP calls (via ``pytest-httpx``), verifying status codes,
response shapes, and error handling.
"""

import re

import pytest
from httpx import AsyncClient

from tests.factories import (
    make_owm_current_weather_response,
    make_owm_forecast_response,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# GET /api/weather/current
# ---------------------------------------------------------------------------


class TestGetCurrentWeather:
    """Integration tests for the current weather endpoint."""

    async def test_returns_200_with_valid_coords(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """A valid request returns 200 with current weather data."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(),
        )

        response = await client.get(
            "/api/weather/current", params={"lat": 51.51, "lon": -0.13}
        )

        assert response.status_code == 200
        data = response.json()
        assert "temperature" in data
        assert "humidity" in data
        assert data["location_name"] == "London"
        assert data["units"] == "celsius"

    async def test_returns_200_with_fahrenheit_units(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """Requesting Fahrenheit converts temperatures in the response."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(temp=0.0, feels_like=-5.0),
        )

        response = await client.get(
            "/api/weather/current",
            params={"lat": 51.51, "lon": -0.13, "units": "fahrenheit"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 32.0
        assert data["units"] == "fahrenheit"

    async def test_returns_422_for_missing_params(self, client: AsyncClient) -> None:
        """Missing required parameters returns 422."""
        response = await client.get("/api/weather/current")

        assert response.status_code == 422

    async def test_returns_422_for_invalid_lat(self, client: AsyncClient) -> None:
        """Latitude out of range returns 422."""
        response = await client.get(
            "/api/weather/current", params={"lat": 100, "lon": 0}
        )

        assert response.status_code == 422

    async def test_returns_404_when_location_not_found(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """When the external API returns 404, the endpoint returns 404."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            status_code=404,
            json={"cod": "404", "message": "city not found"},
        )

        response = await client.get("/api/weather/current", params={"lat": 0, "lon": 0})

        assert response.status_code == 404

    async def test_returns_502_on_api_error(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """When the external API returns a server error, we return 502."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            status_code=500,
            json={"cod": 500, "message": "internal error"},
        )

        response = await client.get(
            "/api/weather/current", params={"lat": 51.51, "lon": -0.13}
        )

        assert response.status_code == 502


# ---------------------------------------------------------------------------
# GET /api/weather/forecast
# ---------------------------------------------------------------------------


class TestGetForecast:
    """Integration tests for the forecast endpoint."""

    async def test_returns_200_with_forecast_data(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """A valid request returns 200 with forecast days."""
        httpx_mock.add_response(
            url=re.compile(r".*/forecast\?.*"),
            json=make_owm_forecast_response(),
        )

        response = await client.get(
            "/api/weather/forecast", params={"lat": 51.51, "lon": -0.13}
        )

        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert isinstance(data["days"], list)
        assert data["units"] == "celsius"

    async def test_respects_days_parameter(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """The days parameter limits the number of forecast days returned."""
        httpx_mock.add_response(
            url=re.compile(r".*/forecast\?.*"),
            json=make_owm_forecast_response(num_entries=40, base_dt=1718452800),
        )

        response = await client.get(
            "/api/weather/forecast",
            params={"lat": 51.51, "lon": -0.13, "days": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["days"]) <= 2

    async def test_returns_422_for_days_out_of_range(self, client: AsyncClient) -> None:
        """Days outside 1-5 returns 422."""
        response = await client.get(
            "/api/weather/forecast",
            params={"lat": 51.51, "lon": -0.13, "days": 10},
        )

        assert response.status_code == 422

    async def test_forecast_with_kelvin_units(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """Requesting Kelvin returns temperatures in Kelvin."""
        httpx_mock.add_response(
            url=re.compile(r".*/forecast\?.*"),
            json=make_owm_forecast_response(base_temp=0.0),
        )

        response = await client.get(
            "/api/weather/forecast",
            params={"lat": 51.51, "lon": -0.13, "units": "kelvin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["units"] == "kelvin"
        # 0°C = 273.15K, so all temps should be around there
        for day in data["days"]:
            assert day["temp_min"] > 250


# ---------------------------------------------------------------------------
# GET /api/weather/alerts
# ---------------------------------------------------------------------------


class TestGetAlerts:
    """Integration tests for the alerts endpoint."""

    async def test_returns_200_with_no_alerts(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """Normal conditions return an empty alerts list."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(
                wind_speed=5.0, temp=20.0, humidity=60.0
            ),
        )

        response = await client.get(
            "/api/weather/alerts", params={"lat": 51.51, "lon": -0.13}
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_200_with_alerts(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """Extreme conditions return alerts in the response."""
        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(
                wind_speed=25.0, temp=42.0, humidity=95.0
            ),
        )

        response = await client.get(
            "/api/weather/alerts", params={"lat": 51.51, "lon": -0.13}
        )

        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) >= 2
        alert_types = {a["alert_type"] for a in alerts}
        assert "high_wind" in alert_types
        assert "extreme_heat" in alert_types
