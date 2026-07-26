# Tasks: Vencimiento de pago al Colegio y régimen Monotributo

**Feature Branch**: `008-factura-vencimiento-monotributo`  
**Input**: `specs/008-factura-vencimiento-monotributo/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD-first — tests en estado FAILING antes de cada implementación (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature (research R-005, plan Technical Context). Indicadores funcionales con tokens CSS existentes (`--color-success`, `--color-warning`, `--color-danger`). El campo `figma:` **no aplica** — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario (US1–US5)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar prerequisitos y alinear artefactos de diseño.

- [x] T001 Revisar alineación entre `specs/008-factura-vencimiento-monotributo/contracts/openapi-delta.yaml` y `specs/008-factura-vencimiento-monotributo/data-model.md`
- [x] T002 Verificar que feature `007-refactor-factura-montos` está mergeada (migración `009_factura_totales` y columna `total_impuestos` en factura)
- [x] T003 [P] Agregar tipos stub `PlazoColegioResponse` e `ImputacionPagoColegio` en `frontend/src/types/api.ts`

**Checkpoint**: Contratos alineados. Dependencia 007 confirmada. Tipos TS listos.

---

## Phase 2: Foundational — Cálculo puro de plazo (bloqueante)

**Purpose**: Lógica pura de vencimiento, bandas de color y estados — prerequisito de US1, US2 y US3.

**Independent Test**: `pytest backend/tests/unit/test_plazo_colegio.py -v` — todos los estados y bandas sin DB.

### Tests TDD — Foundational (⚠️ FAIL FIRST)

- [x] T004 ⚠️ FAIL FIRST Crear `backend/tests/unit/test_plazo_colegio.py`: `no_aplica` (total_impuestos=0), `pagado`, `pendiente` verde/amarillo/rojo, `vencido`, límites inclusivos 30/20/10 días (research R-001)

### Implementación — Foundational

- [x] T005 [P] Crear `backend/src/schemas/plazo_colegio.py` con `PlazoColegioResponse` y enums `PlazoColegioEstado`, `PlazoColegioUrgencia`
- [x] T006 Implementar `calcular_plazo_colegio()` y `sum_pagos_impuestos()` en `backend/src/services/plazo_colegio.py` con `PLAZO_COLEGIO_DIAS = 30` hasta que `T004` pase

**Checkpoint**: Motor de plazo puro verde. Sin dependencia de migración.

---

## Phase 3: User Story 5 — Imputar pagos al Colegio (Priority: P1)

**Goal**: Imputación obligatoria en pagos al Colegio; solo `total_impuestos` cuenta para cerrar el plazo.

**Independent Test**: POST pago sin imputación → 422; pago `honorarios_varios` no cierra plazo; pago `total_impuestos` ≥ Total impuestos → estado `pagado` en API.

**⚠️ CRITICAL**: Bloquea cálculo correcto de `plazo_colegio.monto_pagado` (US1, US3).

### Tests TDD — US5 (⚠️ FAIL FIRST)

- [x] T007 [US5] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_pago_colegio_service.py`: imputación obligatoria, suma filtrada `total_impuestos`, legacy no cuenta
- [x] T008 [P] [US5] ⚠️ FAIL FIRST Agregar tests integración POST `/escrituras/{id}/pagos-colegio` con/sin `imputacion` en `backend/tests/integration/test_escrituras_api.py` (o `test_pagos_colegio_api.py` si existe)

### Implementación backend — US5

- [x] T009 [US5] Crear migración `backend/alembic/versions/011_plazo_colegio_monotributo.py` (parte 1): enum `imputacion_pago_colegio`, columna `pagos_colegio.imputacion`, backfill `honorarios_varios`
- [x] T010 [P] [US5] Agregar columna `imputacion` en `backend/src/models/pago_colegio.py`
- [x] T011 [P] [US5] Extender `PagoColegioInput` / `PagoColegioResponse` con `imputacion` en `backend/src/schemas/pago_colegio.py`
- [x] T012 [US5] Actualizar `create_pago` y `sum_pagos_impuestos` en `backend/src/services/pago_colegio_service.py` hasta que `T007`–`T008` pasen
- [x] T013 [US5] Ejecutar `alembic upgrade head` y verificar backfill legacy

### Implementación frontend — US5

- [x] T014 [US5] Agregar selector obligatorio de imputación (3 opciones) en `frontend/src/components/escrituras/PagoColegioForm.tsx`
- [x] T015 [P] [US5] Mostrar columna/etiqueta de imputación en `frontend/src/components/escrituras/PagoColegioList.tsx`
- [x] T016 [US5] Actualizar tipos `PagoColegioInput` / `PagoColegioResponse` en `frontend/src/types/api.ts`

**Checkpoint**: Pagos nuevos requieren imputación. Suma filtrada operativa.

---

## Phase 4: User Story 1 — Plazo en listado de Escrituras (Priority: P1) 🎯 MVP

**Goal**: Columna/indicador de días restantes y color de urgencia en el listado de Escrituras.

**Independent Test**: Listado muestra `plazo_colegio` con días y color coherentes; estados Pagado / No aplica / Vencido según spec US1.

### Tests TDD — US1 (⚠️ FAIL FIRST)

- [x] T017 [US1] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_escrituras_api.py`: GET list incluye `plazo_colegio` con estados y bandas esperadas (fixtures con fechas controladas)

### Implementación backend — US1

- [x] T018 [US1] Implementar `build_plazo_colegio_fields()` en `backend/src/services/escritura_service.py`; cargar `pagos_colegio` en `_escritura_load_options()`
- [x] T019 [P] [US1] Agregar `plazo_colegio: PlazoColegioResponse` a `EscrituraListItem` y `EscrituraResponse` en `backend/src/schemas/escritura.py`
- [x] T020 [US1] Mapear `plazo_colegio` en rutas/list mappers de `backend/src/api/routes/escrituras.py` hasta que `T017` pase

### Implementación frontend — US1

- [x] T021 [P] [US1] Crear `frontend/src/components/escrituras/PlazoColegioBadge.tsx` con clases `plazo-colegio--{urgencia|pagado|vencido|na}`
- [x] T022 [US1] Agregar estilos `.plazo-colegio--*` en `frontend/src/index.css` usando tokens `--color-success`, `--color-warning`, `--color-danger`
- [x] T023 [US1] Agregar columna Plazo Colegio con `PlazoColegioBadge` en `frontend/src/components/escrituras/EscrituraList.tsx`
- [x] T024 [US1] Extender tipos definitivos `plazo_colegio` en `frontend/src/types/api.ts` (reemplazar stubs T003)

**Checkpoint**: SC-001 parcial — listado muestra plazo y color. MVP visual operativo.

---

## Phase 5: User Story 2 — Ordenar por fecha de vencimiento (Priority: P1)

**Goal**: Ordenar escrituras por `plazo_colegio.fecha_vencimiento`; Pagado/No aplica al final.

**Independent Test**: Activar sort vencimiento asc → escrituras más urgentes primero; filas sin plazo al final (`escrituraList.test.ts` + manual).

### Tests — US2

- [x] T025 [P] [US2] ⚠️ FAIL FIRST Crear/extend `frontend/src/utils/escrituraList.test.ts`: `sortByVencimiento` asc/desc, filas `pagado`/`no_aplica` al final, orden estable

### Implementación — US2

- [x] T026 [US2] Implementar `sortByVencimiento()` en `frontend/src/utils/escrituraList.ts` hasta que `T025` pase
- [x] T027 [US2] Extender `sortField: "created_at" | "vencimiento"` en `frontend/src/hooks/useEscriturasListSession.ts` (persist sessionStorage)
- [x] T028 [US2] Agregar header sortable "Vencimiento" y wiring en `frontend/src/pages/EscriturasPage.tsx`

**Checkpoint**: SC-003 — sort por vencimiento operativo.

---

## Phase 6: User Story 3 — Plazo en encabezado del detalle (Priority: P1)

**Goal**: Mismo indicador de plazo en encabezado de `EscrituraDetail` que en listado.

**Independent Test**: Abrir escritura → encabezado muestra mismos días, color y fecha vencimiento que fila del listado (SC-001).

### Tests TDD — US3

- [x] T029 [US3] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_escrituras_api.py`: GET detail `plazo_colegio` idéntico al list para misma escritura

### Implementación — US3

- [x] T030 [US3] Verificar mapper detail expone `plazo_colegio` (completar si falta tras T020) en `backend/src/api/routes/escrituras.py` hasta que `T029` pase
- [x] T031 [US3] Integrar `PlazoColegioBadge` + fecha vencimiento en encabezado de `frontend/src/pages/EscrituraDetail.tsx`

**Checkpoint**: SC-001 completo — listado y detalle coherentes.

---

## Phase 7: User Story 4 — Configurar escribanos monotributistas (Priority: P2)

**Goal**: Flag `monotributista` editable; IVA=0; recálculo inmediato de escrituras abiertas; Costanza en demo.

**Independent Test**: PATCH monotributista → IVA=0 y `total_factura=total_sin_iva` en escrituras abiertas del escribano; cerradas intactas.

### Tests TDD — US4 (⚠️ FAIL FIRST)

- [x] T032 [US4] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_calcular_totales_factura.py`: caso monotributo (iva=0, total_factura=9_674_809.01 fixture research R-007)
- [x] T033 [P] [US4] ⚠️ FAIL FIRST Crear/extender `backend/tests/integration/test_escribanos_api.py`: PATCH `monotributista`, recalc escrituras abiertas, cerradas sin cambio

### Implementación backend — US4

- [x] T034 [US4] Completar migración `011_plazo_colegio_monotributo.py` (parte 2): `escribano.monotributista`, backfill Costanza `true`
- [x] T035 [P] [US4] Agregar `monotributista` en `backend/src/models/escribano.py`
- [x] T036 [P] [US4] Agregar `EscribanoUpdateRequest` y campo `monotributista` en `backend/src/schemas/escribano.py`
- [x] T037 [US4] Extender `calcular_totales_factura(..., monotributista=)` y propagar desde `calcular_factura_completa` en `backend/src/services/calculo_factura.py` hasta que `T032` pase
- [x] T038 [US4] Implementar `update_monotributista` + `recalcular_escrituras_abiertas` en `backend/src/services/escribano_service.py`; pasar flag en `escritura_service` create/update
- [x] T039 [US4] Agregar `PATCH /configuracion/escribanos/{id}` en `backend/src/api/routes/escribanos.py`; publicar SSE `escribano.updated` hasta que `T033` pase

### Implementación frontend — US4

- [x] T040 [US4] Agregar toggle Monotributista y `useUpdateEscribano` en `frontend/src/hooks/useEscribanos.ts` + `frontend/src/components/configuracion/EscribanosConfig.tsx`
- [x] T041 [P] [US4] Suscribir invalidación a `escribano.updated` en `frontend/src/hooks/useSSE.ts`

**Checkpoint**: SC-004 y SC-005 — monotributo end-to-end.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Seed demo, validación final, documentación.

- [x] T042 [P] Bump `DEMO_SEED_VERSION=5` en `backend/scripts/seed_demo_data.py`: Costanza monotributista, `created_at` escalonados, pagos colegio con imputaciones mixtas
- [x] T043 [P] Actualizar `backend/tests/helpers/escritura_factory.py` con `imputacion` en pagos colegio de test
- [x] T044 Ejecutar checklist manual de `specs/008-factura-vencimiento-monotributo/quickstart.md`
- [x] T045 Ejecutar suite completa `pytest backend/tests/ -v` y `npm test -- --run` en frontend (si aplica)

**Checkpoint**: Demo seed v5 operativo. Suite verde.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias
- **Foundational (Phase 2)**: Depende de Setup — **bloquea US1, US2, US3**
- **US5 imputación (Phase 3)**: Depende de Phase 2 — **bloquea plazo `pagado` correcto**
- **US1 listado (Phase 4)**: Depende de Phases 2 + 3
- **US2 sort (Phase 5)**: Depende de Phase 4 (datos `plazo_colegio` en listado)
- **US3 detalle (Phase 6)**: Depende de Phase 4 (API `plazo_colegio`)
- **US4 monotributo (Phase 7)**: Depende de Setup; **paralelo a US1–US3** tras Phase 2 (backend independiente)
- **Polish (Phase 8)**: Depende de Phases 3–7

### User Story Dependencies

| Story | Depende de | Entregable independiente |
|-------|------------|--------------------------|
| US5 | Phase 2 | Pagos con imputación obligatoria |
| US1 | US5 + Phase 2 | Listado con plazo y color |
| US2 | US1 | Sort por vencimiento |
| US3 | US1 | Encabezado detalle con plazo |
| US4 | Setup (+ 007) | Monotributista + IVA condicional |

### Parallel Opportunities

```bash
# Tras Phase 2, en paralelo:
# Dev A: Phase 3 US5 (imputación)
# Dev B: Phase 7 US4 backend (monotributo) — T032–T039

# Tras Phase 4, en paralelo:
# Dev A: Phase 5 US2 (sort)
# Dev B: Phase 6 US3 (header)

# Dentro de Phase 4:
T021 PlazoColegioBadge.tsx ∥ T019 schemas/escritura.py
```

---

## Parallel Example: User Story 1

```bash
# Tests primero (secuencial):
pytest backend/tests/integration/test_escrituras_api.py -k plazo -v  # T017 FAIL FIRST

# Luego en paralelo:
# T019 schemas/escritura.py
# T021 PlazoColegioBadge.tsx
# T022 index.css

# Integración:
# T023 EscrituraList.tsx + T020 routes
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup  
2. Phase 2: Foundational (plazo puro)  
3. Phase 3: US5 backend (imputación mínima para `pagado`)  
4. Phase 4: US1 (listado con plazo)  
5. **STOP and VALIDATE**: quickstart § Listado items 1–3  
6. Phases 5–6: US2 + US3  
7. Phase 7: US4 monotributo  
8. Phase 8: Polish  

### Task Count Summary

| Phase | Story | Tasks | Parallelizable |
|-------|-------|-------|----------------|
| 1 Setup | — | 3 | 1 |
| 2 Foundational | — | 3 | 1 |
| 3 US5 | US5 | 10 | 4 |
| 4 US1 | US1 | 8 | 3 |
| 5 US2 | US2 | 4 | 1 |
| 6 US3 | US3 | 3 | 0 |
| 7 US4 | US4 | 10 | 4 |
| 8 Polish | — | 4 | 2 |
| **Total** | | **45** | **16** |

### Independent Test Criteria (per story)

| Story | Criterio |
|-------|----------|
| US1 | Listado muestra días, color y estados Pagado/Vencido/No aplica |
| US2 | Sort vencimiento asc pone urgentes primero; sin plazo al final |
| US3 | Detalle encabezado = mismo `plazo_colegio` que listado |
| US4 | Monotributista → IVA=0; toggle recalcula abiertas |
| US5 | Imputación obligatoria; solo `total_impuestos` cierra plazo |

---

## Notes

- Orden de ejecución recomendado: T001→T006 → T007→T013 → T017→T024 (MVP listado) → T025→T028 → T029→T031 → T032→T041 → T042→T045
- US4 puede desarrollarse en paralelo con US1 tras Phase 2 si hay dos desarrolladores
- Sin campo `figma:` en tareas UI — ver nota al inicio del documento
- `/spec-kitti.implement` debe honrar TDD: ningún test ⚠️ FAIL FIRST se marca completo antes de implementación
