# Tasks: Gastos Extraordinarios de la Escribanía

**Feature Branch**: `005-gastos-extraordinarios`  
**Input**: `specs/005-gastos-extraordinarios/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD — tests en estado FAILING antes de cada implementación  
**UI / Figma**: **No se usa Figma** (spec § Assumptions). Reutilizar patrones de `LiquidacionPage`, `LibroSalidaPage` y formularios de pagos. El campo `figma:` **no aplica**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario (US1–US3)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar artefactos de diseño y tipos stub en frontend.

- [ ] T001 Revisar alineación entre `specs/005-gastos-extraordinarios/contracts/openapi-delta.yaml` y `data-model.md`
- [ ] T002 [P] Actualizar `frontend/src/types/api.ts`: tipos stub `GastoExtraordinario`, `GastosExtraordinariosListResponse`, campos delta en `PagoEscribano` y `PagoSalariosResumen`

**Checkpoint**: Contrato y tipos frontend listos para implementación incremental.

---

## Phase 2: Foundational — Reparto, Persistencia (BLOCKING)

**Purpose**: Lógica pura de reparto, migración `008`, modelo ORM. Bloquea todas las user stories.

**⚠️ CRITICAL**: Ninguna fase de user story puede comenzar hasta completar esta fase.

### Tests TDD — Foundational (⚠️ FAIL FIRST)

- [x] T003 ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_gasto_extraordinario_reparto.py`: división exacta ($300.000 ÷ 3), indivisible ($100 ÷ 3, remanente al último alfabético), n=0 retorna lista vacía, suma cuotas = total siempre
- [x] T004 ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_migration_008_gastos_extraordinarios.py`: tabla `gastos_extraordinarios`, columnas, índice en `fecha`

### Implementación — Foundational

- [x] T005 Implementar `backend/src/services/gasto_extraordinario_reparto.py`: `reparto_equitativo(total, n)` hasta que `T003` pase
- [x] T006 Crear migración `backend/alembic/versions/008_gastos_extraordinarios.py`: tabla según data-model
- [x] T007 [P] Crear modelo ORM `backend/src/models/gasto_extraordinario.py`
- [x] T008 [P] Crear `backend/src/schemas/gasto_extraordinario.py`: `GastoExtraordinarioInput`, `GastoExtraordinarioUpdate`, `GastoExtraordinarioResponse`, `GastosExtraordinariosListResponse`
- [x] T009 Actualizar `backend/src/models/__init__.py`: exportar `GastoExtraordinario`
- [x] T010 Ejecutar `alembic upgrade head` y verificar que `T004` pasa

**Checkpoint**: Reparto puro verde. Migración idempotente. Modelo importable.

---

## Phase 3: User Story 1 — Registrar Gastos Extraordinarios del Mes (Priority: P1) 🎯 MVP

**Goal**: CRUD de gastos con concepto, monto y fecha; listado mensual con total; líneas en Libro de Salida.

**Independent Test**: POST gasto → aparece en listado del mes y en Libro de Salida con `origen=extraordinario` sin escritura.

### Tests TDD — US1 (⚠️ FAIL FIRST)

- [x] T011 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_gasto_extraordinario_service.py`: crear válido, rechazar monto ≤ 0, concepto vacío, listar por mes, update, delete
- [x] T012 [P] [US1] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_libros_service.py` (salida): incluir `GastoExtraordinario` del mes con `origen=extraordinario`, `escritura_id` null
- [x] T013 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_gastos_extraordinarios_api.py`: GET list, POST 201, PATCH 200, DELETE 204, 401 sin auth, 422 validación

### Implementación — US1

- [x] T014 [US1] Implementar `backend/src/services/gasto_extraordinario_service.py`: `list_by_month`, `create`, `update`, `delete`
- [x] T015 [US1] Modificar `backend/src/schemas/libros.py`: `origen` incluye `extraordinario`; `escritura_id`/`escritura_nombre` opcionales; `gasto_extraordinario_id` opcional
- [x] T016 [US1] Modificar `get_libro_salida()` en `backend/src/services/libros_service.py`: merge líneas desde `gastos_extraordinarios` por `fecha`
- [x] T017 [US1] Crear `backend/src/api/routes/gastos_extraordinarios.py`: `GET/POST /gastos-extraordinarios`, `PATCH/DELETE /gastos-extraordinarios/{id}`
- [x] T018 [US1] Registrar router en `backend/src/api/router.py`
- [x] T019 [US1] Publicar SSE `gasto_extraordinario.created|updated|deleted` + `libros_updated` en `gasto_extraordinario_service.py`
- [x] T020 [US1] Verificar que `T011`, `T012` y `T013` pasan; ajustar hasta verde

**Checkpoint**: API operativa. Libro de Salida incluye gastos extraordinarios.

---

## Phase 4: User Story 2 — Descontar Gastos del Pago de Escribanos (Priority: P1)

**Goal**: Reparto equitativo del total mensual; deducción y monto neto por escribano; advertencia sin escribanos.

**Independent Test**: $300.000 en gastos, 3 escribanos → deducción $100.000 cada uno; `monto_neto = monto_total - deduccion`.

### Tests TDD — US2 (⚠️ FAIL FIRST)

- [x] T021 [P] [US2] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_salario.py`: deducción por escribano, monto_neto, total_gastos_extraordinarios en resumen, advertencia si 0 escribanos
- [x] T022 [P] [US2] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_gastos_extraordinarios_api.py`: tras POST gasto, GET `/salarios` refleja deducción

### Implementación — US2

- [x] T023 [US2] Modificar `backend/src/schemas/salarios.py`: `deduccion_gastos_extraordinarios`, `monto_neto` en `PagoEscribano`; `total_gastos_extraordinarios`, `advertencia_reparto` en `PagoSalariosResumen`
- [x] T024 [US2] Modificar `get_pagos_mensuales()` en `backend/src/services/salario_service.py`: calcular reparto con `reparto_equitativo`, asignar por nombre alfabético
- [x] T025 [US2] Verificar que `T021` y `T022` pasan; ajustar hasta verde

**Checkpoint**: Pago de Salarios muestra deducción y neto correctos.

---

## Phase 5: User Story 3 — Consultar y Filtrar por Período (Priority: P2)

**Goal**: Selector mes/año en UI; listado filtrado; total coincide con libro.

**Independent Test**: Cambiar mes en UI → solo gastos de ese mes; total = suma líneas extraordinarias del libro.

### Implementación — US3 (Frontend + validación)

- [x] T026 [US3] Crear `frontend/src/api/gastosExtraordinarios.ts`: CRUD según openapi-delta
- [x] T027 [US3] Crear `frontend/src/hooks/useGastosExtraordinarios.ts`: queries y mutations con invalidación de `libros` y `salarios`
- [x] T028 [US3] Crear `frontend/src/components/gastos-extraordinarios/GastoExtraordinarioForm.tsx`: alta/edición concepto, monto, fecha
- [x] T029 [US3] Crear `frontend/src/components/gastos-extraordinarios/GastoExtraordinarioList.tsx`: tabla con acciones editar/eliminar
- [x] T030 [US3] Crear `frontend/src/pages/GastosExtraordinariosPage.tsx`: selector mes/año, total del mes, form + list
- [x] T031 [US3] Modificar `frontend/src/components/layout/Navbar.tsx`: link "Gastos Extraordinarios" en **2.ª posición** (después de Escrituras)
- [x] T032 [US3] Modificar `frontend/src/App.tsx`: ruta `/gastos-extraordinarios`
- [x] T033 [P] [US3] Modificar `frontend/src/components/libros/LibroLineaRow.tsx`: badge Extraordinario; sin link si no hay escritura
- [x] T034 [P] [US3] Modificar `frontend/src/components/salarios/PagoEscribanoCard.tsx`: filas deducción y monto neto
- [x] T035 [US3] Modificar `frontend/src/pages/SalariosPage.tsx`: mostrar `advertencia_reparto` y `total_gastos_extraordinarios` si aplica
- [x] T036 [US3] Modificar `frontend/src/hooks/useSSE.ts`: eventos `gasto_extraordinario.*` → invalidar `gastos-extraordinarios`, `libros`, `salarios`
- [x] T037 [US3] Actualizar `frontend/src/types/api.ts`: tipos finales alineados con backend

**Checkpoint**: Flujo end-to-end US1–US3 operativo en UI.

---

## Phase 6: Polish & Validación

**Purpose**: Suite completa, quickstart, documentación.

- [x] T038 [P] Extender `backend/tests/integration/test_sse_events.py`: eventos `gasto_extraordinario.*`
- [x] T039 [P] Agregar datos demo opcionales en `backend/scripts/seed_demo_data.py` (gastos julio 2026)
- [x] T040 Ejecutar suite backend: `cd backend && .venv/bin/pytest tests/ -v` — todos verdes
- [x] T041 [P] Ejecutar suite frontend: `cd frontend && npm test && npm run build`
- [x] T042 Validación manual según `specs/005-gastos-extraordinarios/quickstart.md`
- [x] T043 Actualizar `specs/005-gastos-extraordinarios/spec.md`: Status → Implemented (tras merge)

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depende de |
|-------|------------|
| 1 Setup | — |
| 2 Foundational | Phase 1 |
| 3 US1 | Phase 2 |
| 4 US2 | Phase 3 (libros + CRUD) |
| 5 US3 | Phase 3–4 (API + salarios backend) |
| 6 Polish | Phase 5 |

### User Story Dependencies

- **US1 (P1)**: MVP — CRUD + libro salida
- **US2 (P1)**: Requiere US1 (total mensual de gastos)
- **US3 (P2)**: UI; puede desarrollarse en paralelo con US2 una vez API lista

### Parallel Opportunities

```text
T003 + T004 (tests) en paralelo
T007 + T008 (model + schema) en paralelo
T011 + T012 + T013 (tests US1) en paralelo
T033 + T034 (libros + salarios UI) en paralelo
```

---

## Implementation Strategy

### MVP (US1 only)

1. Phase 1 + 2 + 3
2. Validar: gasto en listado + libro salida
3. Demo parcial sin deducción en salarios

### Entrega completa

1. MVP + Phase 4 (salarios)
2. Phase 5 (UI completa)
3. Phase 6 (polish)

---

## Task Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| 1 Setup | T001–T002 | — |
| 2 Foundational | T003–T010 | — |
| 3 US1 | T011–T020 | US1 |
| 4 US2 | T021–T025 | US2 |
| 5 US3 | T026–T037 | US3 |
| 6 Polish | T038–T043 | — |

**Total**: 43 tasks
