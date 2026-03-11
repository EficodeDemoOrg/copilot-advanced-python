# Weather App

A medium-complexity FastAPI weather service designed as a **GitHub Copilot exercise environment** for Python developers.

## Purpose

This repository is **not** a product — it's a realistic codebase for practicing GitHub Copilot (chat, completions, agent mode) on real-world Python patterns. The goal is to eliminate setup time so participants can jump straight into Copilot exercises.

## Exercises

See [EXERCISES.md](EXERCISES.md) for the workshop exercises. They cover custom agents, agent skills, subagent orchestration, hooks, and MCP server integration.

## What It Does

- Fetches real-time weather data from the [OpenWeatherMap API](https://openweathermap.org/api)
- Manages a collection of saved locations (in-memory)
- Serves a static HTML/JS dashboard with current weather, 5-day forecast charts, and weather alerts
- Provides a clean REST API with full CRUD for locations and weather queries

## Tech Stack

| Component       | Tool                 |
|-----------------|----------------------|
| Runtime         | Python 3.12+         |
| Package manager | uv                   |
| Web framework   | FastAPI              |
| HTTP client     | httpx (async)        |
| Config          | pydantic-settings    |
| Linter/Formatter| Ruff                 |
| Testing         | pytest + pytest-asyncio + pytest-httpx |
| Frontend        | Vanilla JS + Chart.js (CDN) |

## Quick Start

### 1. Get an OpenWeatherMap API Key

Sign up at [openweathermap.org](https://openweathermap.org/api) and get a free API key.

### 2. Set Up the Project

```bash
# Clone the repo
git clone <repo-url>
cd copilot-python-advanced

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your OPENWEATHERMAP_API_KEY
```

### 3. Run the Application

```bash
uv run uvicorn weather_app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) to see the dashboard.

### 4. Run Tests

```bash
# All tests (no API key needed — external calls are mocked)
uv run pytest

# Unit tests only
uv run pytest -m unit

# Integration tests only
uv run pytest -m integration

# With verbose output
uv run pytest -v
```

### 5. Lint & Format

```bash
# Check for lint errors
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Check formatting
uv run ruff format --check src/ tests/

# Apply formatting
uv run ruff format src/ tests/
```

## Project Structure

```
src/weather_app/
├── __init__.py              # Package marker
├── main.py                  # FastAPI app factory, static file mount, exception handlers
├── config.py                # Settings from env vars via pydantic-settings
├── models.py                # Pydantic models and enums
├── dependencies.py          # FastAPI dependency injection wiring
├── routers/
│   ├── weather.py           # /api/weather/* endpoints
│   └── locations.py         # /api/locations/* endpoints
├── services/
│   ├── exceptions.py        # Custom exception hierarchy
│   ├── openweathermap.py    # Async OpenWeatherMap API client
│   └── weather_service.py   # Business logic: conversion, alerts
├── repositories/
│   └── location_repo.py     # In-memory CRUD for saved locations
├── utils/
│   └── converters.py        # Pure conversion functions
└── static/
    ├── index.html           # Dashboard
    ├── style.css            # Styles
    └── app.js               # Client-side logic

tests/
├── conftest.py              # Shared fixtures: app, client, settings
├── factories.py             # Test data factories for all models
├── unit/
│   ├── conftest.py          # Mock fixtures for unit tests
│   ├── test_models.py       # Pydantic model validation tests
│   ├── test_converters.py   # Pure function tests (parametrized)
│   ├── test_weather_service.py  # Service logic with mocked API client
│   └── test_location_repo.py   # Repository CRUD tests
└── integration/
    ├── conftest.py          # Integration-specific fixtures
    ├── test_weather_api.py  # Full /api/weather/* endpoint tests
    └── test_locations_api.py # Full /api/locations/* CRUD tests
```

## API Endpoints

### Weather

| Method | Endpoint                  | Description                    |
|--------|---------------------------|--------------------------------|
| GET    | `/api/weather/current`    | Current weather for coordinates |
| GET    | `/api/weather/forecast`   | Multi-day forecast             |
| GET    | `/api/weather/alerts`     | Weather alerts for coordinates  |

### Locations

| Method | Endpoint                         | Description                     |
|--------|----------------------------------|---------------------------------|
| GET    | `/api/locations`                 | List all saved locations        |
| POST   | `/api/locations`                 | Save a new location             |
| GET    | `/api/locations/{id}`            | Get a saved location            |
| PUT    | `/api/locations/{id}`            | Update a saved location         |
| DELETE | `/api/locations/{id}`            | Delete a saved location         |
| GET    | `/api/locations/{id}/weather`    | Get weather for a saved location |

Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) when the app is running.

## Backlog

Improvement ideas to tackle as Copilot exercises:

- [ ] **Align test factories with real OWM API schema** — The factory functions
  `make_owm_current_weather_response` and `make_owm_forecast_response` in
  `tests/factories.py` produce simplified JSON that is structurally consistent
  with the parser but missing fields present in real OpenWeatherMap responses
  (e.g. `visibility`, `clouds`, `sys`, `wind.gust`, `pop`).  Compare against
  the [Current Weather](https://openweathermap.org/current#example_JSON) and
  [5-Day Forecast](https://openweathermap.org/forecast5#JSON) documentation,
  then update the factories to match the full schema.
