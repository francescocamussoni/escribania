from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from models.impuesto_escritura import TipoImpuesto
from schemas.common import MoneyStr

LibroOrigen = Literal["honorario", "impuesto", "extraordinario"]
TipoPagoLibroSalida = Literal["colegio", "otros"]


class LibroLineaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str | None = None
    escritura_nombre: str | None = None
    concepto: str
    monto: MoneyStr
    fecha_pago: date
    origen: LibroOrigen = "honorario"
    tipo_pago: TipoPagoLibroSalida | None = None
    tipo_impuesto: TipoImpuesto | None = None
    gasto_extraordinario_id: str | None = None


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
