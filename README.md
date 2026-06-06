# Kenya Farm & Weather Intelligence API

Monorepo for a FastAPI backend integrating the [WeatherAI](https://weather-ai.co) free tier to give Kenyan farmers and extension officers: farm registration, 7-day agro-weather advisory with deterministic risk scoring, operation-specific go/no-go checks, and drone-image tree/canopy analysis paired with weather forecasts.

**Status:** Phases 0–7 complete. Phase 8 (Docker, observability, README) in progress.

| Phase | Feature | Status |
|-------|---------|--------|
| 0 | Scaffolding — FastAPI + SQLAlchemy async + Alembic + Docker | ✅ |
| 1 | Farm CRUD — create/read/update/delete farms | ✅ |
| 2 | Cache + WeatherClient — Redis cache-aside, WeatherAI integration | ✅ |
| 3 | Advisory Engine + Endpoint — 7-day risk scoring, persistence | ✅ |
| 4 | Operation Advisories — spraying/irrigation/harvesting go/no-go | ✅ |
| 5 | Tree Analysis + Quota Guard — AI vision, 100/month free tier | ✅ |
| 6 | Tree Analysis History — paginated GET /tree-analyses | ✅ |
| 7 | Usage Endpoint — aggregated API usage summary | 🔜 |
| 8 | Docker, observability, README | 🔜 |

## Layout
```
kenya_farm_weather_api/
├── backend/           # FastAPI service (this build)
└── frontend/          # placeholder, deferred
```

The full phased build plan lives at `/mnt/e/weatherai_project/.claude/plan/kenya_farm_weather_api_build_plan.md`.

## Backend quick start

All commands run from `backend/`.

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (for Redis)
- A [WeatherAI](https://weather-ai.co) free-tier API key

### Install dependencies
```bash
cd backend
uv venv
uv pip install -e ".[dev]"
```

### Configure environment
Create `backend/.env` with:
```dotenv
WEATHERAI_API_KEY=your-key-here
WEATHERAI_BASE_URL=https://api.weather-ai.co
WEATHERAI_TIMEOUT_S=10
APP_ENV=development
LOG_LEVEL=info
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
WEATHERAI_RATE_LIMIT_WARN=100
TREE_IMAGE_MAX_MB=20
TREE_QUOTA_LIMIT=100
OPENAI_API_KEY=your-key-here   # for tree image analysis
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Start Redis
```bash
cd backend
docker compose up -d redis
```

### Run the API
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Swagger UI: <http://localhost:8000/docs>

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
| GET | `/api/v1/farms/{id}/operations/{type}` | Operation go/no-go (spraying/irrigation/harvesting) |
| POST | `/api/v1/farms/{id}/tree-analysis` | Upload tree image for AI health analysis |
| GET | `/api/v1/farms/{id}/tree-analyses` | Tree analysis history (paginated) |
| GET | `/api/v1/farms/{id}/quota` | Tree analysis quota usage |
| GET | `/api/v1/usage` | Aggregated API usage summary |

## Tests
```bash
cd backend
source .venv/bin/activate
pytest -q
pytest --cov=app --cov-report=term-missing
```

## Backend module layout
```
backend/app/
├── main.py             # FastAPI app factory
├── core/               # config + database engine/session
├── utils/              # exception handlers, helpers
├── models/             # SQLAlchemy ORM
├── routers/            # FastAPI routers
├── schemas/            # Pydantic v2 schemas
└── services/           # external clients + business logic
```