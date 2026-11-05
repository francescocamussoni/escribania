"""Catálogo de líneas de factura y máscara de montos efectivos (feature 009)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

TWOPLACES = Decimal("0.01")

FACTURA_LINEA_KEYS: tuple[str, ...] = (
    "honorario_principal",
    "certificacion",
    "aporte_12pct",
    "cinco_pct_hon",
    "firma_honorarios",
    "art2_a",
    "art12_a",
    "art12_c",
    "art12_f",
    "tasa_3pm",
    "sellos",
    "tasa_75pm",
    "firma_impuestos",
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
)

IMPUESTO_LINEA_KEYS: tuple[str, ...] = (
    "tasa_3pm",
    "sellos",
    "tasa_75pm",
    "firma_impuestos",
)

_LINEA_SECCION: dict[str, str] = {
    "honorario_principal": "honorarios",
    "certificacion": "honorarios",
    "aporte_12pct": "honorarios",
    "cinco_pct_hon": "honorarios",
    "firma_honorarios": "honorarios",
    "art2_a": "leyes_notariales",
    "art12_a": "leyes_notariales",
    "art12_c": "leyes_notariales",
    "art12_f": "leyes_notariales",
    "tasa_3pm": "impuestos",
    "sellos": "impuestos",
    "tasa_75pm": "impuestos",
    "firma_impuestos": "impuestos",
    "inscripcion": "gastos_admin",
    "protocolo": "gastos_admin",
    "ii_certificados": "gastos_admin",
    "municipio": "gastos_admin",
    "fotocopias_urgentes": "gastos_admin",
    "certificaciones_extra": "gastos_admin",
    "catastro": "gastos_admin",
    "testimonio": "gastos_admin",
    "concuerda": "gastos_admin",
    "informes_notariales": "gastos_admin",
    "extracto": "gastos_admin",
    "fotocopias_simples": "gastos_admin",
    "tasas_minimas": "gastos_admin",
}

_LINEA_LABELS: dict[str, str] = {
    "honorario_principal": "Honorario principal",
    "certificacion": "Certificación",
    "aporte_12pct": "Aporte 12%",
    "cinco_pct_hon": "5% honorarios",
    "firma_honorarios": "Firma honorarios",
    "art2_a": "Art. 2-a",
    "art12_a": "Art. 12-a",
    "art12_c": "Art. 12-c",
    "art12_f": "Art. 12-f",
    "tasa_3pm": "Tasa 3‰",
    "sellos": "Sellos",
    "tasa_75pm": "Tasa 7.5‰",
    "firma_impuestos": "Firma impuestos",
    "inscripcion": "Inscripción",
    "protocolo": "Protocolo",
    "ii_certificados": "II certificados",
    "municipio": "Municipio",
    "fotocopias_urgentes": "Fotocopias urgentes",
    "certificaciones_extra": "Certificaciones extra",
    "catastro": "Catastro",
    "testimonio": "Testimonio",
    "concuerda": "Concuerda",
    "informes_notariales": "Informes notariales",
    "extracto": "Extracto",
    "fotocopias_simples": "Fotocopias simples",
    "tasas_minimas": "Tasas mínimas",
}


class LineasFacturaValidationError(ValueError):
    """Raised when lineas_deshabilitadas violates business rules."""


@dataclass(frozen=True)
class FacturaLineaItem:
    key: str
    label: str
    monto: Decimal
    monto_efectivo: Decimal
    habilitada: bool
    seccion: str


@dataclass(frozen=True)
class FacturaEfectiva:
    lineas: tuple[FacturaLineaItem, ...]
    total_impuestos_efectivo: Decimal
    total_factura_efectivo: Decimal
    subtotal_honorarios_efectivo: Decimal
    total_leyes_notariales_efectivo: Decimal
    total_gastos_admin_efectivo: Decimal


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _monto_linea(calculo: dict[str, Any], key: str) -> Decimal:
    raw = calculo[key]
    if not isinstance(raw, Decimal):
        return _q(Decimal(str(raw)))
    return _q(raw)


def aplicar_lineas_habilitadas(
    calculo: dict[str, Any],
    lineas_deshabilitadas: list[str],
) -> FacturaEfectiva:
    """Apply disabled-line mask; recalculate effective totals (constitution single-reading)."""
    deshabilitadas = set(lineas_deshabilitadas)
    if len(deshabilitadas) >= len(FACTURA_LINEA_KEYS):
        raise LineasFacturaValidationError("At least one invoice line must remain enabled")

    unknown = deshabilitadas - set(FACTURA_LINEA_KEYS)
    if unknown:
        raise LineasFacturaValidationError(f"Unknown line keys: {sorted(unknown)}")

    lineas: list[FacturaLineaItem] = []
    descuento_total = Decimal("0.00")

    for key in FACTURA_LINEA_KEYS:
        monto = _monto_linea(calculo, key)
        habilitada = key not in deshabilitadas
        monto_efectivo = monto if habilitada else Decimal("0.00")
        if not habilitada:
            descuento_total += monto
        lineas.append(
            FacturaLineaItem(
                key=key,
                label=_LINEA_LABELS[key],
                monto=monto,
                monto_efectivo=monto_efectivo,
                habilitada=habilitada,
                seccion=_LINEA_SECCION[key],
            )
        )

    total_impuestos_efectivo = _q(
        sum(
            (_monto_linea(calculo, key) for key in IMPUESTO_LINEA_KEYS if key not in deshabilitadas),
            Decimal("0.00"),
        )
    )

    honorarios_keys = ("honorario_principal", "certificacion", "aporte_12pct", "cinco_pct_hon", "firma_honorarios")
    leyes_keys = ("art2_a", "art12_a", "art12_c", "art12_f")
    gastos_keys = tuple(k for k in FACTURA_LINEA_KEYS if _LINEA_SECCION[k] == "gastos_admin")

    subtotal_honorarios_efectivo = _q(
        sum(
            (item.monto_efectivo for item in lineas if item.key in honorarios_keys),
            Decimal("0.00"),
        )
    )
    total_leyes_notariales_efectivo = _q(
        sum(
            (item.monto_efectivo for item in lineas if item.key in leyes_keys),
            Decimal("0.00"),
        )
    )
    total_gastos_admin_efectivo = _q(
        sum(
            (item.monto_efectivo for item in lineas if item.key in gastos_keys),
            Decimal("0.00"),
        )
    )

    total_factura_canonica = _monto_linea(calculo, "total_factura")
    total_factura_efectivo = _q(total_factura_canonica - descuento_total)

    return FacturaEfectiva(
        lineas=tuple(lineas),
        total_impuestos_efectivo=total_impuestos_efectivo,
        total_factura_efectivo=total_factura_efectivo,
        subtotal_honorarios_efectivo=subtotal_honorarios_efectivo,
        total_leyes_notariales_efectivo=total_leyes_notariales_efectivo,
        total_gastos_admin_efectivo=total_gastos_admin_efectivo,
    )
