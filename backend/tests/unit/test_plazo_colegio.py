"""TDD unit tests for plazo_colegio service (WU-010 — FAIL FIRST until WU-011)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from models.pago_colegio import TipoPagoEscribania
from schemas.plazo_colegio import PlazoColegioEstado, PlazoColegioUrgencia
from services.plazo_colegio import PLAZO_COLEGIO_DIAS, calcular_plazo_colegio, sum_pagos_colegio

CANONICAL_TOTAL_IMPUESTOS = Decimal("5311489.50")
CANONICAL_SELLOS = Decimal("3740375.00")
TOTAL_IMPUESTOS_EFECTIVO_SIN_SELLOS = CANONICAL_TOTAL_IMPUESTOS - CANONICAL_SELLOS


def _pago(monto: str, tipo: TipoPagoEscribania) -> SimpleNamespace:
    return SimpleNamespace(monto=Decimal(monto), tipo=tipo)


class TestSumPagosColegio:
    def test_solo_tipo_colegio_cuenta(self) -> None:
        pagos = [
            _pago("1000.00", TipoPagoEscribania.COLEGIO),
            _pago("500.00", TipoPagoEscribania.OTROS),
            _pago("200.00", TipoPagoEscribania.OTROS),
        ]
        assert sum_pagos_colegio(pagos) == Decimal("1000.00")

    def test_pagos_otros_ignorados_en_plazo(self) -> None:
        pagos = [
            _pago("300.00", TipoPagoEscribania.OTROS),
            _pago("700.00", TipoPagoEscribania.COLEGIO),
        ]
        assert sum_pagos_colegio(pagos) == Decimal("700.00")

    def test_sin_pagos(self) -> None:
        assert sum_pagos_colegio([]) == Decimal("0.00")


class TestCalcularPlazoColegio:
    CREATED = date(2026, 7, 1)
    VENCIMIENTO = date(2026, 7, 31)  # +30 días de corrido

    def test_monto_referencia_desde_total_impuestos_efectivo(self) -> None:
        """El caller debe pasar total_impuestos_efectivo (post-máscara líneas)."""
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=TOTAL_IMPUESTOS_EFECTIVO_SIN_SELLOS,
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=self.CREATED,
        )
        assert result.monto_referencia == TOTAL_IMPUESTOS_EFECTIVO_SIN_SELLOS

    def test_no_aplica_cuando_total_impuestos_efectivo_cero(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("0"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=self.CREATED,
        )
        assert result.estado == PlazoColegioEstado.NO_APLICA
        assert result.fecha_vencimiento is None
        assert result.dias_restantes is None
        assert result.urgencia is None

    def test_pagado_cuando_monto_cubre_total(self) -> None:
        total = Decimal("5311489.50")
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=total,
            monto_pagado_impuestos=total,
            fecha_referencia=self.CREATED,
        )
        assert result.estado == PlazoColegioEstado.PAGADO
        assert result.urgencia is None
        assert result.monto_pendiente == Decimal("0.00")

    def test_pagado_con_pago_parcial_mayor_no_cambia_estado_pagado(self) -> None:
        total = Decimal("1000.00")
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=total,
            monto_pagado_impuestos=Decimal("1500.00"),
            fecha_referencia=self.CREATED,
        )
        assert result.estado == PlazoColegioEstado.PAGADO

    def test_verde_25_dias_restantes(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 6),  # 25 días hasta 31/07
        )
        assert result.dias_restantes == 25
        assert result.urgencia == PlazoColegioUrgencia.VERDE
        assert result.estado == PlazoColegioEstado.PENDIENTE

    def test_verde_limite_21_dias(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 10),
        )
        assert result.dias_restantes == 21
        assert result.urgencia == PlazoColegioUrgencia.VERDE

    def test_amarillo_15_dias(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 16),
        )
        assert result.dias_restantes == 15
        assert result.urgencia == PlazoColegioUrgencia.AMARILLO

    def test_amarillo_limite_20_dias(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 11),
        )
        assert result.dias_restantes == 20
        assert result.urgencia == PlazoColegioUrgencia.AMARILLO

    def test_rojo_5_dias(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 26),
        )
        assert result.dias_restantes == 5
        assert result.urgencia == PlazoColegioUrgencia.ROJO

    def test_rojo_limite_10_dias(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 21),
        )
        assert result.dias_restantes == 10
        assert result.urgencia == PlazoColegioUrgencia.ROJO

    def test_dia_vencimiento_cero_dias_pendiente_rojo(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=self.VENCIMIENTO,
        )
        assert result.dias_restantes == 0
        assert result.urgencia == PlazoColegioUrgencia.ROJO
        assert result.estado == PlazoColegioEstado.PENDIENTE

    def test_vencido_despues_de_fecha_limite(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 8, 1),
        )
        assert result.dias_restantes == 0
        assert result.estado == PlazoColegioEstado.VENCIDO
        assert result.urgencia == PlazoColegioUrgencia.ROJO

    def test_creado_hoy_30_dias_verde(self) -> None:
        created = date(2026, 7, 26)
        result = calcular_plazo_colegio(
            fecha_creacion=created,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=created,
        )
        assert result.dias_restantes == PLAZO_COLEGIO_DIAS
        assert result.urgencia == PlazoColegioUrgencia.VERDE

    def test_pago_parcial_sigue_pendiente(self) -> None:
        result = calcular_plazo_colegio(
            fecha_creacion=self.CREATED,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("400.00"),
            fecha_referencia=date(2026, 7, 16),
        )
        assert result.estado == PlazoColegioEstado.PENDIENTE
        assert result.monto_pendiente == Decimal("600.00")

    def test_dias_restantes_no_supera_plazo_cuando_referencia_anterior_a_creacion(self) -> None:
        created = date(2026, 12, 1)
        result = calcular_plazo_colegio(
            fecha_creacion=created,
            total_impuestos=Decimal("1000.00"),
            monto_pagado_impuestos=Decimal("0"),
            fecha_referencia=date(2026, 7, 1),
        )
        assert result.dias_restantes == PLAZO_COLEGIO_DIAS
        assert result.estado == PlazoColegioEstado.PENDIENTE
        assert result.urgencia == PlazoColegioUrgencia.VERDE
