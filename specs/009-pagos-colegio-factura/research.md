# Research: Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Feature**: `009-pagos-colegio-factura`  
**Date**: 2026-07-26  
**Source**: spec.md + clarify session 2026-07-26 + codebase analysis

---

## R-001 — Reemplazo de imputación 008 por tipo Colegio / Otros

**Decision**: Reemplazar `ImputacionPagoColegio` (`total_impuestos` \| `honorarios_varios` \| `otro`) por
`TipoPagoEscribania` (`colegio` \| `otros`) en `pagos_colegio`.

| Tipo API | UI | Libro de Salida | Afecta plazo Total impuestos |
|---|---|---|---|
| `colegio` | Pago al colegio de escribanos | Sí | Sí — reduce pendiente |
| `otros` | Otros (detalle obligatorio) | Sí — muestra detalle | No |

**Migración `012`**:

1. Crear enum `tipo_pago_escribania`
2. Agregar columna `tipo` con backfill:
   - `imputacion IN (total_impuestos, honorarios_varios)` → `colegio`
   - `imputacion = otro` → `otros` (conservar `concepto` como detalle)
3. Eliminar columna `imputacion` y tipo `imputacion_pago_colegio`

**Rationale**: Clarify Q2; elimina selector de honorarios varios; simplifica `plazo_colegio` (suma pagos
`tipo=colegio` en lugar de filtrar imputación).

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Mantener imputación + tipo | UX redundante; honorarios varios explícitamente excluido |
| Tabla separada `pagos_otros` | Duplica modelo; mismo libro y misma solapa |

---

## R-002 — Libro de Salida: solo Pagos de la escribanía

**Decision**: `get_libro_salida` consulta **únicamente** `pagos_colegio` del mes. Eliminar agregación de
`pagos_impuesto_escribania` y `gastos_extraordinarios`.

**Línea de libro** (`LibroLineaResponse` extendido):

- `tipo_pago`: `colegio` \| `otros`
- `concepto`: etiqueta fija "Pago al colegio de escribanos" o detalle libre para `otros`
- `origen` deprecado → reemplazar por `tipo_pago` en UI (mantener compatibilidad temporal en API con
  `origen="honorario"` mapeado a colegio si necesario para tests legacy)

**Rationale**: FR-007; alinea libro con solapa única de egresos de escribanía.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Vista filtrada sobre libro actual | Sigue mezclando fuentes; confuso para secretaria |
| Reporte separado para impuestos 006 | Fuera de scope; módulo 006 conserva su historial |

---

## R-003 — Ítems de factura habilitables (por línea)

**Decision**:

1. Catálogo canónico `FACTURA_LINEA_KEYS` en `services/factura_lineas.py` (~30 claves leaf, sin
   subtotales derivados).
2. Columna `lineas_deshabilitadas` JSONB en `facturas_principales` — array de strings; `[]` = todo
   habilitado (default migración).
3. Función pura `aplicar_lineas_habilitadas(calculo_completo, deshabilitadas) -> FacturaEfectiva`:
   - Monto efectivo por línea = calculado si habilitada, else `0`
   - Recalcula subtotales y totales desde montos efectivos
   - `total_impuestos_efectivo` = suma de líneas impuesto habilitadas (`tasa_3pm`, `sellos`,
     `tasa_75pm`, `firma_impuestos`)
4. `costo_total` escritura = `total_factura` efectivo (Total + IVA sobre ítems habilitados)
5. Plazo colegio usa `total_impuestos_efectivo` y pagos `tipo=colegio`

**Claves impuesto** (afectan Colegio):

```text
IMPUESTO_LINEA_KEYS = ("tasa_3pm", "sellos", "tasa_75pm", "firma_impuestos")
```

**Validación**: al menos una línea cobrable habilitada (`len(deshabilitadas) < len(FACTURA_LINEA_KEYS)`).

**Rationale**: Clarify Q3 (ítem de línea) + Q5 (una sola lectura para Total impuestos).

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Tabla `factura_linea_estado` normalizada | Overkill para ~30 flags por factura |
| Doble lectura (cliente vs colegio) | Rechazado en clarify Q5 |

---

## R-004 — Pago masivo al Colegio

**Decision**: Nuevo endpoint `POST /api/v1/escrituras/pagos-colegio/bulk` + preview opcional
`POST /api/v1/escrituras/pagos-colegio/bulk/preview`.

**Flujo**:

1. Listado Escrituras: checkboxes + barra de acción
2. Preview: `{ escritura_ids[] }` → por escritura `{ id, nombre, pendiente, elegible, motivo? }`
3. Confirm: `{ fecha, items: [{ escritura_id, monto }] }` → crea N pagos `tipo=colegio`, misma `fecha`
4. Transacción única; publicar SSE `pago_colegio.created` por escritura (existente)
5. Monto editable por fila en modal; sin validación estricta vs pendiente (edge case spec)

**Pendiente propuesto**: `max(0, total_impuestos_efectivo - SUM(pagos tipo colegio))`.

**Rationale**: FR-020–024; fecha única (clarify Q4).

---

## R-005 — Plazo colegio (ajuste sobre 008)

**Decision**: Actualizar `sum_pagos_impuestos` → `sum_pagos_colegio` (todos los pagos `tipo=colegio`).
`monto_referencia` = `total_impuestos_efectivo` de factura (post-máscara habilitación).

**Rationale**: Sin imputación; colegio siempre cubre Total impuestos; pagos Otros no cuentan (FR-012).

---

## R-006 — TDD y orden de implementación

**Decision**: Orden TDD recomendado:

1. `test_factura_lineas.py` — máscara habilitación + total_impuestos efectivo
2. `test_plazo_colegio.py` — adaptar suma por tipo colegio + referencia efectiva
3. `test_libros_service.py` — salida solo pagos_colegio; línea otros con detalle
4. `test_pago_colegio_service.py` — tipo + validación detalle
5. `test_pago_colegio_bulk.py` — preview + bulk
6. Integración API + frontend

**Rationale**: Spec Testing Strategy TDD-first; dependencias 007/008 ya merged.

---

## R-007 — SSE y saldo cliente

**Decision**: Reutilizar eventos `pago_colegio.created`; agregar `escritura.updated` tras cambio de
`lineas_deshabilitadas` para invalidar listado, detalle y libros.

**Rationale**: P5 constitution; sin polling.
