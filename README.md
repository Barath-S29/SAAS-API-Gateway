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

## Getting started (current state)

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd gateway

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env with your local Postgres connection string

# 4. Run migrations against a running Postgres instance
alembic upgrade head
```

A `docker-compose.yml` for one-command local setup (Postgres + Redis)
is planned for the Phase 1 foundations work and not yet present.

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


