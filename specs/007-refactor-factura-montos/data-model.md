# Data Model: Refactorización de montos de Factura Principal

**Feature**: `007-refactor-factura-montos`  
**Date**: 2026-07-26  
**Source**: spec.md + research.md  
**Extends**: `001-plataforma-contaduria/data-model.md`

---

## Entity Relationship Overview (delta)

```
Escritura (unchanged)
    │
    └── FacturaPrincipal (EXTENDED)
            ├── line items (unchanged formulas)
            ├── subtotals (unchanged logic)
            └── totales resumen (NEW columns)
```

No new tables. No new relationships.

---

## FacturaPrincipal (`facturas_principales`) — delta

### New columns (migration `009_factura_totales`)

| Column | Type | Constraints | UI label |
|---|---|---|---|
| `dif_honorarios` | NUMERIC(18,2) | NOT NULL | Dif Honorarios |
| `total_parcial` | NUMERIC(18,2) | NOT NULL | Total parcial |
| `total_sin_iva` | NUMERIC(18,2) | NOT NULL | Total |
| `iva` | NUMERIC(18,2) | NOT NULL | IVA |

### Changed semantics

| Column | Before | After |
|---|---|---|
| `total_factura` | Suma de suma_hon_cert + subtotal + leyes + impuestos + gastos | **Total + IVA** (= `total_sin_iva + iva`) |

### Unchanged columns (display labels only)

| Column | DB name | New UI label (frontend) |
|---|---|---|
| `precio_base_nacion` | `precio_base_nacion` | Precio base Valor |
| `total_leyes_notariales` | `total_leyes_notariales` | Total honorarios varios |

### Line items & subtotals (no schema change)

Honorarios, Honorarios varios (arts.), impuestos, gastos admin.: mismas columnas y fórmulas.

---

## Derived fields (API only, not persisted)

| Field | Source |
|---|---|
| `costo_total` (EscrituraDetail) | `factura.total_factura` |
| `saldo_pendiente` | `costo_total - SUM(pagos_cliente.monto)` |
| `total_leyes_notariales_proyectadas` | `factura.total_leyes_notariales` (alias; label UI "Honorarios varios proyectados") |

---

## Calculation rules (totales)

All computed in `calcular_factura_completa`; stored on every create/update of escritura abierta.

```text
dif_honorarios  = suma_hon_cert - aporte_12pct
total_parcial   = dif_honorarios + total_gastos_admin
                  - fotocopias_urgentes - informes_notariales
                  - municipio - ii_certificados - catastro
total_sin_iva   = total_parcial + subtotal_honorarios + total_impuestos
iva             = (dif_honorarios + total_impuestos) * 0.21
total_factura   = total_sin_iva + iva
```

**Excluded from Total parcial formulas**: `total_leyes_notariales` (Honorarios varios).

**Rounding**: `Decimal.quantize("0.01", ROUND_HALF_UP)` at each step.

---

## Validation rules

- All monetary columns NOT NULL after migration backfill.
- `total_factura` MUST equal `total_sin_iva + iva` (enforced in tests, not DB constraint).
- Escritura `cerrada`: factura read-only; totales frozen at close time.

---

## Migration strategy

1. `009_factura_totales.py`: ADD columns nullable → backfill via `calcular_factura_completa` per row → SET NOT NULL.
2. Demo seed: `DEMO_SEED_VERSION` 4; wipe `[DEMO]` escrituras when version mismatch.
3. Non-demo rows: backfill in migration from parent escritura inputs.

---

## Downstream consumers (read `total_factura`)

| Consumer | Impact |
|---|---|
| `pago_cliente_service` / saldo | Automático (nuevo monto) |
| `libros_service._build_resumen_deudas` | Automático |
| `liquidacion_service` (honorarios cobrados) | Sin cambio de fórmula; montos distintos si escritura recalculada |
| `seed_demo_data.py` | Regenerar |
| Integration tests `EXPECTED_FACTURA` | Actualizar |

---

## Pydantic / TypeScript types (delta)

`FacturaPrincipalResponse` gains:

```text
dif_honorarios: MoneyStr
total_parcial: MoneyStr
total_sin_iva: MoneyStr
iva: MoneyStr
total_factura: MoneyStr  # now Total + IVA
```

`frontend/src/types/api.ts` — mirror fields.
