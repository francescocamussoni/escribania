"""Rename escribano Victoria to Monica.

Revision ID: 010
Revises: 009
Create Date: 2026-07-26

Victoria was replaced by Monica in the escribanía roster.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE escribano SET nombre = 'Monica' WHERE nombre = 'Victoria'"))
    op.execute(
        sa.text("UPDATE escrituras SET escribano_nombre = 'Monica' WHERE escribano_nombre = 'Victoria'")
    )
    op.alter_column("liquidaciones_mensuales", "total_victoria", new_column_name="total_monica")


def downgrade() -> None:
    op.alter_column("liquidaciones_mensuales", "total_monica", new_column_name="total_victoria")
    op.execute(sa.text("UPDATE escrituras SET escribano_nombre = 'Victoria' WHERE escribano_nombre = 'Monica'"))
    op.execute(sa.text("UPDATE escribano SET nombre = 'Victoria' WHERE nombre = 'Monica'"))
