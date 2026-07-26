from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.escritura import Escritura


class ImputacionPagoColegio(str, Enum):
    TOTAL_IMPUESTOS = "total_impuestos"
    HONORARIOS_VARIOS = "honorarios_varios"
    OTRO = "otro"


class PagoColegio(Base):
    __tablename__ = "pagos_colegio"
    __table_args__ = (
        Index("ix_pagos_colegio_escritura_id", "escritura_id"),
        Index("ix_pagos_colegio_fecha", "fecha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escritura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escrituras.id"),
        nullable=False,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    concepto: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    imputacion: Mapped[ImputacionPagoColegio] = mapped_column(
        SAEnum(
            ImputacionPagoColegio,
            name="imputacion_pago_colegio",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    escritura: Mapped[Escritura] = relationship(back_populates="pagos_colegio")
