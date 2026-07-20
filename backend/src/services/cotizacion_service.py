from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from cachetools import TTLCache

from config import get_settings
from schemas.cotizacion import (
    CasaCotizacion,
    CotizacionAPIError,
    CotizacionNoDisponibleError,
    CotizacionResponse,
)

logger = logging.getLogger(__name__)

_TODAY_CACHE: TTLCache = TTLCache(maxsize=32, ttl=28_800)
_HISTORY_CACHE: dict[tuple[str, str], dict[str, Any]] = {}

_FALLBACK_CASA_MAP = {
    CasaCotizacion.BOLSA.value: "bolsa",
    CasaCotizacion.OFICIAL.value: "oficial",
}


def _cache_for_date(fecha: date) -> TTLCache | dict[tuple[str, str], dict[str, Any]]:
    if fecha >= date.today():
        return _TODAY_CACHE
    return _HISTORY_CACHE


def _validate_rate_values(compra: Decimal, venta: Decimal) -> None:
    if compra <= 0 or venta <= 0:
        raise CotizacionNoDisponibleError("Exchange rate values must be greater than zero")


def _parse_rate_payload(casa: CasaCotizacion, fecha: date, payload: dict[str, Any], source: str) -> CotizacionResponse:
    try:
        compra = Decimal(str(payload["compra"]))
        venta = Decimal(str(payload["venta"]))
    except (KeyError, TypeError, ArithmeticError) as exc:
        raise CotizacionNoDisponibleError("Invalid exchange rate payload") from exc

    _validate_rate_values(compra, venta)
    return CotizacionResponse(
        casa=casa,
        fecha=fecha,
        compra=compra,
        venta=venta,
        source=source,
    )


async def _fetch_argentina_datos(casa: CasaCotizacion, fecha: date) -> dict[str, Any]:
    settings = get_settings()
    fecha_path = fecha.strftime("%Y/%m/%d")
    url = f"{settings.cotizacion_api_url.rstrip('/')}/{casa.value}/{fecha_path}"

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=settings.cotizacion_ssl_verify) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        logger.warning("ArgentinaDatos request failed for %s %s", casa.value, fecha)
        raise CotizacionAPIError("No se pudo consultar la cotización oficial") from exc

    if response.status_code == 404:
        raise CotizacionNoDisponibleError("No hay cotización disponible para esa fecha")
    if response.status_code >= 400:
        raise CotizacionAPIError("No se pudo consultar la cotización oficial")

    return response.json()


async def _fetch_dolarapi_fallback(casa: CasaCotizacion) -> dict[str, Any]:
    settings = get_settings()
    casa_path = _FALLBACK_CASA_MAP[casa.value]
    url = f"{settings.cotizacion_fallback_url.rstrip('/')}/{casa_path}"

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=settings.cotizacion_ssl_verify) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("DolarAPI fallback failed for %s", casa.value)
        raise CotizacionAPIError("No se pudo consultar la cotización oficial") from exc

    return response.json()


async def _load_rate_payload(casa: CasaCotizacion, fecha: date) -> tuple[dict[str, Any], str]:
    try:
        return await _fetch_argentina_datos(casa, fecha), "api"
    except CotizacionNoDisponibleError:
        if fecha == date.today():
            return await _fetch_dolarapi_fallback(casa), "fallback"
        raise
    except CotizacionAPIError:
        if fecha == date.today():
            return await _fetch_dolarapi_fallback(casa), "fallback"
        raise


async def get_exchange_rate(casa: CasaCotizacion, fecha: date) -> CotizacionResponse:
    if fecha > date.today():
        raise CotizacionNoDisponibleError("Future dates are not supported")

    cache = _cache_for_date(fecha)
    cache_key = (casa.value, fecha.isoformat())
    if cache_key in cache:
        cached = cache[cache_key]
        if isinstance(cached, CotizacionResponse):
            return cached.model_copy(update={"source": "cache"})
        return _parse_rate_payload(casa, fecha, cached, "cache")

    try:
        payload, source = await _load_rate_payload(casa, fecha)
    except CotizacionNoDisponibleError:
        raise

    result = _parse_rate_payload(casa, fecha, payload, source)
    cache[cache_key] = result
    return result


def reset_caches_for_tests() -> None:
    _TODAY_CACHE.clear()
    _HISTORY_CACHE.clear()
