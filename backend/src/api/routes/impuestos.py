from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.pago_impuesto_cliente import PagoImpuestoCliente
from models.pago_impuesto_escribania import PagoImpuestoEscribania
from models.usuario import Usuario
from schemas.impuesto import (
    ImpuestoInput,
    ImpuestoResponse,
    ImpuestosListResponse,
    ImpuestoUpdate,
    PagoImpuestoClienteResponse,
    PagoImpuestoEscribaniaResponse,
    PagoImpuestoInput,
)
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.impuesto_service import (
    ImpuestoConPagosError,
    ImpuestoNotFoundError,
    create_impuesto,
    delete_impuesto,
    list_impuestos,
    update_impuesto,
)
from services.pago_impuesto_cliente_service import (
    PagoImpuestoClienteNotFoundError,
    delete_pago as delete_pago_cliente,
    update_pago as update_pago_cliente,
    upsert_pago as upsert_pago_cliente,
)
from services.pago_impuesto_escribania_service import (
    PagoImpuestoEscribaniaNotFoundError,
    delete_pago as delete_pago_escribania,
    update_pago as update_pago_escribania,
    upsert_pago as upsert_pago_escribania,
)

router = APIRouter(prefix="/escrituras", tags=["impuestos"])


def _map_escritura_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, EscrituraNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, EscrituraClosedError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ImpuestoNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ImpuestoConPagosError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


def _map_pago_cliente_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, PagoImpuestoClienteNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _map_escritura_errors(exc)


def _map_pago_escribania_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, PagoImpuestoEscribaniaNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _map_escritura_errors(exc)


@router.get("/{escritura_id}/impuestos", response_model=ImpuestosListResponse)
async def list_impuestos_route(
    escritura_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> ImpuestosListResponse:
    try:
        return await list_impuestos(db, escritura_id)
    except Exception as exc:
        raise _map_escritura_errors(exc) from exc


@router.post(
    "/{escritura_id}/impuestos",
    response_model=ImpuestoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_impuesto_route(
    escritura_id: UUID,
    payload: ImpuestoInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> ImpuestoResponse:
    try:
        return await create_impuesto(db, escritura_id, payload)
    except Exception as exc:
        raise _map_escritura_errors(exc) from exc


@router.patch(
    "/{escritura_id}/impuestos/{impuesto_id}",
    response_model=ImpuestoResponse,
)
async def update_impuesto_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    payload: ImpuestoUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> ImpuestoResponse:
    try:
        return await update_impuesto(db, escritura_id, impuesto_id, payload)
    except Exception as exc:
        raise _map_escritura_errors(exc) from exc


@router.delete(
    "/{escritura_id}/impuestos/{impuesto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_impuesto_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await delete_impuesto(db, escritura_id, impuesto_id)
    except Exception as exc:
        raise _map_escritura_errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-cliente",
    response_model=PagoImpuestoClienteResponse,
)
async def upsert_pago_cliente_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    payload: PagoImpuestoInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoImpuestoClienteResponse:
    existing = await db.scalar(
        select(PagoImpuestoCliente.id).where(
            PagoImpuestoCliente.escritura_id == escritura_id,
            PagoImpuestoCliente.impuesto_id == impuesto_id,
        )
    )
    try:
        pago = await upsert_pago_cliente(db, escritura_id, impuesto_id, payload)
    except Exception as exc:
        raise _map_pago_cliente_errors(exc) from exc
    response.status_code = (
        status.HTTP_200_OK if existing is not None else status.HTTP_201_CREATED
    )
    return PagoImpuestoClienteResponse.model_validate(pago)


@router.patch(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-cliente",
    response_model=PagoImpuestoClienteResponse,
)
async def update_pago_cliente_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    payload: PagoImpuestoInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoImpuestoClienteResponse:
    try:
        pago = await update_pago_cliente(db, escritura_id, impuesto_id, payload)
    except Exception as exc:
        raise _map_pago_cliente_errors(exc) from exc
    return PagoImpuestoClienteResponse.model_validate(pago)


@router.delete(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-cliente",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pago_cliente_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await delete_pago_cliente(db, escritura_id, impuesto_id)
    except Exception as exc:
        raise _map_pago_cliente_errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-escribania",
    response_model=PagoImpuestoEscribaniaResponse,
)
async def upsert_pago_escribania_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    payload: PagoImpuestoInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoImpuestoEscribaniaResponse:
    existing = await db.scalar(
        select(PagoImpuestoEscribania.id).where(
            PagoImpuestoEscribania.escritura_id == escritura_id,
            PagoImpuestoEscribania.impuesto_id == impuesto_id,
        )
    )
    try:
        pago = await upsert_pago_escribania(db, escritura_id, impuesto_id, payload)
    except Exception as exc:
        raise _map_pago_escribania_errors(exc) from exc
    response.status_code = (
        status.HTTP_200_OK if existing is not None else status.HTTP_201_CREATED
    )
    return PagoImpuestoEscribaniaResponse.model_validate(pago)


@router.patch(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-escribania",
    response_model=PagoImpuestoEscribaniaResponse,
)
async def update_pago_escribania_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    payload: PagoImpuestoInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoImpuestoEscribaniaResponse:
    try:
        pago = await update_pago_escribania(db, escritura_id, impuesto_id, payload)
    except Exception as exc:
        raise _map_pago_escribania_errors(exc) from exc
    return PagoImpuestoEscribaniaResponse.model_validate(pago)


@router.delete(
    "/{escritura_id}/impuestos/{impuesto_id}/pago-escribania",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pago_escribania_route(
    escritura_id: UUID,
    impuesto_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await delete_pago_escribania(db, escritura_id, impuesto_id)
    except Exception as exc:
        raise _map_pago_escribania_errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
