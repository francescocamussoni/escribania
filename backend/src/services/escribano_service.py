from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.escribano import Escribano
from models.escritura import Escritura
from services.escribano_errors import (
    EscribanoDuplicateError,
    EscribanoHasEscriturasError,
    EscribanoNotFoundError,
)


async def list_active(session: AsyncSession) -> list[Escribano]:
    result = await session.execute(select(Escribano).order_by(Escribano.nombre))
    return list(result.scalars().all())


async def list_all(session: AsyncSession, *, include_inactive: bool = False) -> list[Escribano]:
    if include_inactive:
        result = await session.execute(
            select(Escribano)
            .execution_options(include_deleted=True)
            .order_by(Escribano.nombre)
        )
        return list(result.scalars().all())
    return await list_active(session)


async def get_active_by_id(session: AsyncSession, escribano_id: uuid.UUID) -> Escribano:
    escribano = await session.get(Escribano, escribano_id)
    if escribano is None or escribano.deleted_at is not None:
        raise EscribanoNotFoundError("Escribano not found or inactive")
    return escribano


async def _active_name_exists(session: AsyncSession, nombre: str) -> bool:
    normalized = nombre.strip()
    existing = await session.scalar(
        select(Escribano.id).where(func.lower(Escribano.nombre) == normalized.lower())
    )
    return existing is not None


async def create(session: AsyncSession, nombre: str) -> Escribano:
    trimmed = nombre.strip()
    if not trimmed:
        raise ValueError("nombre cannot be empty")
    if await _active_name_exists(session, trimmed):  # BR-ESC-001
        raise EscribanoDuplicateError("An active escribano with this name already exists")

    escribano = Escribano(id=uuid.uuid4(), nombre=trimmed)
    session.add(escribano)
    await session.commit()
    await session.refresh(escribano)
    return escribano


async def count_escrituras(session: AsyncSession, escribano_id: uuid.UUID) -> int:
    result = await session.scalar(
        select(func.count()).select_from(Escritura).where(Escritura.escribano_id == escribano_id)
    )
    return int(result or 0)


async def soft_delete(
    session: AsyncSession,
    escribano_id: uuid.UUID,
    *,
    force: bool = False,
) -> None:
    escribano = await session.get(Escribano, escribano_id)
    if escribano is None or escribano.deleted_at is not None:
        raise EscribanoNotFoundError("Escribano not found")

    count = await count_escrituras(session, escribano_id)
    if count > 0 and not force:  # BR-ESC-002
        raise EscribanoHasEscriturasError(count)

    escribano.soft_delete()  # BR003
    await session.commit()
