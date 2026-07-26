"""TDD unit tests for equal split of extraordinary expenses (WU-001)."""

from decimal import Decimal

import pytest

from services.gasto_extraordinario_reparto import reparto_equitativo

_CENTS = Decimal("0.01")


class TestRepartoEquitativoExacto:
    def test_tres_escribanos_division_exacta(self) -> None:
        cuotas = reparto_equitativo(Decimal("300000.00"), 3)
        assert cuotas == [
            Decimal("100000.00"),
            Decimal("100000.00"),
            Decimal("100000.00"),
        ]

    def test_un_solo_escribano_recibe_total(self) -> None:
        assert reparto_equitativo(Decimal("150000.50"), 1) == [Decimal("150000.50")]


class TestRepartoEquitativoIndivisible:
    def test_suma_cuotas_iguala_total(self) -> None:
        total = Decimal("100.00")
        cuotas = reparto_equitativo(total, 3)
        assert sum(cuotas, start=Decimal("0")) == total

    def test_base_por_escribano_redondeada_hacia_abajo(self) -> None:
        cuotas = reparto_equitativo(Decimal("100.00"), 3)
        assert cuotas[0] == Decimal("33.33")
        assert cuotas[1] == Decimal("33.33")
        assert cuotas[2] == Decimal("33.34")

    def test_remanente_al_ultimo_indice_para_orden_alfabetico(self) -> None:
        """Caller ordena escribanos por nombre; el último recibe centavos sobrantes."""
        nombres = sorted(["Monica", "Costanza", "Gabriel"])
        cuotas = reparto_equitativo(Decimal("100.00"), len(nombres))
        asignacion = dict(zip(nombres, cuotas, strict=True))

        assert asignacion["Costanza"] == Decimal("33.33")
        assert asignacion["Gabriel"] == Decimal("33.33")
        assert asignacion["Monica"] == Decimal("33.34")


class TestRepartoEquitativoBordes:
    def test_cero_escribanos_lista_vacia(self) -> None:
        assert reparto_equitativo(Decimal("300000.00"), 0) == []

    def test_escribanos_negativos_lista_vacia(self) -> None:
        assert reparto_equitativo(Decimal("300000.00"), -1) == []

    def test_total_cero_tres_escribanos(self) -> None:
        assert reparto_equitativo(Decimal("0.00"), 3) == [
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
        ]

    def test_rechaza_total_negativo(self) -> None:
        with pytest.raises(ValueError, match="total"):
            reparto_equitativo(Decimal("-1.00"), 2)
