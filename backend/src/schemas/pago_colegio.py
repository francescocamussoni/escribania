from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.pago_colegio import TipoPagoEscribania
from schemas.common import MoneyStr


class PagoColegioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal = Field(gt=0)
    fecha: date
    concepto: str = Field(default="", max_length=500)
    tipo: TipoPagoEscribania = TipoPagoEscribania.COLEGIO

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_otros_concepto(self) -> Self:
        if self.tipo == TipoPagoEscribania.OTROS and not self.concepto.strip():
            raise ValueError("concepto is required when tipo is otros")
        return self


class PagoColegioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    escritura_id: UUID
    monto: MoneyStr
    fecha: date
    concepto: str
    tipo: TipoPagoEscribania
    created_at: datetime
