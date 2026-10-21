"""seed plans (free, pro)

Revision ID: b2358aaf9374
Revises: 73ab33638a56
Create Date: 2026-10-09 02:40:08.034072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2358aaf9374'
down_revision: Union[str, None] = '73ab33638a56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# A lightweight table definition, deliberately NOT imported from app.models.
# A migration is a frozen snapshot of what the schema looked like at this
# point in history. If it imported the live ORM model, a later change to
# that model (a renamed or removed column) would silently break this old
# migration when it is replayed on a fresh database.
plans = sa.table(
    "plans",
    sa.column("name", sa.String),
    sa.column("requests_per_day", sa.Integer),
    sa.column("unit_price_micros", sa.BigInteger),
)


def upgrade() -> None:
    # Reference data, seeded here rather than in app startup code so that
    # schema and seed data are versioned together and repeatable on every
    # environment. unit_price_micros is micro-dollars: 500 = $0.0005/request.
    op.bulk_insert(
        plans,
        [
            {"name": "free", "requests_per_day": 100, "unit_price_micros": 0},
            {"name": "pro", "requests_per_day": 5000, "unit_price_micros": 500},
        ],
    )


def downgrade() -> None:
    # Fails by design if any tenant still references these plans
    # (tenants.plan_id is ON DELETE RESTRICT): we never want a rollback to
    # silently orphan tenants or billing history.
    op.execute("DELETE FROM plans WHERE name IN ('free', 'pro')")