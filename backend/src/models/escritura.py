"""ORM model for Escritura (Deed Document).

Modified in feature 002 to replace the hardcoded Escribano ENUM with a
dynamic FK to the Escribano table. A `escribano_nombre` snapshot column is
added to preserve the display name even after an Escribano is soft-deleted.

Changes from feature 001:
- REMOVED: `Escribano` ENUM class (moved to models/escribano.py as a proper entity).
- REMOVED: `escribano` ENUM column.
- ADDED: `escribano_id` FK → escribano.id (not null).
- ADDED: `escribano_nombre` VARCHAR(100) (not null — snapshot at creation time).

Backward compatibility:
- `Escribano` is re-exported from `models.escribano` so existing imports of
  `from models.escritura import Escribano` continue to work during the
  transition. Services that use the ENUM values will be updated in WU-012+.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.impuesto_escritura import ImpuestoEscritura
    from models.pago_cliente import PagoCliente
    from models.pago_colegio import PagoColegio
    from models.pago_impuesto_cliente import PagoImpuestoCliente
    from models.pago_impuesto_escribania import PagoImpuestoEscribania

# Re-export for backward compatibility: existing imports of
# `from models.escritura import Escribano` still resolve during transition.
# TODO(WU-012+): remove once all services are migrated to use models.escribano directly.
from models.escribano import Escribano as Escribano  # noqa: F401


class EstadoEscritura(str, enum.Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


class Escritura(Base):
    __tablename__ = "escrituras"
    __table_args__ = (
        Index("ix_escrituras_created_at", "created_at"),
        Index("ix_escrituras_escribano_id", "escribano_id"),
        Index("ix_escrituras_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoEscritura] = mapped_column(
        Enum(EstadoEscritura, name="estado_escritura", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EstadoEscritura.ABIERTA,
    )

    # Dynamic FK replacing the old hardcoded ENUM (feature 002)
    escribano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escribano.id"),
        nullable=False,
    )
    # Snapshot of escribano name at creation time — preserved even after soft delete
    escribano_nombre: Mapped[str] = mapped_column(String(100), nullable=False)

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

    escribano_ref: Mapped["Escribano"] = relationship(
        back_populates="escrituras",
        foreign_keys=[escribano_id],
    )
    factura: Mapped["FacturaPrincipal"] = relationship(back_populates="escritura", uselist=False)  # type: ignore[name-defined]  # noqa: F821
    pagos_cliente: Mapped[list["PagoCliente"]] = relationship(back_populates="escritura")
    pagos_colegio: Mapped[list["PagoColegio"]] = relationship(back_populates="escritura")
    impuestos: Mapped[list["ImpuestoEscritura"]] = relationship(back_populates="escritura")
    pagos_impuesto_cliente: Mapped[list["PagoImpuestoCliente"]] = relationship(
        back_populates="escritura",
    )
    pagos_impuesto_escribania: Mapped[list["PagoImpuestoEscribania"]] = relationship(
        back_populates="escritura",
    )
