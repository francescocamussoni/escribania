from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.gasto_adicional import DireccionGasto
from schemas.common import MoneyStr


class GastoAdicionalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepto: str = Field(min_length=1, max_length=500)
    monto: Decimal = Field(gt=0)
    direccion: DireccionGasto
    fecha: date

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")


class GastoAdicionalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    escritura_id: UUID
    concepto: str
    monto: MoneyStr
    direccion: DireccionGasto
    fecha: date
    created_at: datetime
