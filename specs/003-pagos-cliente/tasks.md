# Tasks: Pagos del Cliente y Libros Contables Basados en Caja Real

**Feature Branch**: `003-pagos-cliente`  
**Input**: `specs/003-pagos-cliente/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD completo — tests escritos en estado FAILING antes de cada implementación (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature. El frontend se implementa según la spec, el design system existente del proyecto (feature 001/002) y patrones de componentes ya en el repo. El campo `figma:` **no aplica** a ninguna tarea UI — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario correspondiente (US1–US7)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar contexto y preparar errores de dominio antes de la migración.

- [ ] T001 Revisar alineación entre `specs/003-pagos-cliente/contracts/openapi-patch.yaml` y `specs/003-pagos-cliente/data-model.md`
- [ ] T002 Agregar `EscrituraSaldoPendienteError` (con atributo `saldo_pendiente`) en `backend/src/services/escritura_errors.py`
- [ ] T003 [P] Actualizar `frontend/src/types/api.ts`: agregar tipos stub `PagoCliente`, `PagoColegio`, `EscrituraSaldo`; marcar `GastoAdicional` como deprecated

**Checkpoint**: Errores de dominio listos. Tipos frontend preparados para implementación incremental.

---

## Phase 2: Foundational — Migración DB y Modelos (BLOCKING)

**Purpose**: Tablas `pagos_cliente` y `pagos_colegio`, migración de datos, eliminación de `gastos_adicionales`. Bloquea todas las historias de usuario.

**⚠️ CRITICAL**: Ninguna fase de user story puede comenzar hasta completar esta fase.

- [x] T004 ⚠️ FAIL FIRST Escribir test de migración/smoke en `backend/tests/integration/test_migration_006_pagos_cliente.py`: verificar tablas creadas, datos migrados, `gastos_adicionales` ausente, escrituras cerradas con pago implícito
- [x] T005 Crear migración Alembic `backend/alembic/versions/006_pagos_cliente.py`: tablas `pagos_cliente` y `pagos_colegio` con índices en `escritura_id` y `fecha`
- [x] T006 Implementar en migración `006_pagos_cliente.py`: `INSERT` desde `gastos_adicionales` dirección `entrada` → `pagos_cliente` y `salida` → `pagos_colegio`
- [x] T007 Implementar en migración `006_pagos_cliente.py`: pagos implícitos al 100% para escrituras `cerrada` sin `pagos_cliente` (FR-035)
- [x] T008 Implementar en migración `006_pagos_cliente.py`: drop tabla `gastos_adicionales` y enum `direccion_gasto`
- [x] T009 [P] Crear modelo ORM `backend/src/models/pago_cliente.py` (`id`, `escritura_id`, `monto`, `fecha`, `concepto`, `created_at`)
- [x] T010 [P] Crear modelo ORM `backend/src/models/pago_colegio.py` (misma estructura que `PagoCliente`)
- [x] T011 Modificar `backend/src/models/escritura.py`: reemplazar relación `gastos` por `pagos_cliente` y `pagos_colegio`
- [x] T012 Actualizar `backend/src/models/__init__.py`: exportar `PagoCliente`, `PagoColegio`; eliminar `GastoAdicional`, `DireccionGasto`
- [x] T013 ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_pago_saldo.py`: `calc_saldo`, `can_close`, flag `sobrepago` (casos normales, saldo=0, sobrepago tras recálculo)
- [x] T014 Implementar funciones puras en `backend/src/services/pago_saldo.py` hasta que `T013` pase
- [ ] T015 Ejecutar `alembic upgrade head` y verificar que `T004` pasa

**Checkpoint**: Migración idempotente. Modelos importables. `test_pago_saldo.py` verde.

---

## Phase 3: User Story 1 — Pagos del Cliente y Saldo Pendiente (Priority: P1) 🎯 MVP

**Goal**: Registrar pagos reales del cliente, calcular y exponer saldo pendiente en API.

**Independent Test**: `POST /escrituras/{id}/pagos-cliente` con monto válido actualiza `total_pagado` y `saldo_pendiente`. Monto > saldo → 400. Escritura cerrada → 409.

### Tests TDD — US1 (⚠️ FAIL FIRST)

- [x] T016 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_pago_cliente_service.py`: registrar pago válido, rechazar monto ≤ 0, rechazar monto > saldo, rechazar en escritura cerrada, inmutabilidad (sin update/delete)
- [x] T017 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_pagos_cliente_api.py`: POST 201, GET escritura con saldo actualizado, 400 exceso, 409 cerrada, 401 sin auth

### Implementación — US1

- [x] T018 [US1] Crear `backend/src/schemas/pago_cliente.py`: `PagoClienteInput`, `PagoClienteResponse`
- [x] T019 [US1] Implementar `backend/src/services/pago_cliente_service.py`: `create_pago()`, `sum_pagos()`, integración con `pago_saldo.py`
- [x] T020 [US1] Modificar `backend/src/schemas/escritura.py`: agregar `costo_total`, `total_pagado`, `saldo_pendiente`, `pagada_al_100`, `sobrepago`, `pagos_cliente[]`
- [x] T021 [US1] Modificar `backend/src/services/escritura_service.py`: calcular y exponer campos de saldo en `_get_escritura_or_404` y list; eliminar `add_gasto_adicional`
- [x] T022 [US1] Crear `backend/src/api/routes/pagos_cliente.py`: `POST /escrituras/{id}/pagos-cliente`
- [ ] T023 [US1] Registrar router en `backend/src/api/router.py`; eliminar o desregistrar `backend/src/api/routes/gastos.py`
- [ ] T024 [US1] Publicar SSE `pago_cliente.created` + `liquidacion.updated` + `libros_updated` al registrar pago en `pago_cliente_service.py`
- [ ] T025 [US1] Verificar que `T016` y `T017` pasan; ajustar hasta verde

**Checkpoint**: API de pagos del cliente operativa. Saldo visible en GET escritura.

---

## Phase 4: User Story 2 — Cierre Condicionado al Pago Completo (Priority: P1)

**Goal**: Bloquear cierre de escritura si `saldo_pendiente > 0`.

**Independent Test**: `POST /escrituras/{id}/cerrar` con saldo > 0 → 409 con `saldo_pendiente`. Con saldo = 0 → 200.

### Tests TDD — US2 (⚠️ FAIL FIRST)

- [x] T026 [P] [US2] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_escrituras_api.py`: cerrar con saldo pendiente → 409 + body `saldo_pendiente`; cerrar con saldo 0 → 200; sobrepago permite cierre

### Implementación — US2

- [x] T027 [US2] Modificar `close_escritura()` en `backend/src/services/escritura_service.py`: validar `can_close(saldo_pendiente)` antes de cerrar; lanzar `EscrituraSaldoPendienteError` si falla
- [x] T028 [US2] Modificar `backend/src/api/routes/escrituras.py`: mapear `EscrituraSaldoPendienteError` → HTTP 409 con schema `ErrorSaldoPendiente`
- [x] T029 [US2] Verificar que `T026` pasa; ajustar hasta verde

**Checkpoint**: Cierre bloqueado con deuda pendiente. US1 + US2 backend completas (MVP backend).

---

## Phase 5: User Story 4 — Pagos al Colegio de Escribanos (Priority: P2)

**Goal**: Sección manual de pagos al Colegio, independiente del cobro al cliente.

**Independent Test**: `POST /escrituras/{id}/pagos-colegio` acepta pago en escritura con saldo pendiente del cliente. Expone `total_leyes_notariales_proyectadas` en GET escritura.

### Tests TDD — US4 (⚠️ FAIL FIRST)

- [x] T030 [P] [US4] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_pago_colegio_service.py`: registrar con saldo cliente pendiente OK, monto ≤ 0 rechazado, cerrada rechazada, sin validación contra leyes proyectadas
- [x] T031 [P] [US4] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_pagos_colegio_api.py`: POST 201, 409 cerrada, 401 sin auth, GET escritura incluye `total_leyes_notariales_proyectadas`

### Implementación — US4

- [x] T032 [US4] Crear `backend/src/schemas/pago_colegio.py`: `PagoColegioInput`, `PagoColegioResponse`
- [x] T033 [US4] Implementar `backend/src/services/pago_colegio_service.py`: `create_pago()` sin validación cruzada con saldo cliente
- [x] T034 [US4] Modificar `backend/src/schemas/escritura.py`: agregar `pagos_colegio[]` y `total_leyes_notariales_proyectadas` (desde `FacturaPrincipal.total_leyes_notariales`)
- [x] T035 [US4] Crear `backend/src/api/routes/pagos_colegio.py`: `POST /escrituras/{id}/pagos-colegio`
- [x] T036 [US4] Registrar router en `backend/src/api/router.py`
- [x] T037 [US4] Publicar SSE `pago_colegio.created` + `libros_updated` al registrar pago colegio
- [x] T038 [US4] Verificar que `T030` y `T031` pasan; ajustar hasta verde

**Checkpoint**: Pagos al Colegio registrables independientemente del cobro al cliente.

---

## Phase 6: User Story 3 — Libro de Entrada Basado en Pagos Reales (Priority: P2)

**Goal**: Libro de Entrada con líneas por pago del cliente + resumen de deudas pendientes.

**Independent Test**: `GET /libros/entrada?anio=&mes=` devuelve solo pagos del mes y `resumen_deudas` para escrituras abiertas con saldo > 0.

### Tests TDD — US3 (⚠️ FAIL FIRST)

- [x] T039 [P] [US3] ⚠️ FAIL FIRST Reescribir `backend/tests/unit/test_libros_service.py` (entrada): solo `PagoCliente` del mes, sin líneas derivadas de factura; `resumen_deudas` correcto; total = suma pagos
- [x] T040 [P] [US3] ⚠️ FAIL FIRST Actualizar `backend/tests/integration/test_libros_api.py` (entrada): filtro por fecha de pago, trazabilidad `escritura_id`

### Implementación — US3

- [x] T041 [US3] Modificar `backend/src/schemas/libros.py`: `DeudaResumenItem`, `LibroEntradaResponse` con `resumen_deudas`; `LibroLineaResponse.fecha_pago` (reemplaza `fecha_escritura`)
- [x] T042 [US3] Reescribir `get_libro_entrada()` en `backend/src/services/libros_service.py`: query `pagos_cliente` por mes; construir `resumen_deudas` para escrituras abiertas con saldo > 0
- [x] T043 [US3] Actualizar `backend/src/api/routes/libros.py` para devolver `LibroEntradaResponse`
- [x] T044 [US3] Verificar que `T039` y `T040` pasan; ajustar hasta verde

**Checkpoint**: Libro de Entrada refleja caja real entrante.

---

## Phase 7: User Story 5 — Libro de Salida Basado en Pagos al Colegio (Priority: P2)

**Goal**: Libro de Salida con solo pagos al Colegio registrados manualmente.

**Independent Test**: `GET /libros/salida?anio=&mes=` devuelve solo `PagoColegio` del mes. Sin ítems de factura.

### Tests TDD — US5 (⚠️ FAIL FIRST)

- [x] T045 [P] [US5] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_libros_service.py` (salida): solo `PagoColegio` del mes; sin impuestos/sellos/gastos admin; total correcto
- [x] T046 [P] [US5] ⚠️ FAIL FIRST Extender `backend/tests/integration/test_libros_api.py` (salida): filtro por fecha de pago colegio

### Implementación — US5

- [x] T047 [US5] Reescribir `get_libro_salida()` en `backend/src/services/libros_service.py`: query `pagos_colegio` por mes; eliminar derivación desde `FacturaPrincipal` y `GastoAdicional`
- [x] T048 [US5] Actualizar `backend/src/api/routes/libros.py` para `LibroSalidaResponse` simplificado
- [x] T049 [US5] Verificar que `T045` y `T046` pasan; ajustar hasta verde

**Checkpoint**: Libro de Salida refleja egresos reales al Colegio.

---

## Phase 8: User Story 6 — Liquidación y Pago de Salarios en Caja Real (Priority: P2)

**Goal**: Liquidación y totales de escribanos basados en pagos reales del mes (montón único por escritura).

**Independent Test**: Escritura con pago parcial aporta solo `monto_cobrado` del mes. Sin pagos en mes → excluida. Total escribano = suma de pagos.

### Tests TDD — US6 (⚠️ FAIL FIRST)

- [x] T050 [P] [US6] ⚠️ FAIL FIRST Reescribir `backend/tests/unit/test_liquidacion.py`: montón único por escritura, exclusión sin pagos, dos pagos en mes = una línea sumada
- [x] T051 [P] [US6] ⚠️ FAIL FIRST Actualizar `backend/tests/unit/test_salario.py`: totales escribano desde `monto_cobrado`; secretarias sin cambio
- [x] T052 [P] [US6] ⚠️ FAIL FIRST Actualizar `backend/tests/integration/test_liquidacion_api.py`: response con `monto_cobrado` (sin honorario+certificación proyectados)

### Implementación — US6

- [x] T053 [US6] Modificar `backend/src/schemas/liquidacion.py`: `LiquidacionEscrituraItem` con `monto_cobrado` (eliminar `honorario_principal`, `certificacion`, `subtotal`)
- [x] T054 [US6] Reescribir `get_liquidacion_mensual()` en `backend/src/services/liquidacion_service.py`: scoping por `PagoCliente.fecha` en mes; agrupar por escritura con SUM
- [x] T055 [US6] Modificar `backend/src/services/salario_service.py`: usar nuevos items de liquidación para bloque escribanos
- [x] T056 [US6] Verificar que `T050`, `T051` y `T052` pasan; ajustar hasta verde

**Checkpoint**: Liquidación y Pago de Salarios reflejan caja real. Backend completo.

---

## Phase 9: User Story 1+2+7 — Frontend Pagos del Cliente, Cierre y Saldo (Priority: P1/P3)

**Goal**: UI para registrar pagos del cliente, ver saldo, y cerrar solo al 100%. Listado con columnas de saldo.

**Independent Test**: Registrar pago en UI actualiza saldo sin reload. Botón cerrar deshabilitado si saldo > 0.

### Implementación — US1 + US2 + US7

- [x] T057 [P] [US1] Crear `frontend/src/api/pagosCliente.ts`: `createPagoCliente(escrituraId, payload)`
- [x] T058 [P] [US1] Crear `frontend/src/hooks/usePagosCliente.ts`: mutation + invalidación de queries escritura/liquidación/libros
- [x] T059 [P] [US1] Crear `frontend/src/components/escrituras/PagoClienteForm.tsx` (reemplaza `GastoForm.tsx` para entrada)
- [x] T060 [P] [US1] Crear `frontend/src/components/escrituras/PagoClienteList.tsx`: historial de pagos
- [x] T061 [US7] Modificar `frontend/src/components/escrituras/EscrituraList.tsx`: columnas `costo_total`, `total_pagado`, `saldo_pendiente`, badge 100%
- [x] T062 [US1] Modificar `frontend/src/pages/EscrituraDetail.tsx`: sección "Pagos del Cliente" con resumen saldo superior
- [x] T063 [US2] Modificar `frontend/src/pages/EscrituraDetail.tsx`: botón cerrar deshabilitado con tooltip si `saldo_pendiente > 0`; manejar 409 con monto pendiente
- [x] T064 [US1] Modificar `frontend/src/hooks/useSSE.ts`: escuchar `pago_cliente.created` e invalidar caches relevantes
- [x] T065 [US1] Eliminar `frontend/src/api/gastos.ts`, `frontend/src/components/escrituras/GastoForm.tsx` y referencias a `GastoAdicional`
- [x] T066 [US1] Actualizar `frontend/src/api/escrituras.ts` y tipos en `frontend/src/types/api.ts` con campos de saldo

**Checkpoint**: MVP frontend — pagos del cliente, saldo visible, cierre condicionado.

---

## Phase 10: User Story 4 — Frontend Pagos al Colegio (Priority: P2)

**Goal**: Sección "Pagos al Colegio" con referencia informativa a leyes notariales proyectadas.

**Independent Test**: Registrar pago colegio en escritura con deuda cliente pendiente. Ver total proyectado como referencia.

### Implementación — US4

- [x] T067 [P] [US4] Crear `frontend/src/api/pagosColegio.ts`: `createPagoColegio(escrituraId, payload)`
- [x] T068 [P] [US4] Crear `frontend/src/hooks/usePagosColegio.ts`: mutation + invalidación libros
- [x] T069 [P] [US4] Crear `frontend/src/components/escrituras/PagoColegioForm.tsx`
- [x] T070 [P] [US4] Crear `frontend/src/components/escrituras/PagoColegioList.tsx`
- [x] T071 [US4] Modificar `frontend/src/pages/EscrituraDetail.tsx`: sección "Pagos al Colegio" con `total_leyes_notariales_proyectadas` como referencia informativa
- [x] T072 [US4] Modificar `frontend/src/hooks/useSSE.ts`: escuchar `pago_colegio.created`

**Checkpoint**: Pagos al Colegio registrables desde UI, independientes del cobro al cliente.

---

## Phase 11: User Story 3+5 — Frontend Libros de Entrada y Salida (Priority: P2)

**Goal**: Libros actualizados para caja real.

**Independent Test**: Libro Entrada muestra pagos + resumen deudas. Libro Salida solo pagos colegio.

### Implementación — US3 + US5

- [x] T073 [P] [US3] Actualizar `frontend/src/api/libros.ts` y tipos: `LibroEntradaResponse` con `resumen_deudas`, `fecha_pago` en líneas
- [x] T074 [US3] Modificar `frontend/src/components/libros/LibroEntradaTable.tsx`: líneas por pago + tabla resumen deudas
- [x] T075 [US3] Modificar `frontend/src/pages/LibroEntradaPage.tsx`: totales y layout actualizado
- [x] T076 [P] [US5] Modificar `frontend/src/components/libros/LibroSalidaTable.tsx`: solo pagos colegio del mes
- [x] T077 [US5] Modificar `frontend/src/pages/LibroSalidaPage.tsx`: eliminar columnas/conceptos de factura derivados
- [x] T078 [US3] Modificar `frontend/src/hooks/useLibros.ts` y `useSSE.ts` para invalidación en eventos de pagos

**Checkpoint**: Libros de Entrada y Salida reflejan caja real en UI.

---

## Phase 12: User Story 6 — Frontend Liquidación y Pago de Salarios (Priority: P2)

**Goal**: Mostrar `monto_cobrado` por escritura (montón único) en liquidación y salarios.

**Independent Test**: Liquidación muestra solo escrituras con pagos en el mes. EscribanoCard muestra `monto_cobrado`.

### Implementación — US6

- [x] T079 [US6] Actualizar tipos de liquidación en `frontend/src/types/api.ts`: `monto_cobrado` reemplaza subtotal/honorarios
- [x] T080 [US6] Modificar `frontend/src/components/liquidacion/EscribanoCard.tsx`: mostrar `monto_cobrado` por escritura
- [x] T081 [US6] Modificar `frontend/src/pages/LiquidacionPage.tsx`: adaptar totales a caja real
- [x] T082 [US6] Modificar `frontend/src/pages/LiquidacionPage.tsx` / componentes de Pago de Salarios: totales escribano desde pagos reales

**Checkpoint**: Liquidación y Pago de Salarios alineados con caja real en UI.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Limpieza, documentación, validación end-to-end.

- [x] T083 [P] Eliminar `backend/src/models/gasto_adicional.py`, `backend/src/schemas/gasto.py`, `backend/src/api/routes/gastos.py` y tests obsoletos de gastos
- [x] T084 [P] Actualizar `backend/tests/conftest.py` y `backend/tests/helpers/escritura_factory.py` para usar `PagoCliente`/`PagoColegio` en lugar de `GastoAdicional`
- [x] T085 Actualizar tests existentes afectados: `backend/tests/integration/test_sse_events.py` (nuevos eventos SSE)
- [x] T086 [P] Actualizar `specs/003-pagos-cliente/quickstart.md` si algún comando de validación cambió durante implementación
- [x] T087 Ejecutar suite completa backend: `pytest tests/ -v` — todos verdes
- [ ] T088 [P] Ejecutar validación manual según `specs/003-pagos-cliente/quickstart.md` (pagos, libros, liquidación, SSE)
- [ ] T089 Documentar en PR: constitución §2.3/§2.4 requiere MINOR amendment al mergear (research R-009)

**Checkpoint**: Feature completa, tests verdes, quickstart validado.

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Delivers |
|---|---|---|
| 1 Setup | — | Errores + tipos stub |
| 2 Foundational | Phase 1 | DB + modelos + pago_saldo |
| 3 US1 backend | Phase 2 | Pagos cliente API |
| 4 US2 backend | Phase 3 | Cierre condicionado |
| 5 US4 backend | Phase 2 | Pagos colegio API |
| 6 US3 backend | Phase 3 | Libro entrada |
| 7 US5 backend | Phase 5 | Libro salida |
| 8 US6 backend | Phase 3 | Liquidación caja real |
| 9 US1+2+7 frontend | Phase 3, 4 | MVP UI |
| 10 US4 frontend | Phase 5 | Pagos colegio UI |
| 11 US3+5 frontend | Phase 6, 7 | Libros UI |
| 12 US6 frontend | Phase 8 | Liquidación UI |
| 13 Polish | All | Cleanup |

### User Story Dependencies

- **US1 (P1)**: Foundational → MVP backend
- **US2 (P1)**: US1 (saldo debe existir para validar cierre)
- **US4 (P2)**: Foundational only — **parallelizable con US1** tras Phase 2
- **US3 (P2)**: US1 (necesita pagos cliente en DB)
- **US5 (P2)**: US4 (necesita pagos colegio en DB)
- **US6 (P2)**: US1 (liquidación desde pagos cliente)
- **US7 (P3)**: US1 frontend (saldo en listado/detalle)

### Parallel Opportunities

```bash
# Tras Phase 2 — backend en paralelo:
Developer A: Phase 3+4 (US1+US2 pagos cliente + cierre)
Developer B: Phase 5 (US4 pagos colegio)

# Tras US1+US4 backend:
Developer A: Phase 6+8 (US3 libro entrada + US6 liquidación)
Developer B: Phase 7 (US5 libro salida)

# Frontend — tras backend respectivo:
Developer A: Phase 9 (US1+2+7)
Developer B: Phase 10 (US4) → Phase 11 (US3+5) → Phase 12 (US6)
```

---

## Parallel Example: User Story 1

```bash
# Tests US1 en paralelo (FAIL FIRST):
T016: backend/tests/unit/test_pago_cliente_service.py
T017: backend/tests/integration/test_pagos_cliente_api.py

# Implementación US1 en paralelo (tras schemas):
T018: backend/src/schemas/pago_cliente.py
T022: backend/src/api/routes/pagos_cliente.py  # tras T019 service
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL**)
3. Complete Phase 3: US1 backend (pagos + saldo)
4. Complete Phase 4: US2 backend (cierre)
5. Complete Phase 9: US1+2+7 frontend
6. **STOP and VALIDATE**: Registrar pago parcial, ver saldo, cerrar al 100%

### Incremental Delivery

| Increment | Phases | Value delivered |
|---|---|---|
| MVP | 1–4, 9 | Pagos cliente, saldo, cierre condicionado |
| +Colegio | 5, 10 | Pagos al Colegio manuales |
| +Libros | 6–7, 11 | Libros caja real |
| +Liquidación | 8, 12 | Liquidación y salarios reales |
| Polish | 13 | Production-ready |

---

## Notes

- Total tasks: **89**
- TDD obligatorio: **24** tests ⚠️ FAIL FIRST
- UI tasks: **26** (sin Figma — decisión explícita del equipo)
- Eliminar código legacy `GastoAdicional` solo en Phase 13 tras verificar que nada lo referencia
- `POST /escrituras/{id}/gastos` debe retornar 410 Gone o eliminarse en T023
