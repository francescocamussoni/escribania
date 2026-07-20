"""ORM models for Empleado and SueldoHistorico entities.

Empleado represents an office employee (secretary) with a configurable salary.
It replaces the hardcoded `ConfiguracionFinanciera.salario_secretarias_total` field.

SueldoHistorico is an append-only snapshot of each employee's salary at the
moment a monthly settlement (LiquidacionMensual) is closed.

Business rules:
- BR-EMP-001: sueldo MUST be > 0 (validated at service layer — see empleado_service.py).
- BR-EMP-002: Modifying sueldo MUST update updated_at immediately.
- BR-EMP-003: Closed-month snapshots in SueldoHistorico are immutable.
- BR-EMP-004: Soft-deleted employees are excluded from future salary calculations.
- BR-SH-001: One SueldoHistorico record per (empleado_id, anio, mes) — unique constraint.
- BR-SH-002: SueldoHistorico is never updated after creation (append-only).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.mixins import SoftDeleteMixin


class Empleado(SoftDeleteMixin, Base):
    __tablename__ = "empleado"
    __table_args__ = (
        # Unique name among active employees only
        Index(
            "uq_empleado_nombre_active",
            "nombre",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index("ix_empleado_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    sueldo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # BR-EMP-001: > 0
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )  # BR-EMP-002: updated on sueldo change

    historial: Mapped[list["SueldoHistorico"]] = relationship(
        back_populates="empleado",
        order_by="[SueldoHistorico.anio.desc(), SueldoHistorico.mes.desc()]",
    )


class SueldoHistorico(Base):
    """Immutable salary snapshot created when a monthly settlement is closed.

    Never updated after insertion — append-only record. (BR-SH-002)
    """

    __tablename__ = "sueldo_historico"
    __table_args__ = (
        UniqueConstraint("empleado_id", "anio", "mes", name="uq_sueldo_historico_empleado_mes"),  # BR-SH-001
        Index("ix_sueldo_historico_anio_mes", "anio", "mes"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("empleado.id"),
        nullable=False,
    )
    empleado_nombre: Mapped[str] = mapped_column(String(100), nullable=False)  # snapshot of name at close time
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–12
    sueldo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # frozen at month close
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    empleado: Mapped["Empleado"] = relationship(back_populates="historial")
