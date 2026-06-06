# Farm Intelligence

Backend service that combines WeatherAI's weather forecasting and agroforestry image analysis into actionable farm-level advisories. Built with FastAPI, SQLAlchemy async, Redis, and Docker.

## What it does

Given a registered farm (coordinates + crop type), the API:

- Generates a **7-day agro-weather advisory** with deterministic risk scores for rain, heat, wind, and irrigation need
- Answers **operation go/no-go questions** — is today safe for spraying, irrigation, or harvesting?
- **Analyzes tree health** from drone/aerial images using AI vision (OpenAI GPT-4o-mini), paired with the farm's weather forecast in a single response
- **Persists all results** so history can be compared over time
- **Guards free-tier quota** — caches weather responses, blocks tree analysis when monthly limit is reached

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
| GET | `/api/v1/farms/{id}/operations/{type}` | Go/no-go for spraying / irrigation / harvesting |
| POST | `/api/v1/farms/{id}/tree-analysis` | Upload tree image for AI health analysis |
| GET | `/api/v1/farms/{id}/tree-analyses` | Tree analysis history (paginated) |
| GET | `/api/v1/farms/{id}/quota` | Tree analysis quota usage |
| GET | `/api/v1/usage` | Aggregated API usage summary |
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

# Tree analysis (OpenAI)
OPENAI_API_KEY=your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
TREE_IMAGE_MAX_MB=20
TREE_QUOTA_LIMIT=100
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
│   ├── models/             # SQLAlchemy ORM (Farm, Advisory, QuotaRecord, TreeAnalysis)
│   ├── routers/           # FastAPI routers (farms, advisories, trees, usage)
│   ├── schemas/           # Pydantic v2 request/response schemas
│   ├── services/
│   │   ├── weather_client.py    # WeatherAI integration + cache-aside
│   │   ├── advisory_engine.py   # Deterministic risk scoring
│   │   ├── quota_guard.py      # Monthly quota tracking per farm
│   │   └── tree_client.py       # OpenAI Vision tree analysis
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