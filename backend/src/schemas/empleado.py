from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmpleadoCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=100)
    sueldo: Decimal = Field(gt=0)


class EmpleadoUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sueldo: Decimal = Field(gt=0)


class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    sueldo: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_row(cls, row: object) -> "EmpleadoResponse":
        return cls(
            id=row.id,  # type: ignore[attr-defined]
            nombre=row.nombre,  # type: ignore[attr-defined]
            sueldo=row.sueldo,  # type: ignore[attr-defined]
            activo=row.deleted_at is None,  # type: ignore[attr-defined]
            created_at=row.created_at,  # type: ignore[attr-defined]
            updated_at=row.updated_at,  # type: ignore[attr-defined]
        )
