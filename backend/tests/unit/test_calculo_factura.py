from decimal import Decimal

import pytest

from services.calculo_factura import (
    ConfigCalculo,
    calcular_bases,
    calcular_factura_completa,
    canonical_config,
)


@pytest.fixture
def config() -> ConfigCalculo:
    return canonical_config()


@pytest.fixture
def inputs() -> dict[str, Decimal]:
    return {
        "usd_value": Decimal("105000.00"),
        "dolar_mep": Decimal("1450.34"),
        "dolar_nacion": Decimal("1425.00"),
    }


def test_calcular_bases(inputs: dict[str, Decimal]) -> None:
    monto, precio = calcular_bases(
        inputs["usd_value"], inputs["dolar_mep"], inputs["dolar_nacion"]
    )
    assert monto == Decimal("152285700.00")
    assert precio == Decimal("149625000.00")


def test_calcular_factura_completa_canonical_fixture(
    inputs: dict[str, Decimal], config: ConfigCalculo
) -> None:
    result = calcular_factura_completa(
        inputs["usd_value"],
        inputs["dolar_mep"],
        inputs["dolar_nacion"],
        config,
    )

    assert result["monto_base_mep"] == Decimal("152285700.00")
    assert result["precio_base_nacion"] == Decimal("149625000.00")

    assert result["honorario_principal"] == Decimal("3654856.80")
    assert result["certificacion"] == Decimal("456857.10")
    assert result["suma_hon_cert"] == Decimal("4111713.90")
    assert result["aporte_12pct"] == Decimal("493405.67")
    assert result["cinco_pct_hon"] == Decimal("182742.84")
    assert result["firma_honorarios"] == Decimal("3750.00")
    assert result["subtotal_honorarios"] == Decimal("679898.51")

    assert result["art2_a"] == Decimal("730971.36")
    assert result["art12_a"] == Decimal("609142.80")
    assert result["art12_c"] == Decimal("182742.84")
    assert result["art12_f"] == Decimal("10000.00")
    assert result["total_leyes_notariales"] == Decimal("1532857.00")

    assert result["tasa_3pm"] == Decimal("448875.00")
    assert result["sellos"] == Decimal("3740375.00")
    assert result["tasa_75pm"] == Decimal("1122187.50")
    assert result["firma_impuestos"] == Decimal("52.00")
    assert result["total_impuestos"] == Decimal("5311489.50")

    assert result["inscripcion"] == Decimal("40000.00")
    assert result["protocolo"] == Decimal("10320.00")
    assert result["ii_certificados"] == Decimal("9100.00")
    assert result["municipio"] == Decimal("7232.00")
    assert result["fotocopias_urgentes"] == Decimal("6500.00")
    assert result["certificaciones_extra"] == Decimal("5837.77")
    assert result["catastro"] == Decimal("4500.00")
    assert result["testimonio"] == Decimal("4160.00")
    assert result["concuerda"] == Decimal("3370.00")
    assert result["informes_notariales"] == Decimal("3000.00")
    assert result["extracto"] == Decimal("1065.00")
    assert result["fotocopias_simples"] == Decimal("320.00")
    assert result["tasas_minimas"] == Decimal("40.00")
    assert result["total_gastos_admin"] == Decimal("95444.77")

    assert result["dif_honorarios"] == Decimal("3618308.23")
    assert result["total_parcial"] == Decimal("3683421.00")
    assert result["total_sin_iva"] == Decimal("9674809.01")
    assert result["iva"] == Decimal("1875257.52")
    assert result["total_factura"] == Decimal("11550066.53")
    assert result["total_factura"] == result["total_sin_iva"] + result["iva"]
