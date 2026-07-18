"""Create liquidaciones_mensuales and pagos_salario tables

Revision ID: 004
Revises: 003
Create Date: 2026-07-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tipo_pago = postgresql.ENUM("escribano", "secretaria", name="tipo_pago_salario")
    tipo_pago.create(op.get_bind(), checkfirst=True)
    tipo_pago_col = postgresql.ENUM(
        "escribano", "secretaria", name="tipo_pago_salario", create_type=False
    )

    op.create_table(
        "liquidaciones_mensuales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("total_costanza", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_gabriel", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_victoria", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_global", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("anio", "mes", name="uq_liquidacion_anio_mes"),
    )

    op.create_table(
        "pagos_salario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "liquidacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("liquidaciones_mensuales.id"),
            nullable=False,
        ),
        sa.Column("persona", sa.String(100), nullable=False),
        sa.Column("tipo", tipo_pago_col, nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("detalle_json", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pagos_salario")
    op.drop_table("liquidaciones_mensuales")
    op.execute("DROP TYPE IF EXISTS tipo_pago_salario")
