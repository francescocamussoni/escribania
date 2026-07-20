from __future__ import annotations

from datetime import date
from decimal import Decimal
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.escritura import Escritura
from models.gasto_adicional import DireccionGasto
from models.factura_principal import FacturaPrincipal
from schemas.libros import LibroLineaResponse, LibroResponse
from services.liquidacion_service import month_bounds

ZERO = Decimal("0.00")

ENTRADA_FACTURA_FIELDS: tuple[tuple[str, str], ...] = (
    ("honorario_principal", "Honorarios Profesionales"),
    ("certificacion", "Certificación"),
)

SALIDA_FACTURA_FIELDS: tuple[tuple[str, str], ...] = (
    ("tasa_3pm", "Ing. Brutos (3‰)"),
    ("sellos", "Sellos Fiscales"),
    ("tasa_75pm", "Tasa 7.5‰"),
    ("firma_impuestos", "Firma Impuestos"),
    ("art2_a", "Leyes Notariales Art. 2 inc. a)"),
    ("art12_a", "Leyes Notariales Art. 12 inc. a)"),
    ("art12_c", "Leyes Notariales Art. 12 inc. c)"),
    ("art12_f", "Leyes Notariales Art. 12 inc. f)"),
    ("inscripcion", "Inscripción"),
    ("protocolo", "Protocolo"),
    ("ii_certificados", "I.I. Certificados"),
    ("municipio", "Municipio"),
    ("fotocopias_urgentes", "Fotocopias Urgentes"),
    ("certificaciones_extra", "Certificaciones Extra"),
    ("catastro", "Catastro"),
    ("testimonio", "Testimonio"),
    ("concuerda", "Concuerda"),
    ("informes_notariales", "Informes Notariales"),
    ("extracto", "Extracto"),
    ("fotocopias_simples", "Fotocopias Simples"),
    ("tasas_minimas", "Tasas Mínimas"),
)


def _linea(
    escritura: Escritura,
    *,
    concepto: str,
    monto: Decimal,
) -> LibroLineaResponse:
    return LibroLineaResponse(
        escritura_id=str(escritura.id),
        escritura_nombre=escritura.nombre,
        concepto=concepto,
        monto=monto,
        fecha_escritura=escritura.created_at.date(),
    )


async def _fetch_escrituras_for_month(
    session: AsyncSession,
    anio: int,
    mes: int,
) -> list[Escritura]:
    start, end = month_bounds(anio, mes)
    stmt = (
        select(Escritura)
        .options(selectinload(Escritura.factura), selectinload(Escritura.gastos))
        .where(Escritura.created_at >= start, Escritura.created_at < end)
        .order_by(Escritura.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())


def _entrada_lines(escritura: Escritura, factura: FacturaPrincipal) -> list[LibroLineaResponse]:
    lineas: list[LibroLineaResponse] = []
    for field, label in ENTRADA_FACTURA_FIELDS:
        monto = getattr(factura, field)
        lineas.append(_linea(escritura, concepto=label, monto=monto))

    for gasto in escritura.gastos:
        if gasto.direccion == DireccionGasto.ENTRADA:
            lineas.append(_linea(escritura, concepto=gasto.concepto, monto=gasto.monto))

    return lineas


def _salida_lines(escritura: Escritura, factura: FacturaPrincipal) -> list[LibroLineaResponse]:
    lineas: list[LibroLineaResponse] = []
    for field, label in SALIDA_FACTURA_FIELDS:
        monto = getattr(factura, field)
        if monto > ZERO:
            lineas.append(_linea(escritura, concepto=label, monto=monto))

    for gasto in escritura.gastos:
        if gasto.direccion == DireccionGasto.SALIDA:
            lineas.append(_linea(escritura, concepto=gasto.concepto, monto=gasto.monto))

    return lineas


def _build_response(anio: int, mes: int, lineas: list[LibroLineaResponse]) -> LibroResponse:
    total = sum((linea.monto for linea in lineas), ZERO)
    return LibroResponse(anio=anio, mes=mes, lineas=lineas, total=total)


async def get_libro_entrada(session: AsyncSession, anio: int, mes: int) -> LibroResponse:
    escrituras = await _fetch_escrituras_for_month(session, anio, mes)
    lineas: list[LibroLineaResponse] = []
    for escritura in escrituras:
        if escritura.factura is None:
            continue
        lineas.extend(_entrada_lines(escritura, escritura.factura))
    return _build_response(anio, mes, lineas)


async def get_libro_salida(session: AsyncSession, anio: int, mes: int) -> LibroResponse:
    escrituras = await _fetch_escrituras_for_month(session, anio, mes)
    lineas: list[LibroLineaResponse] = []
    for escritura in escrituras:
        if escritura.factura is None:
            continue
        lineas.extend(_salida_lines(escritura, escritura.factura))
    return _build_response(anio, mes, lineas)
