"""Smoke checks for demo seed constants (feature 009 — seed v6)."""

from scripts.seed_demo_data import (
    DEMO_SEED_VERSION,
    EXPECTED_DEMO_COUNT,
    EXPECTED_DEMO_GASTO_COUNT,
    PLAZO_SHOWCASE,
    PLAZO_SHOWCASE_COUNT,
    SCENARIOS_PER_ESCRIBANO,
    CLOSED_MONTHS,
)


def test_demo_seed_version_is_six() -> None:
    assert DEMO_SEED_VERSION == 6


def test_expected_demo_escritura_count() -> None:
    assert len(PLAZO_SHOWCASE) == PLAZO_SHOWCASE_COUNT == 3
    assert EXPECTED_DEMO_COUNT == len(CLOSED_MONTHS) * 3 + SCENARIOS_PER_ESCRIBANO * 3 + PLAZO_SHOWCASE_COUNT
    assert EXPECTED_DEMO_COUNT == 45


def test_expected_demo_gasto_count() -> None:
    assert EXPECTED_DEMO_GASTO_COUNT == 3
