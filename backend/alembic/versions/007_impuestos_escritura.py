"""Impuestos por escritura: impuestos_escritura and payment tables.

Revision ID: 007
Revises: 006
Create Date: 2026-07-20

Steps (upgrade):
  1. Create enums `tipo_impuesto` and `direccion_prorrateo`.
  2. Create table `impuestos_escritura` with FK to escrituras.
  3. Create tables `pagos_impuesto_cliente` and `pagos_impuesto_escribania`
     with UNIQUE(impuesto_id) and indexes on escritura_id and fecha.

Steps (downgrade):
  Drop payment tables, impuestos_escritura, then enum types.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TIPO_IMPUESTO_VALUES = (
    "API",
    "TGI",
    "AGUAS_SANTAFESINAS",
    "EPE",
    "EXPENSAS",
    "LITORAL_GAS",
)
_DIRECCION_PRORRATEO_VALUES = ("hacia_atras", "hacia_adelante")


def _create_enums() -> tuple[
    postgresql.ENUM,
    postgresql.ENUM,
]:
    tipo_impuesto = postgresql.ENUM(*_TIPO_IMPUESTO_VALUES, name="tipo_impuesto")
    direccion_prorrateo = postgresql.ENUM(
        *_DIRECCION_PRORRATEO_VALUES,
        name="direccion_prorrateo",
    )
    bind = op.get_bind()
    tipo_impuesto.create(bind, checkfirst=True)
    direccion_prorrateo.create(bind, checkfirst=True)

    tipo_impuesto_col = postgresql.ENUM(
        *_TIPO_IMPUESTO_VALUES,
        name="tipo_impuesto",
        create_type=False,
    )
    direccion_prorrateo_col = postgresql.ENUM(
        *_DIRECCION_PRORRATEO_VALUES,
        name="direccion_prorrateo",
        create_type=False,
    )
    return tipo_impuesto_col, direccion_prorrateo_col


def _pago_impuesto_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "impuesto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("impuestos_escritura.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "escritura_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("escrituras.id"),
            nullable=False,
        ),
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
    )


def upgrade() -> None:
    tipo_impuesto_col, direccion_prorrateo_col = _create_enums()

    op.create_table(
        "impuestos_escritura",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "escritura_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("escrituras.id"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_impuesto_col, nullable=False),
        sa.Column("monto_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("periodo_inicio", sa.Date(), nullable=False),
        sa.Column("periodo_fin", sa.Date(), nullable=False),
        sa.Column("fecha_corte", sa.Date(), nullable=False),
        sa.Column("direccion_prorrateo", direccion_prorrateo_col, nullable=False),
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
        sa.CheckConstraint("monto_total > 0", name="ck_impuestos_escritura_monto_positive"),
        sa.CheckConstraint(
            "periodo_fin >= periodo_inicio",
            name="ck_impuestos_escritura_periodo_valido",
        ),
    )
    op.create_index(
        "ix_impuestos_escritura_escritura_id",
        "impuestos_escritura",
        ["escritura_id"],
    )
    op.create_index(
        "ix_impuestos_escritura_tipo_periodo",
        "impuestos_escritura",
        ["tipo", "periodo_inicio", "periodo_fin"],
    )

    op.create_table(
        "pagos_impuesto_cliente",
        *_pago_impuesto_columns(),
        sa.CheckConstraint("monto > 0", name="ck_pagos_impuesto_cliente_monto_positive"),
        sa.UniqueConstraint("impuesto_id", name="uq_pagos_impuesto_cliente_impuesto_id"),
    )
    op.create_index(
        "ix_pagos_impuesto_cliente_escritura_id",
        "pagos_impuesto_cliente",
        ["escritura_id"],
    )
    op.create_index(
        "ix_pagos_impuesto_cliente_fecha",
        "pagos_impuesto_cliente",
        ["fecha"],
    )

    op.create_table(
        "pagos_impuesto_escribania",
        *_pago_impuesto_columns(),
        sa.CheckConstraint("monto > 0", name="ck_pagos_impuesto_escribania_monto_positive"),
        sa.UniqueConstraint("impuesto_id", name="uq_pagos_impuesto_escribania_impuesto_id"),
    )
    op.create_index(
        "ix_pagos_impuesto_escribania_escritura_id",
        "pagos_impuesto_escribania",
        ["escritura_id"],
    )
    op.create_index(
        "ix_pagos_impuesto_escribania_fecha",
        "pagos_impuesto_escribania",
        ["fecha"],
    )

    print("Created impuestos_escritura, pagos_impuesto_cliente, pagos_impuesto_escribania")
    print("OK")


def downgrade() -> None:
    op.drop_index("ix_pagos_impuesto_escribania_fecha", table_name="pagos_impuesto_escribania")
    op.drop_index(
        "ix_pagos_impuesto_escribania_escritura_id",
        table_name="pagos_impuesto_escribania",
    )
    op.drop_table("pagos_impuesto_escribania")

    op.drop_index("ix_pagos_impuesto_cliente_fecha", table_name="pagos_impuesto_cliente")
    op.drop_index(
        "ix_pagos_impuesto_cliente_escritura_id",
        table_name="pagos_impuesto_cliente",
    )
    op.drop_table("pagos_impuesto_cliente")

    op.drop_index("ix_impuestos_escritura_tipo_periodo", table_name="impuestos_escritura")
    op.drop_index("ix_impuestos_escritura_escritura_id", table_name="impuestos_escritura")
    op.drop_table("impuestos_escritura")

    op.execute(sa.text("DROP TYPE IF EXISTS direccion_prorrateo"))
    op.execute(sa.text("DROP TYPE IF EXISTS tipo_impuesto"))
