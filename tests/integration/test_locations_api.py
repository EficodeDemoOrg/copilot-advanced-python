"""Integration tests for the locations API endpoints.

These tests exercise the full CRUD cycle for saved locations through
the FastAPI application, verifying status codes, response shapes,
and error handling.
"""

import re

import pytest
from httpx import AsyncClient

from tests.factories import make_owm_current_weather_response

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# POST /api/locations
# ---------------------------------------------------------------------------


class TestCreateLocation:
    """Integration tests for creating locations."""

    async def test_create_returns_201(self, client: AsyncClient) -> None:
        """Creating a valid location returns 201 with the location data."""
        response = await client.post(
            "/api/locations",
            json={"name": "London", "lat": 51.51, "lon": -0.13},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "London"
        assert data["coordinates"]["lat"] == 51.51
        assert "id" in data

    async def test_create_with_invalid_lat_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Invalid latitude returns 422."""
        response = await client.post(
            "/api/locations",
            json={"name": "Bad", "lat": 100.0, "lon": 0.0},
        )

        assert response.status_code == 422

    async def test_create_with_empty_name_returns_422(
        self, client: AsyncClient
    ) -> None:
        """An empty name returns 422."""
        response = await client.post(
            "/api/locations",
            json={"name": "", "lat": 0.0, "lon": 0.0},
        )

        assert response.status_code == 422

    async def test_create_multiple_locations(self, client: AsyncClient) -> None:
        """Multiple locations can be created with unique IDs."""
        resp1 = await client.post(
            "/api/locations",
            json={"name": "A", "lat": 10.0, "lon": 20.0},
        )
        resp2 = await client.post(
            "/api/locations",
            json={"name": "B", "lat": 30.0, "lon": 40.0},
        )

        assert resp1.json()["id"] != resp2.json()["id"]


# ---------------------------------------------------------------------------
# GET /api/locations
# ---------------------------------------------------------------------------


class TestListLocations:
    """Integration tests for listing locations."""

    async def test_empty_list(self, client: AsyncClient) -> None:
        """An empty repository returns an empty list."""
        response = await client.get("/api/locations")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_after_creating(self, client: AsyncClient) -> None:
        """Created locations appear in the list."""
        await client.post(
            "/api/locations",
            json={"name": "X", "lat": 1.0, "lon": 2.0},
        )
        await client.post(
            "/api/locations",
            json={"name": "Y", "lat": 3.0, "lon": 4.0},
        )

        response = await client.get("/api/locations")

        assert response.status_code == 200
        assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /api/locations/{id}
# ---------------------------------------------------------------------------


class TestGetLocation:
    """Integration tests for getting a single location."""

    async def test_get_existing_location(self, client: AsyncClient) -> None:
        """A created location can be retrieved by ID."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Berlin", "lat": 52.52, "lon": 13.41},
        )
        location_id = create_resp.json()["id"]

        response = await client.get(f"/api/locations/{location_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Berlin"

    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        """A non-existent location ID returns 404."""
        import uuid

        fake_id = str(uuid.uuid4())

        response = await client.get(f"/api/locations/{fake_id}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/locations/{id}
# ---------------------------------------------------------------------------


class TestUpdateLocation:
    """Integration tests for updating locations."""

    async def test_update_name(self, client: AsyncClient) -> None:
        """Updating the name returns the updated location."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Old", "lat": 10.0, "lon": 20.0},
        )
        location_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/locations/{location_id}",
            json={"name": "New"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New"
        assert response.json()["coordinates"]["lat"] == 10.0

    async def test_update_coordinates(self, client: AsyncClient) -> None:
        """Updating coordinates preserves the name."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Stable", "lat": 10.0, "lon": 20.0},
        )
        location_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/locations/{location_id}",
            json={"lat": 50.0, "lon": 60.0},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Stable"
        assert response.json()["coordinates"]["lat"] == 50.0

    async def test_update_nonexistent_returns_404(self, client: AsyncClient) -> None:
        """Updating a non-existent ID returns 404."""
        import uuid

        response = await client.put(
            f"/api/locations/{uuid.uuid4()}",
            json={"name": "Nope"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/locations/{id}
# ---------------------------------------------------------------------------


class TestDeleteLocation:
    """Integration tests for deleting locations."""

    async def test_delete_returns_204(self, client: AsyncClient) -> None:
        """Deleting an existing location returns 204."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Temp", "lat": 0.0, "lon": 0.0},
        )
        location_id = create_resp.json()["id"]

        response = await client.delete(f"/api/locations/{location_id}")

        assert response.status_code == 204

    async def test_deleted_location_no_longer_exists(self, client: AsyncClient) -> None:
        """A deleted location cannot be retrieved."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Gone", "lat": 0.0, "lon": 0.0},
        )
        location_id = create_resp.json()["id"]

        await client.delete(f"/api/locations/{location_id}")
        get_resp = await client.get(f"/api/locations/{location_id}")

        assert get_resp.status_code == 404

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        """Deleting a non-existent ID returns 404."""
        import uuid

        response = await client.delete(f"/api/locations/{uuid.uuid4()}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/locations/{id}/weather
# ---------------------------------------------------------------------------


class TestGetLocationWeather:
    """Integration tests for getting weather at a saved location."""

    async def test_returns_weather_for_saved_location(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """Weather is returned for a saved location's coordinates."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "London", "lat": 51.51, "lon": -0.13},
        )
        location_id = create_resp.json()["id"]

        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(),
        )

        response = await client.get(f"/api/locations/{location_id}/weather")

        assert response.status_code == 200
        data = response.json()
        assert data["location_name"] == "London"

    async def test_weather_for_nonexistent_location_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Requesting weather for a non-existent location returns 404."""
        import uuid

        response = await client.get(f"/api/locations/{uuid.uuid4()}/weather")

        assert response.status_code == 404

    async def test_weather_with_units_parameter(
        self, client: AsyncClient, httpx_mock
    ) -> None:
        """The units parameter is passed through to the weather service."""
        create_resp = await client.post(
            "/api/locations",
            json={"name": "Test", "lat": 51.51, "lon": -0.13},
        )
        location_id = create_resp.json()["id"]

        httpx_mock.add_response(
            url=re.compile(r".*/weather\?.*"),
            json=make_owm_current_weather_response(temp=0.0),
        )

        response = await client.get(
            f"/api/locations/{location_id}/weather",
            params={"units": "fahrenheit"},
        )

        assert response.status_code == 200
        assert response.json()["units"] == "fahrenheit"
        assert response.json()["temperature"] == 32.0
