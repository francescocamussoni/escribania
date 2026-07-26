# Implementation Plan: Vencimiento de pago al Colegio y régimen Monotributo

**Branch**: `008-factura-vencimiento-monotributo` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/008-factura-vencimiento-monotributo/spec.md`

---

## Summary

Expose a **30-day calendar countdown** for paying **Total impuestos** (Corresponde) to the Colegio
in the Escrituras list and escritura detail header, with green/yellow/red urgency bands and
sort-by-due-date. Extend **pagos_colegio** with mandatory **imputación** (only `total_impuestos`
payments count toward the deadline). Add **monotributista** flag on Escribano (Costanza in demo)
so IVA = 0 and Total + IVA = Total, with immediate recalc of all open escrituras on toggle.
**TDD-first** per spec Testing Strategy.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic; React + Vite, TanStack Query — no new packages  
**Storage**: PostgreSQL 16 — migration `011` (`pagos_colegio.imputacion`, `escribano.monotributista`)  
**Testing**: pytest + pytest-asyncio (**TDD-first**); Vitest for `escrituraList` sort + `PlazoColegioBadge`  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: Plazo derived at list read ≤ same p95 as current list endpoint (< 200ms local)  
**Constraints**: No polling (SSE for invalidation); depends on 007 `total_impuestos` / totales columns  
**Scale/Scope**: < 10 users; ~15 backend files, ~10 frontend files, 1 migration

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | Migration + Docker/RDS identical |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | `plazo_colegio.py`, `calculo_factura` extension |
| P4 — Frontend UX | ✅ Pass | Badge + sort in Escrituras; toggle in Configuración |
| P5 — Real-time via SSE | ✅ Pass | `escribano.updated` + existing `pago_colegio.created` |
| P6 — Formula integrity | ✅ Pass | Pure `calcular_plazo_colegio`; `monotributista` branch in `calcular_totales_factura` |
| P7 — Security baseline | ✅ Pass | DTOs; `extra=forbid`; auth on PATCH escribano |
| P8 — Traceability | ✅ Pass | Plazo tied to escritura + factura.total_impuestos |

**Post-design re-check**: ✅ All gates pass. No Complexity Tracking entries required.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-factura-vencimiento-monotributo/
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
│   └── 011_plazo_colegio_monotributo.py       # NEW
├── src/
│   ├── models/
│   │   ├── escribano.py                       # MODIFY — monotributista
│   │   └── pago_colegio.py                    # MODIFY — imputacion enum
│   ├── schemas/
│   │   ├── escribano.py                       # MODIFY — response + update
│   │   ├── escritura.py                       # MODIFY — plazo_colegio
│   │   ├── pago_colegio.py                    # MODIFY — imputacion
│   │   └── plazo_colegio.py                   # NEW — PlazoColegioResponse
│   ├── services/
│   │   ├── plazo_colegio.py                   # NEW — pure calc (TDD)
│   │   ├── calculo_factura.py                 # MODIFY — monotributista param
│   │   ├── escritura_service.py               # MODIFY — plazo fields, load pagos
│   │   ├── escribano_service.py               # MODIFY — update + recalc
│   │   └── pago_colegio_service.py            # MODIFY — imputacion filter sum
│   ├── api/routes/
│   │   └── escribanos.py                      # MODIFY — PATCH route
│   └── scripts/
│       └── seed_demo_data.py                  # MODIFY — v5, Costanza, plazos
├── tests/
│   ├── unit/
│   │   ├── test_plazo_colegio.py              # NEW — TDD first
│   │   ├── test_calcular_totales_factura.py   # MODIFY — monotributo cases
│   │   └── test_pago_colegio_service.py       # MODIFY — imputacion
│   └── integration/
│       ├── test_escribanos_api.py             # MODIFY — PATCH
│       └── test_escrituras_api.py             # MODIFY — plazo_colegio

frontend/
├── src/
│   ├── components/escrituras/
│   │   ├── PlazoColegioBadge.tsx              # NEW
│   │   ├── EscrituraList.tsx                  # MODIFY — column + sort
│   │   ├── PagoColegioForm.tsx                # MODIFY — imputacion select
│   │   └── PagoColegioList.tsx                # MODIFY — show imputacion
│   ├── components/configuracion/
│   │   └── EscribanosConfig.tsx               # MODIFY — monotributista toggle
│   ├── pages/
│   │   ├── EscriturasPage.tsx                 # MODIFY — sort field vencimiento
│   │   └── EscrituraDetail.tsx                # MODIFY — header badge
│   ├── hooks/
│   │   ├── useEscriturasListSession.ts        # MODIFY — sortField
│   │   ├── useEscribanos.ts                   # MODIFY — useUpdateEscribano
│   │   └── useSSE.ts                          # MODIFY — escribano.updated
│   ├── utils/
│   │   └── escrituraList.ts                   # MODIFY — sortByVencimiento
│   ├── types/api.ts                           # MODIFY
│   └── index.css                              # MODIFY — plazo-colegio--*
```

**Structure Decision**: Extends existing escrituras/config flows; no new top-level routes.

---

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

Key decisions:

- Pure `calcular_plazo_colegio` with `PLAZO_COLEGIO_DIAS = 30`
- Enum `imputacion_pago_colegio`; legacy → `honorarios_varios`
- `escribano.monotributista` + PATCH + bulk recalc open escrituras
- Client-side sort by `plazo_colegio.fecha_vencimiento`
- Demo seed v5; Costanza monotributista

---

## Phase 1: Design & Contracts

**Status**: ✅ Complete

| Artifact | Path |
|---|---|
| Data model | [data-model.md](./data-model.md) |
| OpenAPI delta | [contracts/openapi-delta.yaml](./contracts/openapi-delta.yaml) |
| Quickstart | [quickstart.md](./quickstart.md) |

---

## Plan Jerárquico (para Itti-Kit)

### Work Unit 1: Cálculo de plazo Colegio (TDD)

**Propósito**: Implementar y validar la lógica pura de vencimiento, bandas de color y estados.

**Entidades afectadas**: PlazoColegio (derivado)

**Archivos a crear/modificar**:

- `backend/tests/unit/test_plazo_colegio.py` — NEW (fail first)
- `backend/src/services/plazo_colegio.py` — NEW
- `backend/src/schemas/plazo_colegio.py` — NEW

**Subtareas internas**:

1. Tests: no_aplica (total_impuestos=0), pagado, pendiente verde/amarillo/rojo, vencido
2. Tests: límites 30/20/10 días inclusivos
3. Implementar `calcular_plazo_colegio` + constantes
4. Helper `sum_pagos_impuestos(pagos_colegio)`

**Criterio de éxito**: 100 % tests unitarios plazo pasan; sin dependencia DB.

**Estimación**: 3h

---

### Work Unit 2: Imputación en pagos al Colegio (TDD)

**Propósito**: Persistir imputación, migrar legacy, validar API y sumas filtradas.

**Entidades afectadas**: PagoColegio

**Archivos a crear/modificar**:

- `backend/alembic/versions/011_plazo_colegio_monotributo.py` — enum + column (part 1)
- `backend/src/models/pago_colegio.py`
- `backend/src/schemas/pago_colegio.py`
- `backend/src/services/pago_colegio_service.py`
- `backend/tests/unit/test_pago_colegio_service.py`

**Subtareas internas**:

1. Migration enum + column; backfill `honorarios_varios`
2. Tests: create sin imputación → 422; sum solo `total_impuestos`
3. Actualizar `PagoColegioInput` / Response
4. Integration test POST pagos-colegio

**Criterio de éxito**: Pagos legacy migrados; nuevos pagos requieren imputación; suma filtrada correcta.

**Dependencias**: WU-001 (helper sum)

**Estimación**: 4h

---

### Work Unit 3: Monotributista en Escribano (TDD)

**Propósito**: Flag monotributista, IVA condicional, PATCH y recálculo masivo.

**Entidades afectadas**: Escribano, FacturaPrincipal

**Archivos a crear/modificar**:

- `011_plazo_colegio_monotributo.py` — `escribano.monotributista` + Costanza (part 2)
- `backend/src/models/escribano.py`
- `backend/src/schemas/escribano.py`
- `backend/src/services/escribano_service.py` — `update_monotributista`, `recalcular_abiertas`
- `backend/src/services/calculo_factura.py` — `monotributista` param
- `backend/src/api/routes/escribanos.py` — PATCH
- `backend/tests/unit/test_calcular_totales_factura.py`
- `backend/tests/integration/test_escribanos_api.py`

**Subtareas internas**:

1. Tests monotributo: iva=0, total_factura=total_sin_iva (fixture research R-007)
2. Implementar branch en `calcular_totales_factura`
3. PATCH endpoint + SSE `escribano.updated`
4. Recalc todas escrituras abiertas al toggle; cerradas intactas

**Criterio de éxito**: Costanza seed monotributista; toggle recalcula abiertas en un request.

**Estimación**: 5h

---

### Work Unit 4: API plazo_colegio en listado y detalle

**Propósito**: Exponer `plazo_colegio` en EscrituraListItem y EscrituraResponse.

**Entidades afectadas**: Escritura (read path)

**Archivos a crear/modificar**:

- `backend/src/services/escritura_service.py` — `build_plazo_colegio_fields`, load pagos
- `backend/src/schemas/escritura.py`
- `backend/tests/integration/test_escrituras_api.py`

**Subtareas internas**:

1. Tests integración: list + detail incluyen `plazo_colegio` coherente
2. Wire `calcular_plazo_colegio` en mappers
3. Verificar pagos parciales imputados actualizan estado

**Criterio de éxito**: SC-001 API — mismo plazo en list y detail para misma escritura.

**Dependencias**: WU-001, WU-002

**Estimación**: 3h

---

### Work Unit 5: Frontend listado, orden y badge encabezado

**Propósito**: UI de countdown, sort por vencimiento, badge en detalle.

**Entidades afectadas**: EscriturasPage, EscrituraDetail, EscrituraList

**Archivos a crear/modificar**:

- `frontend/src/components/escrituras/PlazoColegioBadge.tsx`
- `frontend/src/components/escrituras/EscrituraList.tsx`
- `frontend/src/pages/EscriturasPage.tsx`
- `frontend/src/pages/EscrituraDetail.tsx`
- `frontend/src/utils/escrituraList.ts`
- `frontend/src/hooks/useEscriturasListSession.ts`
- `frontend/src/types/api.ts`
- `frontend/src/index.css`
- `frontend/src/utils/escrituraList.test.ts` (optional)

**Subtareas internas**:

1. Tipos `PlazoColegioResponse` + extend `EscrituraListItem`
2. `PlazoColegioBadge` con clases semánticas
3. Columna + sort toggle vencimiento (session `sortField`)
4. Badge en encabezado EscrituraDetail

**Criterio de éxito**: Manual checklist quickstart § Listado + Detalle items 1–4.

**Dependencias**: WU-004

**Estimación**: 5h

---

### Work Unit 6: Frontend imputación pagos y config monotributo

**Propósito**: Selector imputación en formulario pago; toggle monotributista en Configuración.

**Archivos a crear/modificar**:

- `frontend/src/components/escrituras/PagoColegioForm.tsx`
- `frontend/src/components/escrituras/PagoColegioList.tsx`
- `frontend/src/components/configuracion/EscribanosConfig.tsx`
- `frontend/src/hooks/useEscribanos.ts`
- `frontend/src/hooks/useSSE.ts`

**Subtareas internas**:

1. Select imputación obligatorio (3 opciones)
2. Mostrar imputación en lista de pagos
3. Toggle monotributista + PATCH hook
4. SSE `escribano.updated` invalidation

**Criterio de éxito**: Quickstart items 5–10 pasan manualmente.

**Dependencias**: WU-002, WU-003, WU-005

**Estimación**: 4h

---

### Work Unit 7: Seed demo v5

**Propósito**: Dataset demo con Costanza monotributista, plazos escalonados, pagos imputados mixtos.

**Archivos a crear/modificar**:

- `backend/scripts/seed_demo_data.py`

**Subtareas internas**:

1. Bump `DEMO_SEED_VERSION=5`
2. Costanza `monotributista=true`
3. Escrituras con `created_at` offset para bandas color
4. Pagos colegio demo con imputaciones variadas

**Criterio de éxito**: `seed_demo_data.py` idempotente; demo muestra verde/amarillo/rojo/pagado.

**Dependencias**: WU-002, WU-003

**Estimación**: 2h

---

### Notas para Itti-Kit

**Total estimado de Work Units**: 7  
**Tiempo total estimado**: ~26h  
**Work Units paralelizables**: WU-001 ∥ inicio WU-003 (tests totales); WU-005 ∥ WU-006 tras WU-004

---

## Complexity Tracking

> No violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
