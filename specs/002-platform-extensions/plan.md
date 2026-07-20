# Implementation Plan: Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Branch**: `002-platform-extensions` | **Date**: 2026-07-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-platform-extensions/spec.md`

---

## Summary

Extend the existing Contaduría Escribanía platform (built in `001-plataforma-contaduria`) with
four capabilities: (1) automatic dollar exchange rate lookup from ArgentinaDatos API with
8-hour TTL cache, (2) dynamic escribano configuration via soft-delete CRUD, (3) employee
salary management with historical snapshots, and (4) Libro de Entrada and Libro de Salida
views derived in real time from existing escritura data. All changes extend the existing
FastAPI/PostgreSQL/React stack without introducing new infrastructure.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged from 001  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async + asyncpg, Alembic, Pydantic v2 (backend); React + Vite, TanStack Query (frontend); **new: `cachetools`, `httpx`** (explicit pin)  
**Storage**: PostgreSQL 16 — unchanged; new tables: `escribano`, `empleado`, `sueldo_historico`; modified: `escritura` (add `escribano_id` FK + `escribano_nombre` snapshot, remove ENUM)  
**Testing**: pytest + pytest-asyncio (TDD); Vitest (frontend) — unchanged  
**Target Platform**: ECS Fargate private subnet + RDS (unchanged); new external dependency: ArgentinaDatos API (proxied via backend)  
**Project Type**: Web application — existing `backend/` + `frontend/` structure  
**Performance Goals**: Cotización API response ≤ 5s (SC-001); SSE propagation ≤ 2s (inherited SC-007); cache hit avoids external call entirely  
**Constraints**: Single Fargate task (no Redis); no public IP on API; no polling; no breaking changes to existing data (migration must be additive)  
**Scale/Scope**: < 10 concurrent users; existing data must migrate cleanly

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments (local ↔ AWS) | ✅ Pass | ArgentinaDatos URL in env var `COTIZACION_API_URL`; cache is in-process (same behavior locally and on Fargate) |
| P2 — Cost-conscious AWS | ✅ Pass | No new AWS services required; `cachetools` is in-process zero-cost |
| P3 — Python backend | ✅ Pass | All new services in Python (cotizacion_service.py, escribano_service.py, etc.) |
| P4 — Frontend UX + navigation | ✅ Pass | Navigation expands to: Escrituras, Liquidación, Pago de Salarios, **Libro de Entrada**, **Libro de Salida**; Configuración as sub-menu |
| P5 — Real-time via SSE, no polling | ✅ Pass | Libros derived from SSE-updated query cache; same existing `/api/v1/events` SSE channel extended |
| P6 — Formula integrity, pure functions | ✅ Pass | Libros derive from existing `FacturaPrincipal` columns; no new calculation logic introduced |
| P7 — Security baseline | ✅ Pass | External API calls backend-only (FR-006); new endpoints auth-protected; soft-delete via `deleted_at` preserves referential integrity |
| P8 — Traceability | ✅ Pass | Every Libro line includes `escritura_id` + `escritura_nombre`; hyperlink to source escritura (FR-019, FR-025) |

**Result**: All gates pass. Implementation may proceed.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-platform-extensions/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output (delta from 001)
├── contracts/
│   └── openapi-patch.yaml  # Phase 1 output — new/modified endpoints only
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/spec-kitti.tasks)
```

### Source Code — New and Modified Files

```text
backend/
├── alembic/
│   └── versions/
│       └── 004_platform_extensions.py   # NEW — single migration for all entities
├── src/
│   ├── models/
│   │   ├── escribano.py                 # NEW — Escribano entity (soft delete)
│   │   ├── empleado.py                  # NEW — Empleado + SueldoHistorico entities
│   │   └── escritura.py                 # MODIFY — replace ENUM escribano with FK
│   ├── schemas/
│   │   ├── cotizacion.py                # NEW — request/response DTOs for API lookup
│   │   ├── escribano.py                 # NEW — DTOs
│   │   ├── empleado.py                  # NEW — DTOs
│   │   └── libros.py                    # NEW — EntradaLibro / SalidaLibro DTOs
│   ├── services/
│   │   ├── cotizacion_service.py        # NEW — proxy + TTL cache logic
│   │   ├── escribano_service.py         # NEW — CRUD + soft delete
│   │   ├── empleado_service.py          # NEW — CRUD + sueldo historico
│   │   └── libros_service.py            # NEW — derive Entrada/Salida from escrituras
│   ├── api/
│   │   └── routes/
│   │       ├── cotizacion.py            # NEW — GET /cotizacion?casa=&fecha=
│   │       ├── escribanos.py            # NEW — CRUD /configuracion/escribanos
│   │       ├── empleados.py             # NEW — CRUD /configuracion/empleados
│   │       └── libros.py                # NEW — GET /libros/entrada, /libros/salida
│   └── models/
│       └── mixins.py                    # NEW — SoftDeleteMixin
├── tests/
│   ├── unit/
│   │   ├── test_cotizacion_service.py   # NEW — TDD: mock httpx, cache hit/miss
│   │   ├── test_libros_service.py       # NEW — TDD: derivation correctness
│   │   └── test_empleado_service.py     # NEW — TDD: sueldo historico, validation
│   └── integration/
│       ├── test_cotizacion_api.py        # NEW
│       ├── test_escribanos_api.py        # NEW
│       ├── test_empleados_api.py         # NEW
│       └── test_libros_api.py            # NEW

frontend/
├── src/
│   ├── api/
│   │   ├── cotizacion.ts               # NEW
│   │   ├── escribanos.ts               # NEW
│   │   ├── empleados.ts                # NEW
│   │   └── libros.ts                   # NEW
│   ├── hooks/
│   │   ├── useCotizacion.ts            # NEW
│   │   ├── useEscribanos.ts            # NEW
│   │   ├── useEmpleados.ts             # NEW
│   │   └── useLibros.ts                # NEW
│   ├── pages/
│   │   ├── LibroEntradaPage.tsx        # NEW
│   │   ├── LibroSalidaPage.tsx         # NEW
│   │   └── ConfiguracionPage.tsx       # MODIFY — add Escribanos + Empleados tabs
│   ├── components/
│   │   ├── escrituras/
│   │   │   └── EscrituraForm.tsx       # MODIFY — add cotización lookup button + date picker
│   │   ├── configuracion/
│   │   │   ├── EscribanosConfig.tsx    # NEW
│   │   │   └── EmpleadosConfig.tsx     # NEW
│   │   └── libros/
│   │       ├── LibroEntradaTable.tsx   # NEW
│   │       └── LibroSalidaTable.tsx    # NEW
│   └── components/layout/
│       └── Navbar.tsx                  # MODIFY — add Libro Entrada, Libro Salida links
```

**Structure Decision**: Extends the existing Web application structure (Option 2 from 001).
No new top-level directories. All additions are additive to `backend/src/` and `frontend/src/`.

---

## Plan Jerárquico

### Work Unit 1: Migración DB + Modelos — Escribano, Empleado, SueldoHistorico

**Propósito**: Crear los nuevos modelos ORM y la migración Alembic que transforma el campo
`Escritura.escribano` de ENUM hardcodeado a FK dinámica hacia la nueva tabla `Escribano`.

**Entidades afectadas**:
- `Escribano` (nueva — reemplaza el ENUM en `Escritura`)
- `Empleado` (nueva)
- `SueldoHistorico` (nueva)
- `Escritura` (modificada — `escribano` ENUM → `escribano_id` FK + `escribano_nombre` snapshot)

**Archivos a crear/modificar**:
- `backend/src/models/mixins.py` — `SoftDeleteMixin` con `deleted_at` + event listener global
- `backend/src/models/escribano.py` — ORM model con partial unique index
- `backend/src/models/empleado.py` — ORM models `Empleado` + `SueldoHistorico`
- `backend/src/models/escritura.py` — reemplazar `escribano` ENUM por `escribano_id` FK + `escribano_nombre` VARCHAR
- `backend/alembic/versions/004_platform_extensions.py` — migración: crear tablas, seed escribanos, migrar FK
- `backend/tests/unit/test_soft_delete.py` — TDD: validar que el event listener filtra filas deleted

**Subtareas internas**:
1. Escribir tests unitarios para `SoftDeleteMixin` (filtro activo, bypass con `include_deleted=True`) — FAIL
2. Implementar `SoftDeleteMixin` y registrar event listener en `database.py`
3. Implementar modelo `Escribano` con partial unique index
4. Implementar modelos `Empleado` + `SueldoHistorico`
5. Modificar `Escritura`: agregar `escribano_id FK`, `escribano_nombre VARCHAR`, mantener ENUM como columna legacy temporal
6. Escribir migración: crear tablas, insertar seed (Costanza, Gabriel, Victoria), migrar `escribano` ENUM → FK en filas existentes, drop ENUM column
7. Verificar migración en DB limpia y en DB con datos existentes

**Criterio de éxito**: Migración aplica en DB limpia y en DB con datos de feature 001.
Tests de soft delete pasan. Las escrituras existentes tienen `escribano_id` populado correctamente.

**Estimación**: 6 horas

---

### Work Unit 2: API de Cotización de Dólar (backend)

**Propósito**: Servicio backend que consulta ArgentinaDatos por fecha, cachea el resultado 8h,
y expone un endpoint autenticado que el frontend consume.

**Entidades afectadas**:
- Ninguna persistida — cotización es efímera (cache in-process)

**Archivos a crear/modificar**:
- `backend/src/services/cotizacion_service.py` — proxy + TTLCache por (casa, fecha)
- `backend/src/schemas/cotizacion.py` — DTOs request/response
- `backend/src/api/routes/cotizacion.py` — `GET /cotizacion?casa=bolsa&fecha=YYYY-MM-DD`
- `backend/tests/unit/test_cotizacion_service.py` — TDD: mock httpx, cache hit, error, valor cero
- `backend/tests/integration/test_cotizacion_api.py` — TDD: integración con mock externo

**Subtareas internas**:
1. Escribir unit tests: éxito, cache hit (sin llamada http), error red, fecha sin cotización, valor cero/negativo — FAIL
2. Implementar `cotizacion_service.py` con `TTLCache` + `httpx.AsyncClient` + fallback DolarAPI
3. Implementar schemas `CotizacionRequest` / `CotizacionResponse`
4. Implementar endpoint `GET /api/v1/cotizacion` con manejo de errores → 422/503
5. Agregar `COTIZACION_API_URL` y `COTIZACION_FALLBACK_URL` a `config.py` (Pydantic BaseSettings)
6. Tests de integración con `respx` (mock de httpx en tests)

**Criterio de éxito**: Tests pasan incluyendo: cache hit no llama httpx, error de red devuelve
mensaje descriptivo (no 500), valor cero/negativo devuelve error. Endpoint retorna 401 sin cookie.

**Estimación**: 5 horas

**Dependencias**: WU-1 (DB setup completado; auth de feature 001 ya operativo)

---

### Work Unit 3: API de Configuración — Escribanos

**Propósito**: CRUD completo para gestión de escribanos con soft delete, confirmación en
eliminación de escribanos con escrituras, y seed automático al primer arranque.

**Archivos a crear/modificar**:
- `backend/src/services/escribano_service.py` — CRUD + validación duplicados + soft delete
- `backend/src/schemas/escribano.py` — DTOs
- `backend/src/api/routes/escribanos.py` — `GET/POST /configuracion/escribanos`, `PATCH/DELETE /configuracion/escribanos/{id}`
- `backend/tests/integration/test_escribanos_api.py` — TDD

**Subtareas internas**:
1. Escribir integration tests: listar activos, crear, duplicado rechazado, desactivar sin escrituras, desactivar con escrituras (requiere confirmación), nombre inactivo reutilizable — FAIL
2. Implementar `EscribanoService.list_active()`, `create()`, `soft_delete()`
3. Implementar endpoints REST con flag `force=true` en DELETE para confirmar eliminación con escrituras
4. Verificar que selector de escribanos en escrituras solo muestra activos

**Criterio de éxito**: Tests pasan. DELETE sin `force=true` en escribano con escrituras retorna 409.
Un escribano inactivo con nombre "García" no bloquea crear otro con el mismo nombre.

**Estimación**: 4 horas

**Dependencias**: WU-1

---

### Work Unit 4: API de Configuración — Empleados y Sueldos

**Propósito**: CRUD para empleados con gestión de sueldos y snapshot histórico automático al
cerrar el mes. Seed automático de Graciela y Guadalupe con sueldos del fixture constitucional.

**Archivos a crear/modificar**:
- `backend/src/services/empleado_service.py` — CRUD + actualización de sueldo + generación SueldoHistorico
- `backend/src/schemas/empleado.py` — DTOs
- `backend/src/api/routes/empleados.py` — `GET/POST /configuracion/empleados`, `PATCH/DELETE /configuracion/empleados/{id}`
- `backend/tests/unit/test_empleado_service.py` — TDD: sueldo histórico, validación cero/negativo
- `backend/tests/integration/test_empleados_api.py` — TDD

**Subtareas internas**:
1. Escribir unit tests: crear empleado, modificar sueldo (nuevo valor vigente inmediato), sueldo cero rechazado, eliminar empleado, SueldoHistorico generado al cierre — FAIL
2. Implementar `EmpleadoService.create()`, `update_sueldo()`, `soft_delete()`
3. Integrar `update_sueldo()` en el cierre mensual de `LiquidacionService` (snapshot al cerrar)
4. Modificar `SalarioService` para leer sueldo del `Empleado` activo en lugar de `ConfiguracionFinanciera.salario_secretarias_total`
5. Seed: Graciela y Guadalupe con $1,000,000 ARS cada una

**Criterio de éxito**: Tests pasan. Modificar sueldo se refleja en `GET /salarios` del mes en
curso en < 2s (vía SSE cache invalidation). Meses cerrados conservan SueldoHistorico.

**Estimación**: 5 horas

**Dependencias**: WU-1; WU-3 (patrón establecido)

---

### Work Unit 5: Libros de Entrada y Salida (backend)

**Propósito**: Servicio que deriva las líneas del Libro de Entrada y Libro de Salida a partir
de los datos de FacturaPrincipal y GastoAdicional de las escrituras del mes seleccionado.

**Clasificación canónica**:
- **Entrada**: `honorario_principal`, `certificacion`, `GastoAdicional.direccion = 'entrada'`
- **Salida**: `tasa_3pm`, `sellos`, `tasa_75pm`, `firma_impuestos`, `art2_a`, `art12_a`, `art12_c`, `art12_f`, `total_gastos_admin` (ítems individuales), `GastoAdicional.direccion = 'salida'`

**Archivos a crear/modificar**:
- `backend/src/services/libros_service.py` — derivación + filtro por mes + totales
- `backend/src/schemas/libros.py` — `EntradaLibroDTO`, `SalidaLibroDTO`
- `backend/src/api/routes/libros.py` — `GET /libros/entrada?anio=&mes=`, `GET /libros/salida?anio=&mes=`
- `backend/tests/unit/test_libros_service.py` — TDD: derivación correcta, trazabilidad, totales
- `backend/tests/integration/test_libros_api.py` — TDD

**Subtareas internas**:
1. Escribir unit tests: entradas solo contienen honorarios+cert, salidas contienen impuestos, gastos adicionales clasificados por dirección, total correcto, cada línea contiene escritura_id + nombre + hiperlink — FAIL
2. Implementar `LibrosService.get_libro_entrada(anio, mes)` y `get_libro_salida(anio, mes)`
3. Implementar endpoints con filtro mes/año (default: mes en curso)
4. Extender publisher SSE para emitir evento `libros_updated` en cambios de escritura
5. Verificar que ambos libros usan el mismo criterio de scoping que la Liquidación Mensual

**Criterio de éxito**: Tests de derivación pasan. Cada línea contiene `escritura_id`,
`escritura_nombre`, `concepto` y `monto`. El total del libro cuadra con la suma manual de
los ítems de las escrituras del mes.

**Estimación**: 5 horas

**Dependencias**: WU-1, feature 001 WU-3 (escrituras API operativo)

---

### Work Unit 6: Frontend — Cotización en EscrituraForm

**Propósito**: Agregar botón "Consultar cotización" con date picker al formulario de
escrituras. Los campos MEP y Banco Nación siguen siendo editables manualmente.

**Archivos a crear/modificar**:
- `frontend/src/api/cotizacion.ts` — cliente para `GET /cotizacion`
- `frontend/src/hooks/useCotizacion.ts` — query hook
- `frontend/src/components/escrituras/EscrituraForm.tsx` — MODIFY: date picker + botón + manejo de error

**Subtareas internas**:
1. Implementar `useCotizacion` hook con estado: idle / loading / success / error
2. Agregar `DatePicker` (nativo `<input type="date">`, default hoy) al formulario
3. Agregar botón "Consultar cotización" que dispara el hook
4. En éxito: poblar campos MEP y Nación (editables post-populated)
5. En error: mostrar mensaje descriptivo, no bloquear formulario
6. En fecha sin cotización: mensaje "Sin datos para esa fecha"

**Criterio de éxito**: SC-001 verificado (cotización en < 5s). Si la API falla, la secretaria
puede escribir los valores manualmente sin fricción adicional.

**Estimación**: 4 horas

**Dependencias**: WU-2 (endpoint cotización operativo)

---

### Work Unit 7: Frontend — Configuración de Escribanos y Empleados

**Propósito**: Expandir `ConfiguracionPage` con dos tabs: Escribanos (CRUD con soft delete
y confirmación) y Empleados (CRUD con edición de sueldo).

**Archivos a crear/modificar**:
- `frontend/src/api/escribanos.ts`, `frontend/src/api/empleados.ts`
- `frontend/src/hooks/useEscribanos.ts`, `frontend/src/hooks/useEmpleados.ts`
- `frontend/src/components/configuracion/EscribanosConfig.tsx` — lista + agregar + desactivar con modal
- `frontend/src/components/configuracion/EmpleadosConfig.tsx` — lista + agregar + editar sueldo + eliminar
- `frontend/src/pages/ConfiguracionPage.tsx` — MODIFY: add tabs Escribanos / Empleados

**Subtareas internas**:
1. Implementar `EscribanosConfig`: lista de activos, form de nuevo escribano, botón desactivar con modal de confirmación (doble paso si tiene escrituras)
2. Implementar `EmpleadosConfig`: lista con sueldo actual, inline edit sueldo, form nuevo empleado, eliminar
3. Validación cliente: nombre vacío, sueldo ≤ 0 bloqueado con mensaje
4. Optimistic updates vía TanStack Query invalidation en cada mutación
5. Etiqueta "(inactivo)" en vistas donde escribano desactivado aparece en escrituras históricas

**Criterio de éxito**: SC-004 verificado (agregar/eliminar en < 60s). Sueldo modificado se
refleja en Pago de Salarios en < 2s (SC-005).

**Estimación**: 5 horas

**Dependencias**: WU-3, WU-4 (APIs operativas)

---

### Work Unit 8: Frontend — Libro de Entrada y Libro de Salida

**Propósito**: Dos nuevas páginas con tabla filtrable por mes, total acumulado, y hipervínculo
por escritura de origen. Actualizaciones en tiempo real vía SSE.

**Archivos a crear/modificar**:
- `frontend/src/api/libros.ts`
- `frontend/src/hooks/useLibros.ts`
- `frontend/src/components/libros/LibroEntradaTable.tsx`
- `frontend/src/components/libros/LibroSalidaTable.tsx`
- `frontend/src/pages/LibroEntradaPage.tsx`
- `frontend/src/pages/LibroSalidaPage.tsx`
- `frontend/src/components/layout/Navbar.tsx` — MODIFY: agregar Libro Entrada / Libro Salida
- `frontend/src/App.tsx` — MODIFY: rutas `/libro-entrada`, `/libro-salida`

**Subtareas internas**:
1. Implementar `LibroEntradaTable` y `LibroSalidaTable` con columnas: Concepto, Monto, Escritura (link), Fecha escritura
2. Implementar selector de mes/año (default: mes en curso)
3. Mostrar total acumulado al pie de cada tabla
4. Integrar SSE: re-fetch on `libros_updated` event
5. Implementar hipervínculo de cada fila a `EscrituraDetail`
6. Agregar entradas de navegación en Navbar

**Criterio de éxito**: SC-002 y SC-003 verificados (100% de líneas con hipervínculo funcional).
SC-007 verificado (actualización en < 2s al crear/editar escritura).

**Estimación**: 5 horas

**Dependencias**: WU-5 (APIs operativas), WU-7 (Navbar actualizado)

---

### Notas para Itti-Kit

**Total Work Units**: 8  
**Tiempo total estimado**: ~39 horas  
**Work Units paralelas posibles**:
- WU-2 (cotización API) puede comenzar en paralelo con WU-3 y WU-4 (todos dependen de WU-1)
- WU-6 y WU-7 y WU-8 (frontend) pueden avanzar en paralelo una vez sus WUs de backend respectivas están listas
- WU-3 y WU-4 son independientes entre sí (mismo patrón, módulos distintos)

**Orden crítico**:
```
WU-1 (DB + modelos) ──► WU-2 (cotización)   ──► WU-6 (frontend cotización)
                    ──► WU-3 (escribanos)    ──► WU-7 (frontend config)
                    ──► WU-4 (empleados)     ──► WU-7 (frontend config)
                    ──► WU-5 (libros)        ──► WU-8 (frontend libros)
```

---

## Complexity Tracking

No violations of constitutional principles detected.

| Decision | Justification |
|---|---|
| `cachetools.TTLCache` in-process (no Redis) | Single Fargate task, < 10 users. Redis would add ~$15/month standing cost with no benefit at this scale. Cache is lost on redeploy — acceptable since rates are re-fetched on next query. |
| `escribano_nombre` snapshot on `Escritura` | Soft delete makes `Escribano` invisible via `with_loader_criteria`. Snapshotting the name at creation ensures display resilience for historical escrituras without bypassing the global soft-delete filter on every read. |
| Libros as computed views (no persistence) | At < 200 escrituras/month, deriving Libro lines on-read is trivial. Persisting them would require maintaining consistency with FacturaPrincipal mutations — extra complexity with no performance benefit at this scale. |
| Single Alembic migration for all 4 new entities | The entities are interdependent (Escritura FK migration requires Escribano table to exist first). A single migration with explicit ordering is cleaner than 4 separate migrations that must be applied in sequence. |
