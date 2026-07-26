"""ORM model for the Escribano entity.

Replaces the hardcoded ENUM ('costanza', 'gabriel', 'victoria') that was
previously defined on Escritura. Uses SoftDeleteMixin for soft deletes so
that historical FK references from Escritura remain valid.

Business rules enforced at the DB level:
- BR-ESC-001: nombre is unique among active rows only (partial unique index).
- BR-ESC-002: Hard delete is forbidden; only soft_delete() is permitted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.mixins import SoftDeleteMixin


class Escribano(SoftDeleteMixin, Base):
    __tablename__ = "escribano"
    __table_args__ = (
        # BR-ESC-001 — unique name among active (non-deleted) escribanos only
        Index(
            "uq_escribano_nombre_active",
            "nombre",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index("ix_escribano_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    monotributista: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship to Escritura — exists after Escritura model is updated (T008)
    # Using string reference to avoid circular imports at import time.
    escrituras: Mapped[list["Escritura"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="escribano_ref",
        foreign_keys="[Escritura.escribano_id]",
    )
