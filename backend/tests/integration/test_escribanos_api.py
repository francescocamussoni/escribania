import uuid

import pytest
from httpx import AsyncClient

from helpers.escritura_factory import insert_test_escritura
from datetime import UTC, datetime


@pytest.mark.asyncio
async def test_list_escribanos_returns_active(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/configuracion/escribanos")
    assert response.status_code == 200
    names = {row["nombre"] for row in response.json()}
    assert {"Costanza", "Gabriel", "Victoria"}.issubset(names)
    assert all(row["activo"] for row in response.json())


@pytest.mark.asyncio
async def test_create_escribano(auth_client: AsyncClient, cleanup_escribanos: list) -> None:
    response = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Martínez"},
    )
    assert response.status_code == 201
    body = response.json()
    cleanup_escribanos.append(uuid.UUID(body["id"]))
    assert body["nombre"] == "Martínez"
    assert body["activo"] is True


@pytest.mark.asyncio
async def test_create_duplicate_escribano_returns_409(auth_client: AsyncClient) -> None:
    first = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Duplicado Test"},
    )
    assert first.status_code == 201

    second = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Duplicado Test"},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_deactivate_without_escrituras_returns_204(
    auth_client: AsyncClient,
    cleanup_escribanos: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Sin Escrituras"},
    )
    escribano_id = created.json()["id"]
    cleanup_escribanos.append(uuid.UUID(escribano_id))

    response = await auth_client.delete(f"/api/v1/configuracion/escribanos/{escribano_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_deactivate_with_escrituras_without_force_returns_409(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from models.escribano import Escribano

    created = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Con Escrituras"},
    )
    escribano_id = uuid.UUID(created.json()["id"])

    escribano = await db_session.get(Escribano, escribano_id)
    assert escribano is not None
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre=escribano.nombre,
        created_at=datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC),
    )
    cleanup_escrituras.append(escritura.id)

    response = await auth_client.delete(f"/api/v1/configuracion/escribanos/{escribano_id}")
    assert response.status_code == 409
    assert response.json()["detail"]["escrituras_count"] == 1


@pytest.mark.asyncio
async def test_deactivate_with_force_returns_204(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from models.escribano import Escribano

    created = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Force Delete"},
    )
    escribano_id = uuid.UUID(created.json()["id"])

    escribano = await db_session.get(Escribano, escribano_id)
    assert escribano is not None
    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre=escribano.nombre,
        created_at=datetime(2026, 7, 11, 12, 0, 0, tzinfo=UTC),
    )
    cleanup_escrituras.append(escritura.id)

    response = await auth_client.delete(
        f"/api/v1/configuracion/escribanos/{escribano_id}",
        params={"force": "true"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reuse_inactive_name_allowed(auth_client: AsyncClient) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "García"},
    )
    escribano_id = created.json()["id"]

    deleted = await auth_client.delete(f"/api/v1/configuracion/escribanos/{escribano_id}")
    assert deleted.status_code == 204

    recreated = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "García"},
    )
    assert recreated.status_code == 201
