"""Pagos cliente/colegio: replace gastos_adicionales with real cash tables.

Revision ID: 006
Revises: 005
Create Date: 2026-07-20

Steps (upgrade):
  1. Create tables `pagos_cliente` and `pagos_colegio` with indexes and monto > 0 checks.
  2. Migrate `gastos_adicionales` WHERE direccion = 'entrada' → `pagos_cliente`.
  3. Migrate `gastos_adicionales` WHERE direccion = 'salida' → `pagos_colegio`.
  4. Insert implicit 100% client payments for closed escrituras without `pagos_cliente` (FR-035).
  5. Drop `gastos_adicionales` and enum `direccion_gasto`.

Steps (downgrade):
  Recreate `gastos_adicionales`, migrate pagos back (excluding implicit migration rows), drop new tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IMPLICIT_PAYMENT_CONCEPT = "Migración: pago implícito al cierre"

_PAGO_TABLE_COLUMNS = (
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    sa.Column(
        "escritura_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("escrituras.id"),
        nullable=False,
    ),
    sa.Column("monto", sa.Numeric(18, 2), nullable=False),
    sa.Column("fecha", sa.Date(), nullable=False),
    sa.Column("concepto", sa.String(500), nullable=False, server_default=""),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
)


def _create_pago_table(table_name: str, monto_check_name: str) -> None:
    op.create_table(
        table_name,
        *_PAGO_TABLE_COLUMNS,
        sa.CheckConstraint("monto > 0", name=monto_check_name),
    )
    op.create_index(f"ix_{table_name}_escritura_id", table_name, ["escritura_id"])
    op.create_index(f"ix_{table_name}_fecha", table_name, ["fecha"])


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create pagos_cliente and pagos_colegio
    # -------------------------------------------------------------------------
    _create_pago_table("pagos_cliente", "ck_pagos_cliente_monto_positive")
    _create_pago_table("pagos_colegio", "ck_pagos_colegio_monto_positive")

    bind = op.get_bind()

    # -------------------------------------------------------------------------
    # 2. Migrate entrada gastos → pagos_cliente
    # -------------------------------------------------------------------------
    entrada_count = bind.execute(
        sa.text(
            """
            INSERT INTO pagos_cliente (id, escritura_id, monto, fecha, concepto, created_at)
            SELECT id, escritura_id, monto, fecha, concepto, created_at
            FROM gastos_adicionales
            WHERE direccion = 'entrada'
            """
        )
    ).rowcount
    print(f"Migrated {entrada_count} gastos entrada → pagos_cliente")

    # -------------------------------------------------------------------------
    # 3. Migrate salida gastos → pagos_colegio
    # -------------------------------------------------------------------------
    salida_count = bind.execute(
        sa.text(
            """
            INSERT INTO pagos_colegio (id, escritura_id, monto, fecha, concepto, created_at)
            SELECT id, escritura_id, monto, fecha, concepto, created_at
            FROM gastos_adicionales
            WHERE direccion = 'salida'
            """
        )
    ).rowcount
    print(f"Migrated {salida_count} gastos salida → pagos_colegio")

    # -------------------------------------------------------------------------
    # 4. Implicit 100% payments for closed escrituras without client payments (FR-035)
    # -------------------------------------------------------------------------
    implicit_count = bind.execute(
        sa.text(
            f"""
            INSERT INTO pagos_cliente (id, escritura_id, monto, fecha, concepto, created_at)
            SELECT
                gen_random_uuid(),
                e.id,
                fp.total_factura,
                COALESCE(e.closed_at::date, e.created_at::date),
                :concepto,
                now()
            FROM escrituras e
            INNER JOIN facturas_principales fp ON fp.escritura_id = e.id
            WHERE e.estado = 'cerrada'
              AND NOT EXISTS (
                  SELECT 1 FROM pagos_cliente pc WHERE pc.escritura_id = e.id
              )
            """
        ),
        {"concepto": IMPLICIT_PAYMENT_CONCEPT},
    ).rowcount
    print(f"Inserted {implicit_count} implicit payments for closed escrituras")

    # -------------------------------------------------------------------------
    # 5. Drop legacy gastos_adicionales
    # -------------------------------------------------------------------------
    op.drop_index("ix_gastos_adicionales_fecha", table_name="gastos_adicionales")
    op.drop_index("ix_gastos_adicionales_escritura_id", table_name="gastos_adicionales")
    op.drop_table("gastos_adicionales")
    op.execute(sa.text("DROP TYPE IF EXISTS direccion_gasto"))
    print("Dropped gastos_adicionales")
    print("OK")


def downgrade() -> None:
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

    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            INSERT INTO gastos_adicionales (id, escritura_id, concepto, monto, direccion, fecha, created_at)
            SELECT id, escritura_id, concepto, monto, 'entrada', fecha, created_at
            FROM pagos_cliente
            WHERE concepto != :concepto
            """
        ),
        {"concepto": IMPLICIT_PAYMENT_CONCEPT},
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO gastos_adicionales (id, escritura_id, concepto, monto, direccion, fecha, created_at)
            SELECT id, escritura_id, concepto, monto, 'salida', fecha, created_at
            FROM pagos_colegio
            """
        )
    )

    op.drop_index("ix_pagos_colegio_fecha", table_name="pagos_colegio")
    op.drop_index("ix_pagos_colegio_escritura_id", table_name="pagos_colegio")
    op.drop_table("pagos_colegio")

    op.drop_index("ix_pagos_cliente_fecha", table_name="pagos_cliente")
    op.drop_index("ix_pagos_cliente_escritura_id", table_name="pagos_cliente")
    op.drop_table("pagos_cliente")
