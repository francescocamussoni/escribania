import uuid

import pytest
from httpx import AsyncClient

from tests.integration.test_escrituras_api import (
    EXPECTED_FACTURA,
    _create_escritura,
    _pay_full,
)

MONOTRIBUTO_TOTAL_FACTURA = "9674809.01"


@pytest.mark.asyncio
async def test_patch_monotributista_recalculates_open_escrituras(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    costanza_id = escribano_ids["costanza"]

    # Ensure Costanza starts as non-monotributista for this test.
    await auth_client.patch(
        f"/api/v1/configuracion/escribanos/{costanza_id}",
        json={"monotributista": False},
    )

    open_esc = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Abierta monotributo test",
        escribano="costanza",
    )
    open_before = await auth_client.get(f"/api/v1/escrituras/{open_esc['id']}")
    assert open_before.json()["factura"]["iva"] == EXPECTED_FACTURA["iva"]

    closed_esc = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Cerrada monotributo test",
        escribano="costanza",
    )
    await _pay_full(auth_client, closed_esc["id"], closed_esc["costo_total"])
    close_response = await auth_client.post(f"/api/v1/escrituras/{closed_esc['id']}/close")
    assert close_response.status_code == 200
    closed_before = await auth_client.get(f"/api/v1/escrituras/{closed_esc['id']}")
    closed_iva_before = closed_before.json()["factura"]["iva"]
    closed_total_before = closed_before.json()["factura"]["total_factura"]

    patch_response = await auth_client.patch(
        f"/api/v1/configuracion/escribanos/{costanza_id}",
        json={"monotributista": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["monotributista"] is True

    open_after = await auth_client.get(f"/api/v1/escrituras/{open_esc['id']}")
    open_factura = open_after.json()["factura"]
    assert open_factura["iva"] == "0.00"
    assert open_factura["total_factura"] == open_factura["total_sin_iva"]
    assert open_factura["total_factura"] == MONOTRIBUTO_TOTAL_FACTURA

    closed_after = await auth_client.get(f"/api/v1/escrituras/{closed_esc['id']}")
    closed_factura = closed_after.json()["factura"]
    assert closed_factura["iva"] == closed_iva_before
    assert closed_factura["total_factura"] == closed_total_before


@pytest.mark.asyncio
async def test_new_escritura_uses_monotributista_flag(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    gabriel_id = escribano_ids["gabriel"]
    await auth_client.patch(
        f"/api/v1/configuracion/escribanos/{gabriel_id}",
        json={"monotributista": True},
    )

    created = await _create_escritura(
        auth_client,
        escribano_ids,
        cleanup_escrituras,
        nombre="Gabriel monotributo",
        escribano="gabriel",
    )
    assert created["factura"]["iva"] == "0.00"
    assert created["factura"]["total_factura"] == MONOTRIBUTO_TOTAL_FACTURA

    await auth_client.patch(
        f"/api/v1/configuracion/escribanos/{gabriel_id}",
        json={"monotributista": False},
    )


@pytest.mark.asyncio
async def test_patch_monotributista_inactive_escribano_returns_404(
    auth_client: AsyncClient,
    cleanup_escribanos: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/configuracion/escribanos",
        json={"nombre": "Inactivo Mono"},
    )
    assert created.status_code == 201
    escribano_id = created.json()["id"]
    cleanup_escribanos.append(uuid.UUID(escribano_id))

    deleted = await auth_client.delete(f"/api/v1/configuracion/escribanos/{escribano_id}")
    assert deleted.status_code == 204

    response = await auth_client.patch(
        f"/api/v1/configuracion/escribanos/{escribano_id}",
        json={"monotributista": True},
    )
    assert response.status_code == 404
