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
from schemas.pago_cliente import PagoClienteResponse
from schemas.pago_colegio import PagoColegioResponse
from services.escritura_errors import (
    EscrituraClosedError,
    EscrituraImpuestosBalanceError,
    EscrituraImpuestosPagosPendientesError,
    EscrituraNotFoundError,
    EscrituraSaldoPendienteError,
)
from services.escritura_service import (
    build_plazo_colegio_fields,
    build_saldo_fields,
    close_escritura,
    create_escritura,
    get_escritura,
    list_escrituras,
    update_escritura,
)
from services.impuesto_service import get_balance_impuestos

router = APIRouter(prefix="/escrituras", tags=["escrituras"])


def _to_response(escritura, *, balance_impuestos=None) -> EscrituraResponse:
    saldo = build_saldo_fields(escritura)
    plazo = build_plazo_colegio_fields(escritura)
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
        costo_total=saldo["costo_total"],
        total_pagado=saldo["total_pagado"],
        saldo_pendiente=saldo["saldo_pendiente"],
        pagada_al_100=saldo["pagada_al_100"],
        sobrepago=saldo["sobrepago"],
        total_leyes_notariales_proyectadas=saldo["total_leyes_notariales_proyectadas"],
        balance_impuestos=balance_impuestos,
        plazo_colegio=plazo,
        pagos_cliente=[
            PagoClienteResponse.model_validate(pago) for pago in escritura.pagos_cliente
        ],
        pagos_colegio=[PagoColegioResponse.model_validate(pago) for pago in escritura.pagos_colegio],
    )


async def _to_response_with_balance(db: AsyncSession, escritura) -> EscrituraResponse:
    balance = await get_balance_impuestos(db, escritura.id)
    return _to_response(escritura, balance_impuestos=balance)


@router.get("", response_model=list[EscrituraListItem])
async def list_escrituras_route(
    estado: EstadoEscritura | None = None,
    escribano_id: UUID | None = None,
    anio: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[EscrituraListItem]:
    escrituras = await list_escrituras(
        db,
        estado=estado,
        escribano_id=escribano_id,
        anio=anio,
        mes=mes,
    )
    items: list[EscrituraListItem] = []
    for escritura in escrituras:
        saldo = build_saldo_fields(escritura)
        plazo = build_plazo_colegio_fields(escritura)
        items.append(
            EscrituraListItem(
                id=escritura.id,
                nombre=escritura.nombre,
                estado=escritura.estado.value,
                escribano_id=escritura.escribano_id,
                escribano_nombre=escritura.escribano_nombre,
                usd_value=escritura.usd_value,
                created_at=escritura.created_at,
                costo_total=saldo["costo_total"],
                total_pagado=saldo["total_pagado"],
                saldo_pendiente=saldo["saldo_pendiente"],
                pagada_al_100=saldo["pagada_al_100"],
                sobrepago=saldo["sobrepago"],
                plazo_colegio=plazo,
            )
        )
    return items


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
    return await _to_response_with_balance(db, escritura)


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
    except EscrituraSaldoPendienteError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "No se puede cerrar la escritura: saldo pendiente de cobro",
                "saldo_pendiente": format(exc.saldo_pendiente, "f"),
            },
        ) from exc
    except EscrituraImpuestosPagosPendientesError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": exc.code,
                "detail": "No se puede cerrar la escritura: impuestos con pagos incompletos",
                "impuestos_pendientes": [
                    {
                        "impuesto_id": str(item["impuesto_id"]),
                        "tipo": item["tipo"],
                        "falta_cliente": item["falta_cliente"],
                        "falta_escribania": item["falta_escribania"],
                    }
                    for item in exc.impuestos_pendientes
                ],
            },
        ) from exc
    except EscrituraImpuestosBalanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": exc.code,
                "detail": "No se puede cerrar la escritura: balance de impuestos pendiente",
                "balance": format(exc.balance, "f"),
            },
        ) from exc
    return await _to_response_with_balance(db, escritura)
