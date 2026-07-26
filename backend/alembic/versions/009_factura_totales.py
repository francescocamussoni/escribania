"""Factura principal totales resumen (dif_honorarios, total_parcial, total_sin_iva, iva).

Revision ID: 009
Revises: 008
Create Date: 2026-07-26

Steps (upgrade):
  1. Add totales columns (nullable).
  2. Backfill from existing line items via calcular_totales_factura.
  3. Update total_factura to Total + IVA.
  4. Set columns NOT NULL.

Steps (downgrade):
  Drop new columns (total_factura values are not restored to legacy formula).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS = (
    "dif_honorarios",
    "total_parcial",
    "total_sin_iva",
    "iva",
)


def _backfill_totales(connection: sa.Connection) -> None:
    from services.calculo_factura import calcular_totales_factura

    facturas = connection.execute(
        sa.text(
            """
            SELECT
                id,
                suma_hon_cert,
                aporte_12pct,
                subtotal_honorarios,
                total_impuestos,
                total_gastos_admin,
                fotocopias_urgentes,
                informes_notariales,
                municipio,
                ii_certificados,
                catastro
            FROM facturas_principales
            """
        )
    ).mappings()

    for row in facturas:
        gastos = {
            "fotocopias_urgentes": Decimal(str(row["fotocopias_urgentes"])),
            "informes_notariales": Decimal(str(row["informes_notariales"])),
            "municipio": Decimal(str(row["municipio"])),
            "ii_certificados": Decimal(str(row["ii_certificados"])),
            "catastro": Decimal(str(row["catastro"])),
            "total_gastos_admin": Decimal(str(row["total_gastos_admin"])),
        }
        totales = calcular_totales_factura(
            suma_hon_cert=Decimal(str(row["suma_hon_cert"])),
            aporte_12pct=Decimal(str(row["aporte_12pct"])),
            subtotal_honorarios=Decimal(str(row["subtotal_honorarios"])),
            total_impuestos=Decimal(str(row["total_impuestos"])),
            total_gastos_admin=Decimal(str(row["total_gastos_admin"])),
            gastos=gastos,
        )
        connection.execute(
            sa.text(
                """
                UPDATE facturas_principales
                SET
                    dif_honorarios = :dif_honorarios,
                    total_parcial = :total_parcial,
                    total_sin_iva = :total_sin_iva,
                    iva = :iva,
                    total_factura = :total_factura
                WHERE id = :id
                """
            ),
            {"id": row["id"], **totales},
        )


def upgrade() -> None:
    for column in _NEW_COLUMNS:
        op.add_column(
            "facturas_principales",
            sa.Column(column, sa.Numeric(18, 2), nullable=True),
        )

    connection = op.get_bind()
    _backfill_totales(connection)

    for column in _NEW_COLUMNS:
        op.alter_column("facturas_principales", column, nullable=False)


def downgrade() -> None:
    for column in reversed(_NEW_COLUMNS):
        op.drop_column("facturas_principales", column)
