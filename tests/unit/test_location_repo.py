"""Unit tests for LocationRepository.

Tests cover all CRUD operations, error cases, and ordering behavior
of the in-memory location repository.
"""

from uuid import uuid4

import pytest

from tests.factories import make_location_create, make_location_update
from weather_app.repositories.location_repo import LocationRepository
from weather_app.services.exceptions import LocationNotFoundError

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


class TestLocationRepoAdd:
    """Tests for LocationRepository.add()."""

    def test_add_returns_location_with_id(
        self, location_repo: LocationRepository
    ) -> None:
        """Adding a location returns a Location with a generated UUID."""
        data = make_location_create(name="London", lat=51.51, lon=-0.13)

        result = location_repo.add(data)

        assert result.name == "London"
        assert result.coordinates.lat == 51.51
        assert result.id is not None

    def test_add_multiple_locations(self, location_repo: LocationRepository) -> None:
        """Multiple locations can be added with unique IDs."""
        loc1 = location_repo.add(make_location_create(name="London"))
        loc2 = location_repo.add(make_location_create(name="Paris"))

        assert loc1.id != loc2.id
        assert len(location_repo.list_all()) == 2


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestLocationRepoGet:
    """Tests for LocationRepository.get()."""

    def test_get_existing_location(self, location_repo: LocationRepository) -> None:
        """An existing location is retrieved by its ID."""
        added = location_repo.add(make_location_create(name="Berlin"))

        result = location_repo.get(added.id)

        assert result.name == "Berlin"
        assert result.id == added.id

    def test_get_nonexistent_raises_not_found(
        self, location_repo: LocationRepository
    ) -> None:
        """Requesting a non-existent ID raises LocationNotFoundError."""
        fake_id = uuid4()

        with pytest.raises(LocationNotFoundError) as exc_info:
            location_repo.get(fake_id)

        assert str(fake_id) in str(exc_info.value)


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


class TestLocationRepoListAll:
    """Tests for LocationRepository.list_all()."""

    def test_empty_repo_returns_empty_list(
        self, location_repo: LocationRepository
    ) -> None:
        """An empty repository returns an empty list."""
        result = location_repo.list_all()

        assert result == []

    def test_returns_all_added_locations(
        self, location_repo: LocationRepository
    ) -> None:
        """All added locations appear in the list."""
        location_repo.add(make_location_create(name="A"))
        location_repo.add(make_location_create(name="B"))
        location_repo.add(make_location_create(name="C"))

        result = location_repo.list_all()

        assert len(result) == 3
        names = {loc.name for loc in result}
        assert names == {"A", "B", "C"}

    def test_ordered_by_created_at(self, location_repo: LocationRepository) -> None:
        """Locations are returned in creation order."""
        loc1 = location_repo.add(make_location_create(name="First"))
        loc2 = location_repo.add(make_location_create(name="Second"))
        loc3 = location_repo.add(make_location_create(name="Third"))

        result = location_repo.list_all()

        assert result[0].id == loc1.id
        assert result[1].id == loc2.id
        assert result[2].id == loc3.id


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestLocationRepoDelete:
    """Tests for LocationRepository.delete()."""

    def test_delete_existing_location(self, location_repo: LocationRepository) -> None:
        """Deleting an existing location removes it from the store."""
        added = location_repo.add(make_location_create(name="Tokyo"))

        result = location_repo.delete(added.id)

        assert result is True
        assert location_repo.list_all() == []

    def test_delete_nonexistent_raises_not_found(
        self, location_repo: LocationRepository
    ) -> None:
        """Deleting a non-existent ID raises LocationNotFoundError."""
        with pytest.raises(LocationNotFoundError):
            location_repo.delete(uuid4())

    def test_delete_does_not_affect_other_locations(
        self, location_repo: LocationRepository
    ) -> None:
        """Deleting one location leaves others intact."""
        loc1 = location_repo.add(make_location_create(name="A"))
        loc2 = location_repo.add(make_location_create(name="B"))

        location_repo.delete(loc1.id)

        remaining = location_repo.list_all()
        assert len(remaining) == 1
        assert remaining[0].id == loc2.id


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestLocationRepoUpdate:
    """Tests for LocationRepository.update()."""

    def test_update_name(self, location_repo: LocationRepository) -> None:
        """Updating the name changes only the name field."""
        added = location_repo.add(
            make_location_create(name="Old Name", lat=10.0, lon=20.0)
        )

        updated = location_repo.update(added.id, make_location_update(name="New Name"))

        assert updated.name == "New Name"
        assert updated.coordinates.lat == 10.0
        assert updated.coordinates.lon == 20.0

    def test_update_coordinates(self, location_repo: LocationRepository) -> None:
        """Updating lat/lon changes only coordinate fields."""
        added = location_repo.add(
            make_location_create(name="Place", lat=10.0, lon=20.0)
        )

        updated = location_repo.update(
            added.id, make_location_update(lat=30.0, lon=40.0)
        )

        assert updated.name == "Place"
        assert updated.coordinates.lat == 30.0
        assert updated.coordinates.lon == 40.0

    def test_update_partial_coordinates(
        self, location_repo: LocationRepository
    ) -> None:
        """Updating only lat preserves the existing lon."""
        added = location_repo.add(
            make_location_create(name="Place", lat=10.0, lon=20.0)
        )

        updated = location_repo.update(added.id, make_location_update(lat=50.0))

        assert updated.coordinates.lat == 50.0
        assert updated.coordinates.lon == 20.0

    def test_update_nonexistent_raises_not_found(
        self, location_repo: LocationRepository
    ) -> None:
        """Updating a non-existent ID raises LocationNotFoundError."""
        with pytest.raises(LocationNotFoundError):
            location_repo.update(uuid4(), make_location_update(name="X"))

    def test_update_persists_in_repo(self, location_repo: LocationRepository) -> None:
        """After update, re-fetching returns the updated data."""
        added = location_repo.add(make_location_create(name="Before"))

        location_repo.update(added.id, make_location_update(name="After"))
        fetched = location_repo.get(added.id)

        assert fetched.name == "After"

    def test_noop_update(self, location_repo: LocationRepository) -> None:
        """An update with all None fields leaves the location unchanged."""
        added = location_repo.add(make_location_create(name="Static", lat=1.0, lon=2.0))

        updated = location_repo.update(added.id, make_location_update())

        assert updated.name == "Static"
        assert updated.coordinates.lat == 1.0
        assert updated.coordinates.lon == 2.0
