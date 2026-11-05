import pytest
from decimal import Decimal
from httpx import AsyncClient

from tests.integration.test_escrituras_api import EXPECTED_FACTURA, PAGO_FECHA, _create_escritura

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")

BULK_FECHA = "2026-07-22"


@pytest.mark.asyncio
async def test_bulk_preview_returns_pendientes(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created_a = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Bulk preview A",
    )
    created_b = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Bulk preview B",
        escribano="costanza",
    )

    response = await auth_client.post(
        "/api/v1/escrituras/pagos-colegio/bulk/preview",
        json={"escritura_ids": [created_a["id"], created_b["id"]]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    expected_total = str(Decimal(EXPECTED_FACTURA["total_impuestos"]) * 2)
    assert body["total_propuesto"] == expected_total
    for item in body["items"]:
        assert item["elegible"] is True
        assert item["motivo"] is None
        assert item["pendiente"] == EXPECTED_FACTURA["total_impuestos"]


@pytest.mark.asyncio
async def test_bulk_preview_excludes_closed_escritura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from tests.integration.test_escrituras_api import _pay_full

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await _pay_full(auth_client, created["id"], created["costo_total"])
    close = await auth_client.post(f"/api/v1/escrituras/{created['id']}/close")
    assert close.status_code == 200

    response = await auth_client.post(
        "/api/v1/escrituras/pagos-colegio/bulk/preview",
        json={"escritura_ids": [created["id"]]},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["elegible"] is False
    assert item["motivo"] == "cerrada"
    assert response.json()["total_propuesto"] == "0.00"


@pytest.mark.asyncio
async def test_bulk_confirm_creates_pagos_and_updates_plazo(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Bulk confirm",
    )
    total_impuestos = EXPECTED_FACTURA["total_impuestos"]

    response = await auth_client.post(
        "/api/v1/escrituras/pagos-colegio/bulk",
        json={
            "fecha": BULK_FECHA,
            "items": [
                {
                    "escritura_id": created["id"],
                    "monto": total_impuestos,
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["pagos"]) == 1
    assert body["pagos"][0]["tipo"] == "colegio"
    assert body["pagos"][0]["fecha"] == BULK_FECHA
    assert body["pagos"][0]["monto"] == total_impuestos
    assert body["total"] == total_impuestos

    detail = await auth_client.get(f"/api/v1/escrituras/{created['id']}")
    plazo = detail.json()["plazo_colegio"]
    assert plazo["estado"] == "pagado"
    assert plazo["monto_pagado"] == total_impuestos
    assert plazo["monto_pendiente"] == "0.00"


@pytest.mark.asyncio
async def test_bulk_confirm_rejects_ineligible_escritura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from tests.integration.test_escrituras_api import _pay_full

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await _pay_full(auth_client, created["id"], created["costo_total"])
    close = await auth_client.post(f"/api/v1/escrituras/{created['id']}/close")
    assert close.status_code == 200

    response = await auth_client.post(
        "/api/v1/escrituras/pagos-colegio/bulk",
        json={
            "fecha": BULK_FECHA,
            "items": [
                {
                    "escritura_id": created["id"],
                    "monto": "1000.00",
                }
            ],
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_bulk_confirm_appears_in_libro_salida(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Bulk libro salida",
    )

    bulk = await auth_client.post(
        "/api/v1/escrituras/pagos-colegio/bulk",
        json={
            "fecha": PAGO_FECHA,
            "items": [
                {
                    "escritura_id": created["id"],
                    "monto": "1500.00",
                }
            ],
        },
    )
    assert bulk.status_code == 201

    libro = await auth_client.get("/api/v1/libros/salida", params={"anio": 2026, "mes": 7})
    assert libro.status_code == 200
    lineas = libro.json()["lineas"]
    matching = [linea for linea in lineas if linea["escritura_id"] == created["id"]]
    assert len(matching) == 1
    assert matching[0]["tipo_pago"] == "colegio"
    assert matching[0]["monto"] == "1500.00"


@pytest.mark.asyncio
async def test_bulk_endpoints_require_auth(
    test_app,
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from httpx import ASGITransport, AsyncClient as RawAsyncClient

    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    transport = ASGITransport(app=test_app)
    async with RawAsyncClient(transport=transport, base_url="http://test") as anon_client:
        preview = await anon_client.post(
            "/api/v1/escrituras/pagos-colegio/bulk/preview",
            json={"escritura_ids": [created["id"]]},
        )
        confirm = await anon_client.post(
            "/api/v1/escrituras/pagos-colegio/bulk",
            json={
                "fecha": BULK_FECHA,
                "items": [{"escritura_id": created["id"], "monto": "100.00"}],
            },
        )
    assert preview.status_code == 401
    assert confirm.status_code == 401
