from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


TWOPLACES = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ConfigCalculo:
    honorario_pct: Decimal
    honorario_min: Decimal
    certificacion_pct: Decimal
    aporte_pct: Decimal
    cinco_pct_hon_pct: Decimal
    cinco_pct_hon_min: Decimal
    firma_honorarios: Decimal
    art2_a_pct: Decimal
    art12_a_pct: Decimal
    art12_a_min: Decimal
    art12_c_pct: Decimal
    art12_f: Decimal
    tasa_3pm_pct: Decimal
    sellos_pct: Decimal
    sellos_ajuste_fijo: Decimal
    tasa_75pm_pct: Decimal
    firma_impuestos: Decimal
    inscripcion: Decimal
    protocolo: Decimal
    ii_certificados: Decimal
    municipio: Decimal
    fotocopias_urgentes: Decimal
    certificaciones_extra: Decimal
    catastro: Decimal
    testimonio: Decimal
    concuerda: Decimal
    informes_notariales: Decimal
    extracto: Decimal
    fotocopias_simples: Decimal
    tasas_minimas: Decimal


def canonical_config() -> ConfigCalculo:
    """Default configuration matching constitution.md §5 canonical fixture."""
    return ConfigCalculo(
        honorario_pct=Decimal("0.024"),
        honorario_min=Decimal("1200000.00"),
        certificacion_pct=Decimal("0.003"),
        aporte_pct=Decimal("0.12"),
        cinco_pct_hon_pct=Decimal("0.05"),
        cinco_pct_hon_min=Decimal("150000.00"),
        firma_honorarios=Decimal("3750.00"),
        art2_a_pct=Decimal("0.0048"),
        art12_a_pct=Decimal("0.004"),
        art12_a_min=Decimal("455900.00"),
        art12_c_pct=Decimal("0.0012"),
        art12_f=Decimal("10000.00"),
        tasa_3pm_pct=Decimal("0.003"),
        sellos_pct=Decimal("0.025"),
        sellos_ajuste_fijo=Decimal("250.00"),
        tasa_75pm_pct=Decimal("0.0075"),
        firma_impuestos=Decimal("52.00"),
        inscripcion=Decimal("40000.00"),
        protocolo=Decimal("10320.00"),
        ii_certificados=Decimal("9100.00"),
        municipio=Decimal("7232.00"),
        fotocopias_urgentes=Decimal("6500.00"),
        certificaciones_extra=Decimal("5837.77"),
        catastro=Decimal("4500.00"),
        testimonio=Decimal("4160.00"),
        concuerda=Decimal("3370.00"),
        informes_notariales=Decimal("3000.00"),
        extracto=Decimal("1065.00"),
        fotocopias_simples=Decimal("320.00"),
        tasas_minimas=Decimal("40.00"),
    )


def validate_inputs(usd_value: Decimal, dolar_mep: Decimal, dolar_nacion: Decimal) -> None:
    if usd_value <= 0:
        raise ValueError("usd_value must be greater than zero")
    if dolar_mep <= 0:
        raise ValueError("dolar_mep must be greater than zero")
    if dolar_nacion <= 0:
        raise ValueError("dolar_nacion must be greater than zero")


def calcular_bases(
    usd_value: Decimal, dolar_mep: Decimal, dolar_nacion: Decimal
) -> tuple[Decimal, Decimal]:
    validate_inputs(usd_value, dolar_mep, dolar_nacion)
    monto_base_mep = _q(usd_value * dolar_mep)
    precio_base_nacion = _q(usd_value * dolar_nacion)
    return monto_base_mep, precio_base_nacion


def calcular_honorarios(monto: Decimal, config: ConfigCalculo) -> dict[str, Decimal]:
    honorario_principal = _q(max(monto * config.honorario_pct, config.honorario_min))
    certificacion = _q(monto * config.certificacion_pct)
    suma_hon_cert = _q(honorario_principal + certificacion)
    aporte_12pct = _q(suma_hon_cert * config.aporte_pct)
    cinco_pct_hon = _q(max(honorario_principal * config.cinco_pct_hon_pct, config.cinco_pct_hon_min))
    firma_honorarios = _q(config.firma_honorarios)
    subtotal_honorarios = _q(aporte_12pct + cinco_pct_hon + firma_honorarios)
    return {
        "honorario_principal": honorario_principal,
        "certificacion": certificacion,
        "suma_hon_cert": suma_hon_cert,
        "aporte_12pct": aporte_12pct,
        "cinco_pct_hon": cinco_pct_hon,
        "firma_honorarios": firma_honorarios,
        "subtotal_honorarios": subtotal_honorarios,
    }


def calcular_leyes_notariales(monto: Decimal, config: ConfigCalculo) -> dict[str, Decimal]:
    art2_a = _q(monto * config.art2_a_pct)
    art12_a = _q(max(monto * config.art12_a_pct, config.art12_a_min))
    art12_c = _q(monto * config.art12_c_pct)
    art12_f = _q(config.art12_f)
    total_leyes_notariales = _q(art2_a + art12_a + art12_c + art12_f)
    return {
        "art2_a": art2_a,
        "art12_a": art12_a,
        "art12_c": art12_c,
        "art12_f": art12_f,
        "total_leyes_notariales": total_leyes_notariales,
    }


def calcular_impuestos(precio: Decimal, config: ConfigCalculo) -> dict[str, Decimal]:
    tasa_3pm = _q(precio * config.tasa_3pm_pct)
    sellos = _q(precio * config.sellos_pct - config.sellos_ajuste_fijo)
    tasa_75pm = _q(precio * config.tasa_75pm_pct)
    firma_impuestos = _q(config.firma_impuestos)
    total_impuestos = _q(tasa_3pm + sellos + tasa_75pm + firma_impuestos)
    return {
        "tasa_3pm": tasa_3pm,
        "sellos": sellos,
        "tasa_75pm": tasa_75pm,
        "firma_impuestos": firma_impuestos,
        "total_impuestos": total_impuestos,
    }


def calcular_gastos_admin(config: ConfigCalculo) -> dict[str, Decimal]:
    items = {
        "inscripcion": _q(config.inscripcion),
        "protocolo": _q(config.protocolo),
        "ii_certificados": _q(config.ii_certificados),
        "municipio": _q(config.municipio),
        "fotocopias_urgentes": _q(config.fotocopias_urgentes),
        "certificaciones_extra": _q(config.certificaciones_extra),
        "catastro": _q(config.catastro),
        "testimonio": _q(config.testimonio),
        "concuerda": _q(config.concuerda),
        "informes_notariales": _q(config.informes_notariales),
        "extracto": _q(config.extracto),
        "fotocopias_simples": _q(config.fotocopias_simples),
        "tasas_minimas": _q(config.tasas_minimas),
    }
    items["total_gastos_admin"] = _q(sum(items.values()))
    return items


def calcular_factura_completa(
    usd_value: Decimal,
    dolar_mep: Decimal,
    dolar_nacion: Decimal,
    config: ConfigCalculo,
) -> dict[str, Any]:
    monto_base_mep, precio_base_nacion = calcular_bases(usd_value, dolar_mep, dolar_nacion)
    honorarios = calcular_honorarios(monto_base_mep, config)
    leyes = calcular_leyes_notariales(monto_base_mep, config)
    impuestos = calcular_impuestos(precio_base_nacion, config)
    gastos = calcular_gastos_admin(config)

    total_factura = _q(
        honorarios["suma_hon_cert"]
        + honorarios["subtotal_honorarios"]
        + leyes["total_leyes_notariales"]
        + impuestos["total_impuestos"]
        + gastos["total_gastos_admin"]
    )

    return {
        "monto_base_mep": monto_base_mep,
        "precio_base_nacion": precio_base_nacion,
        **honorarios,
        **leyes,
        **impuestos,
        **gastos,
        "total_factura": total_factura,
    }
