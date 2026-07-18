from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.salarios import PagoSalariosResumen
from services.salario_service import get_pagos_mensuales

router = APIRouter(prefix="/salarios", tags=["salarios"])


@router.get("", response_model=PagoSalariosResumen)
async def get_salarios_route(
    anio: int = Query(...),
    mes: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoSalariosResumen:
    return await get_pagos_mensuales(db, anio, mes)
