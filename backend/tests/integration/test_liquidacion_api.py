from datetime import UTC, date, datetime
from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient

from models.escritura import EstadoEscritura
from models.pago_cliente import PagoCliente
from helpers.escritura_factory import insert_test_escritura

TEST_YEAR = 2026
TEST_MONTH = 7
PAGO_FECHA = "2026-07-20"


def _dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH, day, 12, 0, 0, tzinfo=UTC)


def _prev_month_dt(day: int) -> datetime:
    return datetime(TEST_YEAR, TEST_MONTH - 1, day, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_get_liquidacion_returns_resumen(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    e1 = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Costanza",
        created_at=_dt(3),
    )
    e2 = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Gabriel",
        created_at=_dt(7),
        estado=EstadoEscritura.ABIERTA,
    )
    prev = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Victoria",
        created_at=_prev_month_dt(1),
        estado=EstadoEscritura.CERRADA,
    )
    cleanup_escrituras.extend([e1.id, e2.id, prev.id])

    pago1 = await auth_client.post(
        f"/api/v1/escrituras/{e1.id}/pagos-cliente",
        json={"monto": "200000.00", "fecha": PAGO_FECHA},
    )
    assert pago1.status_code == 201
    pago2 = await auth_client.post(
        f"/api/v1/escrituras/{e2.id}/pagos-cliente",
        json={"monto": "150000.00", "fecha": PAGO_FECHA},
    )
    assert pago2.status_code == 201
    db_session.add(
        PagoCliente(
            id=uuid.uuid4(),
            escritura_id=prev.id,
            concepto="Pago mes anterior",
            monto=Decimal("999999.00"),
            fecha=date(TEST_YEAR, TEST_MONTH - 1, 15),
        )
    )
    await db_session.commit()

    response = await auth_client.get(
        "/api/v1/liquidacion",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["anio"] == TEST_YEAR
    assert body["mes"] == TEST_MONTH
    assert body["total_costanza"] == "200000.00"
    assert body["total_gabriel"] == "150000.00"
    assert body["total_victoria"] == "0.00"
    assert body["total_global"] == "350000.00"

    por_escribano = {item["escribano_nombre"]: item for item in body["por_escribano"]}
    assert len(por_escribano["Costanza"]["escrituras"]) == 1
    assert por_escribano["Costanza"]["escrituras"][0]["escritura_id"] == str(e1.id)
    assert por_escribano["Costanza"]["escrituras"][0]["monto_cobrado"] == "200000.00"
    assert por_escribano["Gabriel"]["escrituras"][0]["escritura_id"] == str(e2.id)
    assert por_escribano["Gabriel"]["escrituras"][0]["monto_cobrado"] == "150000.00"
    assert por_escribano["Victoria"]["escrituras"] == []


@pytest.mark.asyncio
async def test_get_salarios_returns_escribanos_and_secretarias(
    auth_client: AsyncClient,
    db_session,
    seeded_config,
    cleanup_escrituras: list,
) -> None:
    from sqlalchemy import select

    from models.empleado import Empleado

    escritura = await insert_test_escritura(
        db_session,
        seeded_config,
        escribano_nombre="Costanza",
        created_at=_dt(4),
    )
    cleanup_escrituras.append(escritura.id)
    empleados = list((await db_session.execute(select(Empleado))).scalars().all())

    pago = await auth_client.post(
        f"/api/v1/escrituras/{escritura.id}/pagos-cliente",
        json={"monto": "300000.00", "fecha": PAGO_FECHA},
    )
    assert pago.status_code == 201

    response = await auth_client.get(
        "/api/v1/salarios",
        params={"anio": TEST_YEAR, "mes": TEST_MONTH},
    )
    assert response.status_code == 200

    body = response.json()
    costanza = next(item for item in body["escribanos"] if item["nombre"] == "Costanza")
    assert costanza["monto_total"] == "300000.00"
    assert costanza["escrituras"][0]["monto_cobrado"] == "300000.00"
    assert len(body["secretarias"]) == len(empleados)
    expected_total = sum((empleado.sueldo for empleado in empleados), Decimal("0.00"))
    assert body["secretarias"][0]["base_total"] == str(expected_total)
