# Implementation Plan: Impuestos por Escritura

**Branch**: `006-impuestos-escrituras` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/006-impuestos-escrituras/spec.md`

---

## Summary

Add a **property-tax cash-control module** per escritura: six fixed impuesto types (API, TGI,
Aguas Santafesinas, EPE, Expensas, Litoral Gas) with period + linear day proration (cutoff date,
direction), editable client/escribanía payments, libro entries by payment date, monthly
liquidación/salarios impact (neto impuestos per escribano), and escritura close blocked unless
balance impuestos = 0 and every loaded impuesto has both payments.

Approach: extend FastAPI/PostgreSQL/React stack; migration `007`; TDD throughout; reuse pagos
patterns from 003 with **editable** payments (clarify deviation).

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic; React + Vite, TanStack Query — no new packages  
**Storage**: PostgreSQL 16 — new tables `impuestos_escritura`, `pagos_impuesto_cliente`, `pagos_impuesto_escribania`  
**Testing**: pytest + pytest-asyncio (**TDD completo** per spec); Vitest (frontend hooks/forms)  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: SC-001 ≤ 3s load; SC-006 ≤ 2s SSE propagation  
**Constraints**: No polling; honorarios saldo unchanged; liquidación monthly close does NOT require impuestos balance = 0; no Figma  
**Scale/Scope**: < 10 users; ~6 impuesto types × N escrituras; extends liquidación schema (minor breaking: `neto_impuestos`)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | Migration + Docker/RDS identical |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | All logic in Python services |
| P4 — Frontend UX | ✅ Pass | Impuestos section in escritura detail; balance visible; traceable lines |
| P5 — Real-time via SSE | ✅ Pass | New impuesto/pago events → invalidate libros + liquidación |
| P6 — Formula integrity | ✅ Pass | `impuesto_prorrateo.py` pure; canonical 46/61 + 15/61 tests |
| P7 — Security baseline | ✅ Pass | Server validation; DTOs; auth on all routes |
| P8 — Traceability | ✅ Pass | Libro/liquidación lines include escritura_id + tipo_impuesto |

**Post-design re-check**: ✅ All gates pass.

**Governance note**: Constitution §2.3 (Gastos Adicionales) remains superseded by 003; this feature adds a **parallel** cash-control domain for property impuestos without altering honorarios factura flow.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-impuestos-escrituras/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── openapi-delta.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/spec-kitti.tasks)
```

### Source Code — New and Modified Files

```text
backend/
├── alembic/versions/
│   └── 007_impuestos_escritura.py           # NEW
├── src/
│   ├── models/
│   │   ├── impuesto_escritura.py            # NEW
│   │   ├── pago_impuesto_cliente.py         # NEW
│   │   ├── pago_impuesto_escribania.py      # NEW
│   │   └── escritura.py                     # MODIFY — relationships
│   ├── schemas/
│   │   ├── impuesto.py                        # NEW
│   │   ├── escritura.py                     # MODIFY — impuestos + balance fields
│   │   ├── libros.py                        # MODIFY — origen, tipo_impuesto
│   │   └── liquidacion.py                   # MODIFY — neto_impuestos
│   ├── services/
│   │   ├── impuesto_prorrateo.py            # NEW — pure functions (TDD first)
│   │   ├── impuesto_balance.py              # NEW — pure balance/close checks
│   │   ├── impuesto_service.py              # NEW — CRUD impuesto
│   │   ├── pago_impuesto_cliente_service.py # NEW
│   │   ├── pago_impuesto_escribania_service.py # NEW
│   │   ├── escritura_service.py             # MODIFY — close guards
│   │   ├── libros_service.py                # MODIFY — impuesto lines
│   │   ├── liquidacion_service.py           # MODIFY — neto impuestos
│   │   └── escritura_errors.py              # MODIFY — new 409 errors
│   └── api/routes/
│       ├── impuestos.py                     # NEW — nested under escrituras
│       └── router.py                        # MODIFY
├── tests/
│   ├── unit/
│   │   ├── test_impuesto_prorrateo.py       # NEW — TDD first
│   │   ├── test_impuesto_balance.py         # NEW
│   │   ├── test_impuesto_service.py         # NEW
│   │   ├── test_libros_service.py           # MODIFY
│   │   └── test_liquidacion.py              # MODIFY
│   └── integration/
│       ├── test_impuestos_api.py            # NEW
│       └── test_migration_007_impuestos.py    # NEW

frontend/
├── src/
│   ├── api/impuestos.ts                     # NEW
│   ├── hooks/useImpuestos.ts                # NEW
│   ├── components/escrituras/
│   │   ├── ImpuestoForm.tsx                 # NEW
│   │   ├── ImpuestoList.tsx                 # NEW
│   │   ├── ImpuestoPagoClienteForm.tsx      # NEW
│   │   └── ImpuestoPagoEscribaniaForm.tsx   # NEW
│   ├── pages/EscrituraDetail.tsx            # MODIFY — Impuestos section + balance
│   ├── hooks/useSSE.ts                      # MODIFY — new events
│   ├── types/api.ts                         # MODIFY
│   └── utils/errors.ts                      # MODIFY — 409 impuestos messages
```

**Structure Decision**: Existing web app layout unchanged; feature nests under escritura detail
(same pattern as pagos cliente/colegio from 003).

---

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

Key decisions:
- Migration `007`, three tables, 1:1 payments per impuesto
- Linear proration without cutoff overlap
- Libros by payment date; liquidación adds `neto_impuestos`
- Editable payments (deviation from 003 append-only)
- TDD order documented in R-010

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

1. `impuesto_prorrateo.py` + unit tests (46/61, 15/61, edge cutoff on period bounds)
2. `impuesto_balance.py` + unit tests (balance, close eligibility)
3. Migration `007` + integration test
4. Models + schemas
5. `impuesto_service` CRUD
6. Payment services (create/update/delete)
7. Extend `libros_service`, `liquidacion_service`
8. Extend `close_escritura` guards
9. API routes + integration tests
10. SSE events

### Frontend sequence

1. Types + API client
2. `useImpuestos` hooks with query invalidation
3. ImpuestoForm/List + payment forms (prefill suggested monto)
4. EscrituraDetail section + balance banner
5. Close button guard messaging
6. Liquidación/PagoSalarios display `neto_impuestos` (if separate column)
7. SSE handler updates

---

## Plan Jerárquico (para Itti-Kit)

### Work Unit 1: Prorrateo y balance (lógica pura)

**Propósito**: Implementar cálculo lineal y reglas de cierre sin I/O.

**Entidades afectadas**: ImpuestoEscritura (computed fields)

**Archivos**:
- `backend/src/services/impuesto_prorrateo.py`
- `backend/src/services/impuesto_balance.py`
- `backend/tests/unit/test_impuesto_prorrateo.py`
- `backend/tests/unit/test_impuesto_balance.py`

**Subtareas**:
1. Tests 46/61 y 15/61 (spec example)
2. Validación fecha corte fuera de período
3. Cutoff en primer/último día del período
4. `calc_balance`, `can_close_impuestos`, `impuestos_pendientes`

**Criterio de éxito**: 100% tests unitarios puros pasan antes de cualquier modelo DB.

**Estimación**: 4h

---

### Work Unit 2: Persistencia y migración

**Propósito**: Tablas, modelos ORM y migración Alembic 007.

**Entidades**: ImpuestoEscritura, PagoImpuestoCliente, PagoImpuestoEscribania

**Archivos**:
- `backend/alembic/versions/007_impuestos_escritura.py`
- `backend/src/models/impuesto_*.py`
- `backend/src/schemas/impuesto.py`
- `backend/tests/integration/test_migration_007_impuestos.py`

**Dependencias**: WU-1

**Criterio de éxito**: `alembic upgrade head` idempotente; enums y UNIQUE constraints verificados.

**Estimación**: 4h

---

### Work Unit 3: Servicios y API de impuestos

**Propósito**: CRUD impuesto + pagos editables con guards de escritura abierta.

**Archivos**:
- `backend/src/services/impuesto_service.py`
- `backend/src/services/pago_impuesto_*_service.py`
- `backend/src/api/routes/impuestos.py`
- `backend/tests/unit/test_impuesto_service.py`
- `backend/tests/integration/test_impuestos_api.py`

**Dependencias**: WU-2

**Criterio de éxito**: API cumple openapi-delta; 409 en escritura cerrada; un pago por lado.

**Estimación**: 8h

---

### Work Unit 4: Libros, liquidación y cierre

**Propósito**: Integrar impuestos en libros, liquidación mensual y close_escritura.

**Archivos**:
- `backend/src/services/libros_service.py`
- `backend/src/services/liquidacion_service.py`
- `backend/src/services/escritura_service.py`
- `backend/src/schemas/libros.py`, `liquidacion.py`
- Tests unit + integration close 409

**Dependencias**: WU-3

**Criterio de éxito**: SC-002/003/009/010; asimetría mensual permitida; cierre escritura bloqueado con balance ≠ 0.

**Estimación**: 8h

---

### Work Unit 5: Frontend — sección Impuestos

**Propósito**: UI en detalle de escritura con prorrateo, pagos y balance.

**Archivos**:
- `frontend/src/api/impuestos.ts`
- `frontend/src/hooks/useImpuestos.ts`
- `frontend/src/components/escrituras/Impuesto*.tsx`
- `frontend/src/pages/EscrituraDetail.tsx`
- `frontend/src/hooks/useSSE.ts`

**Dependencias**: WU-4 (API estable)

**Criterio de éxito**: SC-001, SC-007; forms editables; balance visible; responsive stack (US8).

**Estimación**: 8h

---

### Work Unit 6: Liquidación/Salarios UI + SSE

**Propósito**: Mostrar neto impuestos en vistas mensuales; tiempo real completo.

**Archivos**:
- `frontend/src/pages/LiquidacionPage.tsx` (o componente hijo)
- `frontend/src/components/salarios/PagoEscribanoCard.tsx`
- SSE types + invalidation

**Dependencias**: WU-4, WU-5

**Criterio de éxito**: SC-006, SC-009; cambios en impuestos refrescan liquidación en < 2s.

**Estimación**: 4h

---

### Notas para Itti-Kit

**Total Work Units**: 6  
**Tiempo estimado**: ~36h  
**Paralelo posible**: WU-1 inmediato; WU-5 mock API tras WU-3 contratos

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Editable payments (vs 003 append-only) | Clarify session Q3 — user correction workflow | Append-only forces delete+recreate UX; spec requires inline edit |
| Extend LiquidacionEscrituraItem | Separate honorarios vs impuestos net per escritura/month | Rolling into monto_cobrado hides asymmetry the secretary must audit |
| No Figma (constitution P10) | Spec assumption — reuse 004 patterns | N/A — explicit product decision |

---

## Testing Strategy (from spec)

**Approach**: TDD — Test-Driven Development completo.

Honored by task generation: tests before implementation for prorrateo, balance, services, libros, liquidación, close guards, API, migration.

---

## Dependencies

| Feature | Relationship |
|---|---|
| 003-pagos-cliente | Libros/liquidación por fecha de pago; honorarios close guard |
| 004-escrituras-ui-mejoras | Columna derecha en detalle (layout Impuestos) |

---

## Generated Artifacts

| File | Phase |
|---|---|
| [research.md](./research.md) | 0 |
| [data-model.md](./data-model.md) | 1 |
| [contracts/openapi-delta.yaml](./contracts/openapi-delta.yaml) | 1 |
| [quickstart.md](./quickstart.md) | 1 |
| [plan.md](./plan.md) | 2 (this file) |

**Next command**: `/spec-kitti.tasks`
