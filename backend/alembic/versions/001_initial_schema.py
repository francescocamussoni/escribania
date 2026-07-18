"""Initial schema: configuracion, escrituras, facturas_principales

Revision ID: 001
Revises:
Create Date: 2026-07-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    estado_escritura = postgresql.ENUM("abierta", "cerrada", name="estado_escritura")
    escribano_enum = postgresql.ENUM("costanza", "gabriel", "victoria", name="escribano")
    estado_escritura.create(op.get_bind(), checkfirst=True)
    escribano_enum.create(op.get_bind(), checkfirst=True)

    estado_escritura_col = postgresql.ENUM(
        "abierta", "cerrada", name="estado_escritura", create_type=False
    )
    escribano_col = postgresql.ENUM(
        "costanza", "gabriel", "victoria", name="escribano", create_type=False
    )

    op.create_table(
        "configuracion_financiera",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("honorario_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("honorario_min", sa.Numeric(18, 2), nullable=False),
        sa.Column("certificacion_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("aporte_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("cinco_pct_hon_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("cinco_pct_hon_min", sa.Numeric(18, 2), nullable=False),
        sa.Column("firma_honorarios", sa.Numeric(18, 2), nullable=False),
        sa.Column("art2_a_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("art12_a_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("art12_a_min", sa.Numeric(18, 2), nullable=False),
        sa.Column("art12_c_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("art12_f", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasa_3pm_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("sellos_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("sellos_ajuste_fijo", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasa_75pm_pct", sa.Numeric(7, 5), nullable=False),
        sa.Column("firma_impuestos", sa.Numeric(18, 2), nullable=False),
        sa.Column("inscripcion", sa.Numeric(18, 2), nullable=False),
        sa.Column("protocolo", sa.Numeric(18, 2), nullable=False),
        sa.Column("ii_certificados", sa.Numeric(18, 2), nullable=False),
        sa.Column("municipio", sa.Numeric(18, 2), nullable=False),
        sa.Column("fotocopias_urgentes", sa.Numeric(18, 2), nullable=False),
        sa.Column("certificaciones_extra", sa.Numeric(18, 2), nullable=False),
        sa.Column("catastro", sa.Numeric(18, 2), nullable=False),
        sa.Column("testimonio", sa.Numeric(18, 2), nullable=False),
        sa.Column("concuerda", sa.Numeric(18, 2), nullable=False),
        sa.Column("informes_notariales", sa.Numeric(18, 2), nullable=False),
        sa.Column("extracto", sa.Numeric(18, 2), nullable=False),
        sa.Column("fotocopias_simples", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasas_minimas", sa.Numeric(18, 2), nullable=False),
        sa.Column("salario_secretarias_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        "escrituras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("estado", estado_escritura_col, nullable=False, server_default="abierta"),
        sa.Column("escribano", escribano_col, nullable=False),
        sa.Column("usd_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("dolar_mep", sa.Numeric(10, 4), nullable=False),
        sa.Column("dolar_nacion", sa.Numeric(10, 4), nullable=False),
        sa.Column("config_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("configuracion_financiera.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_escrituras_created_at", "escrituras", ["created_at"])
    op.create_index("ix_escrituras_escribano", "escrituras", ["escribano"])
    op.create_index("ix_escrituras_estado", "escrituras", ["estado"])

    op.create_table(
        "facturas_principales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("escritura_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("escrituras.id"), unique=True, nullable=False),
        sa.Column("monto_base_mep", sa.Numeric(18, 2), nullable=False),
        sa.Column("precio_base_nacion", sa.Numeric(18, 2), nullable=False),
        sa.Column("honorario_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("certificacion", sa.Numeric(18, 2), nullable=False),
        sa.Column("suma_hon_cert", sa.Numeric(18, 2), nullable=False),
        sa.Column("aporte_12pct", sa.Numeric(18, 2), nullable=False),
        sa.Column("cinco_pct_hon", sa.Numeric(18, 2), nullable=False),
        sa.Column("firma_honorarios", sa.Numeric(18, 2), nullable=False),
        sa.Column("subtotal_honorarios", sa.Numeric(18, 2), nullable=False),
        sa.Column("art2_a", sa.Numeric(18, 2), nullable=False),
        sa.Column("art12_a", sa.Numeric(18, 2), nullable=False),
        sa.Column("art12_c", sa.Numeric(18, 2), nullable=False),
        sa.Column("art12_f", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_leyes_notariales", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasa_3pm", sa.Numeric(18, 2), nullable=False),
        sa.Column("sellos", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasa_75pm", sa.Numeric(18, 2), nullable=False),
        sa.Column("firma_impuestos", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_impuestos", sa.Numeric(18, 2), nullable=False),
        sa.Column("inscripcion", sa.Numeric(18, 2), nullable=False),
        sa.Column("protocolo", sa.Numeric(18, 2), nullable=False),
        sa.Column("ii_certificados", sa.Numeric(18, 2), nullable=False),
        sa.Column("municipio", sa.Numeric(18, 2), nullable=False),
        sa.Column("fotocopias_urgentes", sa.Numeric(18, 2), nullable=False),
        sa.Column("certificaciones_extra", sa.Numeric(18, 2), nullable=False),
        sa.Column("catastro", sa.Numeric(18, 2), nullable=False),
        sa.Column("testimonio", sa.Numeric(18, 2), nullable=False),
        sa.Column("concuerda", sa.Numeric(18, 2), nullable=False),
        sa.Column("informes_notariales", sa.Numeric(18, 2), nullable=False),
        sa.Column("extracto", sa.Numeric(18, 2), nullable=False),
        sa.Column("fotocopias_simples", sa.Numeric(18, 2), nullable=False),
        sa.Column("tasas_minimas", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_gastos_admin", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_factura", sa.Numeric(18, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("facturas_principales")
    op.drop_index("ix_escrituras_estado", table_name="escrituras")
    op.drop_index("ix_escrituras_escribano", table_name="escrituras")
    op.drop_index("ix_escrituras_created_at", table_name="escrituras")
    op.drop_table("escrituras")
    op.drop_table("configuracion_financiera")
    op.execute("DROP TYPE IF EXISTS escribano")
    op.execute("DROP TYPE IF EXISTS estado_escritura")
