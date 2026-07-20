from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from schemas.cotizacion import CotizacionResponse, CasaCotizacion


@pytest.mark.asyncio
async def test_get_cotizacion_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/cotizacion", params={"casa": "bolsa"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_cotizacion_invalid_casa_returns_422(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/cotizacion", params={"casa": "invalid"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_cotizacion_success(auth_client: AsyncClient) -> None:
    mocked = CotizacionResponse(
        casa=CasaCotizacion.BOLSA,
        fecha=date(2026, 7, 10),
        compra=Decimal("1190.50"),
        venta=Decimal("1195.00"),
        source="api",
    )
    with patch(
        "api.routes.cotizacion.get_exchange_rate",
        new=AsyncMock(return_value=mocked),
    ):
        response = await auth_client.get(
            "/api/v1/cotizacion",
            params={"casa": "bolsa", "fecha": "2026-07-10"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["casa"] == "bolsa"
    assert body["compra"] == "1190.50"
    assert body["source"] == "api"


@pytest.mark.asyncio
async def test_get_cotizacion_api_down_returns_503(auth_client: AsyncClient) -> None:
    from schemas.cotizacion import CotizacionAPIError

    with patch(
        "api.routes.cotizacion.get_exchange_rate",
        new=AsyncMock(side_effect=CotizacionAPIError("No se pudo consultar la cotización oficial")),
    ):
        response = await auth_client.get("/api/v1/cotizacion", params={"casa": "bolsa"})

    assert response.status_code == 503
    assert "cotización" in response.json()["detail"].lower()
