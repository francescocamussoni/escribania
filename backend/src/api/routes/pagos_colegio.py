from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.pago_colegio import PagoColegioInput, PagoColegioResponse
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.pago_colegio_service import create_pago

router = APIRouter(prefix="/escrituras", tags=["pagos-colegio"])


@router.post(
    "/{escritura_id}/pagos-colegio",
    response_model=PagoColegioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pago_colegio_route(
    escritura_id: UUID,
    payload: PagoColegioInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoColegioResponse:
    try:
        pago = await create_pago(db, escritura_id, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscrituraClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return PagoColegioResponse.model_validate(pago)
