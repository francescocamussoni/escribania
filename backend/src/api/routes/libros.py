from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.libros import LibroResponse
from services.libros_service import get_libro_entrada, get_libro_salida

router = APIRouter(prefix="/libros", tags=["libros"])


def _default_period() -> tuple[int, int]:
    now = datetime.now(UTC)
    return now.year, now.month


@router.get("/entrada", response_model=LibroResponse)
async def get_libro_entrada_route(
    anio: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> LibroResponse:
    default_anio, default_mes = _default_period()
    return await get_libro_entrada(db, anio or default_anio, mes or default_mes)


@router.get("/salida", response_model=LibroResponse)
async def get_libro_salida_route(
    anio: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> LibroResponse:
    default_anio, default_mes = _default_period()
    return await get_libro_salida(db, anio or default_anio, mes or default_mes)
