from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.empleado import Empleado, SueldoHistorico


class EmpleadoNotFoundError(Exception):
    pass


class EmpleadoDuplicateError(Exception):
    pass


class EmpleadoInvalidSueldoError(Exception):
    pass


async def list_active(session: AsyncSession) -> list[Empleado]:
    result = await session.execute(select(Empleado).order_by(Empleado.nombre))
    return list(result.scalars().all())


async def _active_empleado_name_exists(session: AsyncSession, nombre: str) -> bool:
    normalized = nombre.strip()
    existing = await session.scalar(
        select(Empleado.id).where(func.lower(Empleado.nombre) == normalized.lower())
    )
    return existing is not None


async def create(session: AsyncSession, nombre: str, sueldo: Decimal) -> Empleado:
    trimmed = nombre.strip()
    if not trimmed:
        raise ValueError("nombre cannot be empty")
    if sueldo <= 0:  # BR-EMP-001
        raise EmpleadoInvalidSueldoError("sueldo must be greater than 0")
    if await _active_empleado_name_exists(session, trimmed):
        raise EmpleadoDuplicateError("An active employee with this name already exists")

    empleado = Empleado(id=uuid.uuid4(), nombre=trimmed, sueldo=sueldo)
    session.add(empleado)
    await session.commit()
    await session.refresh(empleado)
    return empleado


async def update_sueldo(session: AsyncSession, empleado_id: uuid.UUID, sueldo: Decimal) -> Empleado:
    if sueldo <= 0:  # BR-EMP-001
        raise EmpleadoInvalidSueldoError("sueldo must be greater than 0")

    empleado = await session.get(Empleado, empleado_id)
    if empleado is None or empleado.deleted_at is not None:
        raise EmpleadoNotFoundError("Employee not found")

    empleado.sueldo = sueldo  # BR-EMP-002
    await session.commit()
    await session.refresh(empleado)
    return empleado


async def soft_delete(session: AsyncSession, empleado_id: uuid.UUID) -> None:
    empleado = await session.get(Empleado, empleado_id)
    if empleado is None or empleado.deleted_at is not None:
        raise EmpleadoNotFoundError("Employee not found")

    empleado.soft_delete()  # BR-EMP-004
    await session.commit()


async def snapshot_month(session: AsyncSession, anio: int, mes: int) -> list[SueldoHistorico]:
    """Generate immutable salary snapshots for all active employees. BR-SH-001, BR-SH-002."""
    empleados = await list_active(session)
    created: list[SueldoHistorico] = []

    for empleado in empleados:
        existing = await session.scalar(
            select(SueldoHistorico).where(
                SueldoHistorico.empleado_id == empleado.id,
                SueldoHistorico.anio == anio,
                SueldoHistorico.mes == mes,
            )
        )
        if existing is not None:
            continue

        snapshot = SueldoHistorico(
            id=uuid.uuid4(),
            empleado_id=empleado.id,
            empleado_nombre=empleado.nombre,
            anio=anio,
            mes=mes,
            sueldo=empleado.sueldo,
        )
        session.add(snapshot)
        created.append(snapshot)

    if created:
        await session.commit()
        for row in created:
            await session.refresh(row)
    return created
