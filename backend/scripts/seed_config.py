"""Seed ConfiguracionFinanciera v1 with canonical constitution values."""

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy import select

from config import get_settings
from database import AsyncSessionLocal
from models.configuracion import ConfiguracionFinanciera
from services.calculo_factura import canonical_config


async def seed() -> None:
    settings = get_settings()
    _ = settings  # ensure settings load without error

    config = canonical_config()
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(ConfiguracionFinanciera).where(ConfiguracionFinanciera.version == 1)
        )
        if existing:
            print("ConfiguracionFinanciera v1 already exists — skipping seed.")
            return

        row = ConfiguracionFinanciera(
            id=uuid.uuid4(),
            version=1,
            descripcion="Configuración inicial — fixture constitucional",
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
        print(f"Seeded ConfiguracionFinanciera v1 (id={row.id})")


if __name__ == "__main__":
    asyncio.run(seed())
