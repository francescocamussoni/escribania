from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.escritura import Escritura
    from models.impuesto_escritura import ImpuestoEscritura


class PagoImpuestoCliente(Base):
    __tablename__ = "pagos_impuesto_cliente"
    __table_args__ = (
        UniqueConstraint("impuesto_id", name="uq_pagos_impuesto_cliente_impuesto_id"),
        Index("ix_pagos_impuesto_cliente_escritura_id", "escritura_id"),
        Index("ix_pagos_impuesto_cliente_fecha", "fecha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    impuesto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("impuestos_escritura.id", ondelete="CASCADE"),
        nullable=False,
    )
    escritura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escrituras.id"),
        nullable=False,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    impuesto: Mapped[ImpuestoEscritura] = relationship(back_populates="pago_cliente")
    escritura: Mapped[Escritura] = relationship(back_populates="pagos_impuesto_cliente")
