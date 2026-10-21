# SaaS API Gateway

A single-provider SaaS API gateway in front of OpenWeatherMap: JWT auth,
per-tenant API keys, Redis-backed rate limiting and response caching,
async usage-based billing via Celery, and production-oriented
observability (structured logging, Prometheus/Grafana).

Built as a learning project to demonstrate backend engineering
fundamentals - concurrency-safe rate limiting, cache correctness,
idempotent async billing - not as a commercial product. Full V1 scope
and non-goals are documented in [`docs/architecture_decisions.md`](docs/architecture_decisions.md).

## Status

**Phase 2 (Database & Identity) - in progress.**
SQLAlchemy models and the initial Alembic migration are complete and
tested against a real Postgres instance. Auth endpoints (signup/login)
and the gateway proxy are not yet implemented.

## Stack

FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · Redis · Celery ·
argon2-cffi · Docker · Nginx · GitHub Actions · Pytest · Loguru ·
Prometheus/Grafana

## Getting started 

Requires Python 3.12 and Docker Desktop.

```bash

git clone https://github.com/Barath-S29/SAAS-API-Gateway.git && cd SAAS-API-Gateway

python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux / macOS
pip install -r requirements.txt

cp .env.example .env                # Windows: Copy-Item .env.example .env
docker compose up -d                # Postgres 18 + Redis 8.6, localhost only
alembic upgrade head                # schema + seeded Free/Pro plans
```

If port 5432 is already in use or reserved on your machine, set `POSTGRES_PORT`
in `.env` (for example `5433`) and use the same port in `DATABASE_URL`.

## Project structure (target - V1 complete)

Not everything below exists yet; this is the structure the project is
building toward. Directories without files yet contain a `.gitkeep`.

```
gateway/
├── .github/
│   └── workflows/
│       └── ci.yml              # lint, test, build, deploy (Phase 7)
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── core/
│   │   ├── config.py            # Settings (env-driven)
│   │   └── logging.py           # Loguru setup (Phase 8)
│   ├── db/
│   │   ├── base.py              # Declarative Base + naming convention
│   │   └── session.py           # Engine, session factory, get_db()
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── plan.py
│   │   ├── api_key.py
│   │   ├── usage_log.py
│   │   └── invoice.py
│   ├── api/
│   │   ├── auth.py              # signup/login (Phase 2)
│   │   ├── keys.py              # API key issuance/revocation (Phase 2)
│   │   └── gateway.py           # weather proxy endpoint (Phase 3)
│   ├── services/
│   │   ├── auth_service.py      # argon2 hashing, JWT issuance (Phase 2)
│   │   ├── rate_limiter.py      # Redis sliding-window limiter (Phase 4)
│   │   ├── cache.py             # Redis response cache (Phase 5)
│   │   ├── upstream.py          # OpenWeatherMap client (Phase 3)
│   │   └── billing.py           # aggregation + invoice generation (Phase 7)
│   └── workers/
│       └── celery_app.py        # Celery app + Beat schedule (Phase 7)
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── <hash>_initial_schema.py
├── alembic.ini
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/
│   └── architecture-decisions.md   # locked-in V1 decisions, kept in sync with /projects memory
├── docker-compose.yml           # Postgres + Redis (+ Celery, MinIO later) for local dev
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## License


