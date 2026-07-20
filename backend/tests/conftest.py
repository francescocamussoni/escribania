from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from config import get_settings
from database import get_db
from events.publisher import event_hub
from main import create_app
from models.configuracion import ConfiguracionFinanciera
from models.usuario import Usuario
from services.auth import hash_password
from services.calculo_factura import canonical_config

TEST_PASSWORD = "test-password-123"

pytest_plugins = ("helpers.escribano_helpers",)


class _SameSessionFactory:
    """Mimics async_sessionmaker for tests using `async with session_factory() as session`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> _SameSessionContext:
        return _SameSessionContext(self._session)


class _SameSessionContext:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *_: object) -> None:
        return None


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(db_engine: AsyncEngine) -> AsyncGenerator[AsyncConnection, None]:
    """Outer transaction per test — rolled back after the test finishes."""
    connection = await db_engine.connect()
    transaction = await connection.begin()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Shared session for the test; service-layer commits become nested savepoints."""
    session = AsyncSession(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def session_factory(db_session: AsyncSession) -> _SameSessionFactory:
    return _SameSessionFactory(db_session)


@pytest_asyncio.fixture
async def seeded_config(db_session: AsyncSession) -> AsyncGenerator[ConfiguracionFinanciera, None]:
    existing = await db_session.scalar(
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
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    yield row


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> AsyncGenerator[Usuario, None]:
    user = Usuario(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        hashed_password=hash_password(TEST_PASSWORD),
        nombre_display="Test User",
        activo=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user


@pytest_asyncio.fixture
async def test_app(db_session: AsyncSession):
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

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
async def isolated_liquidacion_month() -> AsyncGenerator[None, None]:
    """No-op: transactional rollback isolates liquidación data between tests."""
    yield


@pytest_asyncio.fixture
async def escribano_ids(auth_client: AsyncClient) -> dict[str, str]:
    response = await auth_client.get("/api/v1/configuracion/escribanos")
    assert response.status_code == 200
    return {row["nombre"].lower(): row["id"] for row in response.json()}


@pytest_asyncio.fixture
async def cleanup_escrituras() -> AsyncGenerator[list[uuid.UUID], None]:
    """Collects IDs for test readability; teardown is handled by transactional rollback."""
    yield []
