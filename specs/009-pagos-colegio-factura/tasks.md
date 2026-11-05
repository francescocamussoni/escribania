# Tasks: Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Feature Branch**: `009-pagos-colegio-factura`  
**Input**: `specs/009-pagos-colegio-factura/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD-first — tests en estado FAILING antes de cada implementación (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature (research R-006, plan Technical Context). Reutilizar patrones de `PagoColegioForm`, `FacturaDetalle`, `EscrituraList` y tokens existentes en `index.css`. El campo `figma:` **no aplica** — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario (US1–US3)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar prerequisitos y alinear artefactos de diseño.

- [x] T001 Revisar alineación entre `specs/009-pagos-colegio-factura/contracts/openapi-delta.yaml` y `specs/009-pagos-colegio-factura/data-model.md`
- [x] T002 Verificar que features `007-refactor-factura-montos` y `008-factura-vencimiento-monotributo` están mergeadas (migraciones `009`, `011`)
- [x] T003 [P] Agregar tipos stub `TipoPagoEscribania`, `FacturaLineaItem` y `lineas_deshabilitadas` en `frontend/src/types/api.ts`

**Checkpoint**: Contratos alineados. Dependencias 007/008 confirmadas.

---

## Phase 2: Foundational — Líneas de factura habilitables (bloqueante)

**Purpose**: Catálogo de líneas, máscara de montos efectivos y migración `012` (columna `lineas_deshabilitadas`). Prerequisito de US1 (plazo con `total_impuestos_efectivo`) y US2.

**Independent Test**: `pytest backend/tests/unit/test_factura_lineas.py -v` — fixture canónico; deshabilitar `sellos` reduce `total_impuestos_efectivo`; deshabilitar `municipio` no altera impuestos.

### Tests TDD — Foundational (⚠️ FAIL FIRST)

- [x] T004 ⚠️ FAIL FIRST Crear `backend/tests/unit/test_factura_lineas.py`: catálogo `FACTURA_LINEA_KEYS`, `aplicar_lineas_habilitadas`, `total_impuestos_efectivo`, validación al menos una línea habilitada (research R-003)

### Implementación — Foundational

- [x] T005 [P] Crear `backend/src/services/factura_lineas.py` con `FACTURA_LINEA_KEYS`, `IMPUESTO_LINEA_KEYS` y `aplicar_lineas_habilitadas()`
- [x] T006 Integrar máscara en `backend/src/services/factura_lineas.py` + `escritura_service.py` (máscara no en `calculo_factura.py` — cálculo base intacto)
- [x] T007 Crear migración `backend/alembic/versions/012_pagos_colegio_factura_lineas.py`: `facturas_principales.lineas_deshabilitadas` JSONB default `[]`; enum `tipo_pago_escribania`; columna `pagos_colegio.tipo`; backfill desde `imputacion`; drop `imputacion`
- [x] T008 [P] Agregar `lineas_deshabilitadas` en `backend/src/models/factura_principal.py`
- [x] T009 [P] Reemplazar `ImputacionPagoColegio` por `TipoPagoEscribania` en `backend/src/models/pago_colegio.py`
- [x] T010 Ejecutar `alembic upgrade head` y verificar backfill (`colegio` / `otros`)

**Checkpoint**: Motor de líneas habilitables verde. Migración `012` aplicada.

---

## Phase 3: User Story 1 — Pagos de la escribanía y Libro de Salida (Priority: P1) 🎯 MVP

**Goal**: Tipos **Colegio** / **Otros** en Pagos de la escribanía; Libro de Salida solo `pagos_colegio`; plazo usa pagos `tipo=colegio` y `total_impuestos_efectivo`.

**Independent Test**: Registrar pago Colegio y Otros → ambos en Libro de Salida (Otros con detalle); impuestos 006 y gastos 005 ausentes; pago Colegio actualiza plazo.

### Tests TDD — US1 (⚠️ FAIL FIRST)

- [x] T011 [US1] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_pago_colegio_service.py`: `tipo` obligatorio; `otros` exige `concepto`; default `colegio`
- [x] T012 [P] [US1] ⚠️ FAIL FIRST Actualizar `backend/tests/unit/test_libros_service.py`: salida solo `pagos_colegio`; línea Otros muestra detalle; excluir impuesto escribanía y gastos extraordinarios
- [x] T013 [P] [US1] ⚠️ FAIL FIRST Actualizar `backend/tests/unit/test_plazo_colegio.py`: `sum_pagos_colegio` por `tipo=colegio`; `monto_referencia` = `total_impuestos_efectivo`

### Implementación backend — US1

- [x] T014 [P] [US1] Reemplazar `imputacion` por `tipo` en `backend/src/schemas/pago_colegio.py` con validación detalle obligatorio si `otros`
- [x] T015 [US1] Actualizar `create_pago` en `backend/src/services/pago_colegio_service.py` hasta que `T011` pase
- [x] T016 [US1] Renombrar `sum_pagos_impuestos` → `sum_pagos_colegio` en `backend/src/services/plazo_colegio.py` (filtrar `tipo=colegio`)
- [x] T017 [US1] Usar `total_impuestos_efectivo` en `build_plazo_colegio_fields()` en `backend/src/services/escritura_service.py` hasta que `T013` pase
- [x] T018 [US1] Refactorizar `get_libro_salida()` en `backend/src/services/libros_service.py` — solo `pagos_colegio`; mapear `tipo_pago` y detalle hasta que `T012` pase
- [x] T019 [P] [US1] Agregar `tipo_pago` a `LibroLineaResponse` en `backend/src/schemas/libros.py`
- [x] T020 [US1] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_escrituras_api.py`: POST pago `colegio`/`otros`; GET libro salida sin fuentes 005/006

### Implementación frontend — US1

- [x] T021 [US1] Reemplazar selector imputación por tipo Colegio/Otros en `frontend/src/components/escrituras/PagoColegioForm.tsx`
- [x] T022 [P] [US1] Mostrar tipo y detalle en `frontend/src/components/escrituras/PagoColegioList.tsx`
- [x] T023 [US1] Mostrar `tipo_pago` y detalle Otros en `frontend/src/components/libros/LibroSalidaTable.tsx`
- [x] T024 [US1] Actualizar `PagoColegioInput`/`Response` y `LibroLineaResponse` en `frontend/src/types/api.ts`; eliminar `ImputacionPagoColegio`
- [x] T025 [P] [US1] Crear `frontend/src/utils/tipoPagoEscribania.ts` y eliminar `frontend/src/utils/imputacionColegio.ts`

**Checkpoint**: US1 completa — pagos clasificados, libro restringido, plazo coherente. MVP backend+libro operativo.

---

## Phase 4: User Story 2 — Montos opcionales en factura (Priority: P1)

**Goal**: Casillero por ítem de línea; `costo_total` y saldo solo con ítems habilitados; persistir `lineas_deshabilitadas`.

**Independent Test**: Deshabilitar ítems en factura abierta → costo al cliente baja; deshabilitar impuesto baja Total impuestos y pendiente Colegio; escritura cerrada bloquea cambios.

### Tests TDD — US2 (⚠️ FAIL FIRST)

- [x] T026 [US2] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_factura_lineas.py`: integración con `build_saldo_fields` — costo_total efectivo
- [x] T027 [P] [US2] ⚠️ FAIL FIRST Agregar tests PATCH `lineas_deshabilitadas` en `backend/tests/integration/test_escrituras_api.py`: validación mínimo una línea; cerrada → 409

### Implementación backend — US2

- [x] T028 [P] [US2] Agregar `FacturaLineaItem`, `lineas`, `total_impuestos_efectivo` en `backend/src/schemas/factura.py`
- [x] T029 [US2] Extender `EscrituraUpdate` con `lineas_deshabilitadas` en `backend/src/schemas/escritura.py` (`extra=forbid`, validación keys)
- [x] T030 [US2] Integrar `aplicar_lineas_habilitadas` en `build_saldo_fields` y respuesta factura en `backend/src/services/escritura_service.py` hasta que `T026`–`T027` pasen
- [x] T031 [US2] Publicar evento SSE `escritura.updated` al guardar `lineas_deshabilitadas` en `backend/src/services/escritura_service.py`

### Implementación frontend — US2

- [x] T032 [US2] Agregar casillero por ítem de línea (habilitada/no cobrada) en `frontend/src/components/escrituras/FacturaDetalle.tsx`
- [x] T033 [US2] Persistir toggles vía PATCH escritura (`lineas_deshabilitadas`) desde `frontend/src/pages/EscrituraDetail.tsx`
- [x] T034 [P] [US2] Invalidar queries escritura/listado/libro en `frontend/src/hooks/useSSE.ts` ante `escritura.updated`

**Checkpoint**: US2 completa — factura configurable por cliente sin romper plazo Colegio.

---

## Phase 5: User Story 3 — Pago masivo al Colegio (Priority: P2)

**Goal**: Selección múltiple en listado; preview de pendientes; confirmación con fecha única.

**Independent Test**: Seleccionar 2+ escrituras con pendiente → preview → confirm → N pagos `tipo=colegio` misma fecha; cerradas/sin pendiente excluidas.

### Tests TDD — US3 (⚠️ FAIL FIRST)

- [x] T035 [US3] ⚠️ FAIL FIRST Crear `backend/tests/unit/test_pago_colegio_bulk.py`: preview elegibilidad, pendiente propuesto, confirm fecha única
- [x] T036 [P] [US3] ⚠️ FAIL FIRST Crear `backend/tests/integration/test_pagos_colegio_bulk_api.py`: POST preview + bulk end-to-end

### Implementación backend — US3

- [x] T037 [P] [US3] Crear schemas en `backend/src/schemas/pago_colegio_bulk.py` (preview, bulk request/response)
- [x] T038 [US3] Implementar `preview_bulk` y `confirm_bulk` en `backend/src/services/pago_colegio_bulk_service.py` hasta que `T035` pase
- [x] T039 [US3] Registrar rutas `POST /escrituras/pagos-colegio/bulk/preview` y `POST /escrituras/pagos-colegio/bulk` en `backend/src/api/routes/escrituras.py` hasta que `T036` pase

### Implementación frontend — US3

- [x] T040 [P] [US3] Agregar `previewPagoColegioBulk` y `confirmPagoColegioBulk` en `frontend/src/api/pagosColegio.ts`
- [x] T041 [US3] Crear `frontend/src/components/escrituras/PagoColegioBulkModal.tsx` (resumen, montos editables, fecha única)
- [x] T042 [US3] Agregar checkboxes por fila y acción **Pago al colegio de escribanos** en `frontend/src/components/escrituras/EscrituraList.tsx`
- [x] T043 [US3] Wiring modal + invalidación SSE en `frontend/src/pages/EscriturasPage.tsx`

**Checkpoint**: US3 completa — flujo masivo operativo desde listado.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Demo seed, validación integral y limpieza legacy imputación.

- [x] T044 Actualizar `backend/scripts/seed_demo_data.py` a `DEMO_SEED_VERSION=6` con líneas deshabilitadas demo y pagos `tipo` colegio/otros
- [x] T045 [P] Eliminar referencias residuales a `ImputacionPagoColegio` en backend (grep + cleanup tests)
- [x] T046 Ejecutar checklist manual en `specs/009-pagos-colegio-factura/quickstart.md`
- [x] T047 [P] Ejecutar suite completa `pytest backend/tests/ -v`
- [x] T048 [P] Ejecutar `npm test -- --run` en `frontend/` (PagoColegio, FacturaDetalle, EscrituraList si existen)

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational — factura_lineas + migration 012)  ← BLOCKS ALL STORIES
    ↓
    ├── Phase 3 (US1 — pagos + libro + plazo)     🎯 MVP
    ├── Phase 4 (US2 — toggles factura)           [P1, after Phase 2; plazo US1 benefits from US2 data]
    └── Phase 5 (US3 — bulk)                      [P2, after US1 backend]
    ↓
Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depends on | Independent test |
|-------|------------|------------------|
| **US1** (P1) | Phase 2 | Pagos Colegio/Otros + Libro Salida + plazo |
| **US2** (P1) | Phase 2 | Toggles factura + costo_total efectivo |
| **US3** (P2) | US1 backend (tipo colegio, pendiente) | Bulk preview + confirm |

**Recommended sequence**: Phase 2 → US1 → US2 → US3 (US2 puede solaparse con US1 frontend tras T017).

### Parallel Opportunities

- **Phase 1**: T003 en paralelo con T001–T002
- **Phase 2**: T005, T008, T009 en paralelo tras T004; T007 tras T005–T006
- **US1 tests**: T011, T012, T013 en paralelo; T014, T019, T022, T025 en paralelo
- **US2**: T028 en paralelo con T029; T034 en paralelo con T032–T033
- **US3**: T037 en paralelo con T035; T040 en paralelo con T038–T039
- **Polish**: T045, T047, T048 en paralelo

---

## Parallel Example: User Story 1

```bash
# Tests US1 en paralelo (FAIL FIRST):
pytest backend/tests/unit/test_pago_colegio_service.py -v
pytest backend/tests/unit/test_libros_service.py -v -k salida
pytest backend/tests/unit/test_plazo_colegio.py -v

# Backend US1 en paralelo (tras tests failing):
# T014 schemas/pago_colegio.py + T019 schemas/libros.py

# Frontend US1 en paralelo (tras API):
# T022 PagoColegioList.tsx + T025 tipoPagoEscribania.ts
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1 + Phase 2 (foundational)
2. Completar Phase 3 (US1) — pagos, libro, plazo
3. **VALIDAR**: quickstart § Pagos + Libro de Salida
4. Demo/deploy parcial

### Incremental Delivery

1. Foundation → US1 (MVP contable egresos)
2. US2 (flexibilidad factura al cliente)
3. US3 (eficiencia operativa bulk)
4. Polish + seed v6

### Suggested MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1)** — 25 tareas (T001–T025). Entrega valor: clasificación Colegio/Otros, Libro de Salida corregido, plazo coherente.

---

## Task Summary

| Phase | Tasks | Count |
|-------|-------|-------|
| Setup | T001–T003 | 3 |
| Foundational | T004–T010 | 7 |
| US1 (P1) | T011–T025 | 15 |
| US2 (P1) | T026–T034 | 9 |
| US3 (P2) | T035–T043 | 9 |
| Polish | T044–T048 | 5 |
| **Total** | **T001–T048** | **48** |

**Format validation**: ✅ Todas las tareas usan `- [ ]`, ID `T###`, rutas de archivo explícitas; `[Story]` en fases US1–US3; TDD marcado con `⚠️ FAIL FIRST` donde aplica.

---

## Notes

- Sin campo `figma:` — ver nota al inicio del documento
- Migration `012` unifica cambios de US1 (tipo) y foundational (lineas_deshabilitadas)
- Feature 008 `imputacion` queda **superseded** — tests legacy deben actualizarse en T011/T045
- `total_impuestos_efectivo` alimenta plazo y preview bulk (clarify sesión 2026-07-26)
