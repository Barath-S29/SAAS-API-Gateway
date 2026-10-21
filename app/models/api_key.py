import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApiKey(Base):
    """
    Gateway authentication credential, belonging to a tenant.

    The raw key is never stored. key_hash is a fast cryptographic hash
    (SHA-256, computed in the auth service — not here) of the full raw
    key; key_prefix is a short plaintext slice used purely to narrow an
    indexed lookup before the hash comparison. See the api_keys design
    walkthrough for why this differs from password hashing (argon2).
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)

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
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )