# Tasks: Impuestos por Escritura

**Feature Branch**: `006-impuestos-escrituras`  
**Input**: `specs/006-impuestos-escrituras/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD completo — tests escritos en estado FAILING antes de cada implementación (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature (spec § Assumptions). El frontend reutiliza patrones de `EscrituraDetail` y componentes de pagos de feature 003/004. El campo `figma:` **no aplica** a ninguna tarea UI — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario correspondiente (US1–US8)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar artefactos de diseño y preparar errores de dominio y tipos stub.

- [ ] T001 Revisar alineación entre `specs/006-impuestos-escrituras/contracts/openapi-delta.yaml` y `specs/006-impuestos-escrituras/data-model.md`
- [x] T002 Agregar `EscrituraImpuestosBalanceError` y `EscrituraImpuestosPagosPendientesError` en `backend/src/services/escritura_errors.py`
- [x] T003 [P] Actualizar `frontend/src/types/api.ts`: agregar tipos stub `TipoImpuesto`, `ImpuestoEscritura`, `PagoImpuestoCliente`, `PagoImpuestoEscribania`, `BalanceImpuestos`

**Checkpoint**: Errores de dominio listos. Tipos frontend preparados para implementación incremental.

---

## Phase 2: Foundational — Prorrateo, Balance y Persistencia (BLOCKING)

**Purpose**: Lógica pura de prorrateo/balance, migración `007`, modelos ORM. Bloquea todas las historias de usuario.

**⚠️ CRITICAL**: Ninguna fase de user story puede comenzar hasta completar esta fase.

### Tests TDD — Foundational (⚠️ FAIL FIRST)

- [x] T004 ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_impuesto_prorrateo.py`: casos 46/61 y 15/61 (spec ejemplo $10.000, 01/05–30/06, corte 15/06), tramos sin solapamiento, corte fuera de período rechazado, corte en primer/último día del período, redondeo determinístico a 2 decimales
- [x] T005 ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_impuesto_balance.py`: `calc_balance`, `can_close_impuestos`, `impuestos_pendientes` (balance = 0, balance ≠ 0, impuesto sin ambos pagos, escritura sin impuestos)
- [x] T006 ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_migration_007_impuestos.py`: enums `tipo_impuesto`/`direccion_prorrateo`, tablas creadas, UNIQUE `impuesto_id` en pagos, índices en `escritura_id` y `fecha`

### Implementación — Foundational

- [x] T007 Implementar `backend/src/services/impuesto_prorrateo.py`: `calc_dias_tramo`, `calc_monto_sugerido`, validación fecha corte dentro del período hasta que `T004` pase
- [x] T008 Implementar `backend/src/services/impuesto_balance.py`: balance acumulado y elegibilidad de cierre hasta que `T005` pase
- [x] T009 Crear migración Alembic `backend/alembic/versions/007_impuestos_escritura.py`: enums, tablas `impuestos_escritura`, `pagos_impuesto_cliente`, `pagos_impuesto_escribania` con constraints del data-model
- [x] T010 [P] Crear modelo ORM `backend/src/models/impuesto_escritura.py`
- [x] T011 [P] Crear modelo ORM `backend/src/models/pago_impuesto_cliente.py` (UNIQUE `impuesto_id`)
- [x] T012 [P] Crear modelo ORM `backend/src/models/pago_impuesto_escribania.py` (UNIQUE `impuesto_id`)
- [x] T013 Modificar `backend/src/models/escritura.py`: relaciones `impuestos`, `pagos_impuesto_cliente`, `pagos_impuesto_escribania`
- [x] T014 Actualizar `backend/src/models/__init__.py`: exportar nuevos modelos
- [x] T015 [P] Crear `backend/src/schemas/impuesto.py`: `ImpuestoInput`, `ImpuestoUpdate`, `ImpuestoResponse`, `PagoImpuestoInput`, `BalanceImpuestosResponse`
- [x] T016 Ejecutar `alembic upgrade head` y verificar que `T006` pasa

**Checkpoint**: Prorrateo y balance puros verdes. Migración idempotente. Modelos importables.

---

## Phase 3: User Story 1 + 2 — Alta de Impuestos y Prorrateo (Priority: P1) 🎯 MVP

**Goal**: CRUD de impuestos en escritura abierta con cálculo de monto prorrateado sugerido y validaciones de período/tipo.

**Independent Test**: `POST /escrituras/{id}/impuestos` crea impuesto con `monto_prorrateado_sugerido` correcto (46/61 o 15/61). GET lista impuestos con `estado_pagos`. Escritura cerrada → 409.

### Tests TDD — US1 + US2 (⚠️ FAIL FIRST)

- [x] T017 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_impuesto_service.py`: crear impuesto válido, rechazar período inválido, monto ≤ 0, corte fuera de período, tipos enum, escritura cerrada, calcular `monto_prorrateado_sugerido` en response
- [x] T018 [P] [US2] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_impuesto_prorrateo.py`: recálculo al cambiar dirección; complementariedad atrás+adelante = 100% del período
- [x] T019 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_impuestos_api.py` (CRUD impuesto): POST 201, GET list con balance, PATCH 200, DELETE 204 sin pagos, 409 escritura cerrada, 401 sin auth

### Implementación — US1 + US2

- [x] T020 [US1] Implementar `backend/src/services/impuesto_service.py`: `create_impuesto`, `list_impuestos`, `update_impuesto`, `delete_impuesto` (solo sin pagos), guards escritura abierta
- [ ] T021 [US1] Modificar `backend/src/schemas/escritura.py`: campos `impuestos[]`, `total_pagado_impuestos_cliente`, `total_pagado_impuestos_escribania`, `balance_impuestos`, `puede_cerrar_impuestos`
- [x] T022 [US1] Crear `backend/src/api/routes/impuestos.py`: `GET/POST /escrituras/{id}/impuestos`, `PATCH/DELETE /escrituras/{id}/impuestos/{impuesto_id}`
- [x] T023 [US1] Registrar router en `backend/src/api/router.py`
- [x] T024 [US1] Verificar que `T017`, `T018` y `T019` pasan; ajustar hasta verde

**Checkpoint**: API de impuestos operativa con prorrateo en responses.

---

## Phase 4: User Story 3 — Pago del Cliente y Libro de Entrada (Priority: P1)

**Goal**: Registrar/editar/eliminar pago cliente por impuesto; línea en Libro de Entrada por fecha de pago.

**Independent Test**: `POST .../pago-cliente` con monto sugerido precargado crea línea en Libro de Entrada del mes de `fecha`. Editar pago actualiza línea sin duplicar.

### Tests TDD — US3 (⚠️ FAIL FIRST)

- [x] T025 [P] [US3] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_pago_impuesto_cliente_service.py`: crear con prefill sugerido, monto ≤ 0 rechazado, escritura cerrada rechazada, update mismo registro (no segundo pago), delete quita pago, no modifica `saldo_pendiente` honorarios
- [x] T026 [P] [US3] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_libros_service.py` (entrada): incluir `PagoImpuestoCliente` del mes con `origen=impuesto` y `tipo_impuesto`; excluir otros meses
- [x] T027 [P] [US3] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_impuestos_api.py` (pago-cliente): POST 201, PATCH 200, DELETE 204, 409 cerrada

### Implementación — US3

- [x] T028 [US3] Implementar `backend/src/services/pago_impuesto_cliente_service.py`: `upsert_pago`, `update_pago`, `delete_pago` (1:1 por impuesto)
- [x] T029 [US3] Modificar `backend/src/schemas/libros.py`: `origen` (`honorario`|`impuesto`), `tipo_impuesto` en `LibroLineaResponse`
- [x] T030 [US3] Modificar `get_libro_entrada()` en `backend/src/services/libros_service.py`: agregar líneas desde `pagos_impuesto_cliente` filtradas por `fecha`
- [x] T031 [US3] Agregar rutas en `backend/src/api/routes/impuestos.py`: `POST/PATCH/DELETE .../pago-cliente`
- [x] T032 [US3] Publicar SSE `impuesto.pago_cliente.changed` + `libros_updated` + `liquidacion.updated` en `pago_impuesto_cliente_service.py`
- [x] T033 [US3] Verificar que `T025`, `T026` y `T027` pasan; ajustar hasta verde

**Checkpoint**: Pago cliente por impuesto operativo. Libro de Entrada incluye impuestos.

---

## Phase 5: User Story 4 — Pago de la Escribanía y Libro de Salida (Priority: P1)

**Goal**: Registrar/editar/eliminar pago escribanía por impuesto; línea en Libro de Salida por fecha de pago.

**Independent Test**: `POST .../pago-escribania` crea línea en Libro de Salida del mes. Orden de registro cliente/escribanía independiente.

### Tests TDD — US4 (⚠️ FAIL FIRST)

- [x] T034 [P] [US4] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_pago_impuesto_escribania_service.py`: crear, update, delete, escritura cerrada rechazada, monto ≤ 0 rechazado
- [x] T035 [P] [US4] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_libros_service.py` (salida): incluir `PagoImpuestoEscribania` del mes con `origen=impuesto`
- [x] T036 [P] [US4] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_impuestos_api.py` (pago-escribania): POST 201, PATCH 200, DELETE 204

### Implementación — US4

- [x] T037 [US4] Implementar `backend/src/services/pago_impuesto_escribania_service.py`: `upsert_pago`, `update_pago`, `delete_pago`
- [x] T038 [US4] Modificar `get_libro_salida()` en `backend/src/services/libros_service.py`: agregar líneas desde `pagos_impuesto_escribania` filtradas por `fecha`
- [x] T039 [US4] Agregar rutas en `backend/src/api/routes/impuestos.py`: `POST/PATCH/DELETE .../pago-escribania`
- [x] T040 [US4] Publicar SSE `impuesto.pago_escribania.changed` + `libros_updated` + `liquidacion.updated` en `pago_impuesto_escribania_service.py`
- [x] T041 [US4] Verificar que `T034`, `T035` y `T036` pasan; ajustar hasta verde

**Checkpoint**: Pago escribanía operativo. Libro de Salida incluye impuestos.

---

## Phase 6: User Story 5 — Cierre de Escritura con Balance Impuestos = 0 (Priority: P1)

**Goal**: Bloquear cierre si balance impuestos ≠ 0 o impuestos sin ambos pagos; exponer balance en API.

**Independent Test**: `POST /escrituras/{id}/close` con balance ≠ 0 → 409 `impuestos_balance_pendiente`. Con impuesto sin pago → 409 con lista pendientes. Balance = 0 y pagos completos → 200 (si honorarios = 0).

### Tests TDD — US5 (⚠️ FAIL FIRST)

- [x] T042 [P] [US5] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_impuesto_balance.py`: casos balance positivo/negativo, impuestos pendientes con detalle por tipo
- [x] T043 [P] [US5] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_escrituras_api.py` (o `test_impuestos_api.py`): close con balance ≠ 0 → 409; impuesto sin ambos pagos → 409; close OK con balance 0 + honorarios 0

### Implementación — US5

- [x] T044 [US5] Modificar `close_escritura()` en `backend/src/services/escritura_service.py`: validar `can_close_impuestos` y `impuestos_pendientes` antes de cerrar
- [x] T045 [US5] Modificar `backend/src/api/routes/escrituras.py`: mapear nuevos errores → HTTP 409 con schemas `EscrituraImpuestosBalanceError` / pagos pendientes
- [x] T046 [US5] Modificar `backend/src/services/impuesto_service.py` y GET escritura: incluir `BalanceImpuestosResponse` en list/detail
- [x] T047 [US5] Verificar que `T042` y `T043` pasan; ajustar hasta verde

**Checkpoint**: Cierre bloqueado correctamente por reglas de impuestos. Balance visible en API.

---

## Phase 7: User Story 6 — Impacto en Liquidación y Pago de Salarios (Priority: P1)

**Goal**: Incorporar `neto_impuestos` mensual por escritura/escribano; cierre mensual NO bloqueado por balance impuestos.

**Independent Test**: Pago cliente impuesto en julio sin egreso → Liquidación julio `neto_impuestos` +$50.000. Cierre mes permitido. Pago de Salarios incorpora neto.

### Tests TDD — US6 (⚠️ FAIL FIRST)

- [x] T048 [P] [US6] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_liquidacion.py`: `neto_impuestos` cobro sin egreso (+), egreso sin cobro (−), compensados (=0), dos movimientos mismo mes sumados
- [x] T049 [P] [US6] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_salario.py`: total escribano incluye `monto_cobrado` + `neto_impuestos`
- [x] T050 [P] [US6] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_liquidacion_api.py`: response con `neto_impuestos`; cierre mensual con escritura balance ≠ 0 → 200

### Implementación — US6

- [x] T051 [US6] Modificar `backend/src/schemas/liquidacion.py`: agregar `neto_impuestos` a `LiquidacionEscrituraItem`
- [x] T052 [US6] Modificar `get_liquidacion_mensual()` en `backend/src/services/liquidacion_service.py`: calcular `neto_impuestos` por escritura desde pagos impuesto del mes (fecha de pago)
- [x] T053 [US6] Modificar `backend/src/services/salario_service.py`: total escribano = Σ(`monto_cobrado` + `neto_impuestos`)
- [x] T054 [US6] Verificar que `T048`, `T049` y `T050` pasan; ajustar hasta verde

**Checkpoint**: Liquidación y Salarios reflejan neto mensual de impuestos. Backend completo.

---

## Phase 8: User Story 7 — Editar y Eliminar Impuestos y Pagos (Priority: P2)

**Goal**: Edición/eliminación completa mientras escritura abierta; libros y balance actualizados sin duplicar líneas.

**Independent Test**: Editar monto/fecha de pago actualiza libro existente. Eliminar pago bloquea cierre. Eliminar impuesto sin pagos OK. Escritura cerrada → 409 en todo.

### Tests TDD — US7 (⚠️ FAIL FIRST)

- [x] T055 [P] [US7] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_impuesto_service.py`: editar tipo/período/corte/dirección recalcula sugerido; delete con pagos → 409
- [x] T056 [P] [US7] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_pago_impuesto_cliente_service.py` y `test_pago_impuesto_escribania_service.py`: editar fecha mueve línea de mes en libros; delete recalcula balance y bloquea cierre
- [x] T057 [P] [US7] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_impuestos_api.py`: PATCH impuesto con pagos OK; DELETE impuesto con pagos → 409; DELETE pago → balance y `puede_cerrar` actualizados

### Implementación — US7

- [x] T058 [US7] Completar guards en `impuesto_service.py` y payment services: escritura cerrada en todas las mutaciones; delete impuesto solo sin pagos (FR-028)
- [x] T059 [US7] Asegurar idempotencia de libros al editar pagos: una línea por pago, actualización in-place en `libros_service.py`
- [x] T060 [US7] Publicar SSE `impuesto.updated` / `impuesto.deleted` en mutaciones de impuesto
- [x] T061 [US7] Verificar que `T055`, `T056` y `T057` pasan; ajustar hasta verde

**Checkpoint**: Edición/eliminación completa sin duplicar líneas contables.

---

## Phase 9: User Story 1 + 2 — Frontend Alta de Impuestos y Prorrateo (Priority: P1)

**Goal**: Sección Impuestos en detalle de escritura con formulario de alta, listado y monto sugerido visible.

**Independent Test**: Crear impuesto API con período y prorrateo; ver monto sugerido en listado. Cambiar dirección recalcula al instante.

### Implementación — US1 + US2

- [x] T062 [P] [US1] Crear `frontend/src/api/impuestos.ts`: `listImpuestos`, `createImpuesto`, `updateImpuesto`, `deleteImpuesto`
- [x] T063 [P] [US1] Crear `frontend/src/hooks/useImpuestos.ts`: queries/mutations + invalidación escritura/libros/liquidación
- [x] T064 [P] [US1] Crear `frontend/src/components/escrituras/ImpuestoForm.tsx`: selector de 6 tipos, período, corte, dirección, validación cliente
- [x] T065 [P] [US1] Crear `frontend/src/components/escrituras/ImpuestoList.tsx`: tipo, período, corte, dirección, monto sugerido, `estado_pagos`
- [x] T066 [US1] Modificar `frontend/src/pages/EscrituraDetail.tsx`: sección "Impuestos" debajo de Pagos del cliente y Pagos de la escribanía (columna derecha)
- [x] T067 [US2] Modificar `frontend/src/components/escrituras/ImpuestoForm.tsx`: recálculo en vivo de monto sugerido al cambiar período/corte/dirección (optimistic o refetch)

**Checkpoint**: Alta y listado de impuestos operativos en UI con prorrateo visible.

---

## Phase 10: User Story 3 + 4 — Frontend Pagos Cliente y Escribanía (Priority: P1)

**Goal**: Formularios de pago con prefill del monto sugerido (cliente) y registro de egreso escribanía.

**Independent Test**: "Pago cliente" precarga monto sugerido editable. "Pago escribanía" registra egreso. Ambos visibles en listado del impuesto.

### Implementación — US3 + US4

- [x] T068 [P] [US3] Crear `frontend/src/components/escrituras/ImpuestoPagoClienteForm.tsx`: prefill `monto_prorrateado_sugerido`, fecha de pago, edición inline
- [x] T069 [P] [US4] Crear `frontend/src/components/escrituras/ImpuestoPagoEscribaniaForm.tsx`: monto y fecha de pago, edición inline
- [x] T070 [US3] Extender `frontend/src/api/impuestos.ts`: `upsertPagoCliente`, `updatePagoCliente`, `deletePagoCliente`
- [x] T071 [US4] Extender `frontend/src/api/impuestos.ts`: `upsertPagoEscribania`, `updatePagoEscribania`, `deletePagoEscribania`
- [x] T072 [US3] Modificar `frontend/src/components/escrituras/ImpuestoList.tsx`: botones "Pago cliente" y "Pago escribanía" con estado de pagos
- [x] T073 [US3] Modificar `frontend/src/hooks/useSSE.ts`: escuchar `impuesto.pago_cliente.changed`, `impuesto.pago_escribania.changed`

**Checkpoint**: Pagos cliente y escribanía registrables desde UI.

---

## Phase 11: User Story 5 — Frontend Balance y Cierre (Priority: P1)

**Goal**: Banner de balance impuestos visible; botón cerrar deshabilitado o 409 con mensaje claro.

**Independent Test**: Balance muestra totales y diferencia. Cerrar con balance ≠ 0 muestra error con monto. Cerrar OK solo con balance 0 y pagos completos.

### Implementación — US5

- [x] T074 [US5] Modificar `frontend/src/pages/EscrituraDetail.tsx`: banner `balance_impuestos` (total cliente, total escribanía, diferencia)
- [x] T075 [US5] Modificar `frontend/src/pages/EscrituraDetail.tsx`: deshabilitar cerrar si `!puede_cerrar_impuestos`; tooltip con impuestos pendientes
- [x] T076 [US5] Modificar `frontend/src/utils/errors.ts`: mensajes 409 `impuestos_balance_pendiente` y pagos pendientes
- [x] T077 [US5] Actualizar `frontend/src/types/api.ts` y `frontend/src/api/escrituras.ts` con campos de balance impuestos

**Checkpoint**: Balance visible y cierre condicionado por impuestos en UI.

---

## Phase 12: User Story 6 — Frontend Liquidación y Salarios (Priority: P1)

**Goal**: Mostrar `neto_impuestos` por escritura en Liquidación y Pago de Salarios.

**Independent Test**: Liquidación julio muestra neto positivo con solo cobro cliente. Salarios incorpora neto en total escribano.

### Implementación — US6

- [x] T078 [US6] Actualizar tipos en `frontend/src/types/api.ts`: `neto_impuestos` en `LiquidacionEscrituraItem`
- [x] T079 [US6] Modificar `frontend/src/components/liquidacion/EscribanoCard.tsx`: columna o fila `neto_impuestos` por escritura
- [x] T080 [US6] Modificar `frontend/src/pages/LiquidacionPage.tsx`: totales incluyen neto impuestos
- [x] T081 [US6] Modificar `frontend/src/components/salarios/PagoEscribanoCard.tsx`: mostrar neto impuestos en desglose mensual
- [x] T082 [US6] Modificar `frontend/src/hooks/useSSE.ts`: invalidar liquidación/salarios en eventos `impuesto.*`

**Checkpoint**: Liquidación y Salarios muestran impacto mensual de impuestos.

---

## Phase 13: User Story 7 — Frontend Edición y Eliminación (Priority: P2)

**Goal**: Editar impuestos sin pagos; editar/eliminar pagos desde UI; reflejo inmediato en balance y libros.

**Independent Test**: Editar monto de pago actualiza balance sin duplicar. Eliminar impuesto sin pagos desaparece del listado.

### Implementación — US7

- [x] T083 [US7] Modificar `frontend/src/components/escrituras/ImpuestoList.tsx`: acciones editar/eliminar impuesto (sin pagos) y editar/eliminar pagos
- [x] T084 [US7] Modificar `frontend/src/components/escrituras/ImpuestoForm.tsx`: modo edición para impuesto existente
- [x] T085 [US7] Modificar `frontend/src/hooks/useImpuestos.ts`: mutations delete/update con invalidación completa de caches
- [x] T086 [US7] Modificar `frontend/src/pages/EscrituraDetail.tsx`: bloquear acciones de edición si escritura cerrada (solo lectura)

**Checkpoint**: Correcciones operativas sin flujos de anulación separados.

---

## Phase 14: User Story 8 — Layout Responsive (Priority: P2)

**Goal**: Sección Impuestos apilada correctamente en viewports estrechos; formularios usables.

**Independent Test**: Viewport < 768px muestra orden: saldo/datos, factura, pagos cliente, pagos escribanía, impuestos. Botones de pago accesibles.

### Implementación — US8

- [x] T087 [US8] Modificar `frontend/src/pages/EscrituraDetail.tsx`: orden de apilamiento responsive según spec (US8 escenarios 1–2)
- [x] T088 [US8] Modificar `frontend/src/components/escrituras/ImpuestoList.tsx` y formularios: layout mobile sin solapamiento de botones
- [x] T089 [US8] Verificar en `frontend/src/index.css` o clases existentes de feature 004 que breakpoints de columna derecha se mantienen

**Checkpoint**: Impuestos usable en móvil y escritorio (SC-007).

---

## Phase 15: Frontend Libros — Líneas de Impuesto (Cross-cutting)

**Purpose**: Libros de Entrada/Salida muestran líneas de impuesto con trazabilidad.

- [x] T090 [P] [US3] Modificar `frontend/src/components/libros/LibroEntradaTable.tsx`: columna `tipo_impuesto` y badge `origen=impuesto`
- [x] T091 [P] [US4] Modificar `frontend/src/components/libros/LibroSalidaTable.tsx`: columna `tipo_impuesto` y badge `origen=impuesto`
- [x] T092 [P] [US3] Actualizar tipos en `frontend/src/api/libros.ts` con campos extendidos del openapi-delta

**Checkpoint**: Libros UI reflejan movimientos de impuestos.

---

## Phase 16: Polish & Cross-Cutting Concerns

**Purpose**: SSE completo, tests de integración tiempo real, validación end-to-end.

- [ ] T093 [P] Actualizar `backend/tests/integration/test_sse_events.py`: eventos `impuesto.*` y propagación a clientes
- [ ] T094 [P] Actualizar `backend/tests/conftest.py` y factories con fixtures de impuestos/pagos
- [ ] T095 [P] Agregar tests Vitest en `frontend/src/hooks/useImpuestos.test.ts` (opcional: prorrateo display helpers si se extraen)
- [x] T096 Ejecutar suite backend: `cd backend && pytest tests/ -v` — todos verdes
- [x] T097 [P] Ejecutar suite frontend: `cd frontend && npm test` — todos verdes
- [ ] T098 Ejecutar validación manual según `specs/006-impuestos-escrituras/quickstart.md`
- [ ] T099 Actualizar `specs/006-impuestos-escrituras/quickstart.md` si algún comando cambió durante implementación

**Checkpoint**: Feature completa, tests verdes, quickstart validado.

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Delivers |
|---|---|---|
| 1 Setup | — | Errores + tipos stub |
| 2 Foundational | Phase 1 | Prorrateo, balance, DB, modelos |
| 3 US1+US2 backend | Phase 2 | CRUD impuestos + prorrateo API |
| 4 US3 backend | Phase 3 | Pago cliente + libro entrada |
| 5 US4 backend | Phase 3 | Pago escribanía + libro salida |
| 6 US5 backend | Phase 4, 5 | Cierre + balance guards |
| 7 US6 backend | Phase 4, 5 | Liquidación neto_impuestos |
| 8 US7 backend | Phase 4, 5 | Edición/eliminación hardened |
| 9 US1+US2 frontend | Phase 3 | Sección Impuestos + formulario |
| 10 US3+US4 frontend | Phase 4, 5, 9 | Pagos UI |
| 11 US5 frontend | Phase 6, 9 | Balance + cierre UI |
| 12 US6 frontend | Phase 7 | Liquidación/Salarios UI |
| 13 US7 frontend | Phase 8, 10 | Edición UI |
| 14 US8 frontend | Phase 9–10 | Responsive |
| 15 Libros frontend | Phase 4, 5 | Libros con impuestos |
| 16 Polish | All | E2E + SSE |

### User Story Dependencies

- **US1 (P1)**: Foundational → MVP impuestos
- **US2 (P1)**: Foundational (prorrateo puro) → integrado en US1 API/UI
- **US3 (P1)**: US1 (impuesto debe existir)
- **US4 (P1)**: US1 — **parallelizable con US3** tras Phase 3
- **US5 (P1)**: US3 + US4 (pagos para calcular balance)
- **US6 (P1)**: US3 + US4 (movimientos en libros/liquidación)
- **US7 (P2)**: US3 + US4 (pagos editables)
- **US8 (P2)**: US1 frontend (sección debe existir)

### Parallel Opportunities

```bash
# Tras Phase 2 — lógica pura ya verde:
Developer A: Phase 3 (US1+US2 impuestos API)
# En espera: frontend puede mockear contratos tras T022

# Tras Phase 3 — pagos en paralelo:
Developer A: Phase 4 (US3 pago cliente + libro entrada)
Developer B: Phase 5 (US4 pago escribanía + libro salida)

# Tras Phase 5:
Developer A: Phase 6 (US5 cierre)
Developer B: Phase 7 (US6 liquidación)

# Frontend — tras API estable:
Developer A: Phase 9+11 (impuestos + balance/cierre)
Developer B: Phase 10+12 (pagos + liquidación UI)
```

---

## Parallel Example: User Story 3

```bash
# Tests US3 en paralelo (FAIL FIRST):
T025: backend/tests/unit/test_pago_impuesto_cliente_service.py
T026: backend/tests/unit/test_libros_service.py (entrada impuestos)
T027: backend/tests/integration/test_impuestos_api.py (pago-cliente)

# Implementación US3 en paralelo (tras T028 service):
T029: backend/src/schemas/libros.py
T031: backend/src/api/routes/impuestos.py (rutas pago-cliente)
```

---

## Implementation Strategy

### MVP First (User Stories 1–5 backend + UI básica)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL**)
3. Complete Phases 3–6: US1–US5 backend
4. Complete Phases 9–11: UI impuestos, pagos y cierre
5. **STOP and VALIDATE**: Crear impuesto, prorrateo, ambos pagos, cerrar escritura

### Incremental Delivery

| Increment | Phases | Value delivered |
|---|---|---|
| MVP | 1–6, 9–11 | Impuestos, pagos, balance, cierre |
| +Liquidación | 7, 12 | Neto mensual escribano |
| +Edición | 8, 13 | Correcciones operativas |
| +Responsive + Libros | 14–15 | SC-007, trazabilidad en libros |
| Polish | 16 | Production-ready |

---

## Notes

- Total tasks: **99**
- TDD obligatorio: **22** tests ⚠️ FAIL FIRST
- UI tasks: **28** (sin Figma — decisión explícita en spec § Assumptions)
- Migration **007** (006 ya usado por `pagos_cliente`)
- Honorarios `saldo_pendiente` sin cambios (FR-020)
- Cierre mensual liquidación NO valida balance impuestos (FR-020c)
