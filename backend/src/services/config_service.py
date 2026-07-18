from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.configuracion import ConfiguracionFinanciera
from schemas.configuracion import ConfiguracionInput


async def get_active_config(session: AsyncSession) -> ConfiguracionFinanciera:
    config = await session.scalar(
        select(ConfiguracionFinanciera).order_by(ConfiguracionFinanciera.version.desc()).limit(1)
    )
    if config is None:
        raise RuntimeError("No active financial configuration found")
    return config


async def list_config_history(session: AsyncSession) -> list[ConfiguracionFinanciera]:
    result = await session.scalars(
        select(ConfiguracionFinanciera).order_by(ConfiguracionFinanciera.version.desc())
    )
    return list(result.all())


async def create_config_version(
    session: AsyncSession,
    data: ConfiguracionInput,
    *,
    created_by: uuid.UUID | None = None,
) -> ConfiguracionFinanciera:
    current = await get_active_config(session)
    next_version = current.version + 1

    row = ConfiguracionFinanciera(
        id=uuid.uuid4(),
        version=next_version,
        descripcion=data.descripcion,
        honorario_pct=data.honorario_pct,
        honorario_min=data.honorario_min,
        certificacion_pct=data.certificacion_pct,
        aporte_pct=data.aporte_pct,
        cinco_pct_hon_pct=data.cinco_pct_hon_pct,
        cinco_pct_hon_min=data.cinco_pct_hon_min,
        firma_honorarios=data.firma_honorarios,
        art2_a_pct=data.art2_a_pct,
        art12_a_pct=data.art12_a_pct,
        art12_a_min=data.art12_a_min,
        art12_c_pct=data.art12_c_pct,
        art12_f=data.art12_f,
        tasa_3pm_pct=data.tasa_3pm_pct,
        sellos_pct=data.sellos_pct,
        sellos_ajuste_fijo=data.sellos_ajuste_fijo,
        tasa_75pm_pct=data.tasa_75pm_pct,
        firma_impuestos=data.firma_impuestos,
        inscripcion=data.inscripcion,
        protocolo=data.protocolo,
        ii_certificados=data.ii_certificados,
        municipio=data.municipio,
        fotocopias_urgentes=data.fotocopias_urgentes,
        certificaciones_extra=data.certificaciones_extra,
        catastro=data.catastro,
        testimonio=data.testimonio,
        concuerda=data.concuerda,
        informes_notariales=data.informes_notariales,
        extracto=data.extracto,
        fotocopias_simples=data.fotocopias_simples,
        tasas_minimas=data.tasas_minimas,
        salario_secretarias_total=data.salario_secretarias_total,
        created_by=created_by,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
