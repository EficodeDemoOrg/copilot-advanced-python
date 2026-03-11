"""Custom exceptions for weather service operations."""


class WeatherAppError(Exception):
    """Base exception for all Weather App errors."""


class WeatherAPIError(WeatherAppError):
    """Raised when the OpenWeatherMap API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Weather API error ({status_code}): {message}")


class WeatherAPIConnectionError(WeatherAppError):
    """Raised when unable to connect to the OpenWeatherMap API."""

    def __init__(self, message: str = "Failed to connect to weather API") -> None:
        self.message = message
        super().__init__(message)


class WeatherAPINotFoundError(WeatherAPIError):
    """Raised when the requested location is not found by the API."""

    def __init__(self, message: str = "Location not found in weather API") -> None:
        super().__init__(status_code=404, message=message)


class LocationNotFoundError(WeatherAppError):
    """Raised when a saved location is not found in the repository."""

    def __init__(self, location_id: str) -> None:
        self.location_id = location_id
        super().__init__(f"Location not found: {location_id}")
