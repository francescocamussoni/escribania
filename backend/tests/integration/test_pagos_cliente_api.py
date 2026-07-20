import pytest
from httpx import AsyncClient

from tests.integration.test_escrituras_api import (
    PAGO_FECHA,
    _create_escritura,
    _pay_full,
)

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


@pytest.mark.asyncio
async def test_create_pago_cliente_returns_201(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-cliente",
        json={"monto": "400000.00", "fecha": PAGO_FECHA, "concepto": "Anticipo"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["escritura_id"] == created["id"]
    assert body["monto"] == "400000.00"


@pytest.mark.asyncio
async def test_get_escritura_reflects_updated_saldo(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-cliente",
        json={"monto": "400000.00", "fecha": PAGO_FECHA},
    )

    detail = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["total_pagado"] == "400000.00"
    assert body["saldo_pendiente"] != created["costo_total"]


@pytest.mark.asyncio
async def test_create_pago_cliente_exceso_returns_400(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    from decimal import Decimal

    excess = (Decimal(created["costo_total"]) + Decimal("0.01")).quantize(Decimal("0.01"))
    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-cliente",
        json={"monto": format(excess, "f"), "fecha": PAGO_FECHA},
    )
    assert response.status_code == 400
    assert "saldo_pendiente" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_pago_cliente_closed_escritura_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await _pay_full(auth_client, created["id"], created["costo_total"])
    close = await auth_client.post(f"/api/v1/escrituras/{created['id']}/close")
    assert close.status_code == 200

    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-cliente",
        json={"monto": "1000.00", "fecha": PAGO_FECHA},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_pago_cliente_requires_auth(
    test_app,
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from httpx import ASGITransport

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        response = await anon_client.post(
            f"/api/v1/escrituras/{created['id']}/pagos-cliente",
            json={"monto": "1000.00", "fecha": PAGO_FECHA},
        )
    assert response.status_code == 401
