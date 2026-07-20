from datetime import date

from pydantic import BaseModel, ConfigDict

from schemas.common import MoneyStr


class LibroLineaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str
    escritura_nombre: str
    concepto: str
    monto: MoneyStr
    fecha_pago: date


class DeudaResumenItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str
    escritura_nombre: str
    costo_total: MoneyStr
    total_pagado: MoneyStr
    saldo_pendiente: MoneyStr


class LibroEntradaResponse(BaseModel):
    anio: int
    mes: int
    lineas: list[LibroLineaResponse]
    resumen_deudas: list[DeudaResumenItem]
    total: MoneyStr


class LibroSalidaResponse(BaseModel):
    anio: int
    mes: int
    lineas: list[LibroLineaResponse]
    total: MoneyStr
