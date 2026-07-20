"""TDD unit tests for pure saldo functions (WU-007 — FAIL FIRST until WU-008)."""

from decimal import Decimal

from services.pago_saldo import calc_saldo, can_close, is_sobrepago

COSTO = Decimal("1000000.00")


class TestCalcSaldo:
    def test_saldo_normal(self) -> None:
        assert calc_saldo(COSTO, Decimal("300000.00")) == Decimal("700000.00")

    def test_saldo_cero_cuando_pagado_igual_a_costo(self) -> None:
        assert calc_saldo(COSTO, COSTO) == Decimal("0")

    def test_saldo_minimo_cero_con_sobrepago(self) -> None:
        assert calc_saldo(COSTO, Decimal("1200000.00")) == Decimal("0")

    def test_saldo_cero_sin_pagos(self) -> None:
        assert calc_saldo(COSTO, Decimal("0")) == COSTO


class TestCanClose:
    def test_can_close_solo_con_saldo_cero(self) -> None:
        assert can_close(Decimal("0")) is True

    def test_cannot_close_con_saldo_pendiente(self) -> None:
        assert can_close(Decimal("1.00")) is False
        assert can_close(Decimal("500000.00")) is False


class TestIsSobrepago:
    def test_sobrepago_cuando_pagado_supera_costo(self) -> None:
        assert is_sobrepago(COSTO, Decimal("1200000.00")) is True

    def test_no_sobrepago_cuando_pagado_igual_o_menor(self) -> None:
        assert is_sobrepago(COSTO, COSTO) is False
        assert is_sobrepago(COSTO, Decimal("500000.00")) is False

    def test_sobrepago_tras_recalculo_factura(self) -> None:
        """Edge case: factura recalculada baja costo pero pagos históricos quedan altos."""
        costo_recalculado = Decimal("800000.00")
        total_pagado = Decimal("1000000.00")
        assert is_sobrepago(costo_recalculado, total_pagado) is True
        assert calc_saldo(costo_recalculado, total_pagado) == Decimal("0")
        assert can_close(calc_saldo(costo_recalculado, total_pagado)) is True
