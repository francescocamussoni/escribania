# Tasks: Plataforma Contable — Escribanía

**Input**: Design documents from `specs/001-plataforma-contaduria/`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/openapi.yaml ✅  
**Testing Strategy**: TDD completo — tests escritos y en estado FAILING antes de cada implementación  
**Branch**: `001-plataforma-contaduria`

> No se usa Figma en este proyecto. El frontend se implementa directamente siguiendo la spec y el plan.
> Todas las tareas (backend + frontend) están desbloqueadas.

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1–US4)
- TDD tasks marked with 🔴 must FAIL before the paired implementation task runs

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding, tooling, Docker, environment config.

- [x] T001 Initialize backend Python project with `pyproject.toml` (FastAPI, SQLAlchemy 2.0, asyncpg, Alembic, Pydantic v2, pytest, pytest-asyncio, argon2-cffi) in `backend/`
- [x] T002 [P] Initialize frontend project with Vite + React 18 + TypeScript in `frontend/`
- [x] T003 [P] Create `docker-compose.yml` with services: `db` (postgres:16), `backend` (port 8000), `frontend` (port 5173)
- [x] T004 [P] Create `.env.example` with all required environment variables (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, JWT_SECRET, JWT_EXPIRY_HOURS, ENVIRONMENT, CORS_ORIGINS)
- [x] T005 [P] Create `backend/Dockerfile` (python:3.12-slim, non-root user, health check)
- [x] T006 [P] Create `frontend/Dockerfile` (node:20-alpine, multi-stage: build + nginx serve)
- [x] T007 [P] Configure Alembic in `backend/alembic.ini` and `backend/alembic/env.py` (async engine)
- [x] T008 [P] Configure pytest in `backend/pyproject.toml` (asyncio_mode=auto, test paths)
- [x] T009 [P] Configure Vitest in `frontend/vite.config.ts`
- [x] T010 [P] Create `backend/src/config.py` (Pydantic BaseSettings reading all env vars)
- [x] T011 [P] Create `backend/src/database.py` (async engine factory + AsyncSession dependency)
- [x] T012 [P] Create `backend/src/main.py` (FastAPI app factory, CORS middleware, router inclusion, /health endpoint)

**Checkpoint**: `docker compose up` starts all services. `GET /api/v1/health` returns 200.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, calculation engine, and auth — MUST complete before any user story.

> ⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

### 2a — DB Schema (all entities)

- [x] T013 Create SQLAlchemy ORM model `ConfiguracionFinanciera` in `backend/src/models/configuracion.py` (all rate/amount columns as NUMERIC, versioned insert-only)
- [x] T014 [P] Create SQLAlchemy ORM model `Usuario` in `backend/src/models/usuario.py` (UUID pk, username unique, hashed_password, activo, last_login_at)
- [x] T015 [P] Create SQLAlchemy ORM model `Escritura` in `backend/src/models/escritura.py` (FK to ConfiguracionFinanciera, estado enum, escribano enum, created_at index)
- [x] T016 [P] Create SQLAlchemy ORM model `FacturaPrincipal` in `backend/src/models/factura_principal.py` (all calculated amount columns NUMERIC(18,2), 1:1 with Escritura)
- [x] T017 [P] Create SQLAlchemy ORM model `GastoAdicional` in `backend/src/models/gasto_adicional.py` (FK Escritura, direccion enum)
- [x] T018 [P] Create SQLAlchemy ORM model `LiquidacionMensual` in `backend/src/models/liquidacion.py` (unique anio+mes constraint)
- [x] T019 [P] Create SQLAlchemy ORM model `PagoSalario` in `backend/src/models/liquidacion.py` (FK LiquidacionMensual, detalle_json JSONB)
- [x] T020 Write Alembic migration `backend/alembic/versions/001_initial_schema.py` creating all tables with constraints, indexes, and FK relationships
- [x] T021 Write seed script `backend/scripts/seed_config.py` inserting ConfiguracionFinanciera v1 with all canonical values from constitution.md §5
- [x] T022 Write user creation script `backend/scripts/create_user.py` (Argon2id hash, CLI args)
- [x] T023 Create `backend/src/models/__init__.py` exporting all models

**Checkpoint**: `alembic upgrade head` applies cleanly on empty DB. Seed script inserts config v1.

### 2b — Calculation Engine (TDD core)

- [x] T024 🔴 Write unit tests for `calculo_factura.py` in `backend/tests/unit/test_calculo_factura.py` using canonical USD 105,000 fixture — assert EXACT values for all 30+ output fields. Tests MUST FAIL before T025.
- [x] T025 Implement pure calculation engine `backend/src/services/calculo_factura.py` — functions: `calcular_bases()`, `calcular_honorarios()`, `calcular_leyes_notariales()`, `calcular_impuestos()`, `calcular_gastos_admin()`, `calcular_factura_completa()`. All pass T024.
- [x] T026 [P] Write unit tests for edge cases in `backend/tests/unit/test_calculo_factura_edge.py`: zero/negative inputs rejected; minimum values enforced (honorario_min, cinco_pct_hon_min, art12_a_min). Tests MUST FAIL before T027.
- [x] T027 [P] Implement input validation and minimum enforcement in `backend/src/services/calculo_factura.py` until T026 passes.
- [x] T028 [P] Create `backend/src/schemas/factura.py` (Pydantic v2 FacturaPrincipalResponse DTO — all fields as Decimal/str, no ORM objects exposed)
- [x] T029 [P] Create `backend/src/schemas/configuracion.py` (ConfiguracionResponse and ConfiguracionInput DTOs)

**Checkpoint**: `pytest tests/unit/` — all 30+ canonical fixture assertions pass.

### 2c — Auth Foundation

- [x] T030 🔴 Write integration tests for auth in `backend/tests/integration/test_auth_api.py`: login success sets HttpOnly cookie; login failure returns 401; /me with valid cookie returns user; /me without cookie returns 401; logout clears cookie. Tests MUST FAIL before T031.
- [x] T031 Create `backend/src/schemas/auth.py` (LoginInput, UserResponse DTOs)
- [x] T032 Implement `backend/src/api/routes/auth.py` (POST /auth/login with Argon2id verify + JWT sign in cookie, POST /auth/logout, GET /auth/me)
- [x] T033 Implement `backend/src/api/deps.py` — `get_current_user` dependency: extract JWT from cookie, validate signature + expiry, return user or raise 401
- [x] T034 Apply `get_current_user` dependency to all routers except /health and /auth/login in `backend/src/api/router.py` until T030 passes
- [x] T035 [P] Create `backend/src/api/router.py` registering all route modules under `/api/v1`

**Checkpoint**: Auth integration tests pass. Any endpoint without cookie returns 401.

---

## Phase 3: User Story 1 — Gestión de Escrituras (Priority: P1) 🎯 MVP

**Goal**: Secretary can create escrituras with auto-calculated invoices, add expenses, filter, edit, and close them.

**Independent Test**: Create a new escritura with USD 105,000 fixture values → all invoice amounts match constitution exactly. Add a gasto adicional. Close it → returns 409 on subsequent PATCH.

### Tests for US1 ⚠️ Write FIRST — must FAIL before implementation

- [x] T036 🔴 [US1] Write integration tests `backend/tests/integration/test_escrituras_api.py`:
  - POST /escrituras creates escritura + auto-calculates FacturaPrincipal with exact values
  - GET /escrituras returns list; filters by estado, escribano, anio, mes
  - GET /escrituras/{id} returns full detail with factura and gastos
  - PATCH /escrituras/{id} on open escritura recalculates factura
  - PATCH /escrituras/{id} on closed escritura returns 409
  - POST /escrituras/{id}/close sets estado=cerrada and closed_at
  - Tests MUST FAIL before T037

### Implementation for US1

- [x] T037 [US1] Create `backend/src/schemas/escritura.py` (EscrituraInput, EscrituraResponse, EscrituraListItem DTOs — no ORM objects)
- [x] T038 [US1] Create `backend/src/schemas/gasto.py` (GastoAdicionalInput, GastoAdicionalResponse DTOs)
- [x] T039 [US1] Implement `backend/src/services/escritura_service.py`:
  - `create_escritura()` — fetches active config, runs calculo_factura, persists Escritura + FacturaPrincipal atomically
  - `update_escritura()` — validates open state, recalculates, persists
  - `close_escritura()` — sets estado=cerrada, closed_at, freezes factura
  - `get_escritura()`, `list_escrituras()` with filters
- [x] T040 [US1] Implement `backend/src/api/routes/escrituras.py` (GET /escrituras, POST /escrituras, GET /escrituras/{id}, PATCH /escrituras/{id}, POST /escrituras/{id}/close) per OpenAPI contract
- [x] T041 [US1] Implement `backend/src/api/routes/gastos.py` (POST /escrituras/{id}/gastos — validates open state, appends GastoAdicional)
- [x] T042 [US1] Run T036 tests — all must pass. Fix until green.

**Checkpoint**: US1 fully functional and independently testable. `pytest tests/integration/test_escrituras_api.py` green.

---

## Phase 4: User Story 2 — Liquidación Mensual (Priority: P2)

**Goal**: Secretary sees consolidated monthly summary grouped by escribano, with real-time updates and drill-down to escritura.

**Independent Test**: With 2+ escrituras in current month (one open, one closed-same-month), GET /liquidacion shows correct totals per escribano. A 3rd escritura from previous month (closed) does NOT appear.

### Tests for US2 ⚠️ Write FIRST — must FAIL before implementation

- [x] T043 🔴 [US2] Write unit tests `backend/tests/unit/test_liquidacion.py`:
  - Escritura created in month M (open) → included in month M
  - Escritura created in month M (closed same month) → included in month M
  - Escritura created in month M-1 (closed) → NOT included in month M
  - Per-escribano totals = sum(honorario_principal + certificacion) for their escrituras
  - Tests MUST FAIL before T044
- [x] T044 🔴 [US2] Write integration tests `backend/tests/integration/test_liquidacion_api.py`:
  - GET /liquidacion?anio=X&mes=Y returns correct LiquidacionResumen
  - Each LiquidacionEscrituraItem contains escritura_id for traceability
  - Tests MUST FAIL before T045

### Implementation for US2

- [x] T045 [US2] Create `backend/src/schemas/liquidacion.py` (LiquidacionResumen, LiquidacionEscribano, LiquidacionEscrituraItem DTOs)
- [x] T046 [US2] Implement `backend/src/services/liquidacion_service.py`:
  - `get_liquidacion_mensual(anio, mes)` — queries escrituras by created_at range, groups by escribano, computes totals
  - Enforces inclusion rule: created_at in month M regardless of estado
- [x] T047 [US2] Implement `backend/src/api/routes/liquidacion.py` (GET /liquidacion with anio+mes query params) until T043+T044 pass

**Checkpoint**: US1 + US2 independently functional. `pytest tests/unit/test_liquidacion.py tests/integration/test_liquidacion_api.py` green.

---

## Phase 5: User Story 3 — Pago de Salarios (Priority: P3)

**Goal**: Secretary sees per-escribano salary breakdown with traceable escritura references, and fixed salary split for secretarias.

**Independent Test**: With escrituras assigned to Costanza and Gabriel, GET /salarios shows correct amounts per escribano with escritura list, and Graciela + Guadalupe each show salario_secretarias_total/2.

### Tests for US3 ⚠️ Write FIRST — must FAIL before implementation

- [x] T048 🔴 [US3] Write unit tests `backend/tests/unit/test_salario.py`:
  - Escribano payment = sum(honorario_principal + certificacion) per assigned escritura in month
  - Secretaria payment = salario_secretarias_total / 2 from active config
  - PagoEscribano.escrituras list contains escritura_id for each entry
  - Tests MUST FAIL before T049
- [x] T049 🔴 [US3] Write integration tests: GET /salarios returns PagoSalariosResumen with both escribanos and secretarias. Tests MUST FAIL before T050.

### Implementation for US3

- [x] T050 [US3] Create `backend/src/schemas/salarios.py` (PagoSalariosResumen, PagoEscribano, PagoSecretaria DTOs)
- [x] T051 [US3] Implement `backend/src/services/salario_service.py`:
  - `get_pagos_mensuales(anio, mes)` — builds PagoEscribano per escribano with detalle list + PagoSecretaria entries
  - Sources secretaria salary from active ConfiguracionFinanciera
- [x] T052 [US3] Implement `backend/src/api/routes/salarios.py` (GET /salarios) until T048+T049 pass

**Checkpoint**: US1 + US2 + US3 independently functional. All unit + integration tests green.

---

## Phase 6: User Story 4 — SSE Real-Time + Configuración (Priority: P3b)

**Goal**: All changes to escrituras propagate in real time to liquidación and salarios views. Config is updatable without code changes.

**Independent Test**: Subscribe to GET /events in one client; create an escritura in another → receive `escritura.created` event within 2 seconds.

- [x] T053 [US4] Implement PostgreSQL LISTEN/NOTIFY publisher in `backend/src/events/publisher.py`:
  - `publish(event_type, payload)` sends NOTIFY on channel `escribania_events`
  - Call from escritura_service on create/update/close and gastos on create
- [x] T054 [US4] Implement SSE endpoint in `backend/src/api/routes/events.py`:
  - GET /events streams `text/event-stream`
  - Subscribes to PG NOTIFY channel via asyncpg `LISTEN`
  - Each NOTIFY → sends SSE event to all connected clients
- [x] T055 [US4] Implement `backend/src/services/config_service.py`:
  - `get_active_config()` — returns row with highest version
  - `create_config_version(data)` — inserts new row, never UPDATE
  - `list_config_history()` — returns all versions ordered by version desc
- [x] T056 [US4] Implement `backend/src/api/routes/configuracion.py` (GET /configuracion, POST /configuracion, GET /configuracion/history)

**Checkpoint**: SSE stream receives events when escrituras change. Config POST creates a new version row. Old escrituras still reference prior config version FK.

---

## Phase 7: Frontend — Auth + Layout + SSE Hook

- [x] T057 [US4] Implement `frontend/src/api/client.ts` — fetch wrapper with cookie credentials, base URL from env, error handling
- [x] T058 [US4] Implement `frontend/src/pages/LoginPage.tsx` — username/password form, calls POST /auth/login
- [x] T059 [US4] Implement `frontend/src/components/layout/Navbar.tsx` — 3 nav links (Escrituras, Liquidación, Pago de Salarios)
- [x] T060 [US4] Implement `frontend/src/components/layout/Layout.tsx` — wraps pages, includes Navbar, auth guard redirect
- [x] T061 [P] [US4] Implement `frontend/src/hooks/useSSE.ts` — EventSource hook subscribing to /api/v1/events; on event invalidates React Query cache for affected resource
- [x] T062 [P] [US4] Implement `frontend/src/App.tsx` — React Router v6 routes: `/login`, `/escrituras`, `/escrituras/:id`, `/liquidacion`, `/salarios`, `/configuracion` (all protected except /login)

---

## Phase 8: Frontend — Sección Escrituras (US1)

- [x] T063 [US1] Implement `frontend/src/api/escrituras.ts` — typed fetch wrappers for all escrituras + gastos endpoints
- [x] T064 [US1] Implement `frontend/src/hooks/useEscrituras.ts` — React Query hooks: useEscrituras(filters), useEscritura(id), useCreateEscritura, usePatchEscritura, useCloseEscritura, useAddGasto
- [x] T065 [US1] Implement `frontend/src/pages/EscriturasPage.tsx` — list with filter tabs (Todas / Abiertas / Cerradas) and "Nueva Escritura" button
- [x] T066 [US1] Implement `frontend/src/components/escrituras/EscrituraList.tsx` — table/cards showing nombre, escribano, estado, total_factura; click → detail
- [x] T067 [US1] Implement `frontend/src/components/escrituras/EscrituraForm.tsx` — form for nueva/edit: nombre, USD, dolar_mep, dolar_nacion, escribano selector
- [x] T068 [US1] Implement `frontend/src/pages/EscrituraDetail.tsx` — full detail view: factura breakdown table + gastos list + close button
- [x] T069 [US1] Implement `frontend/src/components/escrituras/FacturaDetalle.tsx` — structured breakdown matching Google Sheets layout (honorarios, leyes, impuestos, gastos fijos sections)
- [x] T070 [US1] Implement `frontend/src/components/escrituras/GastoForm.tsx` — inline form: concepto, monto, direccion (entrada/salida), fecha

---

## Phase 9: Frontend — Liquidación y Salarios (US2 + US3)

- [x] T071 [US2] Implement `frontend/src/api/liquidacion.ts` + `frontend/src/api/salarios.ts` — typed fetch wrappers
- [x] T072 [US2] Implement `frontend/src/hooks/useLiquidacion.ts` + `frontend/src/hooks/useSalarios.ts` — React Query hooks with month/year params
- [x] T073 [US2] Implement `frontend/src/pages/LiquidacionPage.tsx` — month selector + resumen cards per escribano
- [x] T074 [US2] Implement `frontend/src/components/liquidacion/LiquidacionResumen.tsx` — totals header (total global + per escribano)
- [x] T075 [US2] Implement `frontend/src/components/liquidacion/EscribanoCard.tsx` — expandable card: list of escrituras with honorario + certificacion + link to detail
- [x] T076 [US3] Implement `frontend/src/pages/SalariosPage.tsx` — month selector + escribano cards + secretarias section
- [x] T077 [US3] Implement `frontend/src/components/salarios/PagoEscribanoCard.tsx` — nombre, monto_total, list of linked escrituras
- [x] T078 [US3] Implement `frontend/src/components/salarios/PagoSecretariaCard.tsx` — nombre, monto, base_total display

---

## Phase 10: Frontend — Configuración + Polish

- [x] T079 [US4] Implement `frontend/src/api/configuracion.ts` — typed fetch wrappers for config endpoints
- [x] T080 [US4] Implement `frontend/src/pages/ConfiguracionPage.tsx` — form showing all numeric config fields; save creates new version
- [x] T081 [P] Polish error and validation messages across all forms (user-friendly Spanish, no technical terms)
- [x] T082 [P] Add loading states and empty states to all list views (Escrituras, Liquidación, Salarios)
- [x] T083 [P] Validate SC-001: walkthrough crear escritura completa en < 3 min as new user
- [x] T084 [P] Validate SC-003: SSE update reaches Liquidación within 2s of escritura creation (manual + automated check)

---

## Phase 11: Polish & Cross-Cutting Concerns

- [x] T085 [P] Write `backend/tests/integration/test_sse_events.py` — assert SSE events emitted on escritura create/close and gasto create
- [x] T086 [P] Write `backend/tests/integration/test_config_api.py` — assert POST /configuracion creates new version; old escritura FKs unchanged
- [x] T087 [P] Add structured JSON logging to backend (request ID, user ID, action, result; no PII in logs) in `backend/src/main.py`
- [x] T088 [P] Add request size limits and rate limiting to FastAPI app in `backend/src/main.py`
- [x] T089 [P] Create `backend/tests/conftest.py` with async test DB fixtures (create/teardown per test, seed config v1)
- [x] T090 [P] Validate quickstart.md end-to-end: run all steps from scratch on clean machine; update any outdated commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2a (DB Schema)**: Depends on Phase 1 completion
- **Phase 2b (Calc Engine)**: Depends on Phase 1; can run in parallel with Phase 2a
- **Phase 2c (Auth)**: Depends on Phase 2a (needs Usuario model + DB)
- **Phase 3 (US1 — Escrituras)**: Depends on ALL of Phase 2
- **Phase 4 (US2 — Liquidación)**: Depends on Phase 3 (needs escrituras data)
- **Phase 5 (US3 — Salarios)**: Depends on Phase 3; can run in parallel with Phase 4
- **Phase 6 (US4 — SSE + Config)**: Depends on Phase 3
- **Phase 7–10 (Frontend)**: Depends on Phase 2c (auth API); can proceed with API mocks while backend phases 3–6 build
- **Phase 11 (Polish)**: Depends on all prior phases

### Backend Parallel Opportunities

```bash
# Phase 2 — run in parallel:
Task: "DB Schema" (T013–T023)
Task: "Calculation Engine TDD" (T024–T029)   # independent of DB

# Phase 3–5 — once Phase 2 done, US1 first, then US2+US3 in parallel:
Task: "US2 Liquidación" (T043–T047)
Task: "US3 Salarios"    (T048–T052)
```

### Frontend Parallel Opportunities

```bash
# Once backend auth (Phase 2c) is done:
Task: "Frontend Layout + SSE" (T057–T062)     # can use API mocks

# Once T057–T062 done:
Task: "Frontend Escrituras" (T063–T070)
Task: "Frontend Liquidación+Salarios" (T071–T078)  # in parallel
```

---

## Implementation Strategy

### MVP First (Backend only — US1 + canonical tests)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (DB + Calc Engine + Auth)
3. Complete Phase 3: US1 Escrituras API
4. **STOP and VALIDATE**: `pytest tests/` all green; canonical fixture matches to the cent
5. Backend MVP: fully functional via API docs (Swagger UI at /docs)

### Incremental Delivery

1. Phase 1+2 → Foundation ready
2. Phase 3 → Escrituras API ✅ → Validate with curl/Swagger
3. Phase 4+5 → Liquidación + Salarios APIs ✅ → Validate
4. Phase 6 → SSE + Config ✅
5. Phase 7–10 → Full frontend
6. Phase 11 → Polish + smoke test on AWS

---

## Notes

- 🔴 Tasks marked with 🔴 MUST be written and confirmed FAILING before the paired implementation
- [P] = different files, no blocking dependencies, can run in parallel
- All monetary amounts use `NUMERIC(18,2)` / `Decimal` — never `float`
- All UUIDs generated server-side; never trust client-supplied IDs for new resources
- Total backend tasks: 56 | Total frontend tasks: 28 | Total: 84
