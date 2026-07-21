from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.common import MoneyStr


class GastoExtraordinarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepto: str = Field(min_length=1, max_length=500)
    monto: Decimal = Field(gt=0)
    fecha: date

    @field_validator("concepto", mode="before")
    @classmethod
    def strip_concepto(cls, value: object) -> str:
        if not isinstance(value, str):
            raise TypeError("concepto must be a string")
        return value.strip()

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_concepto_not_empty(self) -> Self:
        if not self.concepto:
            raise ValueError("concepto cannot be empty")
        return self


class GastoExtraordinarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepto: str | None = Field(default=None, min_length=1, max_length=500)
    monto: Decimal | None = Field(default=None, gt=0)
    fecha: date | None = None

    @field_validator("concepto", mode="before")
    @classmethod
    def strip_concepto(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("concepto must be a string")
        return value.strip()

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
        if self.concepto is not None and not self.concepto:
            raise ValueError("concepto cannot be empty")
        if self.concepto is None and self.monto is None and self.fecha is None:
            raise ValueError("Al menos un campo debe enviarse para actualizar")
        return self


class GastoExtraordinarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    concepto: str
    monto: MoneyStr
    fecha: date
    created_at: datetime
    updated_at: datetime


class GastosExtraordinariosListResponse(BaseModel):
    anio: int
    mes: int
    gastos: list[GastoExtraordinarioResponse]
    total: MoneyStr
