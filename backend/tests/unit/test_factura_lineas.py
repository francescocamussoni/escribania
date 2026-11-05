"""TDD unit tests for factura_lineas service (WU-001 — FAIL FIRST until WU-002)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from datetime import date

from services.calculo_factura import canonical_config, calcular_factura_completa
from services.factura_lineas import (
    FACTURA_LINEA_KEYS,
    IMPUESTO_LINEA_KEYS,
    LineasFacturaValidationError,
    aplicar_lineas_habilitadas,
)

CANONICAL_INPUTS = {
    "usd_value": Decimal("105000.00"),
    "dolar_mep": Decimal("1450.34"),
    "dolar_nacion": Decimal("1425.00"),
}

CANONICAL_TOTAL_IMPUESTOS = Decimal("5311489.50")
CANONICAL_TOTAL_FACTURA = Decimal("11550066.53")
CANONICAL_MUNICIPIO = Decimal("7232.00")
CANONICAL_SELLOS = Decimal("3740375.00")
CANONICAL_FOTOCOPIAS_SIMPLES = Decimal("320.00")


@pytest.fixture
def calculo_canonico() -> dict[str, Decimal]:
    return calcular_factura_completa(
        CANONICAL_INPUTS["usd_value"],
        CANONICAL_INPUTS["dolar_mep"],
        CANONICAL_INPUTS["dolar_nacion"],
        canonical_config(),
    )


class TestFacturaLineaCatalog:
    def test_factura_linea_keys_incluye_honorarios_leyes_impuestos_gastos_admin(self) -> None:
        keys = set(FACTURA_LINEA_KEYS)
        assert {"honorario_principal", "certificacion", "aporte_12pct"}.issubset(keys)
        assert {"art2_a", "art12_a", "art12_c", "art12_f"}.issubset(keys)
        assert {"tasa_3pm", "sellos", "tasa_75pm", "firma_impuestos"}.issubset(keys)
        assert {"inscripcion", "municipio", "tasas_minimas"}.issubset(keys)

    def test_impuesto_linea_keys(self) -> None:
        assert IMPUESTO_LINEA_KEYS == (
            "tasa_3pm",
            "sellos",
            "tasa_75pm",
            "firma_impuestos",
        )


class TestAplicarLineasHabilitadas:
    def test_item_deshabilitado_monto_efectivo_cero(
        self, calculo_canonico: dict[str, Decimal]
    ) -> None:
        efectivo = aplicar_lineas_habilitadas(calculo_canonico, ["municipio"])
        linea = next(item for item in efectivo.lineas if item.key == "municipio")
        assert linea.monto == CANONICAL_MUNICIPIO
        assert linea.monto_efectivo == Decimal("0.00")
        assert linea.habilitada is False

    def test_deshabilitar_municipio_reduce_costo_total_sin_alterar_total_impuestos(
        self, calculo_canonico: dict[str, Decimal]
    ) -> None:
        efectivo = aplicar_lineas_habilitadas(calculo_canonico, ["municipio"])
        assert efectivo.total_factura_efectivo == CANONICAL_TOTAL_FACTURA - CANONICAL_MUNICIPIO
        assert efectivo.total_impuestos_efectivo == CANONICAL_TOTAL_IMPUESTOS

    def test_deshabilitar_sellos_reduce_total_impuestos_efectivo(
        self, calculo_canonico: dict[str, Decimal]
    ) -> None:
        efectivo = aplicar_lineas_habilitadas(calculo_canonico, ["sellos"])
        expected_impuestos = CANONICAL_TOTAL_IMPUESTOS - CANONICAL_SELLOS
        assert efectivo.total_impuestos_efectivo == expected_impuestos
        assert efectivo.total_factura_efectivo < CANONICAL_TOTAL_FACTURA

    def test_deshabilitar_todas_las_lineas_error_validacion(
        self, calculo_canonico: dict[str, Decimal]
    ) -> None:
        with pytest.raises(LineasFacturaValidationError):
            aplicar_lineas_habilitadas(calculo_canonico, list(FACTURA_LINEA_KEYS))

    def test_fixture_canonico_suma_deshabilitados_igual_delta_costo_total(
        self, calculo_canonico: dict[str, Decimal]
    ) -> None:
        deshabilitadas = ["municipio", "fotocopias_simples"]
        efectivo = aplicar_lineas_habilitadas(calculo_canonico, deshabilitadas)
        delta = CANONICAL_MUNICIPIO + CANONICAL_FOTOCOPIAS_SIMPLES
        assert CANONICAL_TOTAL_FACTURA - efectivo.total_factura_efectivo == delta


class TestBuildSaldoFields:
    def test_costo_total_usa_total_factura_efectivo(self, calculo_canonico: dict[str, Decimal]) -> None:
        from types import SimpleNamespace

        from services.escritura_service import build_saldo_fields

        factura = SimpleNamespace(
            **calculo_canonico,
            lineas_deshabilitadas=["municipio"],
        )
        escritura = SimpleNamespace(factura=factura, pagos_cliente=[])
        saldo = build_saldo_fields(escritura)
        expected_costo = CANONICAL_TOTAL_FACTURA - CANONICAL_MUNICIPIO
        assert saldo["costo_total"] == expected_costo
        assert saldo["saldo_pendiente"] == expected_costo

    def test_plazo_usa_total_impuestos_efectivo(self, calculo_canonico: dict[str, Decimal]) -> None:
        from datetime import UTC, datetime
        from types import SimpleNamespace

        from models.escritura import EstadoEscritura
        from models.pago_colegio import TipoPagoEscribania
        from services.escritura_service import build_plazo_colegio_fields

        factura = SimpleNamespace(
            **calculo_canonico,
            lineas_deshabilitadas=["sellos"],
        )
        escritura = SimpleNamespace(
            factura=factura,
            pagos_colegio=[],
            estado=EstadoEscritura.ABIERTA,
            created_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC),
        )
        plazo = build_plazo_colegio_fields(escritura, fecha_referencia=date(2026, 7, 1))
        assert plazo is not None
        expected_impuestos = CANONICAL_TOTAL_IMPUESTOS - CANONICAL_SELLOS
        assert plazo.monto_referencia == expected_impuestos

    def test_plazo_suma_solo_pagos_tipo_colegio(self, calculo_canonico: dict[str, Decimal]) -> None:
        from datetime import UTC, datetime
        from types import SimpleNamespace

        from models.escritura import EstadoEscritura
        from models.pago_colegio import TipoPagoEscribania
        from services.escritura_service import build_plazo_colegio_fields

        factura = SimpleNamespace(**calculo_canonico, lineas_deshabilitadas=[])
        pagos = [
            SimpleNamespace(monto=Decimal("1000.00"), tipo=TipoPagoEscribania.COLEGIO),
            SimpleNamespace(monto=Decimal("500.00"), tipo=TipoPagoEscribania.OTROS),
        ]
        escritura = SimpleNamespace(
            factura=factura,
            pagos_colegio=pagos,
            estado=EstadoEscritura.ABIERTA,
            created_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC),
        )
        plazo = build_plazo_colegio_fields(escritura, fecha_referencia=date(2026, 7, 1))
        assert plazo is not None
        assert plazo.monto_pagado == Decimal("1000.00")
