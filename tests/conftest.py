"""Root-level test fixtures shared across all test suites.

This conftest provides fixtures that are broadly useful: test settings,
the FastAPI app with dependency overrides, and an async HTTP test client.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from weather_app.config import Settings
from weather_app.dependencies import get_location_repository, get_settings
from weather_app.main import create_app
from weather_app.repositories.location_repo import LocationRepository


@pytest.fixture
def test_settings() -> Settings:
    """Application settings configured for testing.

    Uses a dummy API key so no real calls can be made.
    """
    return Settings(
        openweathermap_api_key="test-api-key-not-real",
        openweathermap_base_url="https://api.openweathermap.org/data/2.5",
        debug=True,
    )


@pytest.fixture
def location_repo() -> LocationRepository:
    """A fresh in-memory location repository for each test."""
    return LocationRepository()


@pytest.fixture
def app(test_settings: Settings, location_repo: LocationRepository):
    """FastAPI app instance with test dependency overrides.

    Overrides settings and the location repository so tests are isolated
    from each other and from any real environment configuration.
    """
    application = create_app(settings=test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_location_repository] = lambda: location_repo
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app) -> AsyncClient:
    """Async HTTP client wired to the test FastAPI app.

    Uses ``httpx.ASGITransport`` to send requests directly to the app
    without needing a running server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
