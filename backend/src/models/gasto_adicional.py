from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class DireccionGasto(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


class GastoAdicional(Base):
    __tablename__ = "gastos_adicionales"
    __table_args__ = (
        Index("ix_gastos_adicionales_escritura_id", "escritura_id"),
        Index("ix_gastos_adicionales_fecha", "fecha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escritura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escrituras.id"),
        nullable=False,
    )
    concepto: Mapped[str] = mapped_column(String(500), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    direccion: Mapped[DireccionGasto] = mapped_column(
        Enum(DireccionGasto, name="direccion_gasto", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    escritura: Mapped["Escritura"] = relationship(back_populates="gastos")
