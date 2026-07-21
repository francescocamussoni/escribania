from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura, EstadoEscritura
from models.impuesto_escritura import ImpuestoEscritura, TipoImpuesto
from events.publisher import publish
from schemas.impuesto import (
    BalanceImpuestosResponse,
    EstadoPagos,
    ImpuestoInput,
    ImpuestoPendienteItem,
    ImpuestoResponse,
    ImpuestosListResponse,
    ImpuestoUpdate,
    PagoImpuestoClienteResponse,
    PagoImpuestoEscribaniaResponse,
)
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.impuesto_balance import (
    ImpuestoPagoEstado,
    calc_balance,
    can_close_impuestos,
    impuestos_pendientes,
)
from services.impuesto_prorrateo import DireccionProrrateo as ProrrateoDir
from services.impuesto_prorrateo import calc_monto_sugerido

_CENTS = Decimal("0.01")
_ZERO = Decimal("0.00")


class ImpuestoNotFoundError(Exception):
    """Raised when an impuesto does not exist for the given escritura."""


class ImpuestoConPagosError(Exception):
    """Raised when deleting an impuesto that has registered payments (FR-028)."""


def _ensure_open(escritura: Escritura) -> None:
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Cannot modify a closed escritura")


async def _get_escritura_or_404(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await session.get(Escritura, escritura_id)
    if escritura is None:
        raise EscrituraNotFoundError("Escritura not found")
    return escritura


async def _get_impuesto_or_404(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
) -> ImpuestoEscritura:
    impuesto = await session.scalar(
        select(ImpuestoEscritura)
        .options(
            selectinload(ImpuestoEscritura.pago_cliente),
            selectinload(ImpuestoEscritura.pago_escribania),
        )
        .where(
            ImpuestoEscritura.id == impuesto_id,
            ImpuestoEscritura.escritura_id == escritura_id,
        )
    )
    if impuesto is None:
        raise ImpuestoNotFoundError("Impuesto not found")
    return impuesto


def _calc_sugerido(impuesto: ImpuestoEscritura) -> Decimal:
    return calc_monto_sugerido(
        impuesto.monto_total,
        impuesto.periodo_inicio,
        impuesto.periodo_fin,
        impuesto.fecha_corte,
        ProrrateoDir(impuesto.direccion_prorrateo.value),
    )


def _estado_pagos(impuesto: ImpuestoEscritura) -> EstadoPagos:
    tiene_cliente = impuesto.pago_cliente is not None
    tiene_escribania = impuesto.pago_escribania is not None
    if not tiene_cliente and not tiene_escribania:
        return "sin_pagos"
    if tiene_cliente and not tiene_escribania:
        return "solo_cliente"
    if not tiene_cliente and tiene_escribania:
        return "solo_escribania"
    return "completos"


def _to_response(impuesto: ImpuestoEscritura) -> ImpuestoResponse:
    return ImpuestoResponse(
        id=impuesto.id,
        escritura_id=impuesto.escritura_id,
        tipo=impuesto.tipo,
        monto_total=impuesto.monto_total,
        periodo_inicio=impuesto.periodo_inicio,
        periodo_fin=impuesto.periodo_fin,
        fecha_corte=impuesto.fecha_corte,
        direccion_prorrateo=impuesto.direccion_prorrateo,
        monto_prorrateado_sugerido=_calc_sugerido(impuesto),
        estado_pagos=_estado_pagos(impuesto),
        pago_cliente=(
            PagoImpuestoClienteResponse.model_validate(impuesto.pago_cliente)
            if impuesto.pago_cliente is not None
            else None
        ),
        pago_escribania=(
            PagoImpuestoEscribaniaResponse.model_validate(impuesto.pago_escribania)
            if impuesto.pago_escribania is not None
            else None
        ),
        created_at=impuesto.created_at,
        updated_at=impuesto.updated_at,
    )


def _build_balance(impuestos: list[ImpuestoEscritura]) -> BalanceImpuestosResponse:
    montos_cliente = [
        impuesto.pago_cliente.monto
        for impuesto in impuestos
        if impuesto.pago_cliente is not None
    ]
    montos_escribania = [
        impuesto.pago_escribania.monto
        for impuesto in impuestos
        if impuesto.pago_escribania is not None
    ]
    total_cliente = sum(montos_cliente, start=_ZERO).quantize(_CENTS)
    total_escribania = sum(montos_escribania, start=_ZERO).quantize(_CENTS)
    balance = calc_balance(montos_cliente, montos_escribania)

    estados = [
        ImpuestoPagoEstado(
            impuesto_id=impuesto.id,
            tipo=impuesto.tipo.value,
            tiene_pago_cliente=impuesto.pago_cliente is not None,
            tiene_pago_escribania=impuesto.pago_escribania is not None,
        )
        for impuesto in impuestos
    ]
    pendientes_raw = impuestos_pendientes(estados)
    pendientes = [
        ImpuestoPendienteItem(
            impuesto_id=item["impuesto_id"],
            tipo=TipoImpuesto(item["tipo"]),
            falta_cliente=item["falta_cliente"],
            falta_escribania=item["falta_escribania"],
        )
        for item in pendientes_raw
    ]

    return BalanceImpuestosResponse(
        total_cliente=total_cliente,
        total_escribania=total_escribania,
        balance=balance,
        impuestos_pendientes=pendientes,
        puede_cerrar=can_close_impuestos(balance, pendientes_raw),
    )


async def _publish_impuesto_event(
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
    event_type: str,
) -> None:
    escritura_id_str = str(escritura_id)
    payload = {
        "escritura_id": escritura_id_str,
        "impuesto_id": str(impuesto_id),
    }
    await publish(event_type, payload)
    await publish("libros_updated", {"escritura_id": escritura_id_str})
    await publish("liquidacion.updated", {"escritura_id": escritura_id_str})


async def get_balance_impuestos(
    session: AsyncSession,
    escritura_id: uuid.UUID,
) -> BalanceImpuestosResponse:
    result = await session.scalars(
        select(ImpuestoEscritura)
        .options(
            selectinload(ImpuestoEscritura.pago_cliente),
            selectinload(ImpuestoEscritura.pago_escribania),
        )
        .where(ImpuestoEscritura.escritura_id == escritura_id)
        .order_by(ImpuestoEscritura.created_at)
    )
    return _build_balance(list(result.all()))


async def create_impuesto(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    payload: ImpuestoInput,
) -> ImpuestoResponse:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)

    impuesto = ImpuestoEscritura(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        tipo=payload.tipo,
        monto_total=payload.monto_total.quantize(_CENTS),
        periodo_inicio=payload.periodo_inicio,
        periodo_fin=payload.periodo_fin,
        fecha_corte=payload.fecha_corte,
        direccion_prorrateo=payload.direccion_prorrateo,
    )
    session.add(impuesto)
    await session.commit()
    loaded = await _get_impuesto_or_404(session, escritura_id, impuesto.id)
    await _publish_impuesto_event(escritura_id, impuesto.id, "impuesto.updated")
    return _to_response(loaded)


async def list_impuestos(
    session: AsyncSession,
    escritura_id: uuid.UUID,
) -> ImpuestosListResponse:
    await _get_escritura_or_404(session, escritura_id)

    result = await session.scalars(
        select(ImpuestoEscritura)
        .options(
            selectinload(ImpuestoEscritura.pago_cliente),
            selectinload(ImpuestoEscritura.pago_escribania),
        )
        .where(ImpuestoEscritura.escritura_id == escritura_id)
        .order_by(ImpuestoEscritura.created_at)
    )
    impuestos = list(result.all())

    return ImpuestosListResponse(
        impuestos=[_to_response(impuesto) for impuesto in impuestos],
        balance=_build_balance(impuestos),
    )


async def update_impuesto(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
    payload: ImpuestoUpdate,
) -> ImpuestoResponse:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)
    impuesto = await _get_impuesto_or_404(session, escritura_id, impuesto_id)

    if payload.tipo is not None:
        impuesto.tipo = payload.tipo
    if payload.monto_total is not None:
        impuesto.monto_total = payload.monto_total.quantize(_CENTS)
    if payload.periodo_inicio is not None:
        impuesto.periodo_inicio = payload.periodo_inicio
    if payload.periodo_fin is not None:
        impuesto.periodo_fin = payload.periodo_fin
    if payload.fecha_corte is not None:
        impuesto.fecha_corte = payload.fecha_corte
    if payload.direccion_prorrateo is not None:
        impuesto.direccion_prorrateo = payload.direccion_prorrateo

    _calc_sugerido(impuesto)

    await session.commit()
    loaded = await _get_impuesto_or_404(session, escritura_id, impuesto_id)
    await _publish_impuesto_event(escritura_id, impuesto_id, "impuesto.updated")
    return _to_response(loaded)


async def delete_impuesto(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    impuesto_id: uuid.UUID,
) -> None:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)
    impuesto = await _get_impuesto_or_404(session, escritura_id, impuesto_id)

    if impuesto.pago_cliente is not None or impuesto.pago_escribania is not None:
        raise ImpuestoConPagosError("Cannot delete impuesto with registered payments")

    await session.delete(impuesto)
    await session.commit()
    await _publish_impuesto_event(escritura_id, impuesto_id, "impuesto.deleted")
