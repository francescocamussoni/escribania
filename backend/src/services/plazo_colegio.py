from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Protocol

from models.pago_colegio import ImputacionPagoColegio
from schemas.plazo_colegio import PlazoColegioEstado, PlazoColegioUrgencia

PLAZO_COLEGIO_DIAS = 30
_ZERO = Decimal("0.00")


class PagoColegioLike(Protocol):
    monto: Decimal
    imputacion: ImputacionPagoColegio


@dataclass(frozen=True)
class PlazoColegioCalculation:
    estado: PlazoColegioEstado
    fecha_vencimiento: date | None
    dias_restantes: int | None
    urgencia: PlazoColegioUrgencia | None
    monto_referencia: Decimal
    monto_pagado: Decimal
    monto_pendiente: Decimal


def sum_pagos_impuestos(pagos: Iterable[PagoColegioLike]) -> Decimal:
    total = sum(
        (pago.monto for pago in pagos if pago.imputacion == ImputacionPagoColegio.TOTAL_IMPUESTOS),
        _ZERO,
    )
    return total.quantize(Decimal("0.01"))


def _urgencia_for_dias(dias_restantes: int) -> PlazoColegioUrgencia:
    if dias_restantes > 20:
        return PlazoColegioUrgencia.VERDE
    if dias_restantes > 10:
        return PlazoColegioUrgencia.AMARILLO
    return PlazoColegioUrgencia.ROJO


def calcular_plazo_colegio(
    *,
    fecha_creacion: date,
    total_impuestos: Decimal,
    monto_pagado_impuestos: Decimal,
    fecha_referencia: date,
) -> PlazoColegioCalculation:
    monto_referencia = total_impuestos.quantize(Decimal("0.01"))
    monto_pagado = monto_pagado_impuestos.quantize(Decimal("0.01"))

    if monto_referencia <= _ZERO:
        return PlazoColegioCalculation(
            estado=PlazoColegioEstado.NO_APLICA,
            fecha_vencimiento=None,
            dias_restantes=None,
            urgencia=None,
            monto_referencia=monto_referencia,
            monto_pagado=monto_pagado,
            monto_pendiente=_ZERO,
        )

    if monto_pagado >= monto_referencia:
        return PlazoColegioCalculation(
            estado=PlazoColegioEstado.PAGADO,
            fecha_vencimiento=fecha_creacion + timedelta(days=PLAZO_COLEGIO_DIAS),
            dias_restantes=None,
            urgencia=None,
            monto_referencia=monto_referencia,
            monto_pagado=monto_pagado,
            monto_pendiente=_ZERO,
        )

    fecha_vencimiento = fecha_creacion + timedelta(days=PLAZO_COLEGIO_DIAS)
    fecha_efectiva = max(fecha_referencia, fecha_creacion)
    dias_raw = (fecha_vencimiento - fecha_efectiva).days
    monto_pendiente = (monto_referencia - monto_pagado).quantize(Decimal("0.01"))

    if dias_raw < 0:
        return PlazoColegioCalculation(
            estado=PlazoColegioEstado.VENCIDO,
            fecha_vencimiento=fecha_vencimiento,
            dias_restantes=0,
            urgencia=PlazoColegioUrgencia.ROJO,
            monto_referencia=monto_referencia,
            monto_pagado=monto_pagado,
            monto_pendiente=monto_pendiente,
        )

    dias_restantes = dias_raw
    return PlazoColegioCalculation(
        estado=PlazoColegioEstado.PENDIENTE,
        fecha_vencimiento=fecha_vencimiento,
        dias_restantes=dias_restantes,
        urgencia=_urgencia_for_dias(dias_restantes),
        monto_referencia=monto_referencia,
        monto_pagado=monto_pagado,
        monto_pendiente=monto_pendiente,
    )
