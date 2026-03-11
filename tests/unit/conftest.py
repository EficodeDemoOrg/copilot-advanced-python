"""Unit test fixtures.

Provides mocked versions of external dependencies so unit tests never
make real HTTP requests.
"""

from unittest.mock import AsyncMock

import pytest

from weather_app.config import Settings
from weather_app.services.openweathermap import OpenWeatherMapClient
from weather_app.services.weather_service import WeatherService


@pytest.fixture
def mock_owm_client(test_settings: Settings) -> AsyncMock:
    """A fully mocked ``OpenWeatherMapClient``.

    All async methods are ``AsyncMock`` instances that can be configured
    in individual tests.
    """
    mock = AsyncMock(spec=OpenWeatherMapClient)
    return mock


@pytest.fixture
def weather_service(
    mock_owm_client: AsyncMock, test_settings: Settings
) -> WeatherService:
    """A ``WeatherService`` with a mocked API client for isolated testing."""
    return WeatherService(client=mock_owm_client, settings=test_settings)
