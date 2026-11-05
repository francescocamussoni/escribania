from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.configuracion import ConfiguracionFinanciera
from models.escribano import Escribano
from models.escritura import Escritura, EstadoEscritura
from models.factura_principal import FacturaPrincipal
from models.pago_cliente import PagoCliente
from models.pago_colegio import PagoColegio, TipoPagoEscribania
from services.calculo_factura import calcular_factura_completa
from services.escritura_service import config_from_row

USD = Decimal("105000.00")
DOLAR_MEP = Decimal("1450.34")
DOLAR_NACION = Decimal("1425.00")

CANONICAL_HONORARIO = Decimal("3654856.80")
CANONICAL_CERTIFICACION = Decimal("456857.10")
CANONICAL_SUBTOTAL = Decimal("4111713.90")

CANONICAL_API_BASE = {
    "usd_value": "105000.00",
    "dolar_mep": "1450.34",
    "dolar_nacion": "1425.00",
}


def canonical_escritura_payload(
    escribano_ids: dict[str, str],
    *,
    nombre: str = "Compraventa Calle Falsa 123",
    escribano: str = "costanza",
    **overrides: str,
) -> dict[str, str]:
    return {
        **CANONICAL_API_BASE,
        "nombre": nombre,
        "escribano_id": escribano_ids[escribano],
        **overrides,
    }


FACTURA_FIELDS = (
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
    "dif_honorarios",
    "total_parcial",
    "total_sin_iva",
    "iva",
    "total_factura",
)

PRE_009_FACTURA_FIELDS = tuple(
    field
    for field in FACTURA_FIELDS
    if field not in {"dif_honorarios", "total_parcial", "total_sin_iva", "iva"}
)


async def get_escribano_by_name(session: AsyncSession, nombre: str) -> Escribano:
    escribano = await session.scalar(select(Escribano).where(Escribano.nombre == nombre))
    if escribano is None:
        raise RuntimeError(
            f"Escribano '{nombre}' not found — run alembic upgrade head (migration 005)"
        )
    return escribano


async def insert_test_escritura(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    *,
    escribano_nombre: str = "Gabriel",
    created_at: datetime,
    estado: EstadoEscritura = EstadoEscritura.ABIERTA,
    nombre: str = "Escritura test",
    monotributista: bool | None = None,
) -> Escritura:
    escribano_id = await session.scalar(
        select(Escribano.id).where(Escribano.nombre == escribano_nombre)
    )
    if escribano_id is None:
        raise RuntimeError(
            f"Escribano '{escribano_nombre}' not found — run alembic upgrade head (migration 005)"
        )
    if monotributista is None:
        escribano = await get_escribano_by_name(session, escribano_nombre)
        monotributista = escribano.monotributista
    calc = calcular_factura_completa(
        USD,
        DOLAR_MEP,
        DOLAR_NACION,
        config_from_row(config_row),
        monotributista=monotributista,
    )
    escritura_id = uuid.uuid4()
    escritura = Escritura(
        id=escritura_id,
        nombre=nombre,
        escribano_id=escribano_id,
        escribano_nombre=escribano_nombre,
        usd_value=USD,
        dolar_mep=DOLAR_MEP,
        dolar_nacion=DOLAR_NACION,
        config_version_id=config_row.id,
        estado=estado,
        created_at=created_at,
        closed_at=created_at if estado == EstadoEscritura.CERRADA else None,
    )
    factura = FacturaPrincipal(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        **{field: calc[field] for field in FACTURA_FIELDS},
    )
    session.add(escritura)
    session.add(factura)
    await session.commit()
    await session.refresh(escritura)
    return escritura


async def insert_test_escritura_pre_009(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    *,
    escribano_nombre: str = "Gabriel",
    created_at: datetime,
    estado: EstadoEscritura = EstadoEscritura.ABIERTA,
    nombre: str = "Escritura test",
) -> Escritura:
    """Insert escritura/factura compatible with schema before migration 009."""
    from sqlalchemy import text

    escribano_id = await session.scalar(
        select(Escribano.id).where(Escribano.nombre == escribano_nombre)
    )
    if escribano_id is None:
        raise RuntimeError(
            f"Escribano '{escribano_nombre}' not found — run alembic upgrade head (migration 005)"
        )
    calc = calcular_factura_completa(
        USD,
        DOLAR_MEP,
        DOLAR_NACION,
        config_from_row(config_row),
        monotributista=False,
    )
    escritura_id = uuid.uuid4()
    factura_id = uuid.uuid4()
    escritura = Escritura(
        id=escritura_id,
        nombre=nombre,
        escribano_id=escribano_id,
        escribano_nombre=escribano_nombre,
        usd_value=USD,
        dolar_mep=DOLAR_MEP,
        dolar_nacion=DOLAR_NACION,
        config_version_id=config_row.id,
        estado=estado,
        created_at=created_at,
        closed_at=created_at if estado == EstadoEscritura.CERRADA else None,
    )
    session.add(escritura)
    await session.flush()

    columns = ", ".join(PRE_009_FACTURA_FIELDS)
    placeholders = ", ".join(f":{field}" for field in PRE_009_FACTURA_FIELDS)
    await session.execute(
        text(
            f"""
            INSERT INTO facturas_principales (id, escritura_id, {columns})
            VALUES (:id, :escritura_id, {placeholders})
            """
        ),
        {
            "id": factura_id,
            "escritura_id": escritura_id,
            **{field: calc[field] for field in PRE_009_FACTURA_FIELDS},
        },
    )
    await session.commit()
    await session.refresh(escritura)
    return escritura


async def insert_test_pago_cliente(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    monto: Decimal,
    fecha: date,
    concepto: str = "Pago test",
) -> PagoCliente:
    pago = PagoCliente(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        monto=monto,
        fecha=fecha,
        concepto=concepto,
    )
    session.add(pago)
    await session.commit()
    await session.refresh(pago)
    return pago


async def insert_test_pago_colegio(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    monto: Decimal,
    fecha: date,
    concepto: str = "Pago colegio test",
    tipo: TipoPagoEscribania = TipoPagoEscribania.COLEGIO,
) -> PagoColegio:
    """Insert a test pago colegio row. Default tipo is colegio."""
    pago = PagoColegio(
        id=uuid.uuid4(),
        escritura_id=escritura_id,
        monto=monto,
        fecha=fecha,
        concepto=concepto,
        tipo=tipo,
    )
    session.add(pago)
    await session.commit()
    await session.refresh(pago)
    return pago
