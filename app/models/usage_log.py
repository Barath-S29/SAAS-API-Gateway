import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsageLog(Base):
    """
    One row per request that actually reached the "process it" branch
    of the request flow — i.e. the key was valid AND the tenant was
    under their rate limit. 401s (auth_failures_total) and 429s
    (rate_limit_rejections_total) never produce a row here; they're
    metrics only.

    This table is the highest-write-volume table in the schema and the
    sole input to the monthly billing aggregation job.
    """

    __tablename__ = "usage_logs"

    # BIGINT identity, not UUID: this is a pure internal append-log,
    # never exposed to a client, so there's no enumeration concern,
    # and every byte matters more here given the write volume.
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False
    )

    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Nullable is meaningful: NULL means "no upstream call was made"
    # (a cache hit), not "we forgot to record it."
    upstream_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    response_status: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Computed once, at write time, by the request handler — not
    # re-derived later from response_status/upstream_status.
    billable: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # The one index the billing aggregation query depends on:
        # "all billable usage for tenant X between period_start/end".
        Index("ix_usage_logs_tenant_id_created_at", "tenant_id", "created_at"),
    )