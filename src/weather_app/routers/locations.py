"""API routes for managing saved locations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from weather_app.dependencies import (
    get_location_repository,
    get_weather_service,
)
from weather_app.models import (
    CurrentWeather,
    Location,
    LocationCreate,
    LocationUpdate,
    TemperatureUnit,
)
from weather_app.repositories.location_repo import LocationRepository
from weather_app.services.exceptions import LocationNotFoundError
from weather_app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("", response_model=list[Location])
async def list_locations(
    repo: LocationRepository = Depends(get_location_repository),
) -> list[Location]:
    """List all saved locations."""
    return repo.list_all()


@router.post("", response_model=Location, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    repo: LocationRepository = Depends(get_location_repository),
) -> Location:
    """Save a new location."""
    return repo.add(data)


@router.get("/{location_id}", response_model=Location)
async def get_location(
    location_id: UUID,
    repo: LocationRepository = Depends(get_location_repository),
) -> Location:
    """Get a saved location by ID."""
    try:
        return repo.get(location_id)
    except LocationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )


@router.put("/{location_id}", response_model=Location)
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    repo: LocationRepository = Depends(get_location_repository),
) -> Location:
    """Update a saved location."""
    try:
        return repo.update(location_id, data)
    except LocationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    repo: LocationRepository = Depends(get_location_repository),
) -> None:
    """Delete a saved location."""
    try:
        repo.delete(location_id)
    except LocationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )


@router.get("/{location_id}/weather", response_model=CurrentWeather)
async def get_location_weather(
    location_id: UUID,
    units: Annotated[
        TemperatureUnit, Query(description="Temperature unit")
    ] = TemperatureUnit.CELSIUS,
    repo: LocationRepository = Depends(get_location_repository),
    service: WeatherService = Depends(get_weather_service),
) -> CurrentWeather:
    """Get current weather for a saved location."""
    try:
        location = repo.get(location_id)
    except LocationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )
    return await service.get_current_weather(
        location.coordinates.lat,
        location.coordinates.lon,
        units=units,
    )
