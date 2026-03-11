"""Pure conversion functions for weather data.

All temperature conversions expect input in Celsius (the default unit from
the OpenWeatherMap API when using ``units=metric``).

All wind-speed conversions expect input in meters per second (m/s).
"""

import math

# Compass points for wind direction conversion (16-point compass rose)
_COMPASS_POINTS: list[str] = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.

    Formula: ``F = C * 9/5 + 32``

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit, rounded to 2 decimal places.
    """
    return round(celsius * 9 / 5 + 32, 2)


def celsius_to_kelvin(celsius: float) -> float:
    """Convert Celsius to Kelvin.

    Formula: ``K = C + 273.15``

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in Kelvin, rounded to 2 decimal places.
    """
    return round(celsius + 273.15, 2)


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius.

    Formula: ``C = (F - 32) * 5/9``

    Args:
        fahrenheit: Temperature in degrees Fahrenheit.

    Returns:
        Temperature in degrees Celsius, rounded to 2 decimal places.
    """
    return round((fahrenheit - 32) * 5 / 9, 2)


def mps_to_kmh(mps: float) -> float:
    """Convert meters per second to kilometers per hour.

    Formula: ``km/h = m/s * 3.6``

    Args:
        mps: Speed in meters per second.

    Returns:
        Speed in kilometers per hour, rounded to 2 decimal places.
    """
    return round(mps * 3.6, 2)


def mps_to_mph(mps: float) -> float:
    """Convert meters per second to miles per hour.

    Formula: ``mph = m/s * 2.23694``

    Args:
        mps: Speed in meters per second.

    Returns:
        Speed in miles per hour, rounded to 2 decimal places.
    """
    return round(mps * 2.23694, 2)


def degrees_to_compass(degrees: float) -> str:
    """Convert wind direction in degrees to a 16-point compass direction.

    The 360-degree circle is divided into 16 equal sectors of 22.5° each.
    North is centered at 0° (i.e., 348.75°–11.25° maps to "N").

    Args:
        degrees: Wind direction in degrees (0–360). Values outside this
            range are normalized using modulo 360.

    Returns:
        A compass direction string, e.g. ``"N"``, ``"NNE"``, ``"SW"``.
    """
    normalized = degrees % 360
    index = math.floor((normalized + 11.25) / 22.5) % 16
    return _COMPASS_POINTS[index]
