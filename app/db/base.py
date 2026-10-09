from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Explicit naming convention for constraints and indexes.
# Without this, Postgres/SQLAlchemy auto-generate names that can differ
# across versions or environments, which makes Alembic migrations that
# need to reference a constraint by name (e.g. to drop it) fragile.
# This convention is a common, documented SQLAlchemy pattern.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Shared declarative base. Every model inherits from this so that
    Base.metadata collects all tables in one place — this is what
    Alembic's env.py points at for autogenerate.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)