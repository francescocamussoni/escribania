from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict

from models.pago_colegio import ImputacionPagoColegio
from schemas.common import MoneyStr

__all__ = [
    "ImputacionPagoColegio",
    "PlazoColegioEstado",
    "PlazoColegioUrgencia",
    "PlazoColegioResponse",
]


class PlazoColegioEstado(str, Enum):
    NO_APLICA = "no_aplica"
    PENDIENTE = "pendiente"
    VENCIDO = "vencido"
    PAGADO = "pagado"


class PlazoColegioUrgencia(str, Enum):
    VERDE = "verde"
    AMARILLO = "amarillo"
    ROJO = "rojo"


class PlazoColegioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    estado: PlazoColegioEstado
    fecha_vencimiento: date | None
    dias_restantes: int | None
    urgencia: PlazoColegioUrgencia | None
    monto_referencia: MoneyStr
    monto_pagado: MoneyStr
    monto_pendiente: MoneyStr

    @classmethod
    def from_calculation(
        cls,
        *,
        estado: PlazoColegioEstado,
        fecha_vencimiento: date | None,
        dias_restantes: int | None,
        urgencia: PlazoColegioUrgencia | None,
        monto_referencia: Decimal,
        monto_pagado: Decimal,
        monto_pendiente: Decimal,
    ) -> PlazoColegioResponse:
        return cls(
            estado=estado,
            fecha_vencimiento=fecha_vencimiento,
            dias_restantes=dias_restantes,
            urgencia=urgencia,
            monto_referencia=monto_referencia,
            monto_pagado=monto_pagado,
            monto_pendiente=monto_pendiente,
        )
