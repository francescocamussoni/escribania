# Data Model: Vencimiento de pago al Colegio y régimen Monotributo

**Feature**: `008-factura-vencimiento-monotributo`  
**Date**: 2026-07-26  
**Source**: spec.md + research.md  
**Extends**: `001-plataforma-contaduria/data-model.md`, `007-refactor-factura-montos/data-model.md`

---

## Entity Relationship Overview (delta)

```
Escribano (EXTENDED)
    ├── monotributista: bool
    └── escrituras[]

Escritura (unchanged columns)
    ├── factura → total_impuestos (from 007)
    ├── pagos_colegio[] (EXTENDED)
    └── plazo_colegio (DERIVED — API only)

PagoColegio (EXTENDED)
    └── imputacion: enum
```

No new tables.

---

## Escribano (`escribano`) — delta

### New column (migration `011`)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `monotributista` | BOOLEAN | NOT NULL | `false` |

### Data migration

```sql
UPDATE escribano SET monotributista = true
WHERE lower(nombre) = 'costanza' AND deleted_at IS NULL;
```

### Business rules

- **BR-MONO-001**: Solo escribanos activos (`deleted_at IS NULL`) son editables vía PATCH.
- **BR-MONO-002**: Cambio de `monotributista` dispara recálculo de facturas de escrituras **abiertas** del escribano.
- **BR-MONO-003**: Escrituras **cerradas** no se recalculan (FR-015).

---

## PagoColegio (`pagos_colegio`) — delta

### New enum `imputacion_pago_colegio`

| DB value | UI label |
|---|---|
| `total_impuestos` | Total impuestos / Corresponde |
| `honorarios_varios` | Honorarios varios |
| `otro` | Otro |

### New column

| Column | Type | Constraints |
|---|---|---|
| `imputacion` | `imputacion_pago_colegio` | NOT NULL |

### Migration backfill

Todas las filas existentes → `honorarios_varios` (FR-003b).

### Validation

- `monto > 0` (unchanged)
- `imputacion` required on create (Pydantic + DB NOT NULL)

---

## PlazoColegio (derived — not persisted)

Computed per escritura at read time via `calcular_plazo_colegio`.
**Omitted (`null`) when `escritura.estado = cerrada`.** Only open escrituras expose the countdown.

| Field | Type | Description |
|---|---|---|
| `estado` | string | `no_aplica` \| `pendiente` \| `vencido` \| `pagado` |
| `fecha_vencimiento` | date \| null | `date(created_at) + 30 days` |
| `dias_restantes` | int \| null | Days until due (0 if overdue); **never > 30** (counted from `created_at`) |
| `urgencia` | string \| null | `verde` \| `amarillo` \| `rojo`; null if pagado/no_aplica |
| `monto_referencia` | decimal | `factura.total_impuestos` |
| `monto_pagado` | decimal | SUM pagos `imputacion=total_impuestos` |
| `monto_pendiente` | decimal | `max(0, monto_referencia - monto_pagado)` |

### State transitions

```text
no_aplica     ← total_impuestos == 0
pagado        ← monto_pagado >= total_impuestos (and total_impuestos > 0)
vencido       ← pendiente logic AND dias_restantes == 0 AND fecha_referencia > fecha_vencimiento
pendiente     ← otherwise (with urgencia color band)
```

---

## FacturaPrincipal — calculation delta (monotributo)

`calcular_totales_factura` gains parameter `monotributista: bool`:

```text
# unchanged through total_sin_iva
if monotributista:
    iva = 0
    total_factura = total_sin_iva
else:
    iva = (dif_honorarios + total_impuestos) * IVA_PCT
    total_factura = total_sin_iva + iva
```

`calcular_factura_completa` receives `monotributista` from escribano at create/update/recalc time.

---

## API schema additions

### `PlazoColegioResponse`

Embedded in `EscrituraListItem` and `EscrituraResponse` as `plazo_colegio`.

### `EscribanoResponse`

Add `monotributista: bool`.

### `EscribanoUpdateRequest` (new)

```json
{ "monotributista": true }
```

`extra="forbid"`.

### `PagoColegioInput` / `PagoColegioResponse`

Add `imputacion: ImputacionPagoColegio` (enum string).

---

## Indexes

No new indexes required. Existing `ix_pagos_colegio_escritura_id` sufficient for SUM by escritura + imputacion in memory.

Optional future: partial index on `(escritura_id) WHERE imputacion = 'total_impuestos'` — deferred (low volume).

---

## Libro de Salida impact

**Unchanged aggregation**: all `pagos_colegio` lines still appear in libro de salida regardless of imputacion. Imputacion only affects plazo countdown logic.
