# Farm Intelligence

Backend service that combines WeatherAI's weather forecasting and agroforestry image analysis into actionable farm-level advisories for Kenyan farms (tea, maize, coffee, beans, vegetables). Built with FastAPI, SQLAlchemy async, Redis, and Docker.

## What it does

Given a registered farm (coordinates + crop type), the API:

- Generates a **7-day agro-weather advisory** with deterministic risk scores for rain, heat, wind, and irrigation need
- Answers **operation go/no-go questions** — is today safe for spraying, irrigation, harvesting, planting, or field work?
- **Analyzes tree health** from drone/aerial images via WeatherAI tree analysis API (tree count, canopy health, observations), optionally paired with current weather in a single response
- **Persists all results** so history can be compared over time
- **Guards free-tier quota** — caches weather responses, proxies tree quota to WeatherAI upstream, blocks when limit is reached

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/farms` | Register a farm |
| GET | `/api/v1/farms` | List farms (paginated) |
| GET | `/api/v1/farms/{id}` | Get farm |
| PUT | `/api/v1/farms/{id}` | Update farm |
| DELETE | `/api/v1/farms/{id}` | Delete farm |
| GET | `/api/v1/farms/{id}/advisory` | 7-day weather advisory with risk scores |
| GET | `/api/v1/farms/{id}/advisories` | Advisory history (paginated) |
| GET | `/api/v1/farms/{id}/operations/{type}` | Go/no-go for 5 operations (spraying/irrigation/harvesting/planting/field_work) |
| POST | `/api/v1/farms/{id}/tree-analysis` | Upload tree image for AI health analysis (with_weather=true fetches weather in parallel) |
| GET | `/api/v1/farms/{id}/tree-analyses` | Tree analysis history (paginated) |
| GET | `/api/v1/farms/{id}/quota` | Tree analysis quota from WeatherAI |
| GET | `/api/v1/weather-ai/usage` | Three quota families (api/ai/trees) + status band |
| GET | `/health` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks DB + Redis) |

## Risk scoring

Each day is scored across four factors (max 100 total):

| Factor | Max pts | Thresholds |
|--------|---------|------------|
| Rain | 40 | ≥70% → 40 · ≥40% → 20 · else → 0 |
| Heat | 25 | ≥35°C → 25 · ≥30°C → 12 · else → 0 |
| Wind | 20 | ≥30 km/h → 20 · ≥15 km/h → 10 · else → 0 |
| Humidity | 15 | ≥85% → 15 · ≥65% → 7 · else → 0 |

Overall band: `low` (0–30) · `medium` (31–65) · `high` (66+)

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Docker (for Redis)

### Install dependencies

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
```

### Configure environment

Create `backend/.env`:

```dotenv
# WeatherAI
WEATHERAI_API_KEY=your-weatherai-key
WEATHERAI_BASE_URL=https://api.weather-ai.co
WEATHERAI_TIMEOUT_S=10

# App
APP_ENV=development
LOG_LEVEL=info

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# Cache
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0

# Tree analysis (WeatherAI — 5 free analyses/month)
TREE_IMAGE_MAX_MB=20
```

### Start Redis

```bash
cd backend
docker compose up -d redis
```

### Run migrations

```bash
cd backend
alembic upgrade head
```

### Start the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Swagger UI: <http://localhost:8000/docs>

## Tests

```bash
cd backend
pytest -q
pytest --cov=app --cov-report=term-missing
```

## Deploy backend on Render

This repo includes `render.yaml` for deploying the FastAPI backend as a Render
web service. Use Supabase Postgres for production data; do not use SQLite on
Render free services because their local filesystem is ephemeral.

### Required Render environment variables

Set these on the Render service:

```dotenv
APP_ENV=production
WEATHERAI_API_KEY=your-weatherai-key
DATABASE_URL=postgresql://postgres:<password>@<supabase-host>:5432/postgres?sslmode=require
REDIS_URL=rediss://default:<password>@<upstash-host>:6379
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
ALLOWED_HOSTS=your-render-service.onrender.com
```

`DATABASE_URL` can be the Supabase connection string. The app normalizes
`postgresql://` to SQLAlchemy's async `postgresql+asyncpg://` driver at runtime.
`CORS_ALLOWED_ORIGINS` controls which browser origins can call the API.
`ALLOWED_HOSTS` controls which HTTP Host headers the API accepts; include your
Render service hostname, without `https://`.

Render commands from `render.yaml`:

```bash
pip install --upgrade pip && pip install -e .
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deployment, check:

```text
https://<render-service>.onrender.com/health
https://<render-service>.onrender.com/health/ready
```

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── core/
│   │   ├── config.py        # pydantic-settings + dotenv
│   │   ├── database.py      # SQLAlchemy async engine + session
│   │   └── cache.py        # Redis cache (fakeredis for tests)
│   ├── middleware/
│   │   └── logging.py      # Request ID + structured JSON logs
│   ├── models/             # SQLAlchemy ORM (Farm, Advisory, TreeAnalysis, WeatherApiLog)
│   ├── routers/           # FastAPI routers (farms, advisories, trees, usage)
│   ├── schemas/           # Pydantic v2 request/response schemas
│   ├── services/
│   │   ├── weather_client.py    # WeatherAI integration + cache-aside + call logging
│   │   ├── advisory_engine.py   # Deterministic risk scoring + operation windows
│   │   ├── quota_guard.py      # Proxies tree quota to WeatherAI upstream (no local writes)
│   │   └── tree_client.py       # WeatherAI tree analysis proxy
│   └── utils/
│       └── exceptions.py   # Custom exception handlers
├── migrations/             # Alembic schema migrations
├── tests/                 # pytest + AsyncMock
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Tech stack

| Component | Choice |
|-----------|--------|
| Backend | FastAPI (async) |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy 2.0 async |
| Cache | Redis (prod) / in-memory dict (dev) |
| HTTP client | httpx.AsyncClient |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio |
| Containerisation | Docker + Docker Compose |
