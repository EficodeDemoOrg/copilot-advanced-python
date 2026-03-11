# Copilot Instructions for Weather App

## Project Overview

This is a **GitHub Copilot exercise environment** — a fully working FastAPI weather service.
The codebase is the substrate participants use to practice Copilot features.  All code is
complete and tested; exercises focus on **extending** the application, not fixing it.

## Architecture

**Layered structure with clear separation of concerns:**

- **Routers** (`src/weather_app/routers/`) — HTTP request handling only. Validate input,
  call services, return responses.  No business logic here.
- **Services** (`src/weather_app/services/`) — Business logic layer.  `WeatherService`
  orchestrates the API client, handles unit conversion, and evaluates weather alerts.
  `OpenWeatherMapClient` handles all external HTTP communication.
- **Repositories** (`src/weather_app/repositories/`) — Data access layer.
  `LocationRepository` provides CRUD over an in-memory dict.  No database dependency.
- **Models** (`src/weather_app/models.py`) — Pydantic models shared across all layers.
  Used for request/response validation and internal data passing.
- **Utils** (`src/weather_app/utils/`) — Pure, stateless helper functions (converters).
- **Dependencies** (`src/weather_app/dependencies.py`) — FastAPI dependency injection
  wiring.  Provides factory functions for settings, services, and repositories.

## Coding Conventions

### Python Style
- **Python 3.12+** — use modern syntax: `str | None`, `list[T]`, `StrEnum`
- **Type hints on all function signatures** — parameters and return types
- **Docstrings on all public functions and classes** — Google-style, brief
- **Ruff** for linting and formatting — config in `pyproject.toml`
- **Line length**: 88 characters
- **Imports**: sorted by Ruff (isort rules), grouped standard → third-party → first-party

### Naming
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: prefix with `_`

### Error Handling
- Custom exceptions in `services/exceptions.py` — inherit from `WeatherAppError`
- Routers catch domain exceptions and raise `fastapi.HTTPException`
- Exception handlers in `main.py` catch service-level errors globally

### Async
- All HTTP-facing code is async (routers, services, API client)
- Use `httpx.AsyncClient` for outgoing HTTP requests
- Repository is synchronous (in-memory dict operations)

## Testing Conventions

### Structure
- `tests/unit/` — isolated tests with mocked dependencies
- `tests/integration/` — full request/response through FastAPI with mocked external HTTP
- `tests/factories.py` — centralized test data factories for all models

### Rules
- **Naming**: `test_{feature}_{scenario}_{expected_outcome}`
- **AAA pattern**: Arrange → Act → Assert, separated by blank lines
- **One behavior per test** — each test verifies exactly one thing
- **Parametrize** with `@pytest.mark.parametrize` for multiple input/output cases
- **Factories over raw dicts** — use `make_location()`, `make_current_weather()` etc.
- **Markers**: `@pytest.mark.unit` and `@pytest.mark.integration` on every test module
- **No real API calls** — unit tests mock at service boundary, integration tests mock
  external HTTP via `pytest-httpx`
- **Async tests** are auto-detected via `asyncio_mode = "auto"` in pytest config

### Mocking Strategy
- **Unit tests**: inject `AsyncMock(spec=OpenWeatherMapClient)` into `WeatherService`
- **Integration tests**: use `pytest-httpx` (`httpx_mock` fixture) to intercept outgoing
  `httpx` requests from `OpenWeatherMapClient`
- **Dependency overrides**: the test `app` fixture overrides `get_settings` and
  `get_location_repository` via `app.dependency_overrides`

## Dependencies

- **fastapi** — web framework
- **uvicorn** — ASGI server
- **httpx** — async HTTP client for OpenWeatherMap API
- **pydantic-settings** — config from environment variables / `.env`
- **pytest / pytest-asyncio / pytest-httpx** — testing stack
- **ruff** — linting and formatting

## Running

```bash
uv sync                                          # install dependencies
uv run pytest                                     # run all tests
uv run pytest -m unit                             # unit tests only
uv run pytest -m integration                      # integration tests only
uv run ruff check src/ tests/                     # lint
uv run ruff format src/ tests/                    # format
uv run uvicorn weather_app.main:app --reload      # start dev server
```
