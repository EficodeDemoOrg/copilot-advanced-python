"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the Weather App.

    Settings are loaded from environment variables or a `.env` file.
    The ``OPENWEATHERMAP_API_KEY`` is required for real API calls but
    defaults to an empty string so that tests can run without it.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openweathermap_api_key: str = ""
    openweathermap_base_url: str = "https://api.openweathermap.org/data/2.5"

    app_name: str = "Weather App"
    debug: bool = False

    # Weather alert thresholds
    alert_wind_speed_threshold: float = 20.0  # m/s
    alert_temp_high_threshold: float = 40.0  # °C
    alert_temp_low_threshold: float = -20.0  # °C
    alert_humidity_threshold: float = 90.0  # %
