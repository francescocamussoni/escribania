# Data Model: Pagos del Cliente y Libros Contables Basados en Caja Real

**Feature**: `003-pagos-cliente`  
**Date**: 2026-07-20  
**Source**: spec.md + research.md  
**Extends**: `001-plataforma-contaduria/data-model.md`, `002-platform-extensions/data-model.md`

---

## Entity Relationship Overview (delta)

```
                    Escritura
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
   FacturaPrincipal  PagoCliente   PagoColegio
   (unchanged calc)   (NEW)         (NEW)
          │             │             │
          │             ▼             ▼
          │      EntradaLibro    SalidaLibro
          │      (derived)       (derived)
          │             │
          └──── saldo derivado ────┘
                costo_total - SUM(pagos_cliente)

GastoAdicional — REMOVED (migrated → PagoCliente / PagoColegio)
```

---

## New Entities

### PagoCliente

Registro append-only de un pago real del cliente contra una Escritura.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `escritura_id` | UUID | FK → Escritura.id, not null | |
| `monto` | NUMERIC(18,2) | not null, > 0 | |
| `fecha` | DATE | not null | Filtro mensual para Libro Entrada y Liquidación |
| `concepto` | VARCHAR(500) | not null, default `''` | Opcional en API |
| `created_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- Solo en escrituras `abierta` (FR-005)
- `monto` ≤ `saldo_pendiente` vigente al registrar (FR-004)
- Inmutable post-creación (FR-006)
- Rechazado si `monto` ≤ 0

**Indexes**: `escritura_id` (btree), `fecha` (btree)

---

### PagoColegio

Registro append-only de un pago de la escribanía al Colegio de Escribanos.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `escritura_id` | UUID | FK → Escritura.id, not null | |
| `monto` | NUMERIC(18,2) | not null, > 0 | |
| `fecha` | DATE | not null | Filtro mensual para Libro Salida |
| `concepto` | VARCHAR(500) | not null, default `''` | Opcional en API |
| `created_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- Solo en escrituras `abierta` (FR-019)
- **Sin** validación contra saldo del cliente ni contra leyes notariales (FR-018)
- Inmutable post-creación (FR-020)
- Independiente del estado de cobro del cliente

**Indexes**: `escritura_id` (btree), `fecha` (btree)

---

## Modified Entities

### Escritura (computed fields — not persisted)

| Field | Type | Derivation |
|---|---|---|
| `costo_total` | NUMERIC(18,2) | `FacturaPrincipal.total_factura` |
| `total_pagado` | NUMERIC(18,2) | `SUM(PagoCliente.monto)` para la escritura |
| `saldo_pendiente` | NUMERIC(18,2) | `max(costo_total - total_pagado, 0)` |
| `sobrepago` | boolean | `total_pagado > costo_total` |
| `pagada_al_100` | boolean | `saldo_pendiente == 0` |
| `total_leyes_notariales_proyectadas` | NUMERIC(18,2) | `FacturaPrincipal.total_leyes_notariales` (solo para UI referencia) |

**Lifecycle change**:
- `cerrar` permitido solo si `saldo_pendiente == 0` (FR-007)

**Relationships**:
- `pagos_cliente: list[PagoCliente]` — reemplaza gastos entrada
- `pagos_colegio: list[PagoColegio]` — reemplaza gastos salida
- Eliminar relación `gastos: list[GastoAdicional]`

---

## Removed Entities

### GastoAdicional

**Status**: Deprecated → migrated and dropped in migration `006_pagos_cliente`.

| Legacy `direccion` | Migrates to |
|---|---|
| `entrada` | `pagos_cliente` |
| `salida` | `pagos_colegio` |

Escrituras cerradas sin pagos cliente: pago implícito al 100% (FR-035).

---

## Derived Views (no persistence)

### EntradaLibro

| Source | Line shape |
|---|---|
| `PagoCliente` WHERE `fecha` in month | monto, fecha_pago, escritura_id, escritura_nombre, concepto |

Plus `resumen_deudas`: escrituras abiertas con `saldo_pendiente > 0` → costo_total, total_pagado, saldo_pendiente.

### SalidaLibro

| Source | Line shape |
|---|---|
| `PagoColegio` WHERE `fecha` in month | monto, fecha_pago, escritura_id, escritura_nombre, concepto |

### LiquidacionMensual (recomputed)

| Source | Line shape |
|---|---|
| `PagoCliente` grouped by escritura WHERE `fecha` in month | escritura_id, nombre, monto_cobrado = SUM(pagos mes) |

Escrituras sin pagos en el mes: **excluidas**.

### PagoSalario — bloque escribanos (recomputed)

Misma fuente que Liquidación: suma de `monto_cobrado` por escribano. Bloque secretarias sin cambio (Empleado.sueldo).

---

## State Transitions

### Escritura — cierre

```
abierta + saldo_pendiente > 0  ──cerrar──►  RECHAZADO (409)
abierta + saldo_pendiente == 0 ──cerrar──►  cerrada (inmutable)
```

### PagoCliente / PagoColegio

```
escritura abierta ──registrar──►  creado (inmutable)
escritura cerrada ──registrar──►  RECHAZADO (409)
```

---

## Validation Summary

| Rule | Entity | Enforcement |
|---|---|---|
| monto > 0 | PagoCliente, PagoColegio | Pydantic + DB CHECK |
| pago cliente ≤ saldo pendiente | PagoCliente | Service layer |
| solo escritura abierta | Ambos | Service layer `_ensure_open` |
| cierre solo si saldo = 0 | Escritura | `close_escritura` guard |
| append-only | PagoCliente, PagoColegio | No UPDATE/DELETE endpoints |
