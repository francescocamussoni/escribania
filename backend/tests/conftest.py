from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from config import get_settings
from database import get_db
from events.publisher import event_hub
from main import create_app
from models.configuracion import ConfiguracionFinanciera
from models.escritura import Escritura
from models.factura_principal import FacturaPrincipal
from models.gasto_adicional import GastoAdicional
from models.usuario import Usuario
from services.auth import hash_password
from services.calculo_factura import canonical_config

TEST_PASSWORD = "test-password-123"
LIQUIDACION_TEST_YEAR = 2026
LIQUIDACION_TEST_MONTH = 7


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def _session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_config(db_engine: AsyncEngine) -> AsyncGenerator[ConfiguracionFinanciera, None]:
    session_factory = _session_factory(db_engine)
    async with session_factory() as session:
        existing = await session.scalar(
            select(ConfiguracionFinanciera).order_by(ConfiguracionFinanciera.version.desc()).limit(1)
        )
        if existing is not None:
            yield existing
            return

        config = canonical_config()
        row = ConfiguracionFinanciera(
            id=uuid.uuid4(),
            version=1,
            descripcion="Test config",
            honorario_pct=config.honorario_pct,
            honorario_min=config.honorario_min,
            certificacion_pct=config.certificacion_pct,
            aporte_pct=config.aporte_pct,
            cinco_pct_hon_pct=config.cinco_pct_hon_pct,
            cinco_pct_hon_min=config.cinco_pct_hon_min,
            firma_honorarios=config.firma_honorarios,
            art2_a_pct=config.art2_a_pct,
            art12_a_pct=config.art12_a_pct,
            art12_a_min=config.art12_a_min,
            art12_c_pct=config.art12_c_pct,
            art12_f=config.art12_f,
            tasa_3pm_pct=config.tasa_3pm_pct,
            sellos_pct=config.sellos_pct,
            sellos_ajuste_fijo=config.sellos_ajuste_fijo,
            tasa_75pm_pct=config.tasa_75pm_pct,
            firma_impuestos=config.firma_impuestos,
            inscripcion=config.inscripcion,
            protocolo=config.protocolo,
            ii_certificados=config.ii_certificados,
            municipio=config.municipio,
            fotocopias_urgentes=config.fotocopias_urgentes,
            certificaciones_extra=config.certificaciones_extra,
            catastro=config.catastro,
            testimonio=config.testimonio,
            concuerda=config.concuerda,
            informes_notariales=config.informes_notariales,
            extracto=config.extracto,
            fotocopias_simples=config.fotocopias_simples,
            tasas_minimas=config.tasas_minimas,
            salario_secretarias_total=Decimal("2000000.00"),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        yield row


@pytest_asyncio.fixture
async def test_user(db_engine: AsyncEngine) -> AsyncGenerator[Usuario, None]:
    session_factory = _session_factory(db_engine)
    user = Usuario(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        hashed_password=hash_password(TEST_PASSWORD),
        nombre_display="Test User",
        activo=True,
    )

    async with session_factory() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)

    yield user

    async with session_factory() as session:
        await session.execute(delete(Usuario).where(Usuario.id == user.id))
        await session.commit()


@pytest_asyncio.fixture
async def test_app(db_engine: AsyncEngine):
    session_factory = _session_factory(db_engine)
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    await event_hub.start()
    yield app
    app.dependency_overrides.clear()
    await event_hub.stop()


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, test_user: Usuario) -> AsyncClient:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return client


@pytest_asyncio.fixture
async def isolated_liquidacion_month(db_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Clear escrituras in the canonical liquidación test month to avoid dev DB pollution."""
    start, end = _month_bounds(LIQUIDACION_TEST_YEAR, LIQUIDACION_TEST_MONTH)
    session_factory = _session_factory(db_engine)
    async with session_factory() as session:
        result = await session.execute(
            select(Escritura.id).where(
                Escritura.created_at >= start,
                Escritura.created_at < end,
            )
        )
        ids = list(result.scalars())
        if ids:
            await session.execute(delete(GastoAdicional).where(GastoAdicional.escritura_id.in_(ids)))
            await session.execute(delete(FacturaPrincipal).where(FacturaPrincipal.escritura_id.in_(ids)))
            await session.execute(delete(Escritura).where(Escritura.id.in_(ids)))
            await session.commit()
    yield


@pytest_asyncio.fixture
async def cleanup_escrituras(db_engine: AsyncEngine) -> AsyncGenerator[list[uuid.UUID], None]:
    created_ids: list[uuid.UUID] = []
    yield created_ids

    if not created_ids:
        return

    session_factory = _session_factory(db_engine)
    async with session_factory() as session:
        await session.execute(delete(GastoAdicional).where(GastoAdicional.escritura_id.in_(created_ids)))
        await session.execute(delete(FacturaPrincipal).where(FacturaPrincipal.escritura_id.in_(created_ids)))
        await session.execute(delete(Escritura).where(Escritura.id.in_(created_ids)))
        await session.commit()
