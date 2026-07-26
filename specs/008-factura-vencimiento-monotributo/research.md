# Research: Vencimiento de pago al Colegio y régimen Monotributo

**Feature**: `008-factura-vencimiento-monotributo`  
**Date**: 2026-07-26  
**Source**: spec.md + clarify session 2026-07-26 + codebase analysis

---

## R-001 — Cálculo de plazo (función pura)

**Decision**: Nuevo módulo `services/plazo_colegio.py` con función pura `calcular_plazo_colegio(...)` y constantes nombradas:

```text
PLAZO_COLEGIO_DIAS = 30
```

**Inputs**:

- `fecha_creacion: date` — fecha calendario de `escritura.created_at` (zona local AR al serializar)
- `total_impuestos: Decimal`
- `monto_pagado_impuestos: Decimal` — suma de `pagos_colegio.monto` donde `imputacion == total_impuestos`
- `fecha_referencia: date` — hoy (inyectable en tests)

**Outputs** (`PlazoColegioResult`):

| Campo | Tipo | Regla |
|---|---|---|
| `estado` | enum | `no_aplica` \| `pendiente` \| `vencido` \| `pagado` |
| `fecha_vencimiento` | date \| null | `fecha_creacion + 30 días` si aplica |
| `dias_restantes` | int \| null | `max(0, (fecha_vencimiento - fecha_referencia).days)` |
| `urgencia` | enum \| null | `verde` \| `amarillo` \| `rojo` \| null (null si pagado/no_aplica) |
| `monto_referencia` | Decimal | `total_impuestos` |
| `monto_pagado` | Decimal | imputado a impuestos |
| `monto_pendiente` | Decimal | `max(0, total_impuestos - monto_pagado)` |

**Bandas de color** (límites superiores inclusivos en spec):

| Urgencia | Días restantes |
|---|---|
| `verde` | 21–30 |
| `amarillo` | 11–20 |
| `rojo` | 0–10 o vencido |

**Rationale**: P6 (funciones puras, testeables); misma función alimenta listado y detalle (SC-001).

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Calcular solo en frontend | Duplica reglas; rompe SC-001 |
| Persistir `fecha_vencimiento` en DB | Derivable de `created_at`; riesgo de desincronización |

---

## R-002 — Imputación en pagos al Colegio

**Decision**: Columna `imputacion` en `pagos_colegio` como `ENUM` PostgreSQL:

- `total_impuestos` — UI: "Total impuestos / Corresponde"
- `honorarios_varios` — UI: "Honorarios varios"
- `otro` — UI: "Otro"

Migración `011_plazo_colegio_monotributo`:

1. Crear tipo `imputacion_pago_colegio`
2. Agregar columna `NOT NULL` con default temporal `honorarios_varios`
3. Backfill filas existentes → `honorarios_varios` (clarify Q4)
4. Quitar default server-side tras backfill (input obligatorio en API)

**Rationale**: FR-003a/b; separación explícita impuestos vs honorarios varios; libro de salida sin cambio de agregación.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Fungible (suma total pagos) | Rechazado en clarify Q2 |
| Campo `concepto` libre parseado | Frágil; no validable |

---

## R-003 — Monotributista en Escribano

**Decision**:

- Columna `escribano.monotributista BOOLEAN NOT NULL DEFAULT false`
- Migración setea `true` donde `lower(nombre) = 'costanza'`
- Nuevo endpoint `PATCH /api/v1/configuracion/escribanos/{id}` con body `{ monotributista: bool }`
- `calcular_totales_factura(..., *, monotributista: bool = False)`:
  - si `monotributista`: `iva = 0`, `total_factura = total_sin_iva`
  - si no: fórmula 007 sin cambios
- Al PATCH monotributista: servicio `recalcular_escrituras_abiertas_escribano(session, escribano_id)` — solo `estado == abierta`

**Rationale**: FR-011–FR-013; clarify recálculo inmediato; Costanza en seed (FR-014).

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Lazy recalc | Rechazado en clarify Q3 |
| Flag en Escritura | Duplica régimen; escribano es fuente de verdad tributaria |

---

## R-004 — Exposición API (listado y detalle)

**Decision**: Objeto anidado `plazo_colegio` en `EscrituraListItem` y `EscrituraResponse`, calculado en `escritura_service` al mapear cada fila:

```python
build_plazo_colegio_fields(escritura, fecha_referencia=date.today())
```

Requiere cargar `pagos_colegio` en list query (añadir a `_escritura_load_options()`).

**Ordenamiento por vencimiento**: client-side en frontend (`sortByVencimiento` en `escrituraList.ts`), igual que `sortByCreatedAt`. Session state extiende `sortField: "created_at" | "vencimiento"`. Filas `no_aplica` / `pagado` al final (sort key secundario estable por `id`).

**Rationale**: Volumen bajo (<500 escrituras); evita nuevo query param server-side; patrón existente en `EscriturasPage`.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Sort server-side | Overkill para <10 usuarios; más API surface |
| Campo plano suelto | Menos cohesión que objeto `plazo_colegio` |

---

## R-005 — UI y tokens de color

**Decision**: Componentes nuevos/reutilizados:

- `PlazoColegioBadge.tsx` — badge con clase `plazo-colegio--{urgencia|pagado|vencido|na}`
- Colores desde variables CSS existentes del theme (`--color-success`, `--color-warning`, `--color-danger`); sin Figma node (indicadores funcionales sobre layout existente — reorganización de alerta, no nueva pantalla).

**Encabezado**: `EscrituraDetail.tsx` — fila junto a estado/escribano con mismo `PlazoColegioBadge` + fecha vencimiento.

**Listado**: nueva columna en `EscrituraList.tsx` + header sortable alternando `created_at` ↔ `vencimiento`.

**PagoColegioForm**: `<select>` obligatorio imputación (3 opciones).

**EscribanosConfig**: toggle/checkbox Monotributista + `PATCH` vía nuevo hook `useUpdateEscribano`.

**Rationale**: P4 (claridad secretaria); spec-kitti-figma no aplica (sin frame nuevo; tokens semánticos del design system).

---

## R-006 — SSE y eventos

**Decision**:

- `pago_colegio.created` — ya invalida escritura; sin cambio de payload (frontend refetch trae nuevo `plazo_colegio`)
- Nuevo evento `escribano.updated` con `{ escribano_id }` tras PATCH monotributista → invalidar escrituras list + liquidación

**Rationale**: P5 (push, no polling).

---

## R-007 — Seed demo y tests

**Decision**:

- `DEMO_SEED_VERSION` bump → `5`
- Costanza `monotributista=true`; escrituras demo suyas con `iva=0`, `total_factura=total_sin_iva`
- Pagos colegio demo: mezcla de imputaciones para probar countdown
- Escrituras demo con `created_at` escalonadas (hoy, -15d, -28d) para bandas de color

**Canonical fixture monotributo** (mismos inputs USD/MEP/Nación):

| Campo | No monotributo (007) | Monotributo |
|---|---|---|
| `iva` | 1_875_257.52 | 0.00 |
| `total_factura` | 11_550_066.53 | 9_674_809.01 |

**Rationale**: TDD-first; fixtures explícitos en research para plan/tasks.

---

## R-008 — Dependencia feature 007

**Decision**: Feature 008 asume 007 merged (`total_impuestos`, `total_sin_iva`, `iva`, `total_factura` en schema). Branch base: `007-refactor-factura-montos` o `main` si ya mergeado.

**Rationale**: spec Dependencies; `total_impuestos` proviene de Corresponde.
