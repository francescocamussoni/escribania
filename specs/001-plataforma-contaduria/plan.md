# Implementation Plan: Plataforma Contable — Escribanía

**Branch**: `001-plataforma-contaduria` | **Date**: 2026-07-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-plataforma-contaduria/spec.md`

---

## Summary

Build a fullstack internal accounting platform for a notary office. Secretaries
manage property deeds (escrituras), each with an auto-calculated invoice (factura
principal) based on Argentine notarial fee formulas. The platform provides monthly
settlement (liquidación) and salary payment views that update in real time as
escrituras change. Backend: Python/FastAPI with PostgreSQL. Frontend: React/Vite SPA.
Deployed on AWS ECS Fargate (private VPC) + RDS + S3/CloudFront.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async + asyncpg, Alembic, Pydantic v2 (backend); React + Vite, React Query / TanStack Query (frontend)  
**Storage**: PostgreSQL 16 — local: Docker container; prod: AWS RDS db.t4g.micro  
**Testing**: pytest + pytest-asyncio (backend, TDD); Vitest (frontend unit tests)  
**Target Platform**: Linux container (ECS Fargate, private subnet); static assets on S3 + CloudFront  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: SSE updates ≤ 2s end-to-end; API p95 < 500ms; UI first paint < 2s on LAN  
**Constraints**: ≤ USD 50/month AWS standing cost; no public IP on API; no polling; calculation results must match constitutional fixture to the cent  
**Scale/Scope**: < 10 concurrent users; < 200 escrituras/month; internal office use

---

## Constitution Check

*GATE: Must pass before implementation. Re-check after data model design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments (local ↔ AWS) | ✅ Pass | Docker Compose mirrors ECS+RDS; env-vars only for config differences |
| P2 — Cost-conscious AWS | ✅ Pass | ECS Fargate 0.25vCPU + RDS t4g.micro + S3/CF; est. $15–25/mo |
| P3 — Python backend | ✅ Pass | FastAPI chosen |
| P4 — Frontend UX + 3 sections | ✅ Pass | React SPA; Escrituras, Liquidación, Pago de Salarios |
| P5 — Real-time via SSE/WS, no polling | ✅ Pass | SSE via FastAPI StreamingResponse + PG LISTEN/NOTIFY |
| P6 — Formula integrity, pure functions | ✅ Pass | Calculation engine in pure Python; canonical fixture in tests |
| P7 — Security baseline | ✅ Pass | JWT in HttpOnly cookies; Pydantic DTOs; env-injected secrets; private VPC |
| P8 — Traceability | ✅ Pass | PagoSalario.detalle_json links every payment line to escritura_id |

**Result**: All gates pass. Implementation may proceed.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-plataforma-contaduria/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── openapi.yaml     # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/spec-kitti.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   ├── main.py                    # FastAPI app factory
│   ├── config.py                  # Settings (Pydantic BaseSettings)
│   ├── database.py                # Async engine + session factory
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── escritura.py
│   │   ├── factura_principal.py
│   │   ├── gasto_adicional.py
│   │   ├── configuracion.py
│   │   ├── liquidacion.py
│   │   └── usuario.py
│   ├── schemas/                   # Pydantic v2 DTOs (request/response)
│   │   ├── escritura.py
│   │   ├── factura.py
│   │   ├── gasto.py
│   │   ├── liquidacion.py
│   │   ├── salarios.py
│   │   ├── configuracion.py
│   │   └── auth.py
│   ├── services/                  # Business logic
│   │   ├── calculo_factura.py     # Pure calculation engine (TDD core)
│   │   ├── escritura_service.py
│   │   ├── liquidacion_service.py
│   │   ├── salario_service.py
│   │   └── config_service.py
│   ├── api/
│   │   ├── deps.py                # Auth dependency injection
│   │   ├── router.py              # Main router
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── escrituras.py
│   │       ├── gastos.py
│   │       ├── liquidacion.py
│   │       ├── salarios.py
│   │       ├── configuracion.py
│   │       └── events.py          # SSE endpoint
│   └── events/
│       └── publisher.py           # PG LISTEN/NOTIFY pub/sub
├── tests/
│   ├── unit/
│   │   ├── test_calculo_factura.py  # TDD — canonical fixture tests
│   │   ├── test_liquidacion.py
│   │   └── test_salario.py
│   ├── integration/
│   │   ├── test_escrituras_api.py
│   │   ├── test_liquidacion_api.py
│   │   └── test_auth_api.py
│   └── conftest.py
├── scripts/
│   ├── seed_config.py
│   └── create_user.py
├── Dockerfile
├── pyproject.toml
└── alembic.ini

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/                       # API client (fetch wrappers)
│   │   ├── client.ts
│   │   ├── escrituras.ts
│   │   ├── liquidacion.ts
│   │   ├── salarios.ts
│   │   └── configuracion.ts
│   ├── hooks/
│   │   ├── useSSE.ts              # SSE subscription hook
│   │   ├── useEscrituras.ts
│   │   ├── useLiquidacion.ts
│   │   └── useSalarios.ts
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── EscriturasPage.tsx
│   │   ├── EscrituraDetail.tsx
│   │   ├── LiquidacionPage.tsx
│   │   ├── SalariosPage.tsx
│   │   └── ConfiguracionPage.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   └── Layout.tsx
│   │   ├── escrituras/
│   │   │   ├── EscrituraForm.tsx
│   │   │   ├── EscrituraList.tsx
│   │   │   ├── FacturaDetalle.tsx
│   │   │   └── GastoForm.tsx
│   │   ├── liquidacion/
│   │   │   ├── LiquidacionResumen.tsx
│   │   │   └── EscribanoCard.tsx
│   │   └── salarios/
│   │       ├── PagoEscribanoCard.tsx
│   │       └── PagoSecretariaCard.tsx
│   └── types/
│       └── api.ts                 # TypeScript types from OpenAPI schema
├── tests/
│   └── unit/
│       └── test_calculo_display.test.tsx
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json

docker-compose.yml
docker-compose.prod.yml
.env.example
```

**Structure Decision**: Web application (Option 2) — separate `backend/` and `frontend/`
directories. Backend is a Python FastAPI app; frontend is a React/Vite SPA.

---

## Plan Jerárquico

### Work Unit 1: Motor de Cálculo y Base de Datos

**Propósito**: Implementar el motor de cálculo puro de la factura principal y el schema
de base de datos completo. Es la fundación de todo lo demás.

**Entidades afectadas**:
- `ConfiguracionFinanciera` (nueva — tabla de parámetros versionados)
- `Escritura` (nueva)
- `FacturaPrincipal` (nueva)

**Archivos a crear/modificar**:
- `backend/src/services/calculo_factura.py` — motor de cálculo puro (sin efectos secundarios)
- `backend/src/models/configuracion.py` — ORM model
- `backend/src/models/escritura.py` — ORM model
- `backend/src/models/factura_principal.py` — ORM model
- `backend/alembic/versions/001_initial_schema.py` — migración inicial
- `backend/tests/unit/test_calculo_factura.py` — TDD: canonical fixture tests (FAIL first)

**Subtareas internas**:
1. Escribir tests unitarios para `calculo_factura.py` usando el fixture de USD 105,000 (FAIL)
2. Implementar `calculo_factura.py` como funciones puras hasta que todos los tests pasen
3. Crear ORM models: `ConfiguracionFinanciera`, `Escritura`, `FacturaPrincipal`
4. Escribir migración Alembic inicial con todos los constraints
5. Verificar migración local con `alembic upgrade head`
6. Seed script para `ConfiguracionFinanciera` con valores del fixture

**Criterio de éxito**: Todos los tests de `test_calculo_factura.py` pasan con valores
exactos del fixture constitucional. Migración aplica sin errores en DB limpia.

**Estimación**: 8 horas

---

### Work Unit 2: API de Autenticación

**Propósito**: Implementar login/logout con JWT en HttpOnly cookies. Prerequisito para
todos los endpoints protegidos.

**Entidades afectadas**:
- `Usuario` (nueva)

**Archivos a crear/modificar**:
- `backend/src/models/usuario.py`
- `backend/src/schemas/auth.py`
- `backend/src/api/routes/auth.py`
- `backend/src/api/deps.py` — `get_current_user` dependency
- `backend/alembic/versions/002_usuarios.py`
- `backend/tests/integration/test_auth_api.py` — TDD (FAIL first)
- `backend/scripts/create_user.py`

**Subtareas internas**:
1. Escribir integration tests para login/logout/me (FAIL)
2. Crear modelo `Usuario` con Argon2id password hashing
3. Implementar `/auth/login`, `/auth/logout`, `/auth/me`
4. Implementar `get_current_user` dependency con JWT cookie validation
5. Aplicar dependency a todos los routers (guard all routes except /health)

**Criterio de éxito**: Tests de auth pasan. Endpoint sin cookie devuelve 401.
Login exitoso setea cookie HttpOnly.

**Estimación**: 4 horas

**Dependencias**: WU-1 (DB setup)

---

### Work Unit 3: API de Escrituras (CRUD + Cierre)

**Propósito**: Endpoints completos para crear, consultar, actualizar y cerrar
escrituras, con recálculo automático de la factura.

**Entidades afectadas**:
- `Escritura`, `FacturaPrincipal` (crud)

**Archivos a crear/modificar**:
- `backend/src/schemas/escritura.py`, `backend/src/schemas/factura.py`
- `backend/src/services/escritura_service.py`
- `backend/src/api/routes/escrituras.py`
- `backend/tests/integration/test_escrituras_api.py` — TDD (FAIL first)

**Subtareas internas**:
1. Escribir integration tests: crear, listar, filtrar, editar, cerrar (FAIL)
2. Implementar `EscrituraService` con recálculo automático al guardar
3. Implementar endpoints REST según contrato OpenAPI
4. Enforcar inmutabilidad de escrituras cerradas (409 en PATCH de escritura cerrada)
5. Implementar filtros: por estado, por escribano, por mes/año

**Criterio de éxito**: Todos los tests de escrituras pasan. Un PATCH sobre escritura
cerrada retorna 409. Los valores calculados coinciden con el motor de WU-1.

**Estimación**: 6 horas

**Dependencias**: WU-1, WU-2

---

### Work Unit 4: API de Gastos Adicionales + SSE

**Propósito**: Endpoint para registrar gastos adicionales en una escritura abierta, y
el stream SSE para notificar cambios en tiempo real al frontend.

**Entidades afectadas**:
- `GastoAdicional` (nueva)

**Archivos a crear/modificar**:
- `backend/src/models/gasto_adicional.py`
- `backend/src/schemas/gasto.py`
- `backend/src/api/routes/gastos.py`
- `backend/src/api/routes/events.py` — SSE endpoint
- `backend/src/events/publisher.py` — PG LISTEN/NOTIFY pub/sub
- `backend/alembic/versions/003_gastos.py`

**Subtareas internas**:
1. Crear modelo `GastoAdicional` y migración
2. Implementar `POST /escrituras/{id}/gastos`
3. Implementar publisher PG LISTEN/NOTIFY
4. Implementar `GET /events` SSE endpoint (StreamingResponse)
5. Publicar evento en cada escritura create/update/close y gasto create
6. Probar SSE con dos tabs en browser local

**Criterio de éxito**: Agregar un gasto en Tab B actualiza la liquidación en Tab A
en ≤ 2 segundos. Gasto en escritura cerrada retorna 409.

**Estimación**: 5 horas

**Dependencias**: WU-3

---

### Work Unit 5: API de Liquidación y Salarios

**Propósito**: Endpoints que calculan y exponen el resumen mensual de liquidación y
el desglose de pagos de salarios, con trazabilidad a escrituras origen.

**Entidades afectadas**:
- `LiquidacionMensual`, `PagoSalario` (nuevas)

**Archivos a crear/modificar**:
- `backend/src/models/liquidacion.py`
- `backend/src/schemas/liquidacion.py`, `backend/src/schemas/salarios.py`
- `backend/src/services/liquidacion_service.py`
- `backend/src/services/salario_service.py`
- `backend/src/api/routes/liquidacion.py`
- `backend/src/api/routes/salarios.py`
- `backend/tests/unit/test_liquidacion.py` — TDD (FAIL first)
- `backend/tests/unit/test_salario.py` — TDD (FAIL first)
- `backend/tests/integration/test_liquidacion_api.py`

**Subtareas internas**:
1. Escribir unit tests para regla de inclusión mensual y cálculo por escribano (FAIL)
2. Implementar `LiquidacionService` con lógica de scoping por mes de creación
3. Implementar `SalarioService` (honorarios por escribano + split secretarias)
4. Implementar endpoints `GET /liquidacion` y `GET /salarios`
5. Verificar que `PagoSalario.detalle_json` contiene referencias a escritura_id

**Criterio de éxito**: Tests pasan incluyendo el caso "escritura abierta y cerrada en
mismo mes". Cada línea de salario tiene referencia trazable a su escritura.

**Estimación**: 5 horas

**Dependencias**: WU-3

---

### Work Unit 6: API de Configuración

**Propósito**: Endpoint para consultar y actualizar la configuración financiera
(versioned insert-only).

**Archivos a crear/modificar**:
- `backend/src/schemas/configuracion.py`
- `backend/src/services/config_service.py`
- `backend/src/api/routes/configuracion.py`

**Subtareas internas**:
1. Implementar `GET /configuracion` (devuelve versión más alta)
2. Implementar `POST /configuracion` (inserta nueva versión, no UPDATE)
3. Implementar `GET /configuracion/history`
4. Verificar que nueva config no afecta escrituras existentes

**Criterio de éxito**: Cambiar una tasa en producción crea una nueva versión. Las
escrituras existentes siguen usando su FK a la versión anterior.

**Estimación**: 3 horas

**Dependencias**: WU-2

---

### Work Unit 7: Frontend — Autenticación y Layout

**Propósito**: Login screen, layout principal con navegación de 3 secciones, y
hook SSE global para recibir actualizaciones en tiempo real.

**Archivos a crear/modificar**:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/components/layout/Navbar.tsx`, `Layout.tsx`
- `frontend/src/hooks/useSSE.ts`
- `frontend/src/api/client.ts` — authenticated fetch wrapper
- `frontend/src/App.tsx` — routing

**Subtareas internas**:
1. Implementar `LoginPage` con formulario usuario/contraseña
2. Implementar `Layout` con navbar: Escrituras | Liquidación | Pago de Salarios
3. Implementar `useSSE` hook que se conecta a `/api/v1/events` y emite eventos a query cache
4. Configurar React Router con rutas protegidas (redirect a login si no auth)

**Criterio de éxito**: Login funciona. Navegación entre 3 secciones funciona.
SSE se conecta y reconecta automáticamente.

**Estimación**: 4 horas

**Dependencias**: WU-2

---

### Work Unit 8: Frontend — Sección Escrituras

**Propósito**: Lista de escrituras con filtros, formulario de creación/edición,
detalle completo de factura principal y sección de gastos adicionales.

**Archivos a crear/modificar**:
- `frontend/src/pages/EscriturasPage.tsx`
- `frontend/src/pages/EscrituraDetail.tsx`
- `frontend/src/components/escrituras/EscrituraForm.tsx`
- `frontend/src/components/escrituras/EscrituraList.tsx`
- `frontend/src/components/escrituras/FacturaDetalle.tsx`
- `frontend/src/components/escrituras/GastoForm.tsx`
- `frontend/src/hooks/useEscrituras.ts`
- `frontend/src/api/escrituras.ts`

**Subtareas internas**:
1. Implementar lista de escrituras con filtros por estado y escribano
2. Implementar formulario de nueva escritura (nombre, USD, tipos de cambio, escribano)
3. Implementar vista de detalle con tabla de factura principal (formato Google Sheets)
4. Implementar formulario de gasto adicional
5. Implementar botón de cierre con confirmación
6. Integrar SSE para actualizar lista cuando llega evento

**Criterio de éxito**: Crear una escritura desde el formulario muestra todos los montos
calculados correctamente. Escritura cerrada muestra solo lectura.

**Estimación**: 8 horas

**Dependencias**: WU-3, WU-4, WU-7

---

### Work Unit 9: Frontend — Liquidación y Salarios

**Propósito**: Vistas de liquidación mensual y pago de salarios con trazabilidad
a escrituras y actualizaciones en tiempo real.

**Archivos a crear/modificar**:
- `frontend/src/pages/LiquidacionPage.tsx`
- `frontend/src/pages/SalariosPage.tsx`
- `frontend/src/components/liquidacion/LiquidacionResumen.tsx`
- `frontend/src/components/liquidacion/EscribanoCard.tsx`
- `frontend/src/components/salarios/PagoEscribanoCard.tsx`
- `frontend/src/components/salarios/PagoSecretariaCard.tsx`
- `frontend/src/hooks/useLiquidacion.ts`, `useSalarios.ts`

**Subtareas internas**:
1. Implementar selector de mes/año y `LiquidacionPage`
2. Implementar cards por escribano con lista de escrituras clicables
3. Implementar `SalariosPage` con detalle por escribano y fila de secretarias
4. Conectar SSE: actualizar liquidación y salarios en tiempo real
5. Implementar navegación escritura ← desde liquidación y salarios

**Criterio de éxito**: Crear una escritura en Tab B actualiza los totales de liquidación
en Tab A en ≤ 2s. Cada monto tiene link a la escritura origen.

**Estimación**: 6 horas

**Dependencias**: WU-5, WU-7

---

### Work Unit 10: Configuración UI + Polish

**Propósito**: Pantalla de configuración para actualizar tasas y salarios, y pulido
general de UX para el usuario no técnico.

**Archivos a crear/modificar**:
- `frontend/src/pages/ConfiguracionPage.tsx`
- `frontend/src/api/configuracion.ts`
- CSS/Tailwind polish en todos los componentes

**Subtareas internas**:
1. Implementar formulario de configuración con campos numéricos para todas las tasas
2. Guardar nueva versión de config y mostrar confirmación
3. Pulir mensajes de error y validación en formularios
4. Validar SC-001 (< 3 min para crear escritura completa con un usuario nuevo)

**Criterio de éxito**: Cambiar el salario de secretarias desde la UI crea nueva versión
de config. SC-001 verificado manualmente.

**Estimación**: 4 horas

**Dependencias**: WU-6, WU-7

---

### Notas para Itti-Kit

**Total Work Units**: 10  
**Tiempo total estimado**: ~53 horas  
**Work Units paralelas posibles**:
- WU-2 y WU-1 (base de datos y auth son independientes durante el desarrollo)
- WU-3, WU-4, WU-5, WU-6 pueden solaparse (distintos módulos de servicio)
- WU-7 puede empezar en paralelo con WU-3 (usando mocks de API)
- WU-8 y WU-9 pueden avanzar en paralelo una vez WU-7 está listo

**Orden crítico**:
```
WU-1 (DB + motor) → WU-2 (auth) → WU-3 (escrituras) → WU-4 (gastos+SSE)
                                 → WU-5 (liquidacion)
                                 → WU-6 (config)
WU-7 (frontend layout) → WU-8 (escrituras UI)
                       → WU-9 (liquidacion UI)
                       → WU-10 (config UI + polish)
```

---

## Complexity Tracking

No violations of constitutional principles detected.

| Decision | Justification |
|---|---|
| `detalle_json` JSONB on PagoSalario | Performance trade-off: avoids a join table for a low-volume read-heavy endpoint. Constitution P8 (traceability) still satisfied via embedded `escritura_id` references. |
| SSE via PG LISTEN/NOTIFY (single Fargate task) | Simpler than Redis pub/sub for <10 users. If horizontally scaled later, replace publisher with Redis or AWS SNS. Documented in research.md. |
