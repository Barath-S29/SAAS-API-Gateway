import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    """
    A developer account. V1 is 1 user = 1 tenant, so auth fields
    (email, password_hash) live directly on this table rather than
    a separate users table.

    UUID primary key: tenant IDs may eventually appear in URLs/logs
    the tenant can see, so we avoid a sequential, guessable ID.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # argon2id encoded hash string (includes algorithm, params, salt —
    # never store these separately). Hashing itself happens in the
    # auth service layer in Phase 2's identity work, not here.
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    plan_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Both defaults are intentional; do not "clean up" one of them.
    # default=      -> Python-side: SQLAlchemy fills it in, ORM inserts only.
    # server_default -> a real DB-level DEFAULT clause: applies to ANY insert
    #                   (raw SQL, admin scripts, other services). Without it,
    #                   a raw INSERT omitting this column hits NOT NULL.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plan: Mapped["Plan"] = relationship()  # noqa: F821

    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )