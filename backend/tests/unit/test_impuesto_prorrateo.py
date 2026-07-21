"""TDD unit tests for linear impuesto proration (WU-001 — FAIL FIRST until WU-002)."""

from datetime import date
from decimal import Decimal

import pytest

from services.impuesto_prorrateo import (
    DireccionProrrateo,
    calc_dias_periodo,
    calc_dias_tramo,
    calc_monto_sugerido,
)

MONTO_TOTAL = Decimal("10000.00")
PERIODO_INICIO = date(2026, 5, 1)
PERIODO_FIN = date(2026, 6, 30)
FECHA_CORTE = date(2026, 6, 15)


class TestDiasPeriodo:
    def test_periodo_mayo_junio_61_dias(self) -> None:
        assert calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN) == 61


class TestDiasTramo:
    def test_hacia_atras_46_dias(self) -> None:
        dias = calc_dias_tramo(
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ATRAS,
        )
        assert dias == 46

    def test_hacia_adelante_15_dias(self) -> None:
        dias = calc_dias_tramo(
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ADELANTE,
        )
        assert dias == 15

    def test_tramos_sin_solapamiento_suman_periodo(self) -> None:
        dias_atras = calc_dias_tramo(
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ATRAS,
        )
        dias_adelante = calc_dias_tramo(
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ADELANTE,
        )
        assert dias_atras + dias_adelante == calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN)

    def test_corte_primer_dia_hacia_atras_un_dia(self) -> None:
        assert (
            calc_dias_tramo(
                PERIODO_INICIO,
                PERIODO_FIN,
                PERIODO_INICIO,
                DireccionProrrateo.HACIA_ATRAS,
            )
            == 1
        )

    def test_corte_primer_dia_hacia_adelante_resto_del_periodo(self) -> None:
        dias = calc_dias_tramo(
            PERIODO_INICIO,
            PERIODO_FIN,
            PERIODO_INICIO,
            DireccionProrrateo.HACIA_ADELANTE,
        )
        assert dias == calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN) - 1

    def test_corte_ultimo_dia_hacia_adelante_cero_dias(self) -> None:
        assert (
            calc_dias_tramo(
                PERIODO_INICIO,
                PERIODO_FIN,
                PERIODO_FIN,
                DireccionProrrateo.HACIA_ADELANTE,
            )
            == 0
        )

    def test_corte_ultimo_dia_hacia_atras_cubre_periodo_completo(self) -> None:
        assert (
            calc_dias_tramo(
                PERIODO_INICIO,
                PERIODO_FIN,
                PERIODO_FIN,
                DireccionProrrateo.HACIA_ATRAS,
            )
            == calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN)
        )


class TestCalcMontoSugerido:
    def test_hacia_atras_monto_canonico_46_61(self) -> None:
        monto = calc_monto_sugerido(
            MONTO_TOTAL,
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ATRAS,
        )
        assert monto == Decimal("7540.98")

    def test_hacia_adelante_monto_canonico_15_61(self) -> None:
        monto = calc_monto_sugerido(
            MONTO_TOTAL,
            PERIODO_INICIO,
            PERIODO_FIN,
            FECHA_CORTE,
            DireccionProrrateo.HACIA_ADELANTE,
        )
        assert monto == Decimal("2459.02")

    def test_complementariedad_fracciones_suman_total(self) -> None:
        monto_atras = (
            MONTO_TOTAL
            * Decimal(calc_dias_tramo(
                PERIODO_INICIO,
                PERIODO_FIN,
                FECHA_CORTE,
                DireccionProrrateo.HACIA_ATRAS,
            ))
            / Decimal(calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN))
        )
        monto_adelante = (
            MONTO_TOTAL
            * Decimal(calc_dias_tramo(
                PERIODO_INICIO,
                PERIODO_FIN,
                FECHA_CORTE,
                DireccionProrrateo.HACIA_ADELANTE,
            ))
            / Decimal(calc_dias_periodo(PERIODO_INICIO, PERIODO_FIN))
        )
        assert monto_atras + monto_adelante == MONTO_TOTAL

    def test_corte_ultimo_dia_hacia_adelante_monto_cero(self) -> None:
        monto = calc_monto_sugerido(
            MONTO_TOTAL,
            PERIODO_INICIO,
            PERIODO_FIN,
            PERIODO_FIN,
            DireccionProrrateo.HACIA_ADELANTE,
        )
        assert monto == Decimal("0.00")

    def test_redondeo_half_up_a_dos_decimales(self) -> None:
        """Monto que requiere redondeo explícito (no solo fracción exacta)."""
        monto = calc_monto_sugerido(
            Decimal("100.00"),
            date(2026, 1, 1),
            date(2026, 1, 3),
            date(2026, 1, 1),
            DireccionProrrateo.HACIA_ATRAS,
        )
        assert monto == Decimal("33.33")


class TestValidacionFechaCorte:
    def test_corte_antes_del_periodo_rechazado(self) -> None:
        with pytest.raises(ValueError, match="fecha de corte"):
            calc_monto_sugerido(
                MONTO_TOTAL,
                PERIODO_INICIO,
                PERIODO_FIN,
                date(2026, 4, 30),
                DireccionProrrateo.HACIA_ATRAS,
            )

    def test_corte_despues_del_periodo_rechazado(self) -> None:
        with pytest.raises(ValueError, match="fecha de corte"):
            calc_monto_sugerido(
                MONTO_TOTAL,
                PERIODO_INICIO,
                PERIODO_FIN,
                date(2026, 7, 1),
                DireccionProrrateo.HACIA_ATRAS,
            )

    def test_periodo_fin_antes_de_inicio_rechazado(self) -> None:
        with pytest.raises(ValueError, match="período"):
            calc_monto_sugerido(
                MONTO_TOTAL,
                PERIODO_FIN,
                PERIODO_INICIO,
                FECHA_CORTE,
                DireccionProrrateo.HACIA_ATRAS,
            )

    def test_monto_total_no_positivo_rechazado(self) -> None:
        with pytest.raises(ValueError, match="monto"):
            calc_monto_sugerido(
                Decimal("0"),
                PERIODO_INICIO,
                PERIODO_FIN,
                FECHA_CORTE,
                DireccionProrrateo.HACIA_ATRAS,
            )
