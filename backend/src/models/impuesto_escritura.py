from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.escritura import Escritura
    from models.pago_impuesto_cliente import PagoImpuestoCliente
    from models.pago_impuesto_escribania import PagoImpuestoEscribania


class TipoImpuesto(str, enum.Enum):
    API = "API"
    TGI = "TGI"
    AGUAS_SANTAFESINAS = "AGUAS_SANTAFESINAS"
    EPE = "EPE"
    EXPENSAS = "EXPENSAS"
    LITORAL_GAS = "LITORAL_GAS"


class DireccionProrrateo(str, enum.Enum):
    HACIA_ATRAS = "hacia_atras"
    HACIA_ADELANTE = "hacia_adelante"


class ImpuestoEscritura(Base):
    __tablename__ = "impuestos_escritura"
    __table_args__ = (
        Index("ix_impuestos_escritura_escritura_id", "escritura_id"),
        Index(
            "ix_impuestos_escritura_tipo_periodo",
            "tipo",
            "periodo_inicio",
            "periodo_fin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escritura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escrituras.id"),
        nullable=False,
    )
    tipo: Mapped[TipoImpuesto] = mapped_column(
        Enum(TipoImpuesto, name="tipo_impuesto", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    monto_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    periodo_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_fin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_corte: Mapped[date] = mapped_column(Date, nullable=False)
    direccion_prorrateo: Mapped[DireccionProrrateo] = mapped_column(
        Enum(
            DireccionProrrateo,
            name="direccion_prorrateo",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
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

    escritura: Mapped[Escritura] = relationship(back_populates="impuestos")
    pago_cliente: Mapped[PagoImpuestoCliente | None] = relationship(
        back_populates="impuesto",
        uselist=False,
        cascade="all, delete-orphan",
    )
    pago_escribania: Mapped[PagoImpuestoEscribania | None] = relationship(
        back_populates="impuesto",
        uselist=False,
        cascade="all, delete-orphan",
    )
