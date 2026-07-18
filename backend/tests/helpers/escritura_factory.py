from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from models.configuracion import ConfiguracionFinanciera
from models.escritura import Escritura, Escribano, EstadoEscritura
from models.factura_principal import FacturaPrincipal
from services.calculo_factura import calcular_factura_completa
from services.escritura_service import config_from_row

USD = Decimal("105000.00")
DOLAR_MEP = Decimal("1450.34")
DOLAR_NACION = Decimal("1425.00")

CANONICAL_HONORARIO = Decimal("3654856.80")
CANONICAL_CERTIFICACION = Decimal("456857.10")
CANONICAL_SUBTOTAL = Decimal("4111713.90")

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


async def insert_test_escritura(
    session: AsyncSession,
    config_row: ConfiguracionFinanciera,
    *,
    escribano: Escribano,
    created_at: datetime,
    estado: EstadoEscritura = EstadoEscritura.ABIERTA,
    nombre: str = "Escritura test",
) -> Escritura:
    calc = calcular_factura_completa(
        USD,
        DOLAR_MEP,
        DOLAR_NACION,
        config_from_row(config_row),
    )
    escritura_id = uuid.uuid4()
    escritura = Escritura(
        id=escritura_id,
        nombre=nombre,
        escribano=escribano,
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
