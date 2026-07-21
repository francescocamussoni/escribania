# Data Model: Impuestos por Escritura

**Feature**: `006-impuestos-escrituras`  
**Date**: 2026-07-20  
**Source**: spec.md + research.md  
**Extends**: `003-pagos-cliente/data-model.md`

---

## Entity Relationship Overview (delta)

```
                    Escritura
                        │
          ┌─────────────┼─────────────────────────┐
          │             │                         │
          ▼             ▼                         ▼
   PagoCliente    PagoColegio            ImpuestoEscritura (NEW)
   (honorarios)  (honorarios)                    │
                        │              ┌──────────┴──────────┐
                        │              ▼                     ▼
                        │     PagoImpuestoCliente    PagoImpuestoEscribania
                        │         (NEW, 0..1)            (NEW, 0..1)
                        │              │                     │
                        ▼              ▼                     ▼
                  SalidaLibro    EntradaLibro          SalidaLibro
                  (honorarios)   (honorarios +         (honorarios +
                                  impuestos)            impuestos)
```

---

## New Entities

### ImpuestoEscritura (`impuestos_escritura`)

Gasto impositivo o de servicio del inmueble vinculado a una escritura.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `escritura_id` | UUID | FK → escrituras, not null | |
| `tipo` | `tipo_impuesto` ENUM | not null | API, TGI, AGUAS_SANTAFESINAS, EPE, EXPENSAS, LITORAL_GAS |
| `monto_total` | NUMERIC(18,2) | not null, > 0 | Base del prorrateo |
| `periodo_inicio` | DATE | not null | |
| `periodo_fin` | DATE | not null, >= inicio | |
| `fecha_corte` | DATE | not null, within period | |
| `direccion_prorrateo` | ENUM `hacia_atras` \| `hacia_adelante` | not null | |
| `created_at` | TIMESTAMPTZ | not null | |
| `updated_at` | TIMESTAMPTZ | not null | Editable |

**Computed (not persisted)**:
- `monto_prorrateado_sugerido` — from `impuesto_prorrateo.calc_monto_sugerido(...)`
- `estado_pagos` — derivado de existencia de pagos cliente/escribanía

**Business rules**:
- Solo CRUD en escrituras `abierta` (FR-007)
- Eliminable solo sin pagos registrados (FR-028)
- Período independiente de `escritura.created_at`

**Indexes**: `(escritura_id)`, `(tipo, periodo_inicio, periodo_fin)`

---

### PagoImpuestoCliente (`pagos_impuesto_cliente`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `impuesto_id` | UUID | FK → impuestos_escritura, **UNIQUE** | 0..1 por impuesto |
| `escritura_id` | UUID | FK → escrituras, not null | Denormalized for queries |
| `monto` | NUMERIC(18,2) | not null, > 0 | Editable; prefill sugerido |
| `fecha` | DATE | not null | Mes del Libro de Entrada |
| `created_at` | TIMESTAMPTZ | not null | |
| `updated_at` | TIMESTAMPTZ | not null | |

**Business rules**: Editable/eliminable con escritura abierta (FR-029). No afecta `saldo_pendiente` honorarios.

**Indexes**: `(escritura_id)`, `(fecha)`, UNIQUE `(impuesto_id)`

---

### PagoImpuestoEscribania (`pagos_impuesto_escribania`)

Misma estructura que `PagoImpuestoCliente`; genera línea en Libro de Salida.

---

## Enums

### `tipo_impuesto`

| DB value | UI label |
|---|---|
| `API` | API |
| `TGI` | TGI |
| `AGUAS_SANTAFESINAS` | Aguas Santafesinas |
| `EPE` | EPE |
| `EXPENSAS` | Expensas |
| `LITORAL_GAS` | Litoral Gas |

### `direccion_prorrateo`

- `hacia_atras` — tramo: `periodo_inicio` → `fecha_corte` (inclusive)
- `hacia_adelante` — tramo: `fecha_corte + 1 día` → `periodo_fin` (inclusive)

---

## Modified Entities (computed / API only)

### Escritura (response extensions)

| Field | Type | Derivation |
|---|---|---|
| `impuestos` | `list[ImpuestoEscrituraResponse]` | Relación 1:N |
| `total_pagado_impuestos_cliente` | NUMERIC | Σ montos pagos cliente impuestos |
| `total_pagado_impuestos_escribania` | NUMERIC | Σ montos pagos escribanía impuestos |
| `balance_impuestos` | NUMERIC | cliente − escribanía |
| `puede_cerrar_impuestos` | boolean | balance = 0 AND todos los impuestos con ambos pagos |

**Sin cambios** en `saldo_pendiente` / honorarios (FR-020).

### LiquidacionEscrituraItem (extended)

| Field | Type | Derivation |
|---|---|---|
| `monto_cobrado` | NUMERIC | Existente — honorarios (pagos_cliente) |
| `neto_impuestos` | NUMERIC | Σ pagos impuesto cliente mes − Σ pagos impuesto escribanía mes |

`LiquidacionEscribano.total` = Σ(`monto_cobrado` + `neto_impuestos`) por escrituras del escribano en el mes.

---

## Derived Views

### EntradaLibro (extended)

| Source | Line |
|---|---|
| `PagoCliente` (mes) | existente |
| `PagoImpuestoCliente` (mes) | monto, fecha, escritura, tipo_impuesto, origen=`impuesto` |

### SalidaLibro (extended)

| Source | Line |
|---|---|
| `PagoColegio` (mes) | existente |
| `PagoImpuestoEscribania` (mes) | monto, fecha, escritura, tipo_impuesto, origen=`impuesto` |

---

## State Transitions

### ImpuestoEscritura lifecycle

```text
[creado sin pagos] ──registrar pagos──► [con pagos parciales o completos]
       │                                        │
       │ eliminar (sin pagos)                   │ editar pagos / impuesto
       ▼                                        ▼
   [eliminado]                          [actualizado en libros/liquidación]

Al cerrar escritura: todos los impuestos deben tener ambos pagos y balance = 0.
Tras cierre: solo lectura (igual que otros movimientos).
```

### Close escritura guards (combined)

```text
close_escritura:
  1. saldo_pendiente honorarios == 0     (003, existente)
  2. balance_impuestos == 0              (006, nuevo)
  3. ∀ impuesto cargado: pago cliente ∧ pago escribanía  (006, nuevo)
```

---

## Migration `007_impuestos_escritura`

1. CREATE TYPE `tipo_impuesto`, `direccion_prorrateo`
2. CREATE TABLE `impuestos_escritura`
3. CREATE TABLE `pagos_impuesto_cliente` (UNIQUE impuesto_id)
4. CREATE TABLE `pagos_impuesto_escribania` (UNIQUE impuesto_id)
5. Indexes + FK cascades on escritura delete (TBD: RESTRICT if pagos exist)

No data migration from legacy tables (greenfield feature).
