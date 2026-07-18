from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.liquidacion import LiquidacionResumen
from services.liquidacion_service import get_liquidacion_mensual

router = APIRouter(prefix="/liquidacion", tags=["liquidacion"])


@router.get("", response_model=LiquidacionResumen)
async def get_liquidacion_route(
    anio: int = Query(...),
    mes: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> LiquidacionResumen:
    return await get_liquidacion_mensual(db, anio, mes)
