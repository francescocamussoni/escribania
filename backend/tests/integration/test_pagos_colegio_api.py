import pytest
from httpx import ASGITransport, AsyncClient

from tests.integration.test_escrituras_api import (
    EXPECTED_FACTURA,
    PAGO_FECHA,
    _create_escritura,
    _pay_full,
)

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")


@pytest.mark.asyncio
async def test_create_pago_colegio_returns_201(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-colegio",
        json={"monto": "250000.00", "fecha": PAGO_FECHA, "concepto": "Aporte Colegio"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["escritura_id"] == created["id"]
    assert body["monto"] == "250000.00"
    assert body["concepto"] == "Aporte Colegio"


@pytest.mark.asyncio
async def test_create_pago_colegio_ok_con_saldo_cliente_pendiente(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    detail_before = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    assert detail_before.json()["saldo_pendiente"] == created["costo_total"]

    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/pagos-colegio",
        json={"monto": "150000.00", "fecha": PAGO_FECHA},
    )
    assert response.status_code == 201

    detail = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    body = detail.json()
    assert body["saldo_pendiente"] == created["costo_total"]
    assert len(body["pagos_colegio"]) == 1
    assert body["pagos_colegio"][0]["monto"] == "150000.00"


@pytest.mark.asyncio
async def test_get_escritura_includes_total_leyes_notariales_proyectadas(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    detail = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    assert detail.status_code == 200
    assert (
        detail.json()["total_leyes_notariales_proyectadas"]
        == EXPECTED_FACTURA["total_leyes_notariales"]
    )


@pytest.mark.asyncio
async def test_create_pago_colegio_closed_escritura_returns_409(
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
        f"/api/v1/escrituras/{created['id']}/pagos-colegio",
        json={"monto": "1000.00", "fecha": PAGO_FECHA},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_pago_colegio_requires_auth(
    test_app,
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        response = await anon_client.post(
            f"/api/v1/escrituras/{created['id']}/pagos-colegio",
            json={"monto": "1000.00", "fecha": PAGO_FECHA},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_legacy_gastos_endpoint_removed(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    response = await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/gastos",
        json={"monto": "1000.00", "fecha": PAGO_FECHA, "direccion": "entrada"},
    )
    assert response.status_code == 404
