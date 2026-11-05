"""Pagos colegio tipo + factura lineas deshabilitadas.

Revision ID: 012
Revises: 011
Create Date: 2026-07-26

Steps (upgrade):
  1. Add facturas_principales.lineas_deshabilitadas JSONB default [].
  2. Create tipo_pago_escribania enum; add pagos_colegio.tipo.
  3. Backfill tipo from imputacion.
  4. Drop pagos_colegio.imputacion and imputacion_pago_colegio enum.

Steps (downgrade):
  Restore imputacion enum/column; drop tipo and lineas_deshabilitadas.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPO_ENUM = postgresql.ENUM(
    "colegio",
    "otros",
    name="tipo_pago_escribania",
    create_type=False,
)

IMPUTACION_ENUM = postgresql.ENUM(
    "total_impuestos",
    "honorarios_varios",
    "otro",
    name="imputacion_pago_colegio",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "facturas_principales",
        sa.Column(
            "lineas_deshabilitadas",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.alter_column("facturas_principales", "lineas_deshabilitadas", server_default=None)

    tipo_type = postgresql.ENUM(
        "colegio",
        "otros",
        name="tipo_pago_escribania",
    )
    tipo_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "pagos_colegio",
        sa.Column("tipo", TIPO_ENUM, nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE pagos_colegio SET tipo = 'colegio' "
            "WHERE imputacion IN ('total_impuestos', 'honorarios_varios')"
        )
    )
    op.execute(sa.text("UPDATE pagos_colegio SET tipo = 'otros' WHERE imputacion = 'otro'"))
    op.alter_column("pagos_colegio", "tipo", nullable=False)

    op.drop_column("pagos_colegio", "imputacion")
    op.execute(sa.text("DROP TYPE IF EXISTS imputacion_pago_colegio"))


def downgrade() -> None:
    imputacion_type = postgresql.ENUM(
        "total_impuestos",
        "honorarios_varios",
        "otro",
        name="imputacion_pago_colegio",
    )
    imputacion_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "pagos_colegio",
        sa.Column(
            "imputacion",
            IMPUTACION_ENUM,
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE pagos_colegio SET imputacion = 'total_impuestos' WHERE tipo = 'colegio'"
        )
    )
    op.execute(sa.text("UPDATE pagos_colegio SET imputacion = 'otro' WHERE tipo = 'otros'"))
    op.alter_column("pagos_colegio", "imputacion", nullable=False)

    op.drop_column("pagos_colegio", "tipo")
    op.execute(sa.text("DROP TYPE IF EXISTS tipo_pago_escribania"))

    op.drop_column("facturas_principales", "lineas_deshabilitadas")
