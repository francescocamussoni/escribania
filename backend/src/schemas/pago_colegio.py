from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.common import MoneyStr
from schemas.plazo_colegio import ImputacionPagoColegio


class PagoColegioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal = Field(gt=0)
    fecha: date
    concepto: str = Field(default="", max_length=500)
    imputacion: ImputacionPagoColegio

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")


class PagoColegioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    escritura_id: UUID
    monto: MoneyStr
    fecha: date
    concepto: str
    imputacion: ImputacionPagoColegio
    created_at: datetime
