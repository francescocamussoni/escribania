from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.escribano import EscribanoCreateRequest, EscribanoResponse
from services.escribano_errors import (
    EscribanoDuplicateError,
    EscribanoHasEscriturasError,
    EscribanoNotFoundError,
)
from services.escribano_service import create, list_all, soft_delete

router = APIRouter(prefix="/configuracion/escribanos", tags=["escribanos"])


@router.get("", response_model=list[EscribanoResponse])
async def list_escribanos_route(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[EscribanoResponse]:
    rows = await list_all(db, include_inactive=include_inactive)
    return [EscribanoResponse.from_orm_row(row) for row in rows]


@router.post("", response_model=EscribanoResponse, status_code=status.HTTP_201_CREATED)
async def create_escribano_route(
    payload: EscribanoCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EscribanoResponse:
    try:
        row = await create(db, payload.nombre)
    except EscribanoDuplicateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EscribanoResponse.from_orm_row(row)


@router.delete("/{escribano_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_escribano_route(
    escribano_id: UUID,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await soft_delete(db, escribano_id, force=force)
    except EscribanoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscribanoHasEscriturasError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": str(exc),
                "escrituras_count": exc.escrituras_count,
            },
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
