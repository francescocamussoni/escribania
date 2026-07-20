from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.configuracion import ConfiguracionFinanciera
from models.escritura import Escritura, EstadoEscritura
from services.escribano_errors import EscribanoNotFoundError
from services.escribano_service import get_active_by_id
from models.factura_principal import FacturaPrincipal
from models.gasto_adicional import GastoAdicional
from schemas.escritura import EscrituraInput, EscrituraUpdate
from schemas.gasto import GastoAdicionalInput
from events.publisher import publish
from services.calculo_factura import ConfigCalculo, calcular_factura_completa
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError

FACTURA_CALC_FIELDS = (
    "monto_base_mep",
    "precio_base_nacion",
    "honorario_principal",
    "certificacion",
    "suma_hon_cert",
    "aporte_12pct",
    "cinco_pct_hon",
    "firma_honorarios",
    "subtotal_honorarios",
    "art2_a",
    "art12_a",
    "art12_c",
    "art12_f",
    "total_leyes_notariales",
    "tasa_3pm",
    "sellos",
    "tasa_75pm",
    "firma_impuestos",
    "total_impuestos",
    "inscripcion",
    "protocolo",
    "ii_certificados",
    "municipio",
    "fotocopias_urgentes",
    "certificaciones_extra",
    "catastro",
    "testimonio",
    "concuerda",
    "informes_notariales",
    "extracto",
    "fotocopias_simples",
    "tasas_minimas",
    "total_gastos_admin",
    "total_factura",
)


def config_from_row(row: ConfiguracionFinanciera) -> ConfigCalculo:
    return ConfigCalculo(
        honorario_pct=row.honorario_pct,
        honorario_min=row.honorario_min,
        certificacion_pct=row.certificacion_pct,
        aporte_pct=row.aporte_pct,
        cinco_pct_hon_pct=row.cinco_pct_hon_pct,
        cinco_pct_hon_min=row.cinco_pct_hon_min,
        firma_honorarios=row.firma_honorarios,
        art2_a_pct=row.art2_a_pct,
        art12_a_pct=row.art12_a_pct,
        art12_a_min=row.art12_a_min,
        art12_c_pct=row.art12_c_pct,
        art12_f=row.art12_f,
        tasa_3pm_pct=row.tasa_3pm_pct,
        sellos_pct=row.sellos_pct,
        sellos_ajuste_fijo=row.sellos_ajuste_fijo,
        tasa_75pm_pct=row.tasa_75pm_pct,
        firma_impuestos=row.firma_impuestos,
        inscripcion=row.inscripcion,
        protocolo=row.protocolo,
        ii_certificados=row.ii_certificados,
        municipio=row.municipio,
        fotocopias_urgentes=row.fotocopias_urgentes,
        certificaciones_extra=row.certificaciones_extra,
        catastro=row.catastro,
        testimonio=row.testimonio,
        concuerda=row.concuerda,
        informes_notariales=row.informes_notariales,
        extracto=row.extracto,
        fotocopias_simples=row.fotocopias_simples,
        tasas_minimas=row.tasas_minimas,
    )


async def get_active_config(session: AsyncSession) -> ConfiguracionFinanciera:
    config = await session.scalar(
        select(ConfiguracionFinanciera).order_by(ConfiguracionFinanciera.version.desc()).limit(1)
    )
    if config is None:
        raise RuntimeError("No active financial configuration found")
    return config


def _build_factura(escritura_id: uuid.UUID, calc: dict[str, Decimal]) -> FacturaPrincipal:
    return FacturaPrincipal(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        **{field: calc[field] for field in FACTURA_CALC_FIELDS},
    )


def _apply_calc_to_factura(factura: FacturaPrincipal, calc: dict[str, Decimal]) -> None:
    for field in FACTURA_CALC_FIELDS:
        setattr(factura, field, calc[field])


def _ensure_open(escritura: Escritura) -> None:
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Cannot modify a closed escritura")


async def _get_escritura_or_404(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await session.scalar(
        select(Escritura)
        .options(selectinload(Escritura.factura), selectinload(Escritura.gastos))
        .where(Escritura.id == escritura_id)
    )
    if escritura is None:
        raise EscrituraNotFoundError("Escritura not found")
    return escritura


async def _resolve_escribano(session: AsyncSession, escribano_id: uuid.UUID):
    try:
        return await get_active_by_id(session, escribano_id)
    except EscribanoNotFoundError as exc:
        raise ValueError("escribano_id does not reference an active escribano") from exc


async def create_escritura(session: AsyncSession, payload: EscrituraInput) -> Escritura:
    escribano = await _resolve_escribano(session, payload.escribano_id)
    config_row = await get_active_config(session)
    config = config_from_row(config_row)
    calc = calcular_factura_completa(
        payload.usd_value,
        payload.dolar_mep,
        payload.dolar_nacion,
        config,
    )

    escritura = Escritura(
        id=uuid.uuid4(),
        nombre=payload.nombre,
        escribano_id=escribano.id,
        escribano_nombre=escribano.nombre,
        usd_value=payload.usd_value,
        dolar_mep=payload.dolar_mep,
        dolar_nacion=payload.dolar_nacion,
        config_version_id=config_row.id,
        estado=EstadoEscritura.ABIERTA,
    )
    factura = _build_factura(escritura.id, calc)
    session.add(escritura)
    session.add(factura)
    await session.commit()

    escritura_id = escritura.id
    await publish("escritura.created", {"escritura_id": str(escritura_id)})
    await publish("liquidacion.updated", {"escritura_id": str(escritura_id)})
    await publish("libros_updated", {"escritura_id": str(escritura_id)})

    return await _get_escritura_or_404(session, escritura_id)


async def get_escritura(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    return await _get_escritura_or_404(session, escritura_id)


async def list_escrituras(
    session: AsyncSession,
    *,
    estado: EstadoEscritura | None = None,
    escribano_id: uuid.UUID | None = None,
    anio: int | None = None,
    mes: int | None = None,
) -> list[tuple[Escritura, Decimal]]:
    stmt = (
        select(Escritura, FacturaPrincipal.total_factura)
        .join(FacturaPrincipal, FacturaPrincipal.escritura_id == Escritura.id)
        .order_by(Escritura.created_at.desc())
    )
    if estado is not None:
        stmt = stmt.where(Escritura.estado == estado)
    if escribano_id is not None:
        stmt = stmt.where(Escritura.escribano_id == escribano_id)
    if anio is not None:
        stmt = stmt.where(extract("year", Escritura.created_at) == anio)
    if mes is not None:
        stmt = stmt.where(extract("month", Escritura.created_at) == mes)

    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def update_escritura(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    payload: EscrituraUpdate,
) -> Escritura:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)

    if payload.nombre is not None:
        escritura.nombre = payload.nombre
    if payload.escribano_id is not None:
        escribano = await _resolve_escribano(session, payload.escribano_id)
        escritura.escribano_id = escribano.id
        escritura.escribano_nombre = escribano.nombre
    if payload.usd_value is not None:
        escritura.usd_value = payload.usd_value
    if payload.dolar_mep is not None:
        escritura.dolar_mep = payload.dolar_mep
    if payload.dolar_nacion is not None:
        escritura.dolar_nacion = payload.dolar_nacion

    config_row = await session.get(ConfiguracionFinanciera, escritura.config_version_id)
    if config_row is None:
        raise RuntimeError("Configuration version not found for escritura")

    calc = calcular_factura_completa(
        escritura.usd_value,
        escritura.dolar_mep,
        escritura.dolar_nacion,
        config_from_row(config_row),
    )
    _apply_calc_to_factura(escritura.factura, calc)
    await session.commit()

    await publish("escritura.updated", {"escritura_id": str(escritura_id)})
    await publish("liquidacion.updated", {"escritura_id": str(escritura_id)})
    await publish("libros_updated", {"escritura_id": str(escritura_id)})

    return await _get_escritura_or_404(session, escritura_id)


async def close_escritura(session: AsyncSession, escritura_id: uuid.UUID) -> Escritura:
    escritura = await _get_escritura_or_404(session, escritura_id)
    if escritura.estado == EstadoEscritura.CERRADA:
        raise EscrituraClosedError("Escritura is already closed")

    escritura.estado = EstadoEscritura.CERRADA
    escritura.closed_at = datetime.now(UTC)
    await session.commit()

    await publish("escritura.closed", {"escritura_id": str(escritura_id)})
    await publish("liquidacion.updated", {"escritura_id": str(escritura_id)})
    await publish("libros_updated", {"escritura_id": str(escritura_id)})

    return await _get_escritura_or_404(session, escritura_id)


async def add_gasto_adicional(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    payload: GastoAdicionalInput,
) -> GastoAdicional:
    escritura = await _get_escritura_or_404(session, escritura_id)
    _ensure_open(escritura)

    gasto = GastoAdicional(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        concepto=payload.concepto,
        monto=payload.monto,
        direccion=payload.direccion,
        fecha=payload.fecha,
    )
    session.add(gasto)
    await session.commit()
    await session.refresh(gasto)

    await publish(
        "gasto.created",
        {"escritura_id": str(escritura_id), "gasto_id": str(gasto.id)},
    )
    await publish("liquidacion.updated", {"escritura_id": str(escritura_id)})
    await publish("libros_updated", {"escritura_id": str(escritura_id)})

    return gasto
