"""Unit tests for Pydantic models.

Tests validate both valid and invalid inputs, ensuring proper field
constraints and default values.
"""

from uuid import UUID

import pytest

from tests.factories import (
    make_coordinates,
    make_current_weather,
    make_forecast_day,
    make_location,
    make_location_create,
    make_weather_alert,
)
from weather_app.models import (
    AlertSeverity,
    Coordinates,
    LocationCreate,
    LocationUpdate,
    TemperatureUnit,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# TemperatureUnit
# ---------------------------------------------------------------------------


class TestTemperatureUnit:
    """Tests for the TemperatureUnit enum."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("celsius", TemperatureUnit.CELSIUS),
            ("fahrenheit", TemperatureUnit.FAHRENHEIT),
            ("kelvin", TemperatureUnit.KELVIN),
        ],
    )
    def test_valid_values(self, value: str, expected: TemperatureUnit) -> None:
        """Each string value maps to the correct enum member."""
        assert TemperatureUnit(value) == expected

    def test_invalid_value_raises(self) -> None:
        """An unsupported string raises a ValueError."""
        with pytest.raises(ValueError):
            TemperatureUnit("rankine")


# ---------------------------------------------------------------------------
# AlertSeverity
# ---------------------------------------------------------------------------


class TestAlertSeverity:
    """Tests for the AlertSeverity enum."""

    @pytest.mark.parametrize("value", ["low", "medium", "high", "extreme"])
    def test_valid_values(self, value: str) -> None:
        """All defined severity levels are accepted."""
        assert AlertSeverity(value).value == value


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------


class TestCoordinates:
    """Tests for the Coordinates model."""

    def test_valid_coordinates(self) -> None:
        """A coordinate pair within bounds is accepted."""
        coords = make_coordinates(lat=48.86, lon=2.35)

        assert coords.lat == 48.86
        assert coords.lon == 2.35

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (-90.0, -180.0),
            (90.0, 180.0),
            (0.0, 0.0),
        ],
    )
    def test_boundary_values_are_valid(self, lat: float, lon: float) -> None:
        """Exact boundary values (-90/90, -180/180) are accepted."""
        coords = Coordinates(lat=lat, lon=lon)

        assert coords.lat == lat
        assert coords.lon == lon

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (91.0, 0.0),
            (-91.0, 0.0),
            (0.0, 181.0),
            (0.0, -181.0),
        ],
    )
    def test_out_of_range_raises_validation_error(self, lat: float, lon: float) -> None:
        """Coordinates outside the valid range are rejected."""
        with pytest.raises(ValueError):
            Coordinates(lat=lat, lon=lon)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


class TestLocation:
    """Tests for the Location model."""

    def test_creates_with_defaults(self) -> None:
        """A location gets a UUID and timestamp by default."""
        loc = make_location()

        assert isinstance(loc.id, UUID)
        assert loc.name == "London"
        assert loc.coordinates.lat == 51.51

    def test_name_min_length_enforcement(self) -> None:
        """An empty name is rejected."""
        with pytest.raises(ValueError):
            make_location(name="")

    def test_name_max_length_enforcement(self) -> None:
        """A name exceeding 200 chars is rejected."""
        with pytest.raises(ValueError):
            make_location(name="x" * 201)


# ---------------------------------------------------------------------------
# LocationCreate
# ---------------------------------------------------------------------------


class TestLocationCreate:
    """Tests for the LocationCreate model."""

    def test_valid_creation(self) -> None:
        """Valid input produces a LocationCreate."""
        data = make_location_create(name="Paris", lat=48.86, lon=2.35)

        assert data.name == "Paris"
        assert data.lat == 48.86
        assert data.lon == 2.35

    def test_empty_name_rejected(self) -> None:
        """An empty name is rejected."""
        with pytest.raises(ValueError):
            LocationCreate(name="", lat=0, lon=0)

    def test_invalid_lat_rejected(self) -> None:
        """Latitude out of range is rejected."""
        with pytest.raises(ValueError):
            LocationCreate(name="Test", lat=100, lon=0)


# ---------------------------------------------------------------------------
# LocationUpdate
# ---------------------------------------------------------------------------


class TestLocationUpdate:
    """Tests for the LocationUpdate model."""

    def test_all_none_is_valid(self) -> None:
        """An update with all None fields is still valid (no-op update)."""
        update = LocationUpdate()

        assert update.name is None
        assert update.lat is None
        assert update.lon is None

    def test_partial_update(self) -> None:
        """Only the provided fields are set."""
        update = LocationUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.lat is None


# ---------------------------------------------------------------------------
# CurrentWeather
# ---------------------------------------------------------------------------


class TestCurrentWeather:
    """Tests for the CurrentWeather model."""

    def test_valid_weather(self) -> None:
        """All fields are populated correctly from factory defaults."""
        weather = make_current_weather()

        assert weather.temperature == 15.0
        assert weather.humidity == 72.0
        assert weather.location_name == "London"
        assert weather.units == TemperatureUnit.CELSIUS

    def test_humidity_upper_bound(self) -> None:
        """Humidity above 100% is rejected."""
        with pytest.raises(ValueError):
            make_current_weather(humidity=101.0)

    def test_negative_wind_speed_rejected(self) -> None:
        """Negative wind speed is rejected."""
        with pytest.raises(ValueError):
            make_current_weather(wind_speed=-1.0)


# ---------------------------------------------------------------------------
# ForecastDay
# ---------------------------------------------------------------------------


class TestForecastDay:
    """Tests for the ForecastDay model."""

    def test_valid_forecast_day(self) -> None:
        """A valid forecast day is created from factory defaults."""
        day = make_forecast_day()

        assert day.temp_min == 10.0
        assert day.temp_max == 20.0
        assert day.humidity == 65.0

    def test_humidity_bounds(self) -> None:
        """Humidity outside 0-100 is rejected."""
        with pytest.raises(ValueError):
            make_forecast_day(humidity=-1.0)

        with pytest.raises(ValueError):
            make_forecast_day(humidity=101.0)


# ---------------------------------------------------------------------------
# WeatherAlert
# ---------------------------------------------------------------------------


class TestWeatherAlert:
    """Tests for the WeatherAlert model."""

    def test_valid_alert(self) -> None:
        """A well-formed alert is created from factory defaults."""
        alert = make_weather_alert()

        assert alert.alert_type == "high_wind"
        assert alert.severity == AlertSeverity.MEDIUM
        assert alert.value == 25.0
        assert alert.threshold == 20.0

    def test_custom_alert(self) -> None:
        """Custom parameters are reflected in the model."""
        alert = make_weather_alert(
            alert_type="extreme_heat",
            severity=AlertSeverity.EXTREME,
            value=45.0,
            threshold=40.0,
        )

        assert alert.alert_type == "extreme_heat"
        assert alert.severity == AlertSeverity.EXTREME
