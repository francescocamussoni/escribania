from decimal import Decimal

import pytest
from httpx import AsyncClient

from helpers.escritura_factory import canonical_escritura_payload


def _config_payload_from_active(active: dict) -> dict:
    payload = {k: v for k, v in active.items() if k not in ("id", "version", "created_at", "created_by")}
    return payload


@pytest.mark.asyncio
async def test_get_configuracion_returns_active_version(
    auth_client: AsyncClient,
    seeded_config,
) -> None:
    response = await auth_client.get("/api/v1/configuracion")
    assert response.status_code == 200

    body = response.json()
    assert body["version"] >= 1
    assert Decimal(body["salario_secretarias_total"]) > 0


@pytest.mark.asyncio
async def test_post_configuracion_creates_new_version(
    auth_client: AsyncClient,
    seeded_config,
) -> None:
    current = await auth_client.get("/api/v1/configuracion")
    assert current.status_code == 200
    current_body = current.json()
    previous_version = current_body["version"]

    payload = _config_payload_from_active(current_body)
    payload["salario_secretarias_total"] = "2500000.00"
    payload["descripcion"] = "Updated salary pool"

    created = await auth_client.post("/api/v1/configuracion", json=payload)
    assert created.status_code == 201

    new_body = created.json()
    assert new_body["version"] == previous_version + 1
    assert new_body["salario_secretarias_total"] == "2500000.00"

    active = await auth_client.get("/api/v1/configuracion")
    assert active.json()["version"] == previous_version + 1
    assert active.json()["salario_secretarias_total"] == "2500000.00"


@pytest.mark.asyncio
async def test_existing_escritura_keeps_original_config_fk(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    before = await auth_client.get("/api/v1/configuracion")
    original_config_id = before.json()["id"]

    created = await auth_client.post(
        "/api/v1/escrituras",
        json=canonical_escritura_payload(escribano_ids),
    )
    assert created.status_code == 201
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)
    assert created.json()["config_version_id"] == original_config_id

    payload = _config_payload_from_active(before.json())
    payload["honorario_min"] = "1300000.00"
    updated = await auth_client.post("/api/v1/configuracion", json=payload)
    assert updated.status_code == 201
    assert updated.json()["id"] != original_config_id

    detail = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    assert detail.status_code == 200
    assert detail.json()["config_version_id"] == original_config_id
    assert detail.json()["factura"]["honorario_principal"] == "3654856.80"


@pytest.mark.asyncio
async def test_config_history_lists_versions_desc(
    auth_client: AsyncClient,
    seeded_config,
) -> None:
    response = await auth_client.get("/api/v1/configuracion/history")
    assert response.status_code == 200

    versions = [row["version"] for row in response.json()]
    assert versions == sorted(versions, reverse=True)


@pytest.mark.asyncio
async def test_new_escritura_uses_latest_config_after_update(
    auth_client: AsyncClient,
    seeded_config,
    escribano_ids: dict[str, str],
    cleanup_escrituras: list,
) -> None:
    current = await auth_client.get("/api/v1/configuracion")
    payload = _config_payload_from_active(current.json())
    payload["honorario_min"] = "2000000.00"

    updated = await auth_client.post("/api/v1/configuracion", json=payload)
    new_config_id = updated.json()["id"]

    created = await auth_client.post(
        "/api/v1/escrituras",
        json=canonical_escritura_payload(escribano_ids, usd_value="10000.00"),
    )
    assert created.status_code == 201
    cleanup_escrituras.append(created.json()["id"])
    assert created.json()["config_version_id"] == new_config_id
    assert Decimal(created.json()["factura"]["honorario_principal"]) == Decimal("2000000.00")
