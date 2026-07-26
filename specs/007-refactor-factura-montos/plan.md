# Implementation Plan: Refactorización de montos de Factura Principal

**Branch**: `007-refactor-factura-montos` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/007-refactor-factura-montos/spec.md`

---

## Summary

Reorganize the Factura Principal UI into five sections (Bases de cálculo, Honorarios,
Honorarios varios, Corresponde, Totales), introduce five new derived totals with IVA,
and redefine `total_factura` as **Total + IVA** for client balance and libro de entrada.
Line-item formulas and rates stay unchanged; TDD-first with canonical fixture updates and
demo seed v4 regeneration.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic; React + Vite, TanStack Query — no new packages  
**Storage**: PostgreSQL 16 — extend `facturas_principales` (migration `009`)  
**Testing**: pytest + pytest-asyncio (**TDD-first** per spec); Vitest optional for `FacturaDetalle`  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: Factura recalc on escritura save ≤ 500ms p95 (unchanged domain)  
**Constraints**: No polling; no Figma reference (layout refactor of existing components); line items unchanged (SC-005)  
**Scale/Scope**: < 10 users; touches calculo engine, 1 UI component, labels, seed + test fixtures

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | Migration + Docker/RDS identical |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | `calcular_totales_factura` in Python |
| P4 — Frontend UX | ✅ Pass | Five clear sections; Colegio items highlighted |
| P5 — Real-time via SSE | ✅ Pass | Escritura update events unchanged |
| P6 — Formula integrity | ✅ Pass | Pure functions; named `IVA_PCT`; canonical fixture extended in research.md |
| P7 — Security baseline | ✅ Pass | DTOs extended; no new endpoints |
| P8 — Traceability | ✅ Pass | Libro salida line items unchanged; saldo traces to escritura |

**Post-design re-check**: ✅ All gates pass.

**Governance follow-up**: Propose constitution §2.2 / §5 MINOR amendment after implementation (research R-007) to reflect new section layout and totales fixture.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-refactor-factura-montos/
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
│   └── 009_factura_totales.py              # NEW
├── src/
│   ├── models/
│   │   └── factura_principal.py            # MODIFY — 4 columns
│   ├── schemas/
│   │   └── factura.py                      # MODIFY — response fields
│   ├── services/
│   │   ├── calculo_factura.py              # MODIFY — calcular_totales + IVA
│   │   └── escritura_service.py            # MODIFY — FACTURA_FIELDS list
│   └── scripts/
│       └── seed_demo_data.py               # MODIFY — v4 + new fields
├── tests/
│   ├── unit/
│   │   ├── test_calcular_totales_factura.py # NEW — TDD first
│   │   └── test_calculo_factura.py          # MODIFY — canonical totales
│   ├── integration/
│   │   └── test_escrituras_api.py           # MODIFY — EXPECTED_FACTURA
│   └── helpers/
│       └── escritura_factory.py             # MODIFY

frontend/
├── src/
│   ├── components/escrituras/
│   │   └── FacturaDetalle.tsx               # MODIFY — 5 sections + Totales
│   ├── pages/
│   │   ├── EscrituraDetail.tsx              # MODIFY — label honorarios varios
│   │   └── ConfiguracionPage.tsx            # MODIFY — label if applicable
│   ├── types/api.ts                         # MODIFY
│   └── index.css                            # MODIFY — .factura-row--colegio
```

**Structure Decision**: Existing web app; no new routes. UI change concentrated in `FacturaDetalle.tsx`.

---

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

Key decisions:

- `total_factura` = Total + IVA; new columns for intermediates
- Migration `009` with backfill
- `calcular_totales_factura` pure function + `IVA_PCT` constant
- Demo seed v4; canonical totales documented
- No Figma (layout refactor only)

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

### Work Unit 1: Cálculo de Totales (TDD)

**Propósito**: Implementar y validar las nuevas fórmulas de Totales en el motor de cálculo puro.

**Entidades afectadas**: FacturaPrincipal (campos derivados)

**Archivos a crear/modificar**:

- `backend/tests/unit/test_calcular_totales_factura.py` — NEW (fail first)
- `backend/src/services/calculo_factura.py` — `calcular_totales_factura`, `IVA_PCT`, gastos excluidos
- `backend/tests/unit/test_calculo_factura.py` — asserts totales + actualizar `total_factura` esperado

**Pruebas de Paridad Legacy**:

- `test_calculo_factura.py` — línea items unchanged; totales nuevos

**Subtareas internas**:

1. Crear tests con fixture canónico (valores research.md R-003)
2. Implementar `calcular_totales_factura`
3. Integrar en `calcular_factura_completa`; remover fórmula antigua de `total_factura`
4. Verificar SC-005 (line items idénticos al fixture constitución)

**Criterio de éxito**: pytest unit calculo pasa; `total_factura` = 11_550_066.53 en fixture canónico.

**Estimación**: 3h

---

### Work Unit 2: Persistencia y migración

**Propósito**: Almacenar totales en DB y backfill datos existentes.

**Entidades afectadas**: FacturaPrincipal

**Archivos a crear/modificar**:

- `backend/alembic/versions/009_factura_totales.py` — NEW
- `backend/src/models/factura_principal.py` — 4 columnas
- `backend/src/schemas/factura.py` — DTO
- `backend/src/services/escritura_service.py` — `FACTURA_FIELDS`
- `backend/tests/helpers/escritura_factory.py` — campos nuevos

**Subtareas internas**:

1. Migración ADD nullable + backfill SQL/Python
2. Model + schema
3. Test migración opcional `test_migration_009_factura_totales.py`

**Criterio de éxito**: `alembic upgrade head` OK; GET escritura devuelve 4 campos nuevos.

**Dependencias**: WU-001

**Estimación**: 2h

---

### Work Unit 3: Integración API y tests

**Propósito**: Asegurar costo_total / saldo / integración alineados con Total + IVA.

**Entidades afectadas**: Escritura (saldo derivado)

**Archivos a crear/modificar**:

- `backend/tests/integration/test_escrituras_api.py` — `EXPECTED_FACTURA`
- `backend/tests/unit/test_pago_cliente_service.py` — si asserta totales
- `backend/scripts/demo_calculo.py` — imprimir totales (opcional)

**Subtareas internas**:

1. Actualizar `EXPECTED_FACTURA` con totales completos
2. Assert `costo_total` / `saldo_pendiente` = nuevo `total_factura`
3. Regresión pagos parciales

**Criterio de éxito**: integración escrituras + pagos cliente verdes.

**Dependencias**: WU-002

**Estimación**: 2h

---

### Work Unit 4: UI Factura Principal

**Propósito**: Reorganizar secciones, etiquetas y resaltado Colegio; mostrar Totales.

**Entidades afectadas**: FacturaPrincipal (presentación)

**Archivos a crear/modificar**:

- `frontend/src/components/escrituras/FacturaDetalle.tsx` — 5 secciones + Totales
- `frontend/src/index.css` — `.factura-row--colegio`
- `frontend/src/types/api.ts` — nuevos campos
- `frontend/src/pages/EscrituraDetail.tsx` — "Honorarios varios proyectados"

**Subtareas internas**:

1. `buildSections`: Honorarios, Honorarios varios, Corresponde (merged)
2. Sección Totales con 5 líneas; eliminar footer `factura-total` duplicado o alinear con Total + IVA
3. Clase visual Colegio en ítems FR-004
4. Labels: Precio base Valor, Total honorarios varios

**Criterio de éxito**: manual quickstart checklist UI; SC-001, SC-003.

**Dependencias**: WU-002 (API fields)

**Estimación**: 3h

---

### Work Unit 5: Seed demo y etiquetas secundarias

**Propósito**: Regenerar dataset demo y actualizar labels residuales.

**Entidades afectadas**: Demo escrituras, Configuracion labels

**Archivos a crear/modificar**:

- `backend/scripts/seed_demo_data.py` — `DEMO_SEED_VERSION=4`, `FACTURA_FIELDS`
- `frontend/src/pages/ConfiguracionPage.tsx` — "Leyes notariales" → "Honorarios varios" si aplica

**Subtareas internas**:

1. Bump seed version; wipe/recreate `[DEMO]`
2. Verificar pagos demo coherentes con nuevo saldo
3. Buscar strings "Leyes notariales" en frontend y actualizar

**Criterio de éxito**: seed idempotente; 42 escrituras demo con totales consistentes.

**Dependencias**: WU-001, WU-002

**Estimación**: 2h

---

### Notas para Itti-Kit

**Total estimado de Work Units**: 5  
**Tiempo total estimado**: ~12h  
**Work Units en paralelo posible**: WU-4 puede iniciar con mocks tras WU-1 (tipos); WU-3 tras WU-2

---

## Complexity Tracking

> No constitution violations requiring justification.

| Item | Notes |
|---|---|
| `total_factura` semantic change | Documented breaking change in quickstart; intentional per clarify |
| DB column `total_sin_iva` | Name avoids ambiguity with `total_factura` (Total + IVA) |

---

## Phase 2

**Status**: Pending — run `/spec-kitti.tasks` to generate `tasks.md` with TDD task ordering.

**Suggested next command**: `/spec-kitti.tasks`
