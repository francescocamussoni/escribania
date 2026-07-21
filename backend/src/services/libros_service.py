from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura, EstadoEscritura
from models.gasto_extraordinario import GastoExtraordinario
from models.pago_cliente import PagoCliente
from models.pago_colegio import PagoColegio
from models.pago_impuesto_cliente import PagoImpuestoCliente
from models.pago_impuesto_escribania import PagoImpuestoEscribania
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
        origen="honorario",
    )


def _pago_colegio_linea(pago: PagoColegio) -> LibroLineaResponse:
    return LibroLineaResponse(
        escritura_id=str(pago.escritura_id),
        escritura_nombre=pago.escritura.nombre,
        concepto=pago.concepto,
        monto=pago.monto,
        fecha_pago=pago.fecha,
        origen="honorario",
    )


def _pago_impuesto_cliente_linea(pago: PagoImpuestoCliente) -> LibroLineaResponse:
    tipo = pago.impuesto.tipo
    return LibroLineaResponse(
        escritura_id=str(pago.escritura_id),
        escritura_nombre=pago.escritura.nombre,
        concepto=f"Impuesto {tipo.value}",
        monto=pago.monto,
        fecha_pago=pago.fecha,
        origen="impuesto",
        tipo_impuesto=tipo,
    )


def _pago_impuesto_escribania_linea(pago: PagoImpuestoEscribania) -> LibroLineaResponse:
    tipo = pago.impuesto.tipo
    return LibroLineaResponse(
        escritura_id=str(pago.escritura_id),
        escritura_nombre=pago.escritura.nombre,
        concepto=f"Impuesto {tipo.value}",
        monto=pago.monto,
        fecha_pago=pago.fecha,
        origen="impuesto",
        tipo_impuesto=tipo,
    )


def _gasto_extraordinario_linea(gasto: GastoExtraordinario) -> LibroLineaResponse:
    return LibroLineaResponse(
        escritura_id=None,
        escritura_nombre=None,
        concepto=gasto.concepto,
        monto=gasto.monto,
        fecha_pago=gasto.fecha,
        origen="extraordinario",
        gasto_extraordinario_id=str(gasto.id),
    )


def _sort_lineas(
  entries: list[tuple[date, datetime, LibroLineaResponse]],
) -> list[LibroLineaResponse]:
    entries.sort(key=lambda item: (item[0], item[1]))
    return [linea for _, _, linea in entries]


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
    pagos_cliente_stmt = (
        select(PagoCliente)
        .join(Escritura)
        .options(selectinload(PagoCliente.escritura))
        .where(PagoCliente.fecha >= start, PagoCliente.fecha < end)
    )
    pagos_impuesto_stmt = (
        select(PagoImpuestoCliente)
        .join(Escritura)
        .options(
            selectinload(PagoImpuestoCliente.escritura),
            selectinload(PagoImpuestoCliente.impuesto),
        )
        .where(PagoImpuestoCliente.fecha >= start, PagoImpuestoCliente.fecha < end)
    )
    pagos_cliente = list((await session.execute(pagos_cliente_stmt)).scalars().all())
    pagos_impuesto = list((await session.execute(pagos_impuesto_stmt)).scalars().all())

    entries: list[tuple[date, datetime, LibroLineaResponse]] = []
    for pago in pagos_cliente:
        entries.append((pago.fecha, pago.created_at, _pago_cliente_linea(pago)))
    for pago in pagos_impuesto:
        entries.append((pago.fecha, pago.created_at, _pago_impuesto_cliente_linea(pago)))

    lineas = _sort_lineas(entries)
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
    pagos_colegio_stmt = (
        select(PagoColegio)
        .join(Escritura)
        .options(selectinload(PagoColegio.escritura))
        .where(PagoColegio.fecha >= start, PagoColegio.fecha < end)
    )
    pagos_impuesto_stmt = (
        select(PagoImpuestoEscribania)
        .join(Escritura)
        .options(
            selectinload(PagoImpuestoEscribania.escritura),
            selectinload(PagoImpuestoEscribania.impuesto),
        )
        .where(PagoImpuestoEscribania.fecha >= start, PagoImpuestoEscribania.fecha < end)
    )
    pagos_colegio = list((await session.execute(pagos_colegio_stmt)).scalars().all())
    pagos_impuesto = list((await session.execute(pagos_impuesto_stmt)).scalars().all())
    gastos_stmt = (
        select(GastoExtraordinario)
        .where(GastoExtraordinario.fecha >= start, GastoExtraordinario.fecha < end)
    )
    gastos = list((await session.execute(gastos_stmt)).scalars().all())

    entries: list[tuple[date, datetime, LibroLineaResponse]] = []
    for pago in pagos_colegio:
        entries.append((pago.fecha, pago.created_at, _pago_colegio_linea(pago)))
    for pago in pagos_impuesto:
        entries.append((pago.fecha, pago.created_at, _pago_impuesto_escribania_linea(pago)))
    for gasto in gastos:
        entries.append((gasto.fecha, gasto.created_at, _gasto_extraordinario_linea(gasto)))

    lineas = _sort_lineas(entries)
    total = sum((linea.monto for linea in lineas), _ZERO)
    return LibroSalidaResponse(anio=anio, mes=mes, lineas=lineas, total=total)
