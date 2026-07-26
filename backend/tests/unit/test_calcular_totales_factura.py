from decimal import Decimal

import pytest

from services.calculo_factura import (
    GASTOS_EXCLUIDOS_TOTAL_PARCIAL,
    calcular_factura_completa,
    calcular_totales_factura,
    canonical_config,
)

CANONICAL_TOTALES = {
    "dif_honorarios": Decimal("3618308.23"),
    "total_parcial": Decimal("3683421.00"),
    "total_sin_iva": Decimal("9674809.01"),
    "iva": Decimal("1875257.52"),
    "total_factura": Decimal("11550066.53"),
}

CANONICAL_TOTALES_MONOTRIBUTO = {
    "dif_honorarios": CANONICAL_TOTALES["dif_honorarios"],
    "total_parcial": CANONICAL_TOTALES["total_parcial"],
    "total_sin_iva": CANONICAL_TOTALES["total_sin_iva"],
    "iva": Decimal("0.00"),
    "total_factura": Decimal("9674809.01"),
}

CANONICAL_LINE_ITEMS = {
    "honorario_principal": Decimal("3654856.80"),
    "certificacion": Decimal("456857.10"),
    "suma_hon_cert": Decimal("4111713.90"),
    "aporte_12pct": Decimal("493405.67"),
    "cinco_pct_hon": Decimal("182742.84"),
    "firma_honorarios": Decimal("3750.00"),
    "subtotal_honorarios": Decimal("679898.51"),
    "art2_a": Decimal("730971.36"),
    "art12_a": Decimal("609142.80"),
    "art12_c": Decimal("182742.84"),
    "art12_f": Decimal("10000.00"),
    "total_leyes_notariales": Decimal("1532857.00"),
    "tasa_3pm": Decimal("448875.00"),
    "sellos": Decimal("3740375.00"),
    "tasa_75pm": Decimal("1122187.50"),
    "firma_impuestos": Decimal("52.00"),
    "total_impuestos": Decimal("5311489.50"),
    "total_gastos_admin": Decimal("95444.77"),
}


@pytest.fixture
def honorarios() -> dict[str, Decimal]:
    return {
        "suma_hon_cert": CANONICAL_LINE_ITEMS["suma_hon_cert"],
        "aporte_12pct": CANONICAL_LINE_ITEMS["aporte_12pct"],
        "subtotal_honorarios": CANONICAL_LINE_ITEMS["subtotal_honorarios"],
    }


@pytest.fixture
def gastos() -> dict[str, Decimal]:
    return {
        "fotocopias_urgentes": Decimal("6500.00"),
        "informes_notariales": Decimal("3000.00"),
        "municipio": Decimal("7232.00"),
        "ii_certificados": Decimal("9100.00"),
        "catastro": Decimal("4500.00"),
        "total_gastos_admin": CANONICAL_LINE_ITEMS["total_gastos_admin"],
    }


def test_calcular_totales_factura_canonical_fixture(
    honorarios: dict[str, Decimal], gastos: dict[str, Decimal]
) -> None:
    result = calcular_totales_factura(
        suma_hon_cert=honorarios["suma_hon_cert"],
        aporte_12pct=honorarios["aporte_12pct"],
        subtotal_honorarios=honorarios["subtotal_honorarios"],
        total_impuestos=CANONICAL_LINE_ITEMS["total_impuestos"],
        total_gastos_admin=gastos["total_gastos_admin"],
        gastos=gastos,
    )
    for key, expected in CANONICAL_TOTALES.items():
        assert result[key] == expected


def test_calcular_totales_factura_monotributista(
    honorarios: dict[str, Decimal], gastos: dict[str, Decimal]
) -> None:
    result = calcular_totales_factura(
        suma_hon_cert=honorarios["suma_hon_cert"],
        aporte_12pct=honorarios["aporte_12pct"],
        subtotal_honorarios=honorarios["subtotal_honorarios"],
        total_impuestos=CANONICAL_LINE_ITEMS["total_impuestos"],
        total_gastos_admin=gastos["total_gastos_admin"],
        gastos=gastos,
        monotributista=True,
    )
    for key, expected in CANONICAL_TOTALES_MONOTRIBUTO.items():
        assert result[key] == expected
    assert result["total_factura"] == result["total_sin_iva"]


def test_total_parcial_excludes_gastos_admin_items(gastos: dict[str, Decimal]) -> None:
    excluded_sum = sum(gastos[k] for k in GASTOS_EXCLUIDOS_TOTAL_PARCIAL)
    result = calcular_totales_factura(
        suma_hon_cert=Decimal("1000.00"),
        aporte_12pct=Decimal("100.00"),
        subtotal_honorarios=Decimal("50.00"),
        total_impuestos=Decimal("200.00"),
        total_gastos_admin=gastos["total_gastos_admin"],
        gastos=gastos,
    )
    expected_parcial = Decimal("900.00") + gastos["total_gastos_admin"] - excluded_sum
    assert result["total_parcial"] == expected_parcial.quantize(Decimal("0.01"))


def test_total_factura_equals_total_sin_iva_plus_iva(
    honorarios: dict[str, Decimal], gastos: dict[str, Decimal]
) -> None:
    result = calcular_totales_factura(
        suma_hon_cert=honorarios["suma_hon_cert"],
        aporte_12pct=honorarios["aporte_12pct"],
        subtotal_honorarios=honorarios["subtotal_honorarios"],
        total_impuestos=CANONICAL_LINE_ITEMS["total_impuestos"],
        total_gastos_admin=gastos["total_gastos_admin"],
        gastos=gastos,
    )
    assert result["total_factura"] == result["total_sin_iva"] + result["iva"]


def test_calcular_factura_completa_line_items_unchanged() -> None:
    result = calcular_factura_completa(
        Decimal("105000.00"),
        Decimal("1450.34"),
        Decimal("1425.00"),
        canonical_config(),
    )
    for key, expected in CANONICAL_LINE_ITEMS.items():
        assert result[key] == expected


def test_calcular_factura_completa_monotributista_totales() -> None:
    result = calcular_factura_completa(
        Decimal("105000.00"),
        Decimal("1450.34"),
        Decimal("1425.00"),
        canonical_config(),
        monotributista=True,
    )
    assert result["iva"] == Decimal("0.00")
    assert result["total_factura"] == Decimal("9674809.01")
    assert result["total_factura"] == result["total_sin_iva"]
