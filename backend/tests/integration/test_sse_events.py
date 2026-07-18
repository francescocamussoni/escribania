from __future__ import annotations

import asyncio
import json

import pytest
from httpx import AsyncClient

from events.publisher import event_hub

CANONICAL_PAYLOAD = {
    "nombre": "Compraventa Calle Falsa 123",
    "escribano": "costanza",
    "usd_value": "105000.00",
    "dolar_mep": "1450.34",
    "dolar_nacion": "1425.00",
}

GASTO_PAYLOAD = {
    "concepto": "Timbre extra",
    "monto": "50000.00",
    "direccion": "salida",
    "fecha": "2026-07-18",
}


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
    cleanup_escrituras: list,
) -> None:
    queue = event_hub.subscribe()
    try:
        response = await auth_client.post("/api/v1/escrituras", json=CANONICAL_PAYLOAD)
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
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post("/api/v1/escrituras", json=CANONICAL_PAYLOAD)
    assert created.status_code == 201
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
        assert response.status_code == 200

        data = await _wait_for_event(queue, "escritura.closed")
        assert data["escritura_id"] == escritura_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_gasto_created(
    auth_client: AsyncClient,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post("/api/v1/escrituras", json=CANONICAL_PAYLOAD)
    assert created.status_code == 201
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    queue = event_hub.subscribe()
    try:
        response = await auth_client.post(
            f"/api/v1/escrituras/{escritura_id}/gastos",
            json=GASTO_PAYLOAD,
        )
        assert response.status_code == 201
        gasto_id = response.json()["id"]

        data = await _wait_for_event(queue, "gasto.created")
        assert data["escritura_id"] == escritura_id
        assert data["gasto_id"] == gasto_id
    finally:
        event_hub.unsubscribe(queue)


@pytest.mark.asyncio
async def test_sse_requires_auth(client: AsyncClient, seeded_config) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 401
