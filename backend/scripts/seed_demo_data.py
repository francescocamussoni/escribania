"""Idempotent demo seed: escrituras y pagos para desarrollo local (Docker Compose).

Crea 4 escenarios × 3 escribanos (Costanza, Gabriel, Victoria) = 12 escrituras.
Solo corre si SEED_DEMO_DATA=true y ENVIRONMENT=local. No duplica si ya existen filas [DEMO].
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import get_settings
from database import AsyncSessionLocal
from models.configuracion import ConfiguracionFinanciera
from models.escribano import Escribano
from models.escritura import Escritura, EstadoEscritura
from models.factura_principal import FacturaPrincipal
from schemas.pago_cliente import PagoClienteInput
from schemas.pago_colegio import PagoColegioInput
from services.calculo_factura import calcular_factura_completa
from services.escritura_service import close_escritura, config_from_row, get_active_config
from services.pago_cliente_service import create_pago
from services.pago_colegio_service import create_pago as create_pago_colegio

DEMO_PREFIX = "[DEMO]"

DOLAR_MEP = Decimal("1450.34")
DOLAR_NACION = Decimal("1425.00")

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
    "total_factura",
)

ESCIBANOS_DEMO = (
    ("Costanza", Decimal("105000.00")),
    ("Gabriel", Decimal("95000.00")),
    ("Victoria", Decimal("85000.00")),
)

# Fechas fijas para libros / liquidación reproducibles
JUN_05 = datetime(2026, 6, 5, 10, 0, 0, tzinfo=UTC)
JUN_08 = datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC)
JUN_10 = datetime(2026, 6, 10, 10, 0, 0, tzinfo=UTC)
JUN_12 = date(2026, 6, 12)
JUN_15 = date(2026, 6, 15)
JUN_15_DT = datetime(2026, 6, 15, 18, 0, 0, tzinfo=UTC)
JUN_20 = date(2026, 6, 20)
JUL_05 = datetime(2026, 7, 5, 10, 0, 0, tzinfo=UTC)
JUL_05_D = date(2026, 7, 5)
JUL_10 = date(2026, 7, 10)
JUL_12_DT = datetime(2026, 7, 12, 18, 0, 0, tzinfo=UTC)
JUL_18 = date(2026, 7, 18)
JUL_20_DT = datetime(2026, 7, 20, 18, 0, 0, tzinfo=UTC)


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _pct(total: Decimal, percent: Decimal) -> Decimal:
    return _q(total * percent / Decimal("100"))


async def _get_escribano_by_name(session: AsyncSession, nombre: str) -> Escribano:
    escribano = await session.scalar(select(Escribano).where(Escribano.nombre == nombre))
    if escribano is None:
        raise RuntimeError(
            f"Escribano '{nombre}' not found — run alembic upgrade head (migration 005)"
        )
    return escribano


async def _demo_already_seeded(session: AsyncSession) -> bool:
    existing = await session.scalar(
        select(Escritura.id).where(Escritura.nombre.like(f"{DEMO_PREFIX}%")).limit(1)
    )
    return existing is not None


async def _insert_demo_escritura(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    *,
    escribano_nombre: str,
    nombre: str,
    created_at: datetime,
    usd_value: Decimal,
) -> Escritura:
    escribano = await _get_escribano_by_name(session, escribano_nombre)
    calc = calcular_factura_completa(
        usd_value,
        DOLAR_MEP,
        DOLAR_NACION,
        config_from_row(config_row),
    )
    escritura_id = uuid.uuid4()
    escritura = Escritura(
        id=escritura_id,
        nombre=nombre,
        escribano_id=escribano.id,
        escribano_nombre=escribano.nombre,
        usd_value=usd_value,
        dolar_mep=DOLAR_MEP,
        dolar_nacion=DOLAR_NACION,
        config_version_id=config_row.id,
        estado=EstadoEscritura.ABIERTA,
        created_at=created_at,
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


async def _costo_total(session: AsyncSession, escritura_id: uuid.UUID) -> Decimal:
    escritura = await session.scalar(
        select(Escritura)
        .options(selectinload(Escritura.factura))
        .where(Escritura.id == escritura_id)
    )
    if escritura is None or escritura.factura is None:
        raise RuntimeError(f"Escritura {escritura_id} sin factura")
    return escritura.factura.total_factura


async def _pay_cliente(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    monto: Decimal,
    fecha: date,
    concepto: str,
) -> None:
    await create_pago(
        session,
        escritura_id,
        PagoClienteInput(monto=monto, fecha=fecha, concepto=concepto),
    )


async def _pay_colegio(
    session: AsyncSession,
    escritura_id: uuid.UUID,
    *,
    monto: Decimal,
    fecha: date,
    concepto: str,
) -> None:
    await create_pago_colegio(
        session,
        escritura_id,
        PagoColegioInput(monto=monto, fecha=fecha, concepto=concepto),
    )


async def _close_at(session: AsyncSession, escritura_id: uuid.UUID, closed_at: datetime) -> None:
    await close_escritura(session, escritura_id)
    escritura = await session.get(Escritura, escritura_id)
    if escritura is None:
        raise RuntimeError(f"Escritura {escritura_id} not found after close")
    escritura.closed_at = closed_at
    await session.commit()


async def _seed_escribano_scenarios(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    escribano_nombre: str,
    usd_value: Decimal,
) -> None:
    prefix = f"{DEMO_PREFIX} {escribano_nombre}"

    # C1 — Creada y cerrada en junio 2026, todo pagado en junio
    c1 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=f"{prefix} — C1 Cerrada en junio (pagada)",
        created_at=JUN_10,
        usd_value=usd_value,
    )
    c1_total = await _costo_total(session, c1.id)
    await _pay_cliente(
        session,
        c1.id,
        monto=c1_total,
        fecha=JUN_12,
        concepto="Pago total junio",
    )
    await _close_at(session, c1.id, JUN_15_DT)

    # C2 — Abierta, creada en junio, pagos junio+julio parciales (+ pago colegio)
    c2 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=f"{prefix} — C2 Abierta con deuda (pagos jun+jul)",
        created_at=JUN_05,
        usd_value=usd_value,
    )
    c2_total = await _costo_total(session, c2.id)
    await _pay_cliente(
        session,
        c2.id,
        monto=_pct(c2_total, Decimal("40")),
        fecha=JUN_15,
        concepto="Anticipo junio",
    )
    await _pay_cliente(
        session,
        c2.id,
        monto=_pct(c2_total, Decimal("20")),
        fecha=JUL_10,
        concepto="Anticipo julio",
    )
    await _pay_colegio(
        session,
        c2.id,
        monto=Decimal("200000.00"),
        fecha=JUL_05_D,
        concepto="Aporte Colegio (con deuda cliente)",
    )

    # C3 — Cerrada, creada en junio, pagos junio+julio, saldada en julio
    c3 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=f"{prefix} — C3 Cerrada pagos jun+jul (pagada)",
        created_at=JUN_08,
        usd_value=usd_value,
    )
    c3_total = await _costo_total(session, c3.id)
    jun_payment = _pct(c3_total, Decimal("50"))
    await _pay_cliente(
        session,
        c3.id,
        monto=jun_payment,
        fecha=JUN_20,
        concepto="Anticipo junio",
    )
    await _pay_cliente(
        session,
        c3.id,
        monto=_q(c3_total - jun_payment),
        fecha=JUL_18,
        concepto="Saldo final julio",
    )
    await _close_at(session, c3.id, JUL_20_DT)

    # C4 — Creada y cerrada en julio 2026, todo pagado en julio
    c4 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=f"{prefix} — C4 Cerrada en julio (pagada)",
        created_at=JUL_05,
        usd_value=usd_value,
    )
    c4_total = await _costo_total(session, c4.id)
    await _pay_cliente(
        session,
        c4.id,
        monto=c4_total,
        fecha=JUL_10,
        concepto="Pago total julio",
    )
    await _close_at(session, c4.id, JUL_12_DT)


async def seed() -> None:
    settings = get_settings()
    if settings.environment != "local":
        print("SEED_DEMO_DATA skipped — ENVIRONMENT is not 'local'.")
        return
    if not settings.seed_demo_data:
        print("SEED_DEMO_DATA skipped — set SEED_DEMO_DATA=true to enable.")
        return

    async with AsyncSessionLocal() as session:
        if await _demo_already_seeded(session):
            print("Demo escrituras already seeded — skipping.")
            return

        config_row = await get_active_config(session)
        for escribano_nombre, usd_value in ESCIBANOS_DEMO:
            await _seed_escribano_scenarios(session, config_row, escribano_nombre, usd_value)

    print(
        f"Seeded {len(ESCIBANOS_DEMO) * 4} demo escrituras "
        f"({len(ESCIBANOS_DEMO)} escribanos × 4 escenarios)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
