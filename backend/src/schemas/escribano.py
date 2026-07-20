from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EscribanoCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=100)


class EscribanoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    activo: bool
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row: object) -> "EscribanoResponse":
        return cls(
            id=row.id,  # type: ignore[attr-defined]
            nombre=row.nombre,  # type: ignore[attr-defined]
            activo=row.deleted_at is None,  # type: ignore[attr-defined]
            created_at=row.created_at,  # type: ignore[attr-defined]
        )
