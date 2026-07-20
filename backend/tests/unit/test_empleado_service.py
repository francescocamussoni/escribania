from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.empleado import SueldoHistorico
from services.empleado_service import (
    EmpleadoInvalidSueldoError,
    create,
    list_active,
    snapshot_month,
    soft_delete,
    update_sueldo,
)


@pytest.mark.asyncio
async def test_create_empleado(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Test Empleado", Decimal("1500000.00"))
        assert empleado.nombre == "Test Empleado"
        assert empleado.sueldo == Decimal("1500000.00")


@pytest.mark.asyncio
async def test_update_sueldo_reflects_immediately(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Sueldo Update", Decimal("1000000.00"))
        updated = await update_sueldo(session, empleado.id, Decimal("1200000.00"))
        assert updated.sueldo == Decimal("1200000.00")


@pytest.mark.asyncio
async def test_zero_sueldo_rejected(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        with pytest.raises(EmpleadoInvalidSueldoError):
            await create(session, "Zero Sueldo", Decimal("0"))


@pytest.mark.asyncio
async def test_negative_sueldo_rejected(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Neg Sueldo", Decimal("1000.00"))
        with pytest.raises(EmpleadoInvalidSueldoError):
            await update_sueldo(session, empleado.id, Decimal("-1"))


@pytest.mark.asyncio
async def test_soft_delete_excludes_from_active_list(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Delete Me", Decimal("1000.00"))
        await soft_delete(session, empleado.id)
        active = await list_active(session)
        assert all(row.id != empleado.id for row in active)


@pytest.mark.asyncio
async def test_snapshot_month_creates_historico(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Snapshot Emp", Decimal("900000.00"))
        created = await snapshot_month(session, 2026, 7)
        assert len(created) >= 1
        snapshot = next(row for row in created if row.empleado_id == empleado.id)
        assert snapshot.sueldo == Decimal("900000.00")
        assert snapshot.empleado_nombre == "Snapshot Emp"


@pytest.mark.asyncio
async def test_post_snapshot_sueldo_change_does_not_alter_historico(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        empleado = await create(session, "Historico Emp", Decimal("800000.00"))
        await snapshot_month(session, 2026, 6)
        await update_sueldo(session, empleado.id, Decimal("950000.00"))

        historico = await session.scalar(
            select(SueldoHistorico).where(
                SueldoHistorico.empleado_id == empleado.id,
                SueldoHistorico.anio == 2026,
                SueldoHistorico.mes == 6,
            )
        )
        assert historico is not None
        assert historico.sueldo == Decimal("800000.00")
