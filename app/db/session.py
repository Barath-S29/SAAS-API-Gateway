from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# One engine per process. Manages a connection pool under the hood —
# connections are reused across requests rather than opened/closed
# per query. This is the "connection pooling" concept from the roadmap.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# sessionmaker produces new Session objects bound to this engine.
# autoflush/autocommit left at SQLAlchemy 2.0 defaults (autocommit
# removed entirely in 2.0 — commits are always explicit).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields one Session per request, always closed
    afterward even if the request raises. Not used until Phase 3's
    route handlers, but defined here alongside the engine it depends on.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()