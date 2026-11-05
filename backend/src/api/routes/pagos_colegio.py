from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.pago_colegio import PagoColegioInput, PagoColegioResponse
from schemas.pago_colegio_bulk import (
    PagoColegioBulkPreviewRequest,
    PagoColegioBulkPreviewResponse,
    PagoColegioBulkRequest,
    PagoColegioBulkResponse,
)
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.pago_colegio_bulk_service import (
    PagoColegioBulkValidationError,
    confirm_bulk,
    preview_bulk,
)
from services.pago_colegio_service import create_pago

router = APIRouter(prefix="/escrituras", tags=["pagos-colegio"])


@router.post(
    "/pagos-colegio/bulk/preview",
    response_model=PagoColegioBulkPreviewResponse,
)
async def preview_pago_colegio_bulk_route(
    payload: PagoColegioBulkPreviewRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoColegioBulkPreviewResponse:
    try:
        return await preview_bulk(db, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/pagos-colegio/bulk",
    response_model=PagoColegioBulkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_pago_colegio_bulk_route(
    payload: PagoColegioBulkRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoColegioBulkResponse:
    try:
        result = await confirm_bulk(db, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PagoColegioBulkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return result


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
