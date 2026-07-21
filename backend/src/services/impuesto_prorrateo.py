"""Pure functions for linear impuesto proration by calendar days (P6)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

_CENTS = Decimal("0.01")


class DireccionProrrateo(StrEnum):
    HACIA_ATRAS = "hacia_atras"
    HACIA_ADELANTE = "hacia_adelante"


def calc_dias_periodo(periodo_inicio: date, periodo_fin: date) -> int:
    """Inclusive calendar days in the billing period."""
    return (periodo_fin - periodo_inicio).days + 1


def calc_dias_tramo(
    periodo_inicio: date,
    periodo_fin: date,
    fecha_corte: date,
    direccion: DireccionProrrateo,
) -> int:
    """Inclusive days in the proration segment for the given direction."""
    if direccion == DireccionProrrateo.HACIA_ATRAS:
        tramo_inicio = periodo_inicio
        tramo_fin = fecha_corte
    else:
        tramo_inicio = fecha_corte + timedelta(days=1)
        tramo_fin = periodo_fin

    if tramo_inicio > tramo_fin:
        return 0

    return (tramo_fin - tramo_inicio).days + 1


def _validate_periodo(periodo_inicio: date, periodo_fin: date) -> None:
    if periodo_fin < periodo_inicio:
        raise ValueError("La fecha de fin del período no puede ser anterior al inicio")


def _validate_fecha_corte(
    periodo_inicio: date,
    periodo_fin: date,
    fecha_corte: date,
) -> None:
    if fecha_corte < periodo_inicio or fecha_corte > periodo_fin:
        raise ValueError("La fecha de corte debe estar dentro del período")


def _validate_monto_total(monto_total: Decimal) -> None:
    if monto_total <= Decimal("0"):
        raise ValueError("El monto total debe ser mayor a cero")


def calc_monto_sugerido(
    monto_total: Decimal,
    periodo_inicio: date,
    periodo_fin: date,
    fecha_corte: date,
    direccion: DireccionProrrateo,
) -> Decimal:
    """Suggested client amount: monto_total × (días_tramo / días_período), rounded half-up."""
    _validate_monto_total(monto_total)
    _validate_periodo(periodo_inicio, periodo_fin)
    _validate_fecha_corte(periodo_inicio, periodo_fin, fecha_corte)

    dias_periodo = calc_dias_periodo(periodo_inicio, periodo_fin)
    dias_tramo = calc_dias_tramo(
        periodo_inicio,
        periodo_fin,
        fecha_corte,
        direccion,
    )

    if dias_tramo == 0:
        return Decimal("0.00")

    monto = monto_total * Decimal(dias_tramo) / Decimal(dias_periodo)
    return monto.quantize(_CENTS, rounding=ROUND_HALF_UP)
