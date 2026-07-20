from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura, EstadoEscritura
from models.pago_cliente import PagoCliente
from models.pago_colegio import PagoColegio
from schemas.libros import (
    DeudaResumenItem,
    LibroEntradaResponse,
    LibroLineaResponse,
    LibroSalidaResponse,
)
from services.escritura_service import build_saldo_fields

_ZERO = Decimal("0.00")


def _payment_date_bounds(anio: int, mes: int) -> tuple[date, date]:
    start = date(anio, mes, 1)
    if mes == 12:
        end = date(anio + 1, 1, 1)
    else:
        end = date(anio, mes + 1, 1)
    return start, end


def _pago_cliente_linea(pago: PagoCliente) -> LibroLineaResponse:
    return LibroLineaResponse(
        escritura_id=str(pago.escritura_id),
        escritura_nombre=pago.escritura.nombre,
        concepto=pago.concepto,
        monto=pago.monto,
        fecha_pago=pago.fecha,
    )


def _pago_colegio_linea(pago: PagoColegio) -> LibroLineaResponse:
    return LibroLineaResponse(
        escritura_id=str(pago.escritura_id),
        escritura_nombre=pago.escritura.nombre,
        concepto=pago.concepto,
        monto=pago.monto,
        fecha_pago=pago.fecha,
    )


async def _build_resumen_deudas(session: AsyncSession) -> list[DeudaResumenItem]:
    stmt = (
        select(Escritura)
        .options(
            selectinload(Escritura.factura),
            selectinload(Escritura.pagos_cliente),
        )
        .where(Escritura.estado == EstadoEscritura.ABIERTA)
        .order_by(Escritura.nombre)
    )
    escrituras = list((await session.execute(stmt)).scalars().all())

    resumen: list[DeudaResumenItem] = []
    for escritura in escrituras:
        if escritura.factura is None:
            continue
        saldo = build_saldo_fields(escritura)
        saldo_pendiente = saldo["saldo_pendiente"]
        assert isinstance(saldo_pendiente, Decimal)
        if saldo_pendiente <= _ZERO:
            continue
        resumen.append(
            DeudaResumenItem(
                escritura_id=str(escritura.id),
                escritura_nombre=escritura.nombre,
                costo_total=saldo["costo_total"],
                total_pagado=saldo["total_pagado"],
                saldo_pendiente=saldo_pendiente,
            )
        )
    return resumen


async def get_libro_entrada(session: AsyncSession, anio: int, mes: int) -> LibroEntradaResponse:
    start, end = _payment_date_bounds(anio, mes)
    stmt = (
        select(PagoCliente)
        .join(Escritura)
        .options(selectinload(PagoCliente.escritura))
        .where(PagoCliente.fecha >= start, PagoCliente.fecha < end)
        .order_by(PagoCliente.fecha, PagoCliente.created_at)
    )
    pagos = list((await session.execute(stmt)).scalars().all())
    lineas = [_pago_cliente_linea(pago) for pago in pagos]
    total = sum((linea.monto for linea in lineas), _ZERO)
    resumen_deudas = await _build_resumen_deudas(session)
    return LibroEntradaResponse(
        anio=anio,
        mes=mes,
        lineas=lineas,
        resumen_deudas=resumen_deudas,
        total=total,
    )


async def get_libro_salida(session: AsyncSession, anio: int, mes: int) -> LibroSalidaResponse:
    start, end = _payment_date_bounds(anio, mes)
    stmt = (
        select(PagoColegio)
        .join(Escritura)
        .options(selectinload(PagoColegio.escritura))
        .where(PagoColegio.fecha >= start, PagoColegio.fecha < end)
        .order_by(PagoColegio.fecha, PagoColegio.created_at)
    )
    pagos = list((await session.execute(stmt)).scalars().all())
    lineas = [_pago_colegio_linea(pago) for pago in pagos]
    total = sum((linea.monto for linea in lineas), _ZERO)
    return LibroSalidaResponse(anio=anio, mes=mes, lineas=lineas, total=total)
