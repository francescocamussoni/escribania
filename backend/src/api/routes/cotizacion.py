from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.cotizacion import (
    CasaCotizacion,
    CotizacionAPIError,
    CotizacionNoDisponibleError,
    CotizacionResponse,
)
from services.cotizacion_service import get_exchange_rate

router = APIRouter(prefix="/cotizacion", tags=["cotizacion"])


@router.get("", response_model=CotizacionResponse)
async def get_cotizacion_route(
    casa: CasaCotizacion,
    fecha: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> CotizacionResponse:
    del db  # auth-only dependency; no DB access required
    query_date = fecha or date.today()
    try:
        return await get_exchange_rate(casa, query_date)
    except CotizacionNoDisponibleError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CotizacionAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
