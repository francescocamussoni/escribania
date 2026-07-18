from decimal import Decimal

import pytest

from services.calculo_factura import (
    ConfigCalculo,
    calcular_factura_completa,
    canonical_config,
    validate_inputs,
)


def test_validate_inputs_rejects_zero_usd() -> None:
    with pytest.raises(ValueError, match="usd_value"):
        validate_inputs(Decimal("0"), Decimal("1450.34"), Decimal("1425.00"))


def test_validate_inputs_rejects_negative_usd() -> None:
    with pytest.raises(ValueError, match="usd_value"):
        validate_inputs(Decimal("-1"), Decimal("1450.34"), Decimal("1425.00"))


def test_validate_inputs_rejects_zero_dolar_mep() -> None:
    with pytest.raises(ValueError, match="dolar_mep"):
        validate_inputs(Decimal("105000"), Decimal("0"), Decimal("1425.00"))


def test_validate_inputs_rejects_zero_dolar_nacion() -> None:
    with pytest.raises(ValueError, match="dolar_nacion"):
        validate_inputs(Decimal("105000"), Decimal("1450.34"), Decimal("0"))


def test_honorario_minimum_enforced() -> None:
    config = canonical_config()
    # Small USD value where 2.4% would be below minimum
    result = calcular_factura_completa(
        Decimal("1000.00"),
        Decimal("1.00"),
        Decimal("1.00"),
        config,
    )
    assert result["honorario_principal"] == config.honorario_min


def test_cinco_pct_hon_minimum_enforced() -> None:
    config = canonical_config()
    result = calcular_factura_completa(
        Decimal("1000.00"),
        Decimal("1.00"),
        Decimal("1.00"),
        config,
    )
    assert result["cinco_pct_hon"] == config.cinco_pct_hon_min


def test_art12_a_minimum_enforced() -> None:
    config = canonical_config()
    result = calcular_factura_completa(
        Decimal("1000.00"),
        Decimal("1.00"),
        Decimal("1.00"),
        config,
    )
    assert result["art12_a"] == config.art12_a_min
