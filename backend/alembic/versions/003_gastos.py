"""Create gastos_adicionales table

Revision ID: 003
Revises: 002
Create Date: 2026-07-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    direccion_gasto = postgresql.ENUM("entrada", "salida", name="direccion_gasto")
    direccion_gasto.create(op.get_bind(), checkfirst=True)

    direccion_col = postgresql.ENUM(
        "entrada", "salida", name="direccion_gasto", create_type=False
    )

    op.create_table(
        "gastos_adicionales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "escritura_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("escrituras.id"),
            nullable=False,
        ),
        sa.Column("concepto", sa.String(500), nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("direccion", direccion_col, nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_gastos_adicionales_escritura_id", "gastos_adicionales", ["escritura_id"])
    op.create_index("ix_gastos_adicionales_fecha", "gastos_adicionales", ["fecha"])


def downgrade() -> None:
    op.drop_index("ix_gastos_adicionales_fecha", table_name="gastos_adicionales")
    op.drop_index("ix_gastos_adicionales_escritura_id", table_name="gastos_adicionales")
    op.drop_table("gastos_adicionales")
    op.execute("DROP TYPE IF EXISTS direccion_gasto")
