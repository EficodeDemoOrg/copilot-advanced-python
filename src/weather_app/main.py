"""FastAPI application entry point.

Creates the FastAPI app, includes routers, and mounts the static file
directory for the frontend dashboard.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from weather_app.config import Settings
from weather_app.dependencies import get_settings
from weather_app.routers import locations, weather
from weather_app.services.exceptions import (
    WeatherAPIConnectionError,
    WeatherAPIError,
    WeatherAPINotFoundError,
    WeatherAppError,
)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup/shutdown tasks."""
    # Startup: nothing special needed for now
    yield
    # Shutdown: nothing special needed for now


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory function to create and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful for testing).

    Returns:
        A fully configured ``FastAPI`` instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="A weather service for GitHub Copilot exercises",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include API routers
    app.include_router(weather.router)
    app.include_router(locations.router)

    # Mount the static frontend
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register exception handlers
    _register_exception_handlers(app)

    # Root endpoint serves the dashboard
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root() -> HTMLResponse:
        """Serve the main dashboard HTML page."""
        index_path = STATIC_DIR / "index.html"
        if index_path.is_file():
            return HTMLResponse(content=index_path.read_text())
        return HTMLResponse(
            content="<h1>Weather App</h1><p>Static files not found.</p>"
        )

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""

    @app.exception_handler(WeatherAPINotFoundError)
    async def weather_not_found_handler(
        request: Request, exc: WeatherAPINotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message},
        )

    @app.exception_handler(WeatherAPIConnectionError)
    async def weather_connection_handler(
        request: Request, exc: WeatherAPIConnectionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message},
        )

    @app.exception_handler(WeatherAPIError)
    async def weather_api_handler(
        request: Request, exc: WeatherAPIError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": exc.message},
        )

    @app.exception_handler(WeatherAppError)
    async def weather_app_handler(
        request: Request, exc: WeatherAppError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )


# Default application instance used by ``uvicorn weather_app.main:app``
app = create_app()
