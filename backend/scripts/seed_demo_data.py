"""Idempotent demo seed: escrituras y pagos para desarrollo local (Docker Compose).

Año demo 2026:
- Ene–May y Ago–Dic: 1 escritura cerrada/mes/escribano (30), nombres de clientes ficticios.
- Jun–Jul: 4 escenarios/escribano (12), algunas abiertas con deuda.
- Costanza: 3 escrituras abiertas con fechas escalonadas (plazo verde/amarillo/rojo).
Total: 45 escrituras [DEMO] (seed v5).

v5: Costanza monotributista, pagos colegio con imputaciones mixtas, fechas relativas para plazo.

Solo corre si SEED_DEMO_DATA=true y ENVIRONMENT=local.
Si existe un seed viejo (conteo distinto), borra y re-crea.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import get_settings
from database import AsyncSessionLocal
from models.configuracion import ConfiguracionFinanciera
from models.escribano import Escribano
from models.escritura import Escritura, EstadoEscritura
from models.factura_principal import FacturaPrincipal
from models.gasto_extraordinario import GastoExtraordinario
from models.pago_cliente import PagoCliente
from models.pago_colegio import ImputacionPagoColegio, PagoColegio
from schemas.pago_cliente import PagoClienteInput
from schemas.pago_colegio import PagoColegioInput
from services.calculo_factura import calcular_factura_completa
from services.escritura_service import close_escritura, config_from_row, get_active_config, total_pagado_from_escritura
from services.pago_cliente_service import create_pago
from services.pago_colegio_service import create_pago as create_pago_colegio
from services.pago_saldo import is_sobrepago

DEMO_PREFIX = "[DEMO]"
DEMO_YEAR = 2026
DEMO_SEED_VERSION = 5
SCENARIOS_PER_ESCRIBANO = 4
PLAZO_SHOWCASE_COUNT = 3
CLOSED_MONTHS = (1, 2, 3, 4, 5, 8, 9, 10, 11, 12)
EXPECTED_DEMO_COUNT = len(CLOSED_MONTHS) * 3 + SCENARIOS_PER_ESCRIBANO * 3 + PLAZO_SHOWCASE_COUNT
EXPECTED_DEMO_GASTO_COUNT = 3

# Gastos extraordinarios julio 2026 (total $300.000 para reparto entre 3 escribanos)
DEMO_GASTOS_JULIO: list[tuple[str, Decimal, int]] = [
    ("Celulares oficina", Decimal("150000.00"), 8),
    ("Papel e insumos", Decimal("100000.00"), 12),
    ("Mantenimiento equipos", Decimal("50000.00"), 18),
]

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
    "dif_honorarios",
    "total_parcial",
    "total_sin_iva",
    "iva",
    "total_factura",
)

# (cliente ficticio, USD valor escritura) — 10 casos por escribano para meses cerrados
MONTHLY_CLIENTS: dict[str, list[tuple[str, Decimal]]] = {
    "Costanza": [
        ("Compraventa García / Rodríguez — Av. Caseros 1450", Decimal("102000")),
        ("Hipoteca López — Larrazábal 320", Decimal("98000")),
        ("Sucesión Martínez", Decimal("88000")),
        ("Donación Fernández / Acosta", Decimal("92000")),
        ("Compraventa Díaz — Brandsen 88", Decimal("110000")),
        ("Cancelación hipoteca Sánchez", Decimal("75000")),
        ("Compraventa Ruiz — Avellaneda 2100", Decimal("115000")),
        ("Subdivisión Torres — Wilde", Decimal("68000")),
        ("Hipoteca Romero (Banco Provincia)", Decimal("125000")),
        ("Compraventa Vega / Molina — Lanús", Decimal("95000")),
    ],
    "Gabriel": [
        ("Compraventa Álvarez / Giménez — Banfield", Decimal("90000")),
        ("Hipoteca Castro — Caballito", Decimal("118000")),
        ("Sucesión Morales", Decimal("82000")),
        ("Donación Ríos / Ponce", Decimal("77000")),
        ("Compraventa Medina — Flores", Decimal("105000")),
        ("Cancelación hipoteca Cabrera", Decimal("72000")),
        ("Compraventa Ibáñez — Parque Patricios", Decimal("108000")),
        ("Subdivisión Acuña — Pompeya", Decimal("65000")),
        ("Hipoteca Navarro (Galicia)", Decimal("122000")),
        ("Compraventa Silvia / Ortega — Barracas", Decimal("87000")),
    ],
    "Monica": [
        ("Compraventa Peralta / Núñez — San Telmo", Decimal("80000")),
        ("Hipoteca Castillo — Constitución", Decimal("112000")),
        ("Sucesión Benítez", Decimal("76000")),
        ("Donación Herrera / Lagos", Decimal("84000")),
        ("Compraventa Maldonado — La Boca", Decimal("99000")),
        ("Cancelación hipoteca Figueroa", Decimal("70000")),
        ("Compraventa Campos — San Cristóbal", Decimal("103000")),
        ("Subdivisión Aguirre — Balvanera", Decimal("62000")),
        ("Hipoteca Suárez (Santander)", Decimal("118000")),
        ("Compraventa Vera / Molina — Monserrat", Decimal("91000")),
    ],
}

# Escrituras abiertas de Costanza con created_at relativo a hoy (bandas plazo colegio)
PLAZO_SHOWCASE: list[tuple[str, int, Decimal]] = [
    ("Plazo colegio — banda verde (~30d)", 0, Decimal("105000")),
    ("Plazo colegio — banda amarilla (~15d)", 15, Decimal("108000")),
    ("Plazo colegio — banda roja (~2d)", 28, Decimal("102000")),
]
JUN_JUL_SCENARIOS: dict[str, list[tuple[str, Decimal]]] = {
    "Costanza": [
        ("Compraventa Peralta / Núñez — Quilmes", Decimal("105000")),
        ("Hipoteca Castillo (Galicia) — Bernal", Decimal("108000")),
        ("Sucesión Benítez — Avellaneda", Decimal("100000")),
        ("Donación Herrera — Wilde", Decimal("102000")),
    ],
    "Gabriel": [
        ("Compraventa Maldonado — Adrogué", Decimal("95000")),
        ("Hipoteca Suárez — Burzaco", Decimal("97000")),
        ("Sucesión Vera — Lomas de Zamora", Decimal("93000")),
        ("Donación Campos — Temperley", Decimal("96000")),
    ],
    "Monica": [
        ("Compraventa Ibáñez — Remedios de Escalada", Decimal("85000")),
        ("Hipoteca Navarro — Lanús Oeste", Decimal("88000")),
        ("Sucesión Ríos — Valentín Alsina", Decimal("82000")),
        ("Donación Álvarez — Sarandí", Decimal("86000")),
    ],
}


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _pct(total: Decimal, percent: Decimal) -> Decimal:
    return _q(total * percent / Decimal("100"))


def _demo_nombre(client_label: str) -> str:
    return f"{DEMO_PREFIX} {client_label}"


def _demo_seed_version_marker() -> str:
    return f"{DEMO_PREFIX} seed-version:{DEMO_SEED_VERSION}"


def _demo_gasto_concepto(label: str) -> str:
    return f"{DEMO_PREFIX} {label}"


def _dt(month: int, day: int, hour: int = 10) -> datetime:
    return datetime(DEMO_YEAR, month, day, hour, 0, 0, tzinfo=UTC)


def _d(month: int, day: int) -> date:
    return date(DEMO_YEAR, month, day)


async def _get_escribano_by_name(session: AsyncSession, nombre: str) -> Escribano:
    escribano = await session.scalar(select(Escribano).where(Escribano.nombre == nombre))
    if escribano is None:
        raise RuntimeError(
            f"Escribano '{nombre}' not found — run alembic upgrade head (migration 005)"
        )
    return escribano


async def _demo_count(session: AsyncSession) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(Escritura)
        .where(Escritura.nombre.like(f"{DEMO_PREFIX}%"))
    )
    return int(count or 0)


async def _demo_gasto_count(session: AsyncSession) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(GastoExtraordinario)
        .where(
            GastoExtraordinario.concepto.like(f"{DEMO_PREFIX}%"),
            GastoExtraordinario.concepto != _demo_seed_version_marker(),
        )
    )
    return int(count or 0)


async def _demo_seed_version_matches(session: AsyncSession) -> bool:
    count = await session.scalar(
        select(func.count())
        .select_from(GastoExtraordinario)
        .where(GastoExtraordinario.concepto == _demo_seed_version_marker())
    )
    return int(count or 0) > 0


async def _demo_has_sobrepago(session: AsyncSession) -> bool:
    escrituras = await session.scalars(
        select(Escritura)
        .options(selectinload(Escritura.factura), selectinload(Escritura.pagos_cliente))
        .where(Escritura.nombre.like(f"{DEMO_PREFIX}%"))
    )
    for escritura in escrituras:
        if escritura.factura is None:
            continue
        total_pagado = total_pagado_from_escritura(escritura)
        if is_sobrepago(escritura.factura.total_factura, total_pagado):
            return True
    return False


async def _demo_needs_refresh(session: AsyncSession) -> bool:
    demo_count = await _demo_count(session)
    demo_gasto_count = await _demo_gasto_count(session)
    if demo_count != EXPECTED_DEMO_COUNT:
        return True
    if demo_gasto_count != EXPECTED_DEMO_GASTO_COUNT:
        return True
    if not await _demo_seed_version_matches(session):
        return True
    return await _demo_has_sobrepago(session)


async def _wipe_demo_gastos(session: AsyncSession) -> None:
    result = await session.execute(
        delete(GastoExtraordinario).where(GastoExtraordinario.concepto.like(f"{DEMO_PREFIX}%"))
    )
    deleted = result.rowcount or 0
    if deleted:
        await session.commit()
        print(f"Removed {deleted} legacy demo gastos extraordinarios.")


async def _wipe_demo_data(session: AsyncSession) -> None:
    await _wipe_demo_gastos(session)
    ids = list(
        await session.scalars(select(Escritura.id).where(Escritura.nombre.like(f"{DEMO_PREFIX}%")))
    )
    if not ids:
        return
    await session.execute(delete(PagoCliente).where(PagoCliente.escritura_id.in_(ids)))
    await session.execute(delete(PagoColegio).where(PagoColegio.escritura_id.in_(ids)))
    await session.execute(delete(FacturaPrincipal).where(FacturaPrincipal.escritura_id.in_(ids)))
    await session.execute(delete(Escritura).where(Escritura.id.in_(ids)))
    await session.commit()
    print(f"Removed {len(ids)} legacy demo escrituras (re-seeding v{DEMO_SEED_VERSION}).")


async def _ensure_costanza_monotributista(session: AsyncSession) -> None:
    costanza = await _get_escribano_by_name(session, "Costanza")
    if not costanza.monotributista:
        costanza.monotributista = True
        await session.commit()


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
        monotributista=escribano.monotributista,
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
    imputacion: ImputacionPagoColegio = ImputacionPagoColegio.TOTAL_IMPUESTOS,
) -> None:
    await create_pago_colegio(
        session,
        escritura_id,
        PagoColegioInput(
            monto=monto,
            fecha=fecha,
            concepto=concepto,
            imputacion=imputacion,
        ),
    )


async def _close_at(session: AsyncSession, escritura_id: uuid.UUID, closed_at: datetime) -> None:
    await close_escritura(session, escritura_id)
    escritura = await session.get(Escritura, escritura_id)
    if escritura is None:
        raise RuntimeError(f"Escritura {escritura_id} not found after close")
    escritura.closed_at = closed_at
    await session.commit()


async def _seed_monthly_closed(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    escribano_nombre: str,
    month: int,
    client_label: str,
    usd_value: Decimal,
) -> None:
    """Una escritura cerrada en el mes (creada, cobrada y cerrada en el mismo mes)."""
    escritura = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=_demo_nombre(client_label),
        created_at=_dt(month, 8),
        usd_value=usd_value,
    )
    total = await _costo_total(session, escritura.id)
    await _pay_cliente(
        session,
        escritura.id,
        monto=total,
        fecha=_d(month, 18),
        concepto="Pago total cliente",
    )
    await _close_at(session, escritura.id, _dt(month, 25, hour=17))


async def _seed_jun_jul_scenarios(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    escribano_nombre: str,
    scenarios: list[tuple[str, Decimal]],
) -> None:
    """Cuatro escenarios en junio/julio: solo una escritura abierta con deuda (índice 1)."""
    name_jun_closed, usd_c1 = scenarios[0]
    name_open, usd_c2 = scenarios[1]
    name_junjul_closed, usd_c3 = scenarios[2]
    name_jul_closed, usd_c4 = scenarios[3]

    # Junio — cerrada y pagada en el mes
    c1 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=_demo_nombre(name_jun_closed),
        created_at=_dt(6, 10),
        usd_value=usd_c1,
    )
    c1_total = await _costo_total(session, c1.id)
    await _pay_cliente(session, c1.id, monto=c1_total, fecha=_d(6, 12), concepto="Pago total junio")
    await _close_at(session, c1.id, _dt(6, 15, hour=18))

    # Junio — abierta, pagos parciales junio+julio + pago colegio
    c2 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=_demo_nombre(name_open),
        created_at=_dt(6, 5),
        usd_value=usd_c2,
    )
    c2_total = await _costo_total(session, c2.id)
    await _pay_cliente(
        session,
        c2.id,
        monto=_pct(c2_total, Decimal("40")),
        fecha=_d(6, 15),
        concepto="Anticipo junio",
    )
    await _pay_cliente(
        session,
        c2.id,
        monto=_pct(c2_total, Decimal("20")),
        fecha=_d(7, 10),
        concepto="Anticipo julio",
    )
    await _pay_colegio(
        session,
        c2.id,
        monto=Decimal("200000.00"),
        fecha=_d(7, 5),
        concepto="Honorarios varios Colegio",
        imputacion=ImputacionPagoColegio.HONORARIOS_VARIOS,
    )
    if escribano_nombre == "Costanza":
        await _pay_colegio(
            session,
            c2.id,
            monto=Decimal("100000.00"),
            fecha=_d(7, 8),
            concepto="Aporte parcial impuestos",
            imputacion=ImputacionPagoColegio.TOTAL_IMPUESTOS,
        )

    # Junio–julio — cerrada tras pagos en ambos meses
    c3 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=_demo_nombre(name_junjul_closed),
        created_at=_dt(6, 8),
        usd_value=usd_c3,
    )
    c3_total = await _costo_total(session, c3.id)
    jun_payment = _pct(c3_total, Decimal("50"))
    await _pay_cliente(session, c3.id, monto=jun_payment, fecha=_d(6, 20), concepto="Anticipo junio")
    await _pay_cliente(
        session,
        c3.id,
        monto=_q(c3_total - jun_payment),
        fecha=_d(7, 18),
        concepto="Saldo final julio",
    )
    await _close_at(session, c3.id, _dt(7, 20, hour=18))

    # Julio — creada y cerrada en julio
    c4 = await _insert_demo_escritura(
        session,
        config_row,
        escribano_nombre=escribano_nombre,
        nombre=_demo_nombre(name_jul_closed),
        created_at=_dt(7, 5),
        usd_value=usd_c4,
    )
    c4_total = await _costo_total(session, c4.id)
    await _pay_cliente(session, c4.id, monto=c4_total, fecha=_d(7, 10), concepto="Pago total julio")
    await _close_at(session, c4.id, _dt(7, 12, hour=18))


async def _seed_plazo_showcase(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
) -> None:
    """Tres escrituras abiertas de Costanza con created_at escalonado (hoy, -15d, -28d)."""
    today = datetime.now(UTC).date()
    for index, (label, days_ago, usd_value) in enumerate(PLAZO_SHOWCASE):
        created_day = today - timedelta(days=days_ago)
        created_at = datetime(
            created_day.year,
            created_day.month,
            created_day.day,
            10,
            0,
            0,
            tzinfo=UTC,
        )
        escritura = await _insert_demo_escritura(
            session,
            config_row,
            escribano_nombre="Costanza",
            nombre=_demo_nombre(label),
            created_at=created_at,
            usd_value=usd_value,
        )
        if index == 1:
            await _pay_colegio(
                session,
                escritura.id,
                monto=Decimal("50000.00"),
                fecha=created_day,
                concepto="Honorarios varios (no cierra plazo)",
                imputacion=ImputacionPagoColegio.HONORARIOS_VARIOS,
            )
        elif index == 2:
            factura = await session.scalar(
                select(FacturaPrincipal).where(FacturaPrincipal.escritura_id == escritura.id)
            )
            if factura is not None:
                await _pay_colegio(
                    session,
                    escritura.id,
                    monto=_q(factura.total_impuestos / 2),
                    fecha=created_day,
                    concepto="Aporte parcial Total impuestos",
                    imputacion=ImputacionPagoColegio.TOTAL_IMPUESTOS,
                )


async def _seed_demo_gastos_julio(session: AsyncSession) -> None:
    for label, monto, day in DEMO_GASTOS_JULIO:
        session.add(
            GastoExtraordinario(
                id=uuid.uuid4(),
                concepto=_demo_gasto_concepto(label),
                monto=monto,
                fecha=_d(7, day),
            )
        )
    await session.commit()
    print(
        f"Seeded {EXPECTED_DEMO_GASTO_COUNT} demo gastos extraordinarios "
        f"(julio {DEMO_YEAR}, total $300.000)."
    )


async def _verify_demo_saldo(session: AsyncSession) -> None:
    if await _demo_has_sobrepago(session):
        raise RuntimeError("Demo seed inconsistente: quedaron escrituras con sobrepago.")


async def seed() -> None:
    settings = get_settings()
    if settings.environment != "local":
        print("SEED_DEMO_DATA skipped — ENVIRONMENT is not 'local'.")
        return
    if not settings.seed_demo_data:
        print("SEED_DEMO_DATA skipped — set SEED_DEMO_DATA=true to enable.")
        return

    async with AsyncSessionLocal() as session:
        if not await _demo_needs_refresh(session):
            print(
                f"Demo seed v{DEMO_SEED_VERSION} already present "
                f"({EXPECTED_DEMO_COUNT} escrituras, {EXPECTED_DEMO_GASTO_COUNT} gastos, sin sobrepago) — skipping."
            )
            return

        if await _demo_has_sobrepago(session):
            print("Demo escrituras con sobrepago detectado — regenerando dataset.")
        await _wipe_demo_data(session)

        config_row = await get_active_config(session)
        await _ensure_costanza_monotributista(session)
        for escribano_nombre, monthly_cases in MONTHLY_CLIENTS.items():
            for month_index, month in enumerate(CLOSED_MONTHS):
                client_label, usd_value = monthly_cases[month_index]
                await _seed_monthly_closed(
                    session,
                    config_row,
                    escribano_nombre,
                    month,
                    client_label,
                    usd_value,
                )
            await _seed_jun_jul_scenarios(
                session,
                config_row,
                escribano_nombre,
                JUN_JUL_SCENARIOS[escribano_nombre],
            )
        await _seed_plazo_showcase(session, config_row)
        await _seed_demo_gastos_julio(session)
        session.add(
            GastoExtraordinario(
                id=uuid.uuid4(),
                concepto=_demo_seed_version_marker(),
                monto=Decimal("0.01"),
                fecha=_d(1, 1),
            )
        )
        await session.commit()
        await _verify_demo_saldo(session)

    print(
        f"Seeded demo v{DEMO_SEED_VERSION}: {EXPECTED_DEMO_COUNT} escrituras "
        f"y {EXPECTED_DEMO_GASTO_COUNT} gastos extraordinarios "
        f"(año {DEMO_YEAR}, 3 escribanos, meses cerrados + escenarios jun/jul + plazo showcase)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
