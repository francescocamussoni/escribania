from datetime import date
from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest
import respx

from schemas.cotizacion import CasaCotizacion, CotizacionAPIError, CotizacionNoDisponibleError
from services.cotizacion_service import get_exchange_rate, reset_caches_for_tests


@pytest.fixture(autouse=True)
def clear_caches() -> None:
    reset_caches_for_tests()


@pytest.mark.asyncio
@respx.mock
async def test_get_exchange_rate_success() -> None:
    fecha = date(2026, 7, 10)
    route = respx.get(
        "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/10"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"compra": 1190.5, "venta": 1195.0, "casa": "bolsa", "fecha": "2026-07-10"},
        )
    )

    result = await get_exchange_rate(CasaCotizacion.BOLSA, fecha)

    assert route.called
    assert result.compra == Decimal("1190.5")
    assert result.venta == Decimal("1195.0")
    assert result.source == "api"


@pytest.mark.asyncio
@respx.mock
async def test_cache_hit_skips_http_call() -> None:
    fecha = date(2026, 7, 10)
    route = respx.get(
        "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/10"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"compra": 1190.5, "venta": 1195.0},
        )
    )

    first = await get_exchange_rate(CasaCotizacion.BOLSA, fecha)
    second = await get_exchange_rate(CasaCotizacion.BOLSA, fecha)

    assert first.source == "api"
    assert second.source == "cache"
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_network_error_raises_api_error() -> None:
    fecha = date(2026, 7, 10)
    respx.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/10").mock(
        side_effect=httpx.ConnectError("network down")
    )

    with pytest.raises(CotizacionAPIError):
        await get_exchange_rate(CasaCotizacion.BOLSA, fecha)


@pytest.mark.asyncio
@respx.mock
async def test_missing_date_returns_not_available() -> None:
    fecha = date(2026, 7, 10)
    respx.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/10").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )

    with pytest.raises(CotizacionNoDisponibleError):
        await get_exchange_rate(CasaCotizacion.BOLSA, fecha)


@pytest.mark.asyncio
@respx.mock
async def test_zero_rate_raises_not_available() -> None:
    fecha = date(2026, 7, 10)
    respx.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/10").mock(
        return_value=httpx.Response(200, json={"compra": 0, "venta": 0})
    )

    with pytest.raises(CotizacionNoDisponibleError):
        await get_exchange_rate(CasaCotizacion.BOLSA, fecha)


@pytest.mark.asyncio
@respx.mock
async def test_today_uses_fallback_when_primary_fails() -> None:
    today = date.today()
    fecha_path = today.strftime("%Y/%m/%d")
    respx.get(
        f"https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial/{fecha_path}"
    ).mock(side_effect=httpx.ConnectError("network down"))
    respx.get("https://dolarapi.com/v1/dolares/oficial").mock(
        return_value=httpx.Response(200, json={"compra": 1200.0, "venta": 1210.0})
    )

    result = await get_exchange_rate(CasaCotizacion.OFICIAL, today)

    assert result.source == "fallback"
    assert result.compra == Decimal("1200.0")
