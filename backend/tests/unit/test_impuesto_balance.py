"""TDD unit tests for impuesto balance and close eligibility (WU-003 — FAIL FIRST until WU-004)."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from services.impuesto_balance import (
    ImpuestoPagoEstado,
    calc_balance,
    can_close_impuestos,
    impuestos_pendientes,
)


@dataclass(frozen=True)
class _ImpuestoFixture:
    impuesto_id: UUID
    tipo: str
    tiene_pago_cliente: bool
    tiene_pago_escribania: bool

    def to_estado(self) -> ImpuestoPagoEstado:
        return ImpuestoPagoEstado(
            impuesto_id=self.impuesto_id,
            tipo=self.tipo,
            tiene_pago_cliente=self.tiene_pago_cliente,
            tiene_pago_escribania=self.tiene_pago_escribania,
        )


class TestCalcBalance:
    def test_balance_es_suma_cliente_menos_escribania(self) -> None:
        balance = calc_balance(
            [Decimal("150000.00"), Decimal("50000.00")],
            [Decimal("100000.00")],
        )
        assert balance == Decimal("100000.00")

    def test_balance_cero_cuando_totales_iguales(self) -> None:
        assert calc_balance(
            [Decimal("75000.00")],
            [Decimal("75000.00")],
        ) == Decimal("0")

    def test_balance_cero_sin_movimientos(self) -> None:
        assert calc_balance([], []) == Decimal("0")


class TestImpuestosPendientes:
    def test_sin_impuestos_lista_vacia(self) -> None:
        assert impuestos_pendientes([]) == []

    def test_impuesto_sin_pago_cliente(self) -> None:
        imp_id = uuid4()
        pendientes = impuestos_pendientes([
            _ImpuestoFixture(imp_id, "API", False, True).to_estado(),
        ])
        assert len(pendientes) == 1
        assert pendientes[0]["impuesto_id"] == imp_id
        assert pendientes[0]["tipo"] == "API"
        assert pendientes[0]["falta_cliente"] is True
        assert pendientes[0]["falta_escribania"] is False

    def test_impuesto_sin_pago_escribania(self) -> None:
        pendientes = impuestos_pendientes([
            _ImpuestoFixture(uuid4(), "TGI", True, False).to_estado(),
        ])
        assert pendientes[0]["falta_cliente"] is False
        assert pendientes[0]["falta_escribania"] is True

    def test_impuesto_sin_ningun_pago(self) -> None:
        pendientes = impuestos_pendientes([
            _ImpuestoFixture(uuid4(), "EPE", False, False).to_estado(),
        ])
        assert pendientes[0]["falta_cliente"] is True
        assert pendientes[0]["falta_escribania"] is True

    def test_impuesto_con_ambos_pagos_no_aparece(self) -> None:
        assert (
            impuestos_pendientes([
                _ImpuestoFixture(uuid4(), "API", True, True).to_estado(),
            ])
            == []
        )


class TestCanCloseImpuestos:
    def test_sin_impuestos_puede_cerrar(self) -> None:
        assert can_close_impuestos(Decimal("0"), []) is True

    def test_balance_positivo_no_puede_cerrar(self) -> None:
        assert can_close_impuestos(Decimal("50000.00"), []) is False

    def test_balance_negativo_no_puede_cerrar(self) -> None:
        assert can_close_impuestos(Decimal("-100.00"), []) is False

    def test_balance_cero_con_pagos_pendientes_no_puede_cerrar(self) -> None:
        pendientes = impuestos_pendientes([
            _ImpuestoFixture(uuid4(), "API", True, False).to_estado(),
        ])
        assert can_close_impuestos(Decimal("0"), pendientes) is False

    def test_balance_cero_sin_pendientes_puede_cerrar(self) -> None:
        assert (
            can_close_impuestos(
                Decimal("0"),
                impuestos_pendientes([
                    _ImpuestoFixture(uuid4(), "API", True, True).to_estado(),
                ]),
            )
            is True
        )

    def test_varios_impuestos_pendientes_con_detalle_por_tipo(self) -> None:
        pendientes = impuestos_pendientes([
            _ImpuestoFixture(uuid4(), "API", False, False).to_estado(),
            _ImpuestoFixture(uuid4(), "TGI", True, False).to_estado(),
            _ImpuestoFixture(uuid4(), "EPE", False, True).to_estado(),
        ])
        assert len(pendientes) == 3
        assert {item["tipo"] for item in pendientes} == {"API", "TGI", "EPE"}
        assert sum(item["falta_cliente"] for item in pendientes) == 2
        assert sum(item["falta_escribania"] for item in pendientes) == 2
