from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TipoPagoSalario(str, enum.Enum):
    ESCRIBANO = "escribano"
    SECRETARIA = "secretaria"


class LiquidacionMensual(Base):
    __tablename__ = "liquidaciones_mensuales"
    __table_args__ = (UniqueConstraint("anio", "mes", name="uq_liquidacion_anio_mes"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total_costanza: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_gabriel: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_monica: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_global: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    pagos: Mapped[list[PagoSalario]] = relationship(back_populates="liquidacion")


class PagoSalario(Base):
    __tablename__ = "pagos_salario"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("liquidaciones_mensuales.id"),
        nullable=False,
    )
    persona: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoPagoSalario] = mapped_column(
        Enum(TipoPagoSalario, name="tipo_pago_salario", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    detalle_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    liquidacion: Mapped[LiquidacionMensual] = relationship(back_populates="pagos")
