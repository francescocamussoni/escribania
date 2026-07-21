from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.gasto_extraordinario import (
    GastoExtraordinarioInput,
    GastoExtraordinarioResponse,
    GastosExtraordinariosListResponse,
    GastoExtraordinarioUpdate,
)
from services.gasto_extraordinario_service import (
    GastoExtraordinarioNotFoundError,
    create_gasto,
    delete_gasto,
    list_by_month,
    update_gasto,
)

router = APIRouter(prefix="/gastos-extraordinarios", tags=["gastos-extraordinarios"])


def _default_period() -> tuple[int, int]:
    now = datetime.now(UTC)
    return now.year, now.month


@router.get("", response_model=GastosExtraordinariosListResponse)
async def list_gastos_extraordinarios_route(
    anio: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> GastosExtraordinariosListResponse:
    default_anio, default_mes = _default_period()
    return await list_by_month(db, anio or default_anio, mes or default_mes)


@router.post("", response_model=GastoExtraordinarioResponse, status_code=status.HTTP_201_CREATED)
async def create_gasto_extraordinario_route(
    payload: GastoExtraordinarioInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> GastoExtraordinarioResponse:
    return await create_gasto(db, payload)


@router.patch("/{gasto_id}", response_model=GastoExtraordinarioResponse)
async def update_gasto_extraordinario_route(
    gasto_id: UUID,
    payload: GastoExtraordinarioUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> GastoExtraordinarioResponse:
    try:
        return await update_gasto(db, gasto_id, payload)
    except GastoExtraordinarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gasto_extraordinario_route(
    gasto_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await delete_gasto(db, gasto_id)
    except GastoExtraordinarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
