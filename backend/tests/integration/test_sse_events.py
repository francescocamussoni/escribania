from __future__ import annotations

import asyncio
import json

import pytest
from httpx import AsyncClient

from events.publisher import event_hub
from helpers.escritura_factory import canonical_escritura_payload
from tests.integration.test_escrituras_api import PAGO_FECHA, _create_escritura, _pay_full


async def _wait_for_event(queue: asyncio.Queue[str], expected_type: str, timeout: float = 5.0) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"Event '{expected_type}' not received within {timeout}s")

        payload = await asyncio.wait_for(queue.get(), timeout=remaining)
        message = json.loads(payload)
        if message["event"] == expected_type:
            return message["data"]


@pytest.mark.asyncio
async def test_sse_escritura_created(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(
            "/api/v1/escrituras",
            json=canonical_escritura_payload(escribano_ids),
        )
        assert response.status_code == 201
        escritura_id = response.json()["id"]
        cleanup_escrituras.append(escritura_id)

        data = await _wait_for_event(queue, "escritura.created")
        assert data["escritura_id"] == escritura_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_escritura_closed(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]
    await _pay_full(auth_client, escritura_id, created["costo_total"])

    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
        assert response.status_code == 200

        data = await _wait_for_event(queue, "escritura.closed")
        assert data["escritura_id"] == escritura_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_pago_cliente_created(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(
            f"/api/v1/escrituras/{escritura_id}/pagos-cliente",
            json={"monto": "50000.00", "fecha": PAGO_FECHA, "concepto": "Anticipo"},
        )
        assert response.status_code == 201
        pago_id = response.json()["id"]

        data = await _wait_for_event(queue, "pago_cliente.created")
        assert data["escritura_id"] == escritura_id
        assert data["pago_id"] == pago_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_pago_colegio_created(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    created = await _create_escritura(auth_client, escribano_ids, cleanup_escrituras)
    escritura_id = created["id"]

    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(
            f"/api/v1/escrituras/{escritura_id}/pagos-colegio",
            json={"monto": "75000.00", "fecha": PAGO_FECHA, "concepto": "Aporte"},
        )
        assert response.status_code == 201
        pago_id = response.json()["id"]

        data = await _wait_for_event(queue, "pago_colegio.created")
        assert data["escritura_id"] == escritura_id
        assert data["pago_id"] == pago_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_requires_auth(client: AsyncClient, seeded_config) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 401


GASTO_EXTRAORDINARIO_PAYLOAD = {
    "concepto": "Celulares SSE",
    "monto": "150000.00",
    "fecha": "2030-07-15",
}


@pytest.mark.asyncio
async def test_sse_gasto_extraordinario_created(auth_client: AsyncClient) -> None:
    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(
            "/api/v1/gastos-extraordinarios",
            json=GASTO_EXTRAORDINARIO_PAYLOAD,
        )
        assert response.status_code == 201
        gasto_id = response.json()["id"]

        data = await _wait_for_event(queue, "gasto_extraordinario.created")
        assert data["gasto_extraordinario_id"] == gasto_id
        assert data["anio"] == 2030
        assert data["mes"] == 7
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_gasto_extraordinario_updated(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/gastos-extraordinarios",
        json=GASTO_EXTRAORDINARIO_PAYLOAD,
    )
    assert created.status_code == 201
    gasto_id = created.json()["id"]

    queue = event_hub.subscribe()
    try:
        response = await auth_client.patch(
            f"/api/v1/gastos-extraordinarios/{gasto_id}",
            json={"monto": "175000.00"},
        )
        assert response.status_code == 200

        data = await _wait_for_event(queue, "gasto_extraordinario.updated")
        assert data["gasto_extraordinario_id"] == gasto_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_gasto_extraordinario_deleted(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/gastos-extraordinarios",
        json=GASTO_EXTRAORDINARIO_PAYLOAD,
    )
    assert created.status_code == 201
    gasto_id = created.json()["id"]

    queue = event_hub.subscribe()
    try:
        response = await auth_client.delete(f"/api/v1/gastos-extraordinarios/{gasto_id}")
        assert response.status_code == 204

        data = await _wait_for_event(queue, "gasto_extraordinario.deleted")
        assert data["gasto_extraordinario_id"] == gasto_id
    finally:
        event_hub.unsubscribe(queue)
