# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`backend/` is a FastAPI async API implementing WeatherAI — proxying WeatherAI weather forecasts and tree analysis into actionable farm-level advisories for Kenyan farms (tea, maize, coffee, beans, vegetables).

## Dev Commands

```bash
cd backend

# Install
uv venv
uv pip install -e ".[dev]"

# Lint
ruff check app/ tests/

# Type check
ruff check app/  # configured as type-checking surrogate (py312)

# Tests (113 tests, 79%+ coverage, fail_under=79)
pytest -q                    # all tests
pytest tests/test_farms.py   # single file
pytest -q --cov=app --cov-report=term-missing

# Migrations
alembic upgrade head

# Run (requires Redis)
docker compose up -d redis
uvicorn app.main:app --reload --port 8000
```

## Architecture

### Request Flow
- `app/main.py:create_app()` — FastAPI factory, wires routers, middleware, exception handlers
- Routers (`app/routers/`) — HTTP layer, parse request/response, call service layer
- Services (`app/services/`) — business logic, external API calls, scoring
- Models (`app/models/`) — SQLAlchemy ORM, one file per table
- Schemas (`app/schemas/`) — Pydantic v2 DTOs, one file per resource

### Database
- SQLAlchemy 2.0 async with aiosqlite (dev) / PostgreSQL (prod)
- Global `_engine` and `_sessionmaker` cached on module level
- `get_db()` dependency yields session, auto-commits on success, rolls back on exception
- Tests override `get_db` with per-test in-memory SQLite via `StaticPool`

### Cache
- `RedisCache` in `app/core/cache.py` wraps `redis.asyncio`
- Weather responses cached-aside by `WeatherClient`
- `fakeredis` used in tests

### External Integrations
- **WeatherAI** (`app/services/weather_client.py`) — `get_daily(lat, lon)` returns 7-day forecast, cache-aside with TTL
- **WeatherAI Tree Analysis** (`app/services/tree_client.py`) — `TreeAnalysisClient.analyze_tree_image()` sends multipart form-data to `/v1/trees/analyze`, returns tree count, canopy health, observations

### Quota Guard
- `QuotaGuard` in `app/services/quota_guard.py` — proxies to WeatherAI `/v1/trees/quota`, no local DB writes; 60s cache
- Limit configurable via `TREE_QUOTA_LIMIT` env var (default 5/month)

### Advisory Scoring
- `app/services/advisory_engine.py` — deterministic, no AI
- Four factors: rain (0–40), heat (0–25), wind (0–20), humidity (0–15) → band: low/medium/high
- `generate_operation_advisory()` for spraying/irrigation/harvesting/planting/field_work go/no-go
- `generate_operation_window()` computes 2-hour best window from hourly forecast

### Middleware
- `RequestIDMiddleware` injects `X-Request-ID` header, logs request start/complete as JSON to stdout
- `setup_logging()` configures root logger with `JsonFormatter`

### Health Probes
- `/health` — liveness, always `{"status": "ok"}`
- `/health/ready` — readiness, checks `SELECT 1` against DB and Redis ping

## Key Patterns

- Async session queries split into separate variable assignments for coverage measurement: `result = await db.execute(...); rows = result.scalars().all()` instead of chained
- `httpx.AsyncClient` used as context manager in each request handler (not injected as dep) to avoid transport sharing issues
- All external HTTP calls raise `HTTPStatusError` caught and re-raised as FastAPI `HTTPException` with appropriate status code