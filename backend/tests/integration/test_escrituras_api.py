from decimal import Decimal

import pytest
from httpx import AsyncClient

BASE_PAYLOAD = {
    "usd_value": "105000.00",
    "dolar_mep": "1450.34",
    "dolar_nacion": "1425.00",
}

EXPECTED_FACTURA = {
    "monto_base_mep": "152285700.00",
    "precio_base_nacion": "149625000.00",
    "honorario_principal": "3654856.80",
    "certificacion": "456857.10",
    "suma_hon_cert": "4111713.90",
    "total_leyes_notariales": "1532857.00",
    "total_impuestos": "5311489.50",
    "total_gastos_admin": "95444.77",
    "total_factura": "11731403.68",
}


def _payload(escribano_ids: dict[str, str], *, nombre: str, escribano: str) -> dict[str, str]:
    return {
        **BASE_PAYLOAD,
        "nombre": nombre,
        "escribano_id": escribano_ids[escribano],
    }


def _assert_canonical_factura(factura: dict) -> None:
    for field, expected in EXPECTED_FACTURA.items():
        assert factura[field] == expected, f"{field}: expected {expected}, got {factura[field]}"


@pytest.mark.asyncio
async def test_create_escritura_calculates_factura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    response = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    assert response.status_code == 201

    body = response.json()
    cleanup_escrituras.append(body["id"])
    assert body["estado"] == "abierta"
    assert body["escribano_nombre"] == "Costanza"
    assert body["gastos_adicionales"] == []
    _assert_canonical_factura(body["factura"])


@pytest.mark.asyncio
async def test_list_escrituras_with_filters(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    create_costanza = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Escritura Costanza", escribano="costanza"),
    )
    create_gabriel = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Escritura Gabriel", escribano="gabriel"),
    )
    assert create_costanza.status_code == 201
    assert create_gabriel.status_code == 201

    costanza_id = create_costanza.json()["id"]
    gabriel_id = create_gabriel.json()["id"]
    gabriel_escribano_id = create_gabriel.json()["escribano_id"]
    cleanup_escrituras.extend([costanza_id, gabriel_id])

    by_escribano = await auth_client.get(
        "/api/v1/escrituras",
        params={"escribano_id": gabriel_escribano_id},
    )
    assert by_escribano.status_code == 200
    gabriel_items = by_escribano.json()
    assert len(gabriel_items) >= 1
    assert all(item["escribano_nombre"] == "Gabriel" for item in gabriel_items)

    by_estado = await auth_client.get("/api/v1/escrituras", params={"estado": "abierta"})
    assert by_estado.status_code == 200
    assert any(item["id"] == costanza_id for item in by_estado.json())

    created_at = create_costanza.json()["created_at"]
    year = int(created_at[0:4])
    month = int(created_at[5:7])
    by_month = await auth_client.get(
        "/api/v1/escrituras",
        params={"anio": year, "mes": month},
    )
    assert by_month.status_code == 200
    assert any(item["id"] == costanza_id for item in by_month.json())


@pytest.mark.asyncio
async def test_get_escritura_detail(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    assert created.status_code == 201
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    response = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["id"] == escritura_id
    assert "factura" in body
    assert isinstance(body["gastos_adicionales"], list)
    _assert_canonical_factura(body["factura"])


@pytest.mark.asyncio
async def test_patch_open_escritura_recalculates(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    config = await auth_client.get("/api/v1/configuracion")
    honorario_min = Decimal(config.json()["honorario_min"])
    honorario_pct = Decimal(config.json()["honorario_pct"])

    created = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    response = await auth_client.patch(
        f"/api/v1/escrituras/{escritura_id}",
        json={"usd_value": "10000.00"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["usd_value"] == "10000.00"
    monto_base = Decimal("10000.00") * Decimal("1450.34")
    expected_honorario = max(monto_base * honorario_pct, honorario_min).quantize(Decimal("0.01"))
    assert Decimal(body["factura"]["honorario_principal"]) == expected_honorario


@pytest.mark.asyncio
async def test_patch_closed_escritura_returns_409(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    closed = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert closed.status_code == 200
    assert closed.json()["estado"] == "cerrada"
    assert closed.json()["closed_at"] is not None

    response = await auth_client.patch(
        f"/api/v1/escrituras/{escritura_id}",
        json={"nombre": "No debe actualizarse"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_close_escritura_sets_cerrada(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    response = await auth_client.post(f"/api/v1/escrituras/{escritura_id}/close")
    assert response.status_code == 200

    body = response.json()
    assert body["estado"] == "cerrada"
    assert body["closed_at"] is not None


@pytest.mark.asyncio
async def test_add_gasto_to_open_escritura(
    auth_client: AsyncClient,
    escribano_ids: dict[str, str],
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    created = await auth_client.post(
        "/api/v1/escrituras",
        json=_payload(escribano_ids, nombre="Compraventa Calle Falsa 123", escribano="costanza"),
    )
    escritura_id = created.json()["id"]
    cleanup_escrituras.append(escritura_id)

    response = await auth_client.post(
        f"/api/v1/escrituras/{escritura_id}/gastos",
        json={
            "concepto": "Timbre extra",
            "monto": "50000.00",
            "direccion": "salida",
            "fecha": "2026-07-18",
        },
    )
    assert response.status_code == 201
    assert response.json()["concepto"] == "Timbre extra"

    detail = await auth_client.get(f"/api/v1/escrituras/{escritura_id}")
    assert len(detail.json()["gastos_adicionales"]) == 1


@pytest.mark.asyncio
async def test_escrituras_require_auth(client: AsyncClient, seeded_config) -> None:
    response = await client.get("/api/v1/escrituras")
    assert response.status_code == 401
