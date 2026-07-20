from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.escritura import EstadoEscritura
from models.usuario import Usuario
from schemas.escritura import (
    EscrituraInput,
    EscrituraListItem,
    EscrituraResponse,
    EscrituraUpdate,
)
from schemas.factura import FacturaPrincipalResponse
from schemas.gasto import GastoAdicionalResponse
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.escritura_service import (
    close_escritura,
    create_escritura,
    get_escritura,
    list_escrituras,
    update_escritura,
)

router = APIRouter(prefix="/escrituras", tags=["escrituras"])


def _to_response(escritura) -> EscrituraResponse:
    return EscrituraResponse(
        id=escritura.id,
        nombre=escritura.nombre,
        estado=escritura.estado.value,
        escribano_id=escritura.escribano_id,
        escribano_nombre=escritura.escribano_nombre,
        usd_value=escritura.usd_value,
        dolar_mep=escritura.dolar_mep,
        dolar_nacion=escritura.dolar_nacion,
        config_version_id=escritura.config_version_id,
        created_at=escritura.created_at,
        closed_at=escritura.closed_at,
        updated_at=escritura.updated_at,
        factura=FacturaPrincipalResponse.model_validate(escritura.factura),
        gastos_adicionales=[
            GastoAdicionalResponse.model_validate(gasto) for gasto in escritura.gastos
        ],
    )


@router.get("", response_model=list[EscrituraListItem])
async def list_escrituras_route(
    estado: EstadoEscritura | None = None,
    escribano_id: UUID | None = None,
    anio: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[EscrituraListItem]:
    rows = await list_escrituras(
        db,
        estado=estado,
        escribano_id=escribano_id,
        anio=anio,
        mes=mes,
    )
    return [
        EscrituraListItem(
            id=escritura.id,
            nombre=escritura.nombre,
            estado=escritura.estado.value,
            escribano_id=escritura.escribano_id,
            escribano_nombre=escritura.escribano_nombre,
            usd_value=escritura.usd_value,
            created_at=escritura.created_at,
            total_factura=total_factura,
        )
        for escritura, total_factura in rows
    ]


@router.post("", response_model=EscrituraResponse, status_code=status.HTTP_201_CREATED)
async def create_escritura_route(
    payload: EscrituraInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EscrituraResponse:
    try:
        escritura = await create_escritura(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(escritura)


@router.get("/{escritura_id}", response_model=EscrituraResponse)
async def get_escritura_route(
    escritura_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EscrituraResponse:
    try:
        escritura = await get_escritura(db, escritura_id)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(escritura)


@router.patch("/{escritura_id}", response_model=EscrituraResponse)
async def update_escritura_route(
    escritura_id: UUID,
    payload: EscrituraUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EscrituraResponse:
    try:
        escritura = await update_escritura(db, escritura_id, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscrituraClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(escritura)


@router.post("/{escritura_id}/close", response_model=EscrituraResponse)
async def close_escritura_route(
    escritura_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EscrituraResponse:
    try:
        escritura = await close_escritura(db, escritura_id)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscrituraClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_response(escritura)
