"""Unit tests for conversion utility functions.

Each converter is tested with standard values, edge cases, and
boundary conditions using parametrize for comprehensive coverage.
"""

import pytest

from weather_app.utils.converters import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    degrees_to_compass,
    fahrenheit_to_celsius,
    mps_to_kmh,
    mps_to_mph,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# celsius_to_fahrenheit
# ---------------------------------------------------------------------------


class TestCelsiusToFahrenheit:
    """Tests for celsius_to_fahrenheit()."""

    @pytest.mark.parametrize(
        "celsius,expected",
        [
            (0.0, 32.0),
            (100.0, 212.0),
            (-40.0, -40.0),
            (37.0, 98.6),
            (-273.15, -459.67),
        ],
        ids=[
            "freezing_point",
            "boiling_point",
            "equal_point_minus_40",
            "body_temperature",
            "absolute_zero",
        ],
    )
    def test_known_conversions(self, celsius: float, expected: float) -> None:
        """Well-known temperature pairs convert correctly."""
        result = celsius_to_fahrenheit(celsius)

        assert result == expected

    def test_returns_float(self) -> None:
        """The result is always a float."""
        result = celsius_to_fahrenheit(20)

        assert isinstance(result, float)

    def test_rounds_to_two_decimals(self) -> None:
        """Result is rounded to 2 decimal places."""
        result = celsius_to_fahrenheit(33.333)

        assert result == pytest.approx(92.0, abs=0.01)


# ---------------------------------------------------------------------------
# celsius_to_kelvin
# ---------------------------------------------------------------------------


class TestCelsiusToKelvin:
    """Tests for celsius_to_kelvin()."""

    @pytest.mark.parametrize(
        "celsius,expected",
        [
            (0.0, 273.15),
            (100.0, 373.15),
            (-273.15, 0.0),
            (25.0, 298.15),
        ],
        ids=[
            "freezing_point",
            "boiling_point",
            "absolute_zero",
            "room_temperature",
        ],
    )
    def test_known_conversions(self, celsius: float, expected: float) -> None:
        """Well-known temperature pairs convert correctly."""
        result = celsius_to_kelvin(celsius)

        assert result == expected

    def test_negative_celsius_gives_positive_kelvin(self) -> None:
        """A negative Celsius value above absolute zero is still positive in Kelvin."""
        result = celsius_to_kelvin(-10.0)

        assert result > 0


# ---------------------------------------------------------------------------
# fahrenheit_to_celsius
# ---------------------------------------------------------------------------


class TestFahrenheitToCelsius:
    """Tests for fahrenheit_to_celsius()."""

    @pytest.mark.parametrize(
        "fahrenheit,expected",
        [
            (32.0, 0.0),
            (212.0, 100.0),
            (-40.0, -40.0),
            (98.6, 37.0),
        ],
        ids=[
            "freezing_point",
            "boiling_point",
            "equal_point_minus_40",
            "body_temperature",
        ],
    )
    def test_known_conversions(self, fahrenheit: float, expected: float) -> None:
        """Well-known temperature pairs convert correctly."""
        result = fahrenheit_to_celsius(fahrenheit)

        assert result == expected

    def test_inverse_of_celsius_to_fahrenheit(self) -> None:
        """Converting C→F→C returns the original value."""
        original = 23.5
        converted = celsius_to_fahrenheit(original)
        result = fahrenheit_to_celsius(converted)

        assert result == pytest.approx(original, abs=0.01)


# ---------------------------------------------------------------------------
# mps_to_kmh
# ---------------------------------------------------------------------------


class TestMpsToKmh:
    """Tests for mps_to_kmh()."""

    @pytest.mark.parametrize(
        "mps,expected",
        [
            (0.0, 0.0),
            (1.0, 3.6),
            (10.0, 36.0),
            (27.78, 100.01),
        ],
        ids=["zero", "one_mps", "ten_mps", "hundred_kmh"],
    )
    def test_known_conversions(self, mps: float, expected: float) -> None:
        """Known speed conversions are correct."""
        result = mps_to_kmh(mps)

        assert result == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# mps_to_mph
# ---------------------------------------------------------------------------


class TestMpsToMph:
    """Tests for mps_to_mph()."""

    @pytest.mark.parametrize(
        "mps,expected",
        [
            (0.0, 0.0),
            (1.0, 2.24),
            (10.0, 22.37),
            (44.704, 100.0),
        ],
        ids=["zero", "one_mps", "ten_mps", "hundred_mph"],
    )
    def test_known_conversions(self, mps: float, expected: float) -> None:
        """Known speed conversions are correct."""
        result = mps_to_mph(mps)

        assert result == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# degrees_to_compass
# ---------------------------------------------------------------------------


class TestDegreesToCompass:
    """Tests for degrees_to_compass()."""

    @pytest.mark.parametrize(
        "degrees,expected",
        [
            (0.0, "N"),
            (45.0, "NE"),
            (90.0, "E"),
            (135.0, "SE"),
            (180.0, "S"),
            (225.0, "SW"),
            (270.0, "W"),
            (315.0, "NW"),
            (360.0, "N"),
        ],
        ids=["N", "NE", "E", "SE", "S", "SW", "W", "NW", "360_wraps_to_N"],
    )
    def test_cardinal_and_intercardinal_directions(
        self, degrees: float, expected: str
    ) -> None:
        """Cardinal and intercardinal directions map correctly."""
        result = degrees_to_compass(degrees)

        assert result == expected

    @pytest.mark.parametrize(
        "degrees,expected",
        [
            (22.5, "NNE"),
            (67.5, "ENE"),
            (112.5, "ESE"),
            (157.5, "SSE"),
            (202.5, "SSW"),
            (247.5, "WSW"),
            (292.5, "WNW"),
            (337.5, "NNW"),
        ],
        ids=["NNE", "ENE", "ESE", "SSE", "SSW", "WSW", "WNW", "NNW"],
    )
    def test_secondary_intercardinal_directions(
        self, degrees: float, expected: str
    ) -> None:
        """16-point compass secondary intercardinals are correct."""
        result = degrees_to_compass(degrees)

        assert result == expected

    def test_negative_degrees_normalized(self) -> None:
        """Negative degree values are normalized to 0-360 range."""
        result = degrees_to_compass(-90)

        assert result == degrees_to_compass(270)

    def test_large_degree_value_normalized(self) -> None:
        """Values above 360 wrap around correctly."""
        result = degrees_to_compass(720)

        assert result == "N"

    @pytest.mark.parametrize(
        "degrees,expected",
        [
            (11.24, "N"),
            (11.26, "NNE"),
            (348.74, "NNW"),
            (348.76, "N"),
        ],
        ids=[
            "just_below_NNE_boundary",
            "just_above_NNE_boundary",
            "just_below_N_boundary",
            "just_above_N_boundary",
        ],
    )
    def test_boundary_values(self, degrees: float, expected: str) -> None:
        """Values at the edge of compass sectors map correctly."""
        result = degrees_to_compass(degrees)

        assert result == expected
