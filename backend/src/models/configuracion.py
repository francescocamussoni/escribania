from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ConfiguracionFinanciera(Base):
    __tablename__ = "configuracion_financiera"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    honorario_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.024"))
    honorario_min: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    certificacion_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.003"))
    aporte_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.12"))
    cinco_pct_hon_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.05"))
    cinco_pct_hon_min: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    firma_honorarios: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art2_a_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.0048"))
    art12_a_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.004"))
    art12_a_min: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    art12_c_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.0012"))
    art12_f: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tasa_3pm_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.003"))
    sellos_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.025"))
    sellos_ajuste_fijo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("250.00"))
    tasa_75pm_pct: Mapped[Decimal] = mapped_column(Numeric(7, 5), nullable=False, default=Decimal("0.0075"))
    firma_impuestos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
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
    salario_secretarias_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
