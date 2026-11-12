"""widen api_keys key_prefix to 16

Revision ID: 046a59383fd2
Revises: b2358aaf9374
Create Date: 2026-11-12 02:54:48.229278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '046a59383fd2'
down_revision: Union[str, None] = 'b2358aaf9374'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The static key label "gw_live_" is itself 8 characters, so a VARCHAR(8)
    # prefix was identical for every key and the index narrowed nothing.
    # 16 = the label + the first 8 characters of the random secret.
    op.alter_column(
        "api_keys",
        "key_prefix",
        existing_type=sa.String(length=8),
        type_=sa.String(length=16),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Fails by design if any stored prefix is longer than 8 characters:
    # a rollback must never silently truncate data.
    op.alter_column(
        "api_keys",
        "key_prefix",
        existing_type=sa.String(length=16),
        type_=sa.String(length=8),
        existing_nullable=False,
    )
