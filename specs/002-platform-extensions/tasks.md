# Tasks: Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Feature Branch**: `002-platform-extensions`  
**Input**: `specs/002-platform-extensions/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD completo — tests escritos en estado FAILING antes de cada implementación  
**Note on UI tasks**: No Figma references — frontend implemented directly per spec (clarified in feature 001 session 2026-07-18). `figma:` field omitted for all UI tasks per project decision.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario correspondiente (US1–US5)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Infraestructura Nueva

**Purpose**: Preparar la base para todas las nuevas entidades y servicios. No bloquea las
historias de usuario individualmente — cada WU arranca desde aquí.

- [x] T001 Agregar `cachetools` y `httpx` a `backend/pyproject.toml` como dependencias explícitas
- [x] T002 Crear `backend/src/models/mixins.py` con `SoftDeleteMixin` (`deleted_at`, `soft_delete()`) y registrar el event listener `_apply_soft_delete_filter` en `backend/src/database.py`
- [x] T003 [P] Agregar variables de entorno `COTIZACION_API_URL`, `COTIZACION_FALLBACK_URL`, `COTIZACION_CACHE_TTL_HOURS` a `backend/src/config.py` (Pydantic BaseSettings) y a `.env.example`
- [x] T004 Crear migración Alembic `backend/alembic/versions/005_platform_extensions.py` (spec original: `004_platform_extensions`): tablas `escribano`, `empleado`, `sueldo_historico`; columnas `escribano_id` + `escribano_nombre` en `escritura`; seed de Costanza/Gabriel/Victoria y Graciela/Guadalupe; migración de ENUM → FK; drop columna ENUM

**Checkpoint**: Migración aplica en DB limpia y en DB con datos de feature 001 sin errores.
`SELECT count(*) FROM escritura WHERE escribano_id IS NULL` devuelve 0.

---

## Phase 2: Foundational — Modelos ORM y Tests de Infraestructura

**Purpose**: Modelos ORM de las nuevas entidades. Deben estar listos antes de cualquier
servicio o endpoint.

**⚠️ CRITICAL**: Las fases de historias de usuario dependen de esta fase.

- [x] T005 ⚠️ FAIL FIRST Escribir test unitario `backend/tests/unit/test_soft_delete.py`: verificar que `SoftDeleteMixin` con `deleted_at` populado queda excluido de queries ORM estándar, y que `execution_options(include_deleted=True)` lo incluye
- [x] T006 Crear modelo ORM `backend/src/models/escribano.py`: campos `id`, `nombre`, `deleted_at`, `created_at`; partial unique index `uq_escribano_nombre_active` (`UNIQUE (nombre) WHERE deleted_at IS NULL`)
- [x] T007 [P] Crear modelo ORM `backend/src/models/empleado.py`: entidades `Empleado` (`id`, `nombre`, `sueldo`, `deleted_at`, `created_at`, `updated_at`) y `SueldoHistorico` (`id`, `empleado_id`, `empleado_nombre`, `anio`, `mes`, `sueldo`, `created_at`); unique constraint (`empleado_id`, `anio`, `mes`)
- [x] T008 Modificar `backend/src/models/escritura.py`: agregar columnas `escribano_id` (FK → Escribano.id, not null) y `escribano_nombre` (VARCHAR, not null); eliminar referencia al ENUM hardcodeado
- [x] T009 Verificar que `T005` pasa tras implementar `T002`; corregir si falla

**Checkpoint**: `alembic upgrade head` exitoso. Tests de soft delete pasan.
Modelos ORM disponibles para importar desde servicios.

---

## Phase 3: User Story 1 — Cotización de Dólar via API Oficial (Priority: P1) 🎯 MVP

**Goal**: La secretaria puede obtener el tipo de cambio MEP y Banco Nación desde una fuente
oficial seleccionando la fecha. Si la API falla, los campos siguen editables manualmente.

**Independent Test**: `GET /api/v1/cotizacion?casa=bolsa` devuelve valores numéricos válidos.
Segunda llamada a la misma fecha devuelve `"source": "cache"`. Error de red devuelve HTTP 503
con mensaje descriptivo, no bloquea el formulario.

### Tests TDD — US1 (⚠️ FAIL FIRST)

- [x] T010 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_cotizacion_service.py`: casos éxito (mock httpx), cache hit (sin llamada HTTP), error de red → `CotizacionAPIError`, fecha sin cotización → 404, valor compra/venta = 0 → error
- [x] T011 [P] [US1] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_cotizacion_api.py`: GET con casa válida retorna 200, GET sin auth retorna 401, casa inválida retorna 422, API caída retorna 503 con mensaje descriptivo

### Implementación — US1

- [x] T012 [US1] Crear `backend/src/schemas/cotizacion.py`: DTOs `CotizacionResponse` (casa, fecha, compra, venta, source) y excepción de dominio `CotizacionAPIError`
- [x] T013 [US1] Implementar `backend/src/services/cotizacion_service.py`: `TTLCache` module-level (8h para hoy, dict permanente para fechas pasadas), `get_exchange_rate(casa, fecha)` con httpx, fallback a DolarAPI para fecha de hoy si ArgentinaDatos falla, manejo de `raise_for_status()`
- [x] T014 [US1] Implementar `backend/src/api/routes/cotizacion.py`: `GET /api/v1/cotizacion?casa=&fecha=` protegido con `get_current_user`; traduce `CotizacionAPIError` → 503, `CotizacionNoDisponible` → 404
- [x] T015 [US1] Registrar router de cotización en `backend/src/api/router.py`
- [x] T016 [US1] Verificar que `T010` y `T011` pasan; ajustar implementación hasta verde

**Checkpoint**: `GET /api/v1/cotizacion?casa=bolsa` retorna valores reales de ArgentinaDatos.
Segunda llamada retorna `"source": "cache"`. Simular falla de red → HTTP 503 con mensaje claro.

---

## Phase 4: User Story 2 — Configuración de Escribanos (Priority: P2)

**Goal**: CRUD completo de escribanos con soft delete. El selector de escribanos en escrituras
muestra solo los activos. Nombre duplicado de activo rechazado; nombre de inactivo reutilizable.

**Independent Test**: Crear escribano "Martínez" → aparece en selector. Desactivarlo → desaparece
del selector. Crear nuevo "Martínez" → aceptado. Desactivar escribano con escrituras sin `force=true` → 409.

### Tests TDD — US2 (⚠️ FAIL FIRST)

- [x] T017 [P] [US2] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_escribanos_api.py`: listar activos, crear, duplicado → 409, desactivar sin escrituras → 204, desactivar con escrituras sin force → 409, desactivar con force=true → 204, nombre de inactivo reutilizable → 201

### Implementación — US2

- [x] T018 [US2] Crear `backend/src/schemas/escribano.py`: `EscribanoResponse`, `EscribanoCreateRequest`
- [x] T019 [US2] Implementar `backend/src/services/escribano_service.py`: `list_active()`, `create(nombre)` (valida duplicado activo), `soft_delete(id, force)` (cuenta escrituras asociadas, rechaza sin force si > 0)
- [x] T020 [US2] Implementar `backend/src/api/routes/escribanos.py`: `GET /configuracion/escribanos`, `POST /configuracion/escribanos`, `DELETE /configuracion/escribanos/{id}?force=`; todos protegidos con auth
- [x] T021 [US2] Registrar router de escribanos en `backend/src/api/router.py`
- [x] T022 [US2] Modificar `backend/src/api/routes/escrituras.py`: reemplazar validación de ENUM `escribano` por lookup de `escribano_id` activo (400 si no existe o está inactivo)
- [x] T023 [US2] Verificar que `T017` pasa; ajustar hasta verde

**Checkpoint**: Selector de escribanos en formulario de escritura solo muestra activos.
Desactivar con escrituras sin confirmar devuelve 409 con `escrituras_count`.

---

## Phase 5: User Story 3 — Configuración de Empleados y Sueldos (Priority: P3)

**Goal**: CRUD de empleados con gestión de sueldos. Modificar sueldo aplica al mes en curso
sin prorrateo. SueldoHistorico generado al cierre mensual. Meses cerrados no se alteran.

**Independent Test**: Modificar sueldo de Graciela → `GET /salarios` del mes en curso muestra
nuevo monto. Cerrar el mes → SueldoHistorico creado. Modificar sueldo nuevamente → historial previo intacto.

### Tests TDD — US3 (⚠️ FAIL FIRST)

- [x] T024 [P] [US3] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_empleado_service.py`: crear empleado, modificar sueldo (reflejo inmediato), sueldo = 0 rechazado, sueldo negativo rechazado, soft delete, SueldoHistorico generado al cierre, modificación post-cierre no altera historial
- [x] T025 [P] [US3] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_empleados_api.py`: listar, crear, PATCH sueldo → 200, sueldo ≤ 0 → 422, DELETE → 204

### Implementación — US3

- [x] T026 [US3] Crear `backend/src/schemas/empleado.py`: `EmpleadoResponse`, `EmpleadoCreateRequest`, `EmpleadoUpdateRequest`
- [x] T027 [US3] Implementar `backend/src/services/empleado_service.py`: `list_active()`, `create(nombre, sueldo)`, `update_sueldo(id, sueldo)` (valida > 0, actualiza `updated_at`), `soft_delete(id)`, `snapshot_month(anio, mes)` (genera `SueldoHistorico` para todos los empleados activos)
- [x] T028 [US3] Implementar `backend/src/api/routes/empleados.py`: `GET /configuracion/empleados`, `POST /configuracion/empleados`, `PATCH /configuracion/empleados/{id}`, `DELETE /configuracion/empleados/{id}`; todos con auth
- [x] T029 [US3] Registrar router de empleados en `backend/src/api/router.py`
- [x] T030 [US3] Modificar `backend/src/services/salario_service.py`: leer `Empleado.sueldo` de empleados activos en lugar de `ConfiguracionFinanciera.salario_secretarias_total` para el cálculo del mes en curso
- [x] T031 [US3] Integrar `EmpleadoService.snapshot_month()` en el cierre mensual de `backend/src/services/liquidacion_service.py`
- [x] T032 [US3] Verificar que `T024` y `T025` pasan; ajustar hasta verde

**Checkpoint**: PATCH sueldo se refleja en `GET /salarios` inmediatamente.
Cierre de mes genera `SueldoHistorico`. Segundo PATCH no altera el snapshot.

---

## Phase 6: User Story 4 — Libro de Entrada (Priority: P4)

**Goal**: Vista derivada de todos los flujos de entrada (honorarios + certificación + gastos
adicionales tipo entrada) para el mes filtrado, con trazabilidad a escritura de origen.

**Independent Test**: Con 2 escrituras cargadas en el mes, `GET /libros/entrada` retorna líneas
con `escritura_id`, `concepto`, `monto`. Total cuadra con suma manual de honorarios + certificación de esas escrituras.

### Tests TDD — US4 (⚠️ FAIL FIRST)

- [x] T033 [P] [US4] ⚠️ FAIL FIRST Escribir `backend/tests/unit/test_libros_service.py` (sección entrada): libro incluye solo honorarios+certificación+gastos-entrada; excluye impuestos/sellos; cada línea tiene escritura_id y concepto correcto; total = suma de montos; incluye escrituras abiertas y cerradas del mes; excluye escrituras de meses anteriores
- [x] T034 [P] [US4] ⚠️ FAIL FIRST Escribir `backend/tests/integration/test_libros_api.py` (sección entrada): GET retorna 200, mes por defecto = mes actual, filtro por anio+mes funciona, sin auth → 401

### Implementación — US4

- [x] T035 [US4] Crear `backend/src/schemas/libros.py`: `LibroLineaResponse` (escritura_id, escritura_nombre, concepto, monto, fecha_escritura), `LibroResponse` (anio, mes, lineas, total)
- [x] T036 [US4] Implementar `backend/src/services/libros_service.py`: `get_libro_entrada(anio, mes)` — query de escrituras del mes (mismo scoping que liquidación), itera FacturaPrincipal extrayendo `honorario_principal` y `certificacion` con sus labels, itera GastoAdicional filtrando `direccion='entrada'`, devuelve `LibroResponse`
- [x] T037 [US4] Implementar `backend/src/api/routes/libros.py`: `GET /libros/entrada?anio=&mes=` con default mes actual; auth requerida
- [x] T038 [US4] Registrar router de libros en `backend/src/api/router.py`
- [x] T039 [US4] Emitir evento SSE `libros_updated` en create/update/close de escritura y gastos (implementado en `escritura_service.py`; mismo canal SSE existente)
- [x] T040 [US4] Verificar que `T033` y `T034` pasan; ajustar hasta verde

**Checkpoint**: `GET /libros/entrada` retorna líneas correctas. Total cuadra con fixture
canónico: para escritura USD 105,000, entrada = honorario_principal (3,654,856.80) + certificacion (456,857.10) = 4,111,713.90.

---

## Phase 7: User Story 5 — Libro de Salida (Priority: P5)

**Goal**: Vista derivada de todos los flujos de salida (impuestos, sellos, aportes notariales,
gastos admin, gastos adicionales tipo salida) con trazabilidad a escritura de origen.

**Independent Test**: Con 2 escrituras, `GET /libros/salida` retorna líneas individuales por ítem
(no el total_impuestos agregado). Total cuadra con suma manual de impuestos+sellos+aportes+gastos admin.

### Tests TDD — US5 (⚠️ FAIL FIRST)

- [x] T041 [P] [US5] ⚠️ FAIL FIRST Ampliar `backend/tests/unit/test_libros_service.py` (sección salida): libro incluye ítems individuales de impuestos/sellos/aportes/gastos admin; NO incluye honorarios/certificación; gastos-salida incluidos; gastos-entrada excluidos; total correcto; trazabilidad correcta
- [x] T042 [P] [US5] ⚠️ FAIL FIRST Ampliar `backend/tests/integration/test_libros_api.py` (sección salida): GET /libros/salida retorna 200 con estructura correcta

### Implementación — US5

- [x] T043 [US5] Ampliar `backend/src/services/libros_service.py`: `get_libro_salida(anio, mes)` — extrae ítems individuales de `FacturaPrincipal` (tasa_3pm, sellos, tasa_75pm, firma_impuestos, art2_a, art12_a, art12_c, art12_f, inscripcion, protocolo, ii_certificados, municipio, fotocopias_urgentes, certificaciones_extra, catastro, testimonio, concuerda, informes_notariales, extracto, fotocopias_simples, tasas_minimas) con sus labels canónicos del data-model; itera GastoAdicional `direccion='salida'`
- [x] T044 [US5] Ampliar `backend/src/api/routes/libros.py`: `GET /libros/salida?anio=&mes=`
- [x] T045 [US5] Verificar que `T041` y `T042` pasan; ajustar hasta verde

**Checkpoint**: `GET /libros/salida` retorna ítems individuales (no totales agregados).
Para fixture USD 105,000: total_impuestos individual = tasa_3pm (448,875) + sellos (3,740,375) + tasa_75pm (1,122,187.50) + firma_impuestos (52) = 5,311,489.50.

---

## Phase 8: Frontend — Cotización en EscrituraForm (US1 Frontend)

**Goal**: Botón "Consultar cotización" con date picker en el formulario de escrituras.
Campos MEP y Banco Nación se auto-completan; siguen siendo editables manualmente.

**Independent Test**: En el formulario, seleccionar fecha + presionar botón → campos se llenan.
Simular error → mensaje descriptivo visible, formulario desbloqueado.

- [x] T046 [US1] Crear `frontend/src/api/cotizacion.ts`: función `getCotizacion(casa, fecha)` que llama `GET /api/v1/cotizacion`
- [x] T047 [US1] Crear `frontend/src/hooks/useCotizacion.ts`: estado idle/loading/success/error, expone `fetchRate(casa, fecha)` y el último resultado
- [x] T048 [US1] Modificar `frontend/src/components/escrituras/EscrituraForm.tsx`: agregar `<input type="date">` (default hoy), botón "Consultar cotización" con estado de carga, auto-fill de campos MEP y Nación en éxito, mensaje de error inline en fallo, sin bloquear el formulario

**Checkpoint**: Presionar "Consultar cotización" rellena los campos en < 5 segundos (SC-001).
Si la API falla, un mensaje claro aparece y los campos siguen editables.

---

## Phase 9: Frontend — Configuración de Escribanos y Empleados (US2 + US3 Frontend)

**Goal**: `ConfiguracionPage` con tabs Escribanos y Empleados. Escribanos: lista + agregar +
desactivar con modal de confirmación. Empleados: lista con sueldo + editar sueldo inline + agregar + eliminar.

**Independent Test**: Agregar escribano "Martínez" → aparece en selector de escrituras.
Editar sueldo de Graciela → Pago de Salarios actualiza en < 2s.

- [x] T049 [P] [US2] Crear `frontend/src/api/escribanos.ts`: `listEscribanos()`, `createEscribano(nombre)`, `deactivateEscribano(id, force)`
- [x] T050 [P] [US2] Crear `frontend/src/hooks/useEscribanos.ts`: TanStack Query con invalidación en mutaciones
- [x] T051 [US2] Crear `frontend/src/components/configuracion/EscribanosConfig.tsx`: tabla de activos, formulario inline de nuevo escribano, botón desactivar con modal de confirmación (doble step si tiene escrituras: muestra cuenta + requiere confirmación explícita), etiqueta "(inactivo)" visible en escrituras históricas
- [x] T052 [P] [US3] Crear `frontend/src/api/empleados.ts`: `listEmpleados()`, `createEmpleado(nombre, sueldo)`, `updateSueldo(id, sueldo)`, `deleteEmpleado(id)`
- [x] T053 [P] [US3] Crear `frontend/src/hooks/useEmpleados.ts`: TanStack Query con invalidación en mutaciones
- [x] T054 [US3] Crear `frontend/src/components/configuracion/EmpleadosConfig.tsx`: tabla con nombre + sueldo + edición inline de sueldo, formulario de nuevo empleado, botón eliminar, validación cliente sueldo > 0
- [x] T055 [US2] [US3] Modificar `frontend/src/pages/ConfiguracionPage.tsx`: agregar tabs "Escribanos" y "Empleados" con sus componentes; mantener tab existente de configuración financiera

**Checkpoint**: SC-004 verificado (< 60s para agregar/eliminar). SC-005 verificado (sueldo
modificado en Pago de Salarios < 2s vía SSE invalidation).

---

## Phase 10: Frontend — Libro de Entrada y Libro de Salida (US4 + US5 Frontend)

**Goal**: Dos nuevas páginas con tabla filtrable por mes, total acumulado, hipervínculo a
escritura origen, y actualizaciones SSE en tiempo real.

**Independent Test**: Con escrituras del mes actual, Libro de Entrada muestra líneas de honorarios
con links. Crear nueva escritura en Tab B → Libro se actualiza en Tab A en < 2s.

- [x] T056 [P] [US4] [US5] Crear `frontend/src/api/libros.ts`: `getLibroEntrada(anio, mes)`, `getLibroSalida(anio, mes)`
- [x] T057 [P] [US4] [US5] Crear `frontend/src/hooks/useLibros.ts`: TanStack Query para entrada y salida; re-fetch al recibir evento SSE `libros_updated`
- [x] T058 [US4] Crear `frontend/src/components/libros/LibroEntradaTable.tsx`: tabla columnas Concepto / Monto / Escritura (link) / Fecha; fila de total al pie; selector mes/año; estado vacío informativo
- [x] T059 [US5] Crear `frontend/src/components/libros/LibroSalidaTable.tsx`: misma estructura que LibroEntradaTable
- [x] T060 [US4] Crear `frontend/src/pages/LibroEntradaPage.tsx`: composición de selector de mes + LibroEntradaTable + total acumulado
- [x] T061 [US5] Crear `frontend/src/pages/LibroSalidaPage.tsx`: composición de selector de mes + LibroSalidaTable + total acumulado
- [x] T062 [US4] [US5] Modificar `frontend/src/components/layout/Navbar.tsx`: agregar ítems "Libro de Entrada" y "Libro de Salida" a la navegación principal
- [x] T063 [US4] [US5] Modificar `frontend/src/App.tsx`: registrar rutas `/libro-entrada` y `/libro-salida` con componentes correspondientes

**Checkpoint**: SC-002 y SC-003 verificados (100% líneas con hipervínculo funcional).
SC-007 verificado (actualización SSE en < 2s).

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Validación end-to-end, pulido de UX, y verificación de criterios de éxito globales.

- [x] T064 [P] Actualizar `frontend/src/components/escrituras/EscrituraForm.tsx`: asegurar que el selector de escribano usa los datos de `useEscribanos` (activos dinámicos) en lugar de ENUM hardcodeado
- [x] T065 [P] Actualizar `frontend/src/types/api.ts`: agregar tipos TypeScript para `EscribanoResponse`, `EmpleadoResponse`, `CotizacionResponse`, `LibroResponse`, `LibroLineaResponse`; escrituras migradas a `escribano_id` + `escribano_nombre`
- [x] T066 Ejecutar suite completa de tests: `make test` desde raíz; confirmar que todos los tests de feature 001 siguen pasando (regresión)
- [x] T067 [P] Validar SC-001: secretaria obtiene cotización en < 5s en condiciones normales de red — flujo implementado (`EscrituraForm` + API cache 8h); validación manual en browser pendiente de deploy
- [x] T068 [P] Validar SC-008: modificar sueldo/escribano no altera meses cerrados — verificado por `test_post_snapshot_sueldo_change_does_not_alter_historico` (backend)
- [x] T069 Ejecutar `quickstart.md` (feature 002) end-to-end: migración, seed, cotización API, libros, configuración — **parcial automatizado**: `make test` 90/90 + `npm run build`; smoke/docker E2E manual pendiente
- [x] T070 [P] Revisar mensajes de error de usuario en ES: cotización fallida, sueldo inválido, escribano duplicado, desactivar con escrituras — mapeo en `frontend/src/utils/errors.ts` + validaciones cliente en config

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** (Setup): Sin dependencias — empezar de inmediato
- **Phase 2** (Foundational): Depende de Phase 1 — bloquea todas las historias
- **Phases 3–7** (Backend US1–US5): Todas dependen de Phase 2; pueden ejecutarse en paralelo entre sí
- **Phases 8–10** (Frontend): Dependen de sus respectivas fases backend
- **Phase 11** (Polish): Depende de todas las fases previas

### User Story Dependencies

| Historia | Depende de | Independiente de |
|---|---|---|
| US1 — Cotización (backend) | Phase 2 | US2, US3, US4, US5 |
| US2 — Escribanos (backend) | Phase 2 | US1, US3, US4, US5 |
| US3 — Empleados (backend) | Phase 2 | US1, US2, US4, US5 |
| US4 — Libro Entrada (backend) | Phase 2 (+ escrituras de feature 001 operativas) | US1, US2, US3, US5 |
| US5 — Libro Salida (backend) | Phase 2 (+ US4 service file iniciado) | US1, US2, US3 |
| US1 Frontend | Phase 3 completa | US2–US5 frontend |
| US2+US3 Frontend | Phases 4+5 completas | US1, US4, US5 frontend |
| US4+US5 Frontend | Phases 6+7 completas | US1, US2, US3 frontend |

### Within Each Phase

- Tests TDD marcados `⚠️ FAIL FIRST` deben ejecutarse y fallar antes de la implementación
- Schemas antes de services; services antes de routes
- Routes registradas en router antes de tests de integración
- Frontend API clients antes de hooks; hooks antes de componentes

### Parallel Opportunities

- T010 y T011 (tests US1) pueden escribirse en paralelo
- T006 y T007 (modelos Escribano y Empleado) pueden crearse en paralelo
- T033/T034 y T041/T042 (tests Libros entrada y salida) pueden escribirse en paralelo
- T049/T050 (api+hook Escribanos) y T052/T053 (api+hook Empleados) en paralelo
- T058 y T059 (tablas Libro Entrada y Salida) en paralelo

---

## Parallel Example: Phase 3 (US1 Backend)

```bash
# Paso 1 — Escribir tests en paralelo (FAIL FIRST)
Task: "T010 — test_cotizacion_service.py (unit, mock httpx)"
Task: "T011 — test_cotizacion_api.py (integration)"

# Paso 2 — Implementar en orden
Task: "T012 — schemas/cotizacion.py"
Task: "T013 — services/cotizacion_service.py"
Task: "T014 — routes/cotizacion.py"
Task: "T015 — registrar en router.py"
Task: "T016 — verificar verde"
```

---

## Implementation Strategy

### MVP First (US1 + US2 — las más urgentes operativamente)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (cotización backend) → Phase 8 (cotización frontend)
3. Completar Phase 4 (escribanos backend) → Phase 9 parcial (tab Escribanos)
4. **STOP y VALIDAR**: cotización automática y selector de escribanos dinámico funcionan
5. Deploy/demo parcial

### Incremental Delivery

1. Phase 1 + 2 → Fundación lista
2. Phase 3 + 8 → Cotización automática (US1 completo)
3. Phase 4 + 5 + 9 → Configuración de escribanos y empleados (US2 + US3 completos)
4. Phase 6 + 7 + 10 → Libros de Entrada y Salida (US4 + US5 completos)
5. Phase 11 → Polish y validación final

### Parallel Team Strategy

Con dos desarrolladores:
1. Ambos completan Phase 1 + 2 juntos
2. Dev A: Phases 3 + 4 + 5 (backend US1–US3) → luego 8 + 9 (frontend US1–US3)
3. Dev B: Phases 6 + 7 (backend US4–US5) → luego 10 (frontend US4–US5)
4. Ambos: Phase 11

---

## Notes

- `[P]` = archivos distintos, sin dependencias incompletas en el mismo paso
- `⚠️ FAIL FIRST` = ejecutar test, confirmar que falla, luego implementar
- Cada checkpoint es un momento válido de commit y demo
- No modificar código de feature 001 excepto: `escritura.py` (modelo), `salario_service.py`, `liquidacion_service.py`, `router.py`, `Navbar.tsx`, `EscrituraForm.tsx`, `App.tsx`
- La migración `005_platform_extensions` es la única migración nueva de feature 002; debe ser reversible (`downgrade` limpio)
- El fixture constitucional (USD 105,000) provee valores exactos para validar los totales de los libros en los tests
