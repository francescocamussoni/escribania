from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.impuesto_escritura import DireccionProrrateo, TipoImpuesto
from schemas.common import MoneyStr

EstadoPagos = Literal["sin_pagos", "solo_cliente", "solo_escribania", "completos"]


class ImpuestoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: TipoImpuesto
    monto_total: Decimal = Field(gt=0)
    periodo_inicio: date
    periodo_fin: date
    fecha_corte: date
    direccion_prorrateo: DireccionProrrateo

    @field_validator("monto_total", mode="before")
    @classmethod
    def parse_monto_total(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_periodo_y_corte(self) -> Self:
        if self.periodo_fin < self.periodo_inicio:
            raise ValueError("La fecha de fin del período no puede ser anterior al inicio")
        if self.fecha_corte < self.periodo_inicio or self.fecha_corte > self.periodo_fin:
            raise ValueError("La fecha de corte debe estar dentro del período")
        return self


class ImpuestoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: TipoImpuesto | None = None
    monto_total: Decimal | None = Field(default=None, gt=0)
    periodo_inicio: date | None = None
    periodo_fin: date | None = None
    fecha_corte: date | None = None
    direccion_prorrateo: DireccionProrrateo | None = None

    @field_validator("monto_total", mode="before")
    @classmethod
    def parse_monto_total(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> Self:
        if not any(
            value is not None
            for value in (
                self.tipo,
                self.monto_total,
                self.periodo_inicio,
                self.periodo_fin,
                self.fecha_corte,
                self.direccion_prorrateo,
            )
        ):
            raise ValueError("Al menos un campo debe enviarse para actualizar")
        return self


class PagoImpuestoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal = Field(gt=0)
    fecha: date

    @field_validator("monto", mode="before")
    @classmethod
    def parse_monto(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")


class PagoImpuestoClienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    impuesto_id: UUID
    escritura_id: UUID
    monto: MoneyStr
    fecha: date
    created_at: datetime
    updated_at: datetime


class PagoImpuestoEscribaniaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    impuesto_id: UUID
    escritura_id: UUID
    monto: MoneyStr
    fecha: date
    created_at: datetime
    updated_at: datetime


class ImpuestoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    escritura_id: UUID
    tipo: TipoImpuesto
    monto_total: MoneyStr
    periodo_inicio: date
    periodo_fin: date
    fecha_corte: date
    direccion_prorrateo: DireccionProrrateo
    monto_prorrateado_sugerido: MoneyStr
    estado_pagos: EstadoPagos
    pago_cliente: PagoImpuestoClienteResponse | None = None
    pago_escribania: PagoImpuestoEscribaniaResponse | None = None
    created_at: datetime
    updated_at: datetime


class ImpuestoPendienteItem(BaseModel):
    impuesto_id: UUID
    tipo: TipoImpuesto
    falta_cliente: bool
    falta_escribania: bool


class BalanceImpuestosResponse(BaseModel):
    total_cliente: MoneyStr
    total_escribania: MoneyStr
    balance: MoneyStr
    impuestos_pendientes: list[ImpuestoPendienteItem] = Field(default_factory=list)
    puede_cerrar: bool


class ImpuestosListResponse(BaseModel):
    impuestos: list[ImpuestoResponse]
    balance: BalanceImpuestosResponse
