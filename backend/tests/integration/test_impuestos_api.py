"""Integration tests for impuestos API (WU-018)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from tests.integration.test_escrituras_api import PAGO_FECHA, _create_escritura, _pay_full

pytestmark = pytest.mark.usefixtures("isolated_liquidacion_month")

IMPUESTO_PAYLOAD = {
    "tipo": "API",
    "monto_total": "10000.00",
    "periodo_inicio": "2026-05-01",
    "periodo_fin": "2026-06-30",
    "fecha_corte": "2026-06-15",
    "direccion_prorrateo": "hacia_atras",
}

MONTO_SUGERIDO_ATRAS = "7540.98"
MONTO_SUGERIDO_ADELANTE = "2459.02"
PAGO_IMPUESTO_FECHA = "2026-07-15"


async def _create_impuesto(auth_client: AsyncClient, escritura_id: str) -> dict:
    response = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/impuestos",
        json=IMPUESTO_PAYLOAD,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_impuesto_returns_201_with_monto_sugerido(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    body = await _create_impuesto(auth_client, created["id"])

    assert body["escritura_id"] == created["id"]
    assert body["tipo"] == "API"
    assert body["monto_prorrateado_sugerido"] == MONTO_SUGERIDO_ATRAS
    assert body["estado_pagos"] == "sin_pagos"


@pytest.mark.asyncio
async def test_list_impuestos_includes_balance(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    await _create_impuesto(auth_client, created["id"])

    response = await auth_client.get(f"/api/v1/escrituras/{created['id']}/impuestos")
    assert response.status_code == 200
    body = response.json()
    assert len(body["impuestos"]) == 1
    assert body["balance"]["total_cliente"] == "0.00"
    assert body["balance"]["total_escribania"] == "0.00"
    assert body["balance"]["balance"] == "0.00"
    assert body["balance"]["puede_cerrar"] is False


@pytest.mark.asyncio
async def test_patch_impuesto_returns_200(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])

    response = await auth_client.patch(
        f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}",
        json={"direccion_prorrateo": "hacia_adelante"},
    )
    assert response.status_code == 200
    assert response.json()["monto_prorrateado_sugerido"] == MONTO_SUGERIDO_ADELANTE


@pytest.mark.asyncio
async def test_delete_impuesto_without_pagos_returns_204(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])

    response = await auth_client.delete(
        f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}",
    )
    assert response.status_code == 204

    listing = await auth_client.get(f"/api/v1/escrituras/{created['id']}/impuestos")
    assert listing.json()["impuestos"] == []


@pytest.mark.asyncio
async def test_create_impuesto_closed_escritura_returns_409(
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
        f"/api/v1/escrituras/{created['id']}/impuestos",
        json=IMPUESTO_PAYLOAD,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_impuestos_routes_require_auth(
    test_app,
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        response = await anon_client.get(f"/api/v1/escrituras/{created['id']}/impuestos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pago_cliente_post_patch_delete_cycle(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])
    base = f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}/pago-cliente"

    create = await auth_client.post(
        base,
        json={"monto": MONTO_SUGERIDO_ATRAS, "fecha": PAGO_IMPUESTO_FECHA},
    )
    assert create.status_code == 201
    pago_id = create.json()["id"]

    upsert = await auth_client.post(
        base,
        json={"monto": "8000.00", "fecha": PAGO_IMPUESTO_FECHA},
    )
    assert upsert.status_code == 200
    assert upsert.json()["id"] == pago_id

    patch = await auth_client.patch(
        base,
        json={"monto": "7500.00", "fecha": "2026-07-16"},
    )
    assert patch.status_code == 200
    assert patch.json()["monto"] == "7500.00"

    delete = await auth_client.delete(base)
    assert delete.status_code == 204

    listing = await auth_client.get(f"/api/v1/escrituras/{created['id']}/impuestos")
    item = listing.json()["impuestos"][0]
    assert item["estado_pagos"] == "sin_pagos"
    assert item["pago_cliente"] is None


@pytest.mark.asyncio
async def test_pago_cliente_closed_escritura_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])
    await _pay_full(auth_client, created["id"], created["costo_total"])
    base = f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}"
    await auth_client.post(
        f"{base}/pago-cliente",
        json={"monto": MONTO_SUGERIDO_ATRAS, "fecha": PAGO_IMPUESTO_FECHA},
    )
    await auth_client.post(
        f"{base}/pago-escribania",
        json={"monto": MONTO_SUGERIDO_ATRAS, "fecha": PAGO_IMPUESTO_FECHA},
    )
    close = await auth_client.post(f"/api/v1/escrituras/{created['id']}/close")
    assert close.status_code == 200

    response = await auth_client.post(
        f"{base}/pago-cliente",
        json={"monto": MONTO_SUGERIDO_ATRAS, "fecha": PAGO_IMPUESTO_FECHA},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pago_escribania_post_patch_delete_cycle(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_escribania_service.publish", AsyncMock())
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])
    base = f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}/pago-escribania"

    create = await auth_client.post(
        base,
        json={"monto": MONTO_SUGERIDO_ADELANTE, "fecha": PAGO_IMPUESTO_FECHA},
    )
    assert create.status_code == 201

    patch = await auth_client.patch(
        base,
        json={"monto": "2500.00", "fecha": "2026-07-18"},
    )
    assert patch.status_code == 200
    assert patch.json()["monto"] == "2500.00"

    delete = await auth_client.delete(base)
    assert delete.status_code == 204

    listing = await auth_client.get(f"/api/v1/escrituras/{created['id']}/impuestos")
    item = listing.json()["impuestos"][0]
    assert item["estado_pagos"] == "sin_pagos"


@pytest.mark.asyncio
async def test_delete_impuesto_with_pagos_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("services.pago_impuesto_cliente_service.publish", AsyncMock())
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    impuesto = await _create_impuesto(auth_client, created["id"])
    await auth_client.post(
        f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}/pago-cliente",
        json={"monto": MONTO_SUGERIDO_ATRAS, "fecha": PAGO_IMPUESTO_FECHA},
    )

    response = await auth_client.delete(
        f"/api/v1/escrituras/{created['id']}/impuestos/{impuesto['id']}",
    )
    assert response.status_code == 409
