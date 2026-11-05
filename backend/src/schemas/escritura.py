from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.common import MoneyStr
from schemas.plazo_colegio import PlazoColegioResponse
from schemas.factura import FacturaPrincipalResponse
from schemas.impuesto import BalanceImpuestosResponse
from schemas.pago_cliente import PagoClienteResponse
from schemas.pago_colegio import PagoColegioResponse
from services.factura_lineas import FACTURA_LINEA_KEYS


class EscrituraInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=255)
    escribano_id: UUID
    usd_value: Decimal = Field(gt=0)
    dolar_mep: Decimal = Field(gt=0)
    dolar_nacion: Decimal = Field(gt=0)

    @field_validator("usd_value", "dolar_mep", "dolar_nacion", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal:
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")


class EscrituraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    escribano_id: UUID | None = None
    usd_value: Decimal | None = Field(default=None, gt=0)
    dolar_mep: Decimal | None = Field(default=None, gt=0)
    dolar_nacion: Decimal | None = Field(default=None, gt=0)
    lineas_deshabilitadas: list[str] | None = None

    @field_validator("usd_value", "dolar_mep", "dolar_nacion", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        raise TypeError("invalid decimal value")

    @model_validator(mode="after")
    def validate_lineas_deshabilitadas(self) -> Self:
        if self.lineas_deshabilitadas is None:
            return self
        unknown = set(self.lineas_deshabilitadas) - set(FACTURA_LINEA_KEYS)
        if unknown:
            raise ValueError(f"Unknown line keys: {sorted(unknown)}")
        if len(self.lineas_deshabilitadas) >= len(FACTURA_LINEA_KEYS):
            raise ValueError("At least one invoice line must remain enabled")
        return self


class EscrituraListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    estado: str
    escribano_id: UUID
    escribano_nombre: str
    usd_value: MoneyStr
    created_at: datetime
    costo_total: MoneyStr
    total_pagado: MoneyStr
    saldo_pendiente: MoneyStr
    pagada_al_100: bool
    sobrepago: bool
    plazo_colegio: PlazoColegioResponse | None = None


class EscrituraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    estado: str
    escribano_id: UUID
    escribano_nombre: str
    usd_value: MoneyStr
    dolar_mep: MoneyStr
    dolar_nacion: MoneyStr
    config_version_id: UUID
    created_at: datetime
    closed_at: datetime | None
    updated_at: datetime
    factura: FacturaPrincipalResponse
    costo_total: MoneyStr
    total_pagado: MoneyStr
    saldo_pendiente: MoneyStr
    pagada_al_100: bool
    sobrepago: bool
    total_leyes_notariales_proyectadas: MoneyStr
    balance_impuestos: BalanceImpuestosResponse | None = None
    plazo_colegio: PlazoColegioResponse | None = None
    pagos_cliente: list[PagoClienteResponse] = Field(default_factory=list)
    pagos_colegio: list[PagoColegioResponse] = Field(default_factory=list)
