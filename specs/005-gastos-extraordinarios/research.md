# Research: Gastos Extraordinarios de la Escribanía

**Feature**: `005-gastos-extraordinarios`  
**Date**: 2026-07-20  
**Source**: spec.md + codebase analysis (libros, salarios, pagos colegio)

---

## R-001 — Persistencia: tabla única sin escritura

**Decision**: Una tabla `gastos_extraordinarios` con `concepto`, `monto`, `fecha`, timestamps. Sin FK a `escrituras`.

**Rationale**: FR-016; gastos de la escribanía global, no por deed. Modelo simple similar a `pagos_colegio` pero sin `escritura_id`.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Reutilizar `pagos_colegio` con escritura ficticia | Viola FR-016 y contamina saldos de escritura |
| Tabla mensual agregada sin detalle | No permite editar/eliminar líneas individuales (FR-005) |

**Migración**: `008_gastos_extraordinarios` (siguiente después de `007_impuestos_escritura`).

---

## R-002 — Libro de Salida

**Decision**: Extender `libros_service.get_libro_salida()` para incluir gastos extraordinarios filtrados por `fecha` en el mes. Extender `LibroOrigen` con `"extraordinario"`. `escritura_id` y `escritura_nombre` opcionales (`null`) en `LibroLineaResponse`.

**Rationale**: FR-007–FR-010; una línea por gasto; sin escritura asociada; diferenciación visual por `origen`.

**Alternatives considered**:
- Líneas sintéticas solo en frontend → rompe FR-015 (consistencia con backend).

---

## R-003 — Reparto en Pago de Salarios

**Decision**: Módulo puro `gasto_extraordinario_reparto.py`:

```text
cuota_base = floor(total / n, 2 decimales)   # ROUND_DOWN por escribano
remanente = total - cuota_base * n
asignar remanente al último escribano en orden alfabético por nombre
```

Extender `PagoEscribano` con `deduccion_gastos_extraordinarios` y `monto_neto = monto_total - deduccion`. Agregar a `PagoSalariosResumen`: `total_gastos_extraordinarios` y `advertencia_reparto` (string opcional si `n = 0`).

**Rationale**: Edge case spec (redondeo determinístico); FR-011–FR-014; SC-003/SC-004.

**Alternatives considered**:
| Alternativa | Por qué se descartó |
|---|---|
| Reparto solo en frontend | Inconsistente entre clientes; viola P3 |
| Ponderar por escrituras del mes | Contradice spec (reparto equitativo) |

---

## R-004 — Liquidación y Libro de Entrada

**Decision**: **Sin cambios**. Gastos extraordinarios no impactan liquidación ni libro de entrada (spec Edge Cases + FR implícito).

---

## R-005 — API y rutas

**Decision**: Router dedicado `GET/POST /gastos-extraordinarios` con query `anio`/`mes` en listado; `PATCH/DELETE /gastos-extraordinarios/{id}`. Prefijo `/api/v1/gastos-extraordinarios`.

**Rationale**: Recurso de primer nivel (no anidado bajo escritura), alineado con páginas mensuales existentes (`/liquidacion`, `/libros`).

---

## R-006 — SSE

**Decision**: Publicar `gasto_extraordinario.created`, `gasto_extraordinario.updated`, `gasto_extraordinario.deleted` + `libros_updated`. Invalidar queries `salarios` y `libros` en frontend (no `liquidacion`).

**Rationale**: FR-010, FR-014; P5 real-time; spec excluye liquidación.

---

## R-007 — UI y navegación

**Decision**: Nueva página `GastosExtraordinariosPage` con selector mes/año (patrón `LiquidacionPage`). Link en navbar **segunda posición** (después de Escrituras). Sin Figma — reutilizar `gasto-form`, `libro-table`, `period-selector` de 004/006.

**Rationale**: spec Assumptions; FR-001.

---

## R-008 — TDD y orden de implementación

**Decision**:

1. `gasto_extraordinario_reparto.py` + tests (división exacta, indivisible, n=0)
2. Migración `008` + modelo + schemas
3. `gasto_extraordinario_service` CRUD + tests
4. Extender `libros_service` + tests
5. Extender `salario_service` + tests
6. API routes + integration tests
7. Frontend página + navbar + salarios/libros UI

**Rationale**: Lógica pura primero (P6); dependencias claras hacia integración.
