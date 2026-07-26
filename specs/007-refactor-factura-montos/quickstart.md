# Quickstart (Delta): Refactorización de montos de Factura Principal

**Feature**: `007-refactor-factura-montos`  
**Date**: 2026-07-26  
**Base**: `specs/001-plataforma-contaduria/quickstart.md`

---

## New Environment Variables

None.

---

## Database Migration

```bash
make migrate
# or
docker compose exec backend alembic upgrade head
```

Migration `009_factura_totales` will:

1. Add `dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva` to `facturas_principales`
2. Backfill all rows recalculating totales from escritura inputs
3. Update `total_factura` semantics to Total + IVA

**Expected**: `Running upgrade ... -> 009_factura_totales`

---

## TDD Workflow (mandatory)

```bash
# 1. Totales puros — write/extend tests FIRST
cd backend && pytest tests/unit/test_calcular_totales_factura.py -v

# 2. Factura completa + fixture canónico
pytest tests/unit/test_calculo_factura.py -v

# 3. Integración escrituras (costo_total / saldo)
pytest tests/integration/test_escrituras_api.py -v

# 4. Pagos cliente (saldo coherente)
pytest tests/unit/test_pago_cliente_service.py -v

# 5. Full backend suite
pytest tests/ -v
```

---

## Demo Seed Regeneration

```bash
# With SEED_DEMO_DATA=true and ENVIRONMENT=local
docker compose exec backend python scripts/seed_demo_data.py
```

Expect `DEMO_SEED_VERSION=4`; old `[DEMO]` escrituras wiped and recreated with new totals.

---

## Manual Validation Checklist

### Factura UI (Escritura detail)

1. Open any escritura → Factura principal shows **5 sections** in order:
   Bases de cálculo → Honorarios → Honorarios varios → Corresponde → Totales.
2. **Bases**: "Monto base MEP", "Precio base Valor".
3. **Honorarios**: Aporte 12%, 5% honorarios, Firma honorarios, Subtotal honorarios visually distinct.
4. **Corresponde**: impuestos + gastos admin with subtotals "Total impuestos" and "Total gastos admin."
5. **Totales**: Dif Honorarios, Total parcial, Total, IVA, Total + IVA (no legacy "Total factura" row alone).

### Canonical fixture (create escritura)

| Input | Value |
|---|---|
| USD | 105_000 |
| Dólar MEP | 1_450.34 |
| Dólar Nación | 1_425.00 |

| Total field | Expected |
|---|---|
| dif_honorarios | 3_618_308.23 |
| total_parcial | 3_683_421.00 |
| total_sin_iva | 9_674_809.01 |
| iva | 1_875_257.52 |
| total_factura (Total + IVA) | 11_550_066.53 |

Line items (honorario_principal, total_impuestos, etc.) match constitution §5 unchanged.

### Pagos y libro de entrada

1. New escritura → `costo_total` and `saldo_pendiente` equal **11_550_066.53** before any payment.
2. Register partial pago cliente → saldo decreases accordingly.
3. Libro de entrada → resumen deudas shows same `costo_total` for open escrituras with debt.

### Pagos al Colegio

1. Escritura detail still shows **Honorarios varios proyectados** (value = `total_leyes_notariales`).
2. Register pago colegio — no validation against total (informative only).

---

## Breaking Changes

| Area | Change |
|---|---|
| `total_factura` | Was ~11_620_603.68 on canonical fixture; now 11_550_066.53 (Total + IVA, excludes honorarios varios from client total) |
| API | Four new fields on `FacturaPrincipalResponse` |
| Demo seed | Version 4; prior demo data removed on seed run |

Clients comparing old `total_factura` must use new formula.
