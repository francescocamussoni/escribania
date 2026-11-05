from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.common import MoneyStr
from schemas.pago_colegio import PagoColegioResponse

PagoColegioBulkMotivoNoElegible = Literal["cerrada", "sin_pendiente"]


class PagoColegioBulkPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    escritura_ids: list[UUID] = Field(min_length=1, max_length=100)

    @field_validator("escritura_ids")
    @classmethod
    def unique_escritura_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("escritura_ids must be unique")
        return value


class PagoColegioBulkPreviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    escritura_id: UUID
    escritura_nombre: str
    pendiente: MoneyStr
    elegible: bool
    motivo: PagoColegioBulkMotivoNoElegible | None = None


class PagoColegioBulkPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PagoColegioBulkPreviewItem]
    total_propuesto: MoneyStr


class PagoColegioBulkItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    escritura_id: UUID
    monto: Decimal = Field(gt=0)

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")


class PagoColegioBulkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    items: list[PagoColegioBulkItemInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_escritura_ids(self) -> Self:
        ids = [item.escritura_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("items must have unique escritura_id values")
        return self


class PagoColegioBulkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pagos: list[PagoColegioResponse]
    total: MoneyStr
