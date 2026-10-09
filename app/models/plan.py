from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Plan(Base):
    """
    Rate limit + pricing tier (Free, Pro). Treated as immutable in
    practice: a price/limit change is a new row, never an UPDATE of
    an existing one, so that past invoices (which snapshot the price
    they charged) stay correct even if pricing changes later.
    """

    __tablename__ = "plans"

    # SMALLINT is deliberate: plans is tiny, admin-only reference data
    # (a handful of rows, ever), unlike tenants/api_keys/invoices which
    # use UUID. Keeping this narrow keeps every FK that references it
    # (tenants.plan_id) narrow too.
    id: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    requests_per_day: Mapped[int] = mapped_column(Integer, nullable=False)

    # Price per request in micro-dollars (1/1,000,000 of a dollar).
    # Stored as an integer, never a float, to avoid floating-point
    # rounding error accumulating across millions of rows.
    unit_price_micros: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("requests_per_day > 0", name="requests_per_day_positive"),
        CheckConstraint(
            "unit_price_micros >= 0", name="unit_price_micros_non_negative"
        ),
    )