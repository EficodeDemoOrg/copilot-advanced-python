"""In-memory repository for saved locations.

Provides simple CRUD operations backed by a Python ``dict``.  This keeps the
application zero-dependency (no database) while still demonstrating a proper
repository pattern.
"""

from uuid import UUID

from weather_app.models import Coordinates, Location, LocationCreate, LocationUpdate
from weather_app.services.exceptions import LocationNotFoundError


class LocationRepository:
    """In-memory store for ``Location`` objects, keyed by UUID."""

    def __init__(self) -> None:
        self._locations: dict[UUID, Location] = {}

    def add(self, data: LocationCreate) -> Location:
        """Create and store a new location.

        Args:
            data: The location data to create.

        Returns:
            The newly created ``Location`` with a generated UUID.
        """
        location = Location(
            name=data.name,
            coordinates=Coordinates(lat=data.lat, lon=data.lon),
        )
        self._locations[location.id] = location
        return location

    def get(self, location_id: UUID) -> Location:
        """Retrieve a location by its ID.

        Args:
            location_id: The UUID of the location.

        Returns:
            The matching ``Location``.

        Raises:
            LocationNotFoundError: If no location exists with the given ID.
        """
        location = self._locations.get(location_id)
        if location is None:
            raise LocationNotFoundError(str(location_id))
        return location

    def list_all(self) -> list[Location]:
        """Return all saved locations, ordered by creation time.

        Returns:
            A list of all stored ``Location`` objects.
        """
        return sorted(self._locations.values(), key=lambda loc: loc.created_at)

    def delete(self, location_id: UUID) -> bool:
        """Delete a location by its ID.

        Args:
            location_id: The UUID of the location to delete.

        Returns:
            ``True`` if the location was deleted.

        Raises:
            LocationNotFoundError: If no location exists with the given ID.
        """
        if location_id not in self._locations:
            raise LocationNotFoundError(str(location_id))
        del self._locations[location_id]
        return True

    def update(self, location_id: UUID, data: LocationUpdate) -> Location:
        """Update an existing location with partial data.

        Only fields that are not ``None`` in *data* are updated.

        Args:
            location_id: The UUID of the location to update.
            data: Fields to update.

        Returns:
            The updated ``Location``.

        Raises:
            LocationNotFoundError: If no location exists with the given ID.
        """
        location = self.get(location_id)

        update_fields: dict[str, object] = {}
        if data.name is not None:
            update_fields["name"] = data.name
        if data.lat is not None or data.lon is not None:
            new_lat = data.lat if data.lat is not None else location.coordinates.lat
            new_lon = data.lon if data.lon is not None else location.coordinates.lon
            update_fields["coordinates"] = Coordinates(lat=new_lat, lon=new_lon)

        updated = location.model_copy(update=update_fields)
        self._locations[location_id] = updated
        return updated
