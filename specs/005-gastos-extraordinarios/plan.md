# Implementation Plan: Gastos Extraordinarios de la Escribanía

**Branch**: `005-gastos-extraordinarios` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/005-gastos-extraordinarios/spec.md`

---

## Summary

Add a **monthly office-expense module** independent of escrituras: CRUD for extraordinary
expenses (concepto, monto, fecha), automatic lines in Libro de Salida (`origen=extraordinario`),
and equal split deduction across active escribanos in Pago de Salarios. New navbar section in
**second position** (after Escrituras). No impact on Liquidación or Libro de Entrada.

Approach: extend FastAPI/PostgreSQL/React stack; migration `008`; TDD; reuse monthly-page and
libro/salarios patterns from 003/006.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic; React + Vite, TanStack Query — no new packages  
**Storage**: PostgreSQL 16 — new table `gastos_extraordinarios`  
**Testing**: pytest + pytest-asyncio (TDD); Vitest (frontend)  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: SC-001 ≤ 3s; SC-005 ≤ 2s propagation via SSE  
**Constraints**: No Figma; no liquidación impact; reparto equitativo con redondeo determinístico  
**Scale/Scope**: < 10 users; gastos mensuales bajos volumen; extends `libros` + `salarios` schemas (minor breaking: nullable `escritura_id` en líneas)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | Migration `008` + Docker/RDS |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | CRUD + reparto + libros/salarios en Python |
| P4 — Frontend UX | ✅ Pass | Página mensual dedicada; navbar 2.ª posición |
| P5 — Real-time via SSE | ✅ Pass | Eventos gasto → libros + salarios |
| P6 — Formula integrity | ✅ Pass | `gasto_extraordinario_reparto.py` puro |
| P7 — Security baseline | ✅ Pass | Auth en todas las rutas; validación server-side |
| P8 — Traceability | ✅ Pass | `gasto_extraordinario_id` en línea de libro |

**Post-design re-check**: ✅ All gates pass.

**Governance note**: Distinto de Gastos Adicionales por escritura (constitution §2.3) y de impuestos (006). Dominio de caja de la escribanía.

---

## Project Structure

### Documentation (this feature)

```text
specs/005-gastos-extraordinarios/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── openapi-delta.yaml
├── checklists/
│   └── requirements.md
├── tasks.md             # Phase 2
└── work-units.json      # Phase 2 (/spec-kitti.tasks.shape)
```

### Source Code — New and Modified Files

```text
backend/
├── alembic/versions/
│   └── 008_gastos_extraordinarios.py              # NEW
├── src/
│   ├── models/
│   │   └── gasto_extraordinario.py                # NEW
│   ├── schemas/
│   │   ├── gasto_extraordinario.py                # NEW
│   │   ├── libros.py                              # MODIFY — origen extraordinario, nullable escritura
│   │   └── salarios.py                            # MODIFY — deducción, monto_neto, advertencia
│   ├── services/
│   │   ├── gasto_extraordinario_reparto.py        # NEW — pure split
│   │   ├── gasto_extraordinario_service.py        # NEW — CRUD
│   │   ├── libros_service.py                      # MODIFY — líneas extraordinarias
│   │   └── salario_service.py                     # MODIFY — deducción mensual
│   └── api/routes/
│       ├── gastos_extraordinarios.py              # NEW
│       └── router.py                              # MODIFY
├── tests/
│   ├── unit/
│   │   ├── test_gasto_extraordinario_reparto.py   # NEW
│   │   ├── test_gasto_extraordinario_service.py   # NEW
│   │   ├── test_libros_service.py                 # MODIFY
│   │   └── test_salario.py                        # MODIFY
│   └── integration/
│       ├── test_gastos_extraordinarios_api.py     # NEW
│       └── test_migration_008_gastos_extraordinarios.py # NEW

frontend/
├── src/
│   ├── api/gastosExtraordinarios.ts               # NEW
│   ├── hooks/useGastosExtraordinarios.ts          # NEW
│   ├── pages/GastosExtraordinariosPage.tsx        # NEW
│   ├── components/gastos-extraordinarios/
│   │   ├── GastoExtraordinarioForm.tsx            # NEW
│   │   └── GastoExtraordinarioList.tsx            # NEW
│   ├── components/layout/Navbar.tsx               # MODIFY — 2.ª posición
│   ├── components/libros/LibroLineaRow.tsx      # MODIFY — badge extraordinario
│   ├── components/salarios/PagoEscribanoCard.tsx # MODIFY — deducción + neto
│   ├── pages/SalariosPage.tsx                     # MODIFY — advertencia reparto
│   ├── App.tsx                                    # MODIFY — ruta
│   ├── hooks/useSSE.ts                            # MODIFY — eventos gasto
│   └── types/api.ts                               # MODIFY
```

**Structure Decision**: Página de primer nivel (como Liquidación), no anidada en escritura.

---

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

Key decisions:
- Migration `008`, tabla única sin `escritura_id`
- Libro salida: `origen=extraordinario`, escritura nullable
- Reparto equitativo con remanente al último escribano alfabético
- Sin impacto en liquidación
- API `/gastos-extraordinarios`
- SSE: `gasto_extraordinario.*` + `libros_updated`

---

## Phase 1: Design & Contracts

**Status**: ✅ Complete

| Artifact | Path |
|---|---|
| Data model | [data-model.md](./data-model.md) |
| OpenAPI delta | [contracts/openapi-delta.yaml](./contracts/openapi-delta.yaml) |
| Quickstart | [quickstart.md](./quickstart.md) |

---

## Phase 2: Implementation Outline (for `/spec-kitti.tasks`)

### Backend sequence (TDD)

1. `gasto_extraordinario_reparto.py` + unit tests (división exacta, indivisible, n=0)
2. Migration `008` + integration test
3. Model + schemas
4. `gasto_extraordinario_service` CRUD + unit tests
5. Extend `libros_service` + unit tests
6. Extend `salario_service` + unit tests
7. API routes + integration tests
8. SSE events

### Frontend sequence

1. Types + API client
2. `useGastosExtraordinarios` hooks
3. `GastosExtraordinariosPage` + form/list
4. Navbar (2.ª posición) + `App.tsx` route
5. `PagoEscribanoCard` + `SalariosPage` deducción/advertencia
6. `LibroLineaRow` badge extraordinario
7. SSE invalidation

---

## Plan Jerárquico (para Itti-Kit)

### Work Unit 1: Reparto equitativo (lógica pura)

**Propósito**: Dividir total mensual entre N escribanos sin pérdida de centavos.

**Archivos**:
- `backend/src/services/gasto_extraordinario_reparto.py`
- `backend/tests/unit/test_gasto_extraordinario_reparto.py`

**Criterio de éxito**: SC-003; suma cuotas = total para casos divisibles e indivisibles.

**Estimación**: 2h

---

### Work Unit 2: Persistencia y migración

**Propósito**: Tabla `gastos_extraordinarios`, modelo ORM, schemas Pydantic.

**Archivos**:
- `backend/alembic/versions/008_gastos_extraordinarios.py`
- `backend/src/models/gasto_extraordinario.py`
- `backend/src/schemas/gasto_extraordinario.py`
- `backend/tests/integration/test_migration_008_gastos_extraordinarios.py`

**Dependencias**: WU-1 (paralelo posible tras tests reparto escritos)

**Criterio de éxito**: `alembic upgrade head` idempotente.

**Estimación**: 3h

---

### Work Unit 3: CRUD y API

**Propósito**: Servicio y rutas REST con validación y SSE.

**Archivos**:
- `backend/src/services/gasto_extraordinario_service.py`
- `backend/src/api/routes/gastos_extraordinarios.py`
- `backend/tests/unit/test_gasto_extraordinario_service.py`
- `backend/tests/integration/test_gastos_extraordinarios_api.py`

**Dependencias**: WU-2

**Criterio de éxito**: openapi-delta cumplido; 401 sin auth; 422 en monto ≤ 0.

**Estimación**: 5h

---

### Work Unit 4: Libros y salarios

**Propósito**: Integrar en libro salida y deducción en pago de escribanos.

**Archivos**:
- `backend/src/services/libros_service.py`
- `backend/src/services/salario_service.py`
- `backend/src/schemas/libros.py`, `salarios.py`
- Tests unit libros + salario

**Dependencias**: WU-3

**Criterio de éxito**: SC-002, SC-004; FR-015; advertencia sin escribanos.

**Estimación**: 5h

---

### Work Unit 5: Frontend página y navegación

**Propósito**: UI mensual + navbar 2.ª posición.

**Archivos**:
- `frontend/src/pages/GastosExtraordinariosPage.tsx`
- `frontend/src/components/gastos-extraordinarios/*`
- `frontend/src/api/gastosExtraordinarios.ts`
- `frontend/src/hooks/useGastosExtraordinarios.ts`
- `frontend/src/components/layout/Navbar.tsx`
- `frontend/src/App.tsx`

**Dependencias**: WU-3

**Criterio de éxito**: SC-001, SC-006.

**Estimación**: 5h

---

### Work Unit 6: Frontend salarios y libros + SSE

**Propósito**: Mostrar deducción, neto, badge en libro, SSE.

**Archivos**:
- `frontend/src/components/salarios/PagoEscribanoCard.tsx`
- `frontend/src/pages/SalariosPage.tsx`
- `frontend/src/components/libros/LibroLineaRow.tsx`
- `frontend/src/hooks/useSSE.ts`
- `frontend/src/types/api.ts`

**Dependencias**: WU-4, WU-5

**Criterio de éxito**: SC-005; quickstart manual verde.

**Estimación**: 4h

---

### Notas para Itti-Kit

**Total estimado de Work Units**: 6  
**Tiempo total estimado**: ~24h  
**Work Units en paralelo**: WU-1 y WU-2 (tests primero); WU-5 puede iniciar cuando API WU-3 exponga contrato

---

## Complexity Tracking

No constitution violations requiring justification.
