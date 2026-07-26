# Setup Verification: feature 008

**Date**: 2026-07-26  
**Branch**: `008-factura-vencimiento-monotributo`

---

## T001 — OpenAPI delta ↔ data-model alignment

| Artifact | Status |
|---|---|
| `ImputacionPagoColegio` enum (`total_impuestos`, `honorarios_varios`, `otro`) | ✅ Aligned |
| `PagoColegio.imputacion` NOT NULL + backfill `honorarios_varios` | ✅ Aligned |
| `PlazoColegioResponse` fields (estado, fechas, montos, urgencia) | ✅ Aligned |
| `Escribano.monotributista` + Costanza backfill | ✅ Aligned |
| `EscribanoUpdateRequest` (`monotributista` only, `additionalProperties: false`) | ✅ Aligned |
| `PATCH /configuracion/escribanos/{escribano_id}` | ✅ Aligned with `escribanos.py` |
| `POST /escrituras/{id}/pagos-colegio` — `imputacion` required | ✅ Aligned |
| `plazo_colegio` on list + detail | ✅ Aligned |
| Monotributo IVA logic (`iva=0`, `total_factura=total_sin_iva`) | ✅ Aligned in data-model § FacturaPrincipal |

### Implementation cross-check (Pydantic / ORM)

| Contract schema | Code location | Match |
|---|---|---|
| `PlazoColegioResponse` | `schemas/plazo_colegio.py` | ✅ |
| `PagoColegioInput` / `Response` | `schemas/pago_colegio.py` | ✅ |
| `EscribanoResponse` / `UpdateRequest` | `schemas/escribano.py` | ✅ |
| `EscrituraListItem.plazo_colegio` | `schemas/escritura.py` | ✅ |

### Doc note (non-blocking)

Spec/plan reference migration file `011_plazo_colegio_monotributo.py`; actual Alembic file is
`backend/alembic/versions/011_plazo_colegio_imputacion.py` (revision `011`). Semantics identical.

**T001 result**: ✅ PASS — contracts aligned; no API/schema gaps requiring code changes.

---

## T002 — Dependency on feature 007

| Check | Result |
|---|---|
| Branch `007-refactor-factura-montos` ancestor of `008-factura-vencimiento-monotributo` | ✅ |
| Branch `007-refactor-factura-montos` merged into `main` (commit `9e21421`) | ✅ |
| Migration `009_factura_totales.py` present | ✅ |
| Column `facturas_principales.total_impuestos` in DB | ✅ |
| Columns `dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva` (007 totales) | ✅ |
| `calcular_totales_factura` uses `total_impuestos` for plazo reference | ✅ |

**T002 result**: ✅ PASS — feature 007 merged and available.

---

## T013 — Migration 011 applied + legacy backfill

| Check | Result |
|---|---|
| `alembic current` | `011 (head)` |
| Enum `imputacion_pago_colegio` exists | ✅ |
| `pagos_colegio.imputacion` NOT NULL | ✅ |
| Legacy rows: `NULL` imputacion count | `0 / 7` |
| Legacy backfill value | all `honorarios_varios` |
| `escribano.monotributista` NOT NULL | ✅ |
| Costanza `monotributista = true` | ✅ |
| Gabriel / Monica `monotributista = false` | ✅ |

**T013 result**: ✅ PASS — migration at head; backfill verified on local DB.
