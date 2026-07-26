import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class FacturaPrincipal(Base):
    __tablename__ = "facturas_principales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escritura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escrituras.id"),
        unique=True,
        nullable=False,
    )
    monto_base_mep: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    precio_base_nacion: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    honorario_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    certificacion: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    suma_hon_cert: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    aporte_12pct: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cinco_pct_hon: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    firma_honorarios: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    subtotal_honorarios: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art2_a: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art12_a: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art12_c: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art12_f: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_leyes_notariales: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tasa_3pm: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    sellos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tasa_75pm: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    firma_impuestos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_impuestos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    inscripcion: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    protocolo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    ii_certificados: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    municipio: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fotocopias_urgentes: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    certificaciones_extra: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    catastro: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    testimonio: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    concuerda: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    informes_notariales: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    extracto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fotocopias_simples: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tasas_minimas: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_gastos_admin: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dif_honorarios: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_parcial: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_sin_iva: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_factura: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    escritura: Mapped["Escritura"] = relationship(back_populates="factura")
