import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Invoice(Base):
    """
    One invoice per tenant per billing period. The UNIQUE constraint
    on (tenant_id, billing_period_start, billing_period_end) is the
    actual idempotency mechanism for the billing job: the Celery task
    always attempts an INSERT, and treats a unique-violation as "this
    period is already billed," never checking existence first.

    unit_price_micros_charged snapshots the plan's price at generation
    time — this is what makes "plans are immutable" a real guarantee:
    a later price change on the plan row can never alter a past
    invoice's amount.
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)

    total_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_micros_charged: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # pending: aggregation done, PDF/S3 not yet complete
    # generated: PDF generated and uploaded to S3 successfully
    # failed: generation attempted and failed (surfaced via logs/metrics;
    #         no automatic retry in V1 — fixed manually)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending", server_default="pending"
    )

    # NULL until status = 'generated' — meaningful absence, not an
    # oversight, same principle as usage_logs.upstream_status.
    pdf_s3_key: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "billing_period_start",
            "billing_period_end",
            name="uq_invoices_tenant_period",
        ),
        CheckConstraint(
            "status in ('pending', 'generated', 'failed')",
            name="status_valid_values",
        ),
    )