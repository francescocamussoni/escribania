"""Gastos extraordinarios de la escribanía (sin escritura asociada).

Revision ID: 008
Revises: 007
Create Date: 2026-07-20

Steps (upgrade):
  1. Create table `gastos_extraordinarios` with index on `fecha`.

Steps (downgrade):
  Drop table `gastos_extraordinarios`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gastos_extraordinarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concepto", sa.String(500), nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("monto > 0", name="ck_gastos_extraordinarios_monto_positive"),
        sa.CheckConstraint(
            "length(trim(concepto)) > 0",
            name="ck_gastos_extraordinarios_concepto_not_empty",
        ),
    )
    op.create_index(
        "ix_gastos_extraordinarios_fecha",
        "gastos_extraordinarios",
        ["fecha"],
    )


def downgrade() -> None:
    op.drop_index("ix_gastos_extraordinarios_fecha", table_name="gastos_extraordinarios")
    op.drop_table("gastos_extraordinarios")
