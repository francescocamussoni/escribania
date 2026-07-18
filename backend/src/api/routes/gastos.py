from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.gasto import GastoAdicionalInput, GastoAdicionalResponse
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.escritura_service import add_gasto_adicional

router = APIRouter(prefix="/escrituras", tags=["gastos"])


@router.post(
    "/{escritura_id}/gastos",
    response_model=GastoAdicionalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_gasto_route(
    escritura_id: UUID,
    payload: GastoAdicionalInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> GastoAdicionalResponse:
    try:
        gasto = await add_gasto_adicional(db, escritura_id, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscrituraClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return GastoAdicionalResponse.model_validate(gasto)
