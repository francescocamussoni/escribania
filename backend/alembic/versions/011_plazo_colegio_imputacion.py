"""Plazo colegio imputacion + escribano monotributista.

Revision ID: 011
Revises: 010
Create Date: 2026-07-26

Adds imputacion enum to pagos_colegio; backfills existing rows as honorarios_varios.
Adds escribano.monotributista; backfills Costanza as monotributista.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IMPUTACION_ENUM = postgresql.ENUM(
    "total_impuestos",
    "honorarios_varios",
    "otro",
    name="imputacion_pago_colegio",
    create_type=False,
)


def upgrade() -> None:
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
            nullable=False,
            server_default="honorarios_varios",
        ),
    )
    op.execute(sa.text("UPDATE pagos_colegio SET imputacion = 'honorarios_varios'"))
    op.alter_column("pagos_colegio", "imputacion", server_default=None)

    op.add_column(
        "escribano",
        sa.Column("monotributista", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        sa.text(
            "UPDATE escribano SET monotributista = true "
            "WHERE lower(nombre) = 'costanza' AND deleted_at IS NULL"
        )
    )
    op.alter_column("escribano", "monotributista", server_default=None)


def downgrade() -> None:
    op.drop_column("escribano", "monotributista")
    op.drop_column("pagos_colegio", "imputacion")
    op.execute(sa.text("DROP TYPE IF EXISTS imputacion_pago_colegio"))
