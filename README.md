# Farm Intelligence

Farm Intelligence is a full-stack farm operations dashboard for Kenyan farms. It combines a React frontend with a FastAPI backend that registers farms, generates weather-based advisories, answers operation go/no-go questions, analyzes tree images, and tracks WeatherAI quota usage.

## Live links

- App: <https://farmintelligence.vercel.app/>
- API: <https://kenya-farm-weather-api.onrender.com>
- API docs: <https://kenya-farm-weather-api.onrender.com/docs>
- Health check: <https://kenya-farm-weather-api.onrender.com/health>

## Features

- Register, view, edit, and delete farms with county, crop, coordinates, and farm size.
- Generate 7-day agro-weather advisories with deterministic risk scoring.
- Check operation safety for spraying, irrigation, harvesting, planting, and field work.
- Upload tree imagery for WeatherAI tree analysis, optionally paired with current weather.
- View advisory history, tree analysis history, and quota/usage status.
- Run locally with Docker Compose or separate frontend/backend dev servers.

## Repository layout

```text
.
├── backend/              # FastAPI API, SQLAlchemy models, Alembic migrations, tests
├── frontend/             # React + Vite + TanStack Router dashboard
├── docker-compose.yml    # Local API + frontend + Redis stack
├── render.yaml           # Render backend deployment
└── README.md
```

## Tech stack

| Area | Stack |
| --- | --- |
| Frontend | React 19, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, shadcn-style components |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic |
| Storage | SQLite for local Docker/dev, PostgreSQL for production |
| Cache | Redis |
| External APIs | WeatherAI weather and tree analysis APIs |
| Tooling | Bun frontend lockfile, uv backend workflow, pytest, Vitest, ESLint |
| Deployment | Vercel frontend, Render backend |

## Local setup with Docker

Create `backend/.env` first:

```dotenv
APP_ENV=development
LOG_LEVEL=info

WEATHERAI_API_KEY=your-weatherai-key
WEATHERAI_BASE_URL=https://api.weather-ai.co
WEATHERAI_TIMEOUT_S=10

CACHE_BACKEND=redis
TREE_IMAGE_MAX_MB=20
```

Then run the full stack:

```bash
docker compose up --build
```

Local services:

- Frontend: <http://localhost:3000>
- API: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- Redis: `localhost:6379`

The Compose setup injects:

- Browser API URL: `VITE_API_BASE_URL=http://localhost:8000`
- Container-to-container API URL: `API_INTERNAL_BASE_URL=http://api:8000`
- API CORS origins for local frontend ports.

## Manual development

### Backend

Prerequisites:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Redis

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Useful backend environment variables:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
ALLOWED_HOSTS=localhost,127.0.0.1,test,testserver
```

### Frontend

Prerequisites:

- Bun

Create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
API_INTERNAL_BASE_URL=http://localhost:8000
```

Run the dev server:

```bash
cd frontend
bun install
bun run dev
```

## API reference

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/farms` | Register a farm |
| `GET` | `/api/v1/farms` | List farms |
| `GET` | `/api/v1/farms/{id}` | Get one farm |
| `PUT` | `/api/v1/farms/{id}` | Update a farm |
| `DELETE` | `/api/v1/farms/{id}` | Delete a farm |
| `GET` | `/api/v1/farms/{id}/advisory` | Generate a 7-day weather advisory |
| `GET` | `/api/v1/farms/{id}/advisories` | List advisory history |
| `GET` | `/api/v1/farms/{id}/operations/{type}` | Get operation go/no-go guidance |
| `POST` | `/api/v1/farms/{id}/tree-analysis` | Upload a tree image for analysis |
| `GET` | `/api/v1/farms/{id}/tree-analyses` | List tree analysis history |
| `GET` | `/api/v1/farms/{id}/quota` | Get tree analysis quota |
| `GET` | `/api/v1/weather-ai/usage` | Get WeatherAI usage summary |
| `GET` | `/health` | Liveness probe |
| `GET` | `/health/ready` | Readiness probe for database and Redis |

Operation types:

```text
spraying
irrigation
harvesting
planting
field_work
```

## Risk scoring

Each advisory day is scored from 0 to 100:

| Factor | Max points | Thresholds |
| --- | ---: | --- |
| Rain | 40 | `>=70%` -> 40, `>=40%` -> 20, else 0 |
| Heat | 25 | `>=35 C` -> 25, `>=30 C` -> 12, else 0 |
| Wind | 20 | `>=30 km/h` -> 20, `>=15 km/h` -> 10, else 0 |
| Humidity | 15 | `>=85%` -> 15, `>=65%` -> 7, else 0 |

Risk bands:

- `low`: 0-30
- `medium`: 31-65
- `high`: 66+

## Tests and checks

Backend:

```bash
cd backend
pytest -q
pytest --cov=app --cov-report=term-missing
ruff check .
```

Frontend:

```bash
cd frontend
bun run test
bun run lint
bun run build
```

## Deployment

### Frontend on Vercel

The frontend lives in `frontend/` and includes `frontend/vercel.json`.

Required Vercel environment variables:

```dotenv
VITE_API_BASE_URL=https://kenya-farm-weather-api.onrender.com
API_INTERNAL_BASE_URL=https://kenya-farm-weather-api.onrender.com
```

### Backend on Render

The backend is configured by `render.yaml` and runs from `backend/`.

Required Render environment variables:

```dotenv
APP_ENV=production
WEATHERAI_API_KEY=your-weatherai-key
DATABASE_URL=postgresql://postgres:<password>@<supabase-host>:5432/postgres?sslmode=require
REDIS_URL=rediss://default:<password>@<upstash-host>:6379
CORS_ALLOWED_ORIGINS=https://farmintelligence.vercel.app,http://localhost:3000
ALLOWED_HOSTS=kenya-farm-weather-api.onrender.com
```

Production notes:

- Use Postgres for production data. Render free service disks are ephemeral, so SQLite is only suitable for local development.
- The app normalizes `postgresql://` URLs to SQLAlchemy's async `postgresql+asyncpg://` driver at runtime.
- `CORS_ALLOWED_ORIGINS` controls which browser origins can call the API.
- `ALLOWED_HOSTS` must include the Render hostname without `https://`.

Render commands from `render.yaml`:

```bash
pip install --upgrade pip && pip install -e .
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deployment, check:

```text
https://kenya-farm-weather-api.onrender.com/health
https://kenya-farm-weather-api.onrender.com/health/ready
```

## Backend internals

```text
backend/app/
├── main.py              # FastAPI app factory and middleware
├── core/                # settings, database, cache
├── middleware/          # request ID and structured logging
├── models/              # Farm, Advisory, TreeAnalysis, QuotaRecord, WeatherApiLog
├── routers/             # farms, advisories, trees, usage
├── schemas/             # Pydantic request/response schemas
├── services/            # WeatherAI clients, advisory engine, quota guard
└── utils/               # exception handlers
```
