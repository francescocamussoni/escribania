import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.gasto_adicional import GastoAdicional


class EstadoEscritura(str, enum.Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


class Escribano(str, enum.Enum):
    COSTANZA = "costanza"
    GABRIEL = "gabriel"
    VICTORIA = "victoria"


class Escritura(Base):
    __tablename__ = "escrituras"
    __table_args__ = (
        Index("ix_escrituras_created_at", "created_at"),
        Index("ix_escrituras_escribano", "escribano"),
        Index("ix_escrituras_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoEscritura] = mapped_column(
        Enum(EstadoEscritura, name="estado_escritura", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EstadoEscritura.ABIERTA,
    )
    escribano: Mapped[Escribano] = mapped_column(
        Enum(Escribano, name="escribano", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    usd_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    dolar_mep: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    dolar_nacion: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    config_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("configuracion_financiera.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    factura: Mapped["FacturaPrincipal"] = relationship(back_populates="escritura", uselist=False)
    gastos: Mapped[list["GastoAdicional"]] = relationship(back_populates="escritura")
