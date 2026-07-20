# Implementation Plan: Mejoras de Usabilidad en Escrituras y Marca

**Branch**: `004-escrituras-ui-mejoras` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/004-escrituras-ui-mejoras/spec.md`

---

## Summary

Frontend-only feature improving the **Escrituras list** (creation date column, sort, dual-row
pill filters, search, session persistence) and **Escritura detail layout** (two-column grid,
compact factura), plus app-wide rebranding to **Escribanía Barat** and renaming visible
**Pagos al Colegio** → **Pagos de la escribanía**.

Approach: extend existing React/Vite stack; pure functions + Vitest for list logic (Hybrid
testing per spec); **no backend or API changes** — consume existing `GET /escrituras` and
`GET /escribanos`.

---

## Technical Context

**Language/Version**: TypeScript/React 18 (frontend only) — backend unchanged  
**Primary Dependencies**: React, Vite, TanStack Query, React Router — no new packages  
**Storage**: N/A (sessionStorage for UI state only)  
**Testing**: Vitest (Hybrid — unit tests for `escrituraList.ts` + session helpers; no mandatory layout/CSS tests)  
**Target Platform**: Web (desktop ≥1024px two-column layout; mobile stacked)  
**Project Type**: Web application — `frontend/` only  
**Performance Goals**: Client search/sort on ≤500 escrituras imperceptible (<50ms); sessionStorage writes negligible  
**Constraints**: No API changes; no rename of `PagoColegio` code symbols; reuse existing CSS tokens  
**Scale/Scope**: ~15–20 files touched; 3 user stories; 0 migrations

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | No infra changes |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | Backend untouched |
| P4 — Frontend UX | ✅ Pass | Primary goal; secretary-facing list + detail improvements |
| P5 — Real-time via SSE | ✅ Pass | No change to SSE; existing invalidation preserved |
| P6 — Formula integrity | ✅ Pass | No calculation changes |
| P7 — Security baseline | ✅ Pass | No new endpoints; sessionStorage holds no secrets |
| P8 — Traceability | ✅ Pass | Unchanged |
| P10 — Figma MCP | ✅ N/A | No Figma reference; layout reuses existing design tokens (research R-009) |

**Post-design re-check**: ✅ All gates pass. No Complexity Tracking entries required.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-escrituras-ui-mejoras/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1 (delta)
├── contracts/
│   └── openapi-delta.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/spec-kitti.tasks)
```

### Source Code — Modified Files

```text
frontend/
├── src/
│   ├── utils/
│   │   ├── escrituraList.ts              # NEW — filterByNombre, sortByCreatedAt
│   │   └── escrituraList.test.ts         # NEW — Hybrid unit tests
│   ├── hooks/
│   │   └── useEscriturasListSession.ts   # NEW — sessionStorage read/write
│   ├── pages/
│   │   ├── EscriturasPage.tsx            # MODIFY — dual filters, search, session
│   │   ├── EscrituraDetail.tsx           # MODIFY — two-column grid
│   │   ├── LoginPage.tsx                 # MODIFY — brand
│   │   └── LibroSalidaPage.tsx           # MODIFY — terminology
│   ├── components/
│   │   ├── escrituras/
│   │   │   ├── EscrituraList.tsx         # MODIFY — created_at column, sort header
│   │   │   ├── FacturaDetalle.tsx        # MODIFY — two-column sections (class/CSS)
│   │   │   ├── PagoColegioForm.tsx       # MODIFY — visible labels only
│   │   │   └── PagoColegioList.tsx       # MODIFY — visible labels only
│   │   ├── layout/
│   │   │   └── Navbar.tsx                # MODIFY — brand
│   │   └── libros/
│   │       └── LibroSalidaTable.tsx      # MODIFY — terminology
│   └── index.css                         # MODIFY — grid columns, search bar, detail layout
```

**Structure Decision**: Monorepo web app; all implementation in `frontend/`. Backend and
OpenAPI root (`swagger/openapi.yaml`) unchanged — delta contract documents consumption only.

---

## Plan Jerárquico (para Itti-Kit)

### Work Unit 1: Utilidades de listado y persistencia de sesión

**Propósito**: Extraer lógica testeable de búsqueda, orden y estado de filtros.

**Entidades afectadas**:
- `EscriturasListSessionState` (frontend state)
- `EscrituraListItem` (consumo)

**Archivos a crear/modificar**:
- `frontend/src/utils/escrituraList.ts` — `filterByNombre`, `sortByCreatedAt`, `buildEscribanoFilterOptions`
- `frontend/src/utils/escrituraList.test.ts` — unit tests (Hybrid)
- `frontend/src/hooks/useEscriturasListSession.ts` — sessionStorage sync

**Pruebas de Paridad Legacy**: N/A (nueva lógica cliente)

**Subtareas internas**:
1. Implementar funciones puras de filtro y orden
2. Implementar serialización/deserialización de session state con defaults seguros
3. Escribir tests Vitest para combinación AND de criterios y sort asc/desc
4. Test de restauración de estado desde sessionStorage mock

**Criterio de éxito**: `npm run test -- escrituraList` verde; funciones exportadas documentadas.

**Estimación**: 3h

---

### Work Unit 2: Listado de escrituras — filtros, búsqueda, columna fecha

**Propósito**: Completar US1 — UI del listado con dos filas de píldoras, búsqueda y fecha.

**Entidades afectadas**: Escritura (listado), Escribano (filtro)

**Archivos a crear/modificar**:
- `frontend/src/pages/EscriturasPage.tsx`
- `frontend/src/components/escrituras/EscrituraList.tsx`
- `frontend/src/index.css` — grid columna extra, search input, segunda fila filtros

**Subtareas internas**:
1. Reemplazar tabs únicos por fila escribano + fila estado (estilo `.filter-tabs`)
2. Conectar `useEscrituras` con `escribano_id` + `estado` desde session hook
3. Agregar barra de búsqueda y aplicar `filterByNombre` en cliente
4. Agregar columna Fecha de creación con `formatDate`
5. Header clickeable para orden con indicador visual
6. Mensaje vacío contextual cuando filtros/búsqueda sin resultados
7. Integrar `useEscriturasListSession` para persistencia

**Criterio de éxito**: Acceptance scenarios US1 (1–9) verificables manualmente; filtros persisten al volver del detalle.

**Dependencias**: WU-1

**Estimación**: 5h

---

### Work Unit 3: Layout de detalle en dos columnas

**Propósito**: Completar US2 — reducir scroll en detalle de escritura.

**Entidades afectadas**: Factura principal, Pagos del cliente, Pagos de la escribanía (layout)

**Archivos a crear/modificar**:
- `frontend/src/pages/EscrituraDetail.tsx`
- `frontend/src/components/escrituras/FacturaDetalle.tsx`
- `frontend/src/index.css` — `.escritura-detail__grid`, `.factura-detalle` 2-col

**Subtareas internas**:
1. Mantener Saldo + Datos full-width arriba
2. Envolver Factura / Pagos en grid 2 columnas ≥1024px
3. Apilar Pagos cliente + Pagos escribanía en columna derecha
4. Distribuir subsecciones de factura en 2 columnas
5. Media query: stack vertical en mobile

**Criterio de éxito**: SC-003 — saldo + inicio factura/pagos visible con ≤1 pantalla scroll en desktop.

**Dependencias**: Ninguna (paralelo a WU-2)

**Estimación**: 4h

---

### Work Unit 4: Rebranding y terminología

**Propósito**: Completar US3 — Escribanía Barat + Pagos de la escribanía en toda la UI.

**Archivos a crear/modificar**:
- `Navbar.tsx`, `LoginPage.tsx`
- `EscrituraDetail.tsx`, `PagoColegioForm.tsx`, `PagoColegioList.tsx`
- `LibroSalidaPage.tsx`, `LibroSalidaTable.tsx`

**Subtareas internas**:
1. Reemplazar strings visibles "Contaduría Escribanía" → "Escribanía Barat"
2. Reemplazar "Pagos al Colegio" / "pago al Colegio" en UI visible
3. Verificar rutas principales (SC-004) sin tocar identificadores API/TS

**Criterio de éxito**: Grep en `frontend/src` sin matches de strings antiguos en JSX visible (excl. tipos/comentarios API).

**Dependencias**: WU-3 (EscrituraDetail overlap — puede mergearse en mismo PR)

**Estimación**: 2h

---

### Notas para Itti-Kit

**Total estimado de Work Units**: 4  
**Tiempo total estimado**: ~14h  
**Work Units en paralelo**: WU-2 y WU-3 tras WU-1

---

## Complexity Tracking

> No constitution violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

---

## Phase 0 & Phase 1 Artifacts

| Artifact | Path | Status |
|---|---|---|
| Research | [research.md](./research.md) | ✅ Complete |
| Data model | [data-model.md](./data-model.md) | ✅ Complete |
| API contract | [contracts/openapi-delta.yaml](./contracts/openapi-delta.yaml) | ✅ Complete (no-op delta) |
| Quickstart | [quickstart.md](./quickstart.md) | ✅ Complete |

**Next command**: `/spec-kitti.tasks` → `/spec-kitti.tasks.shape` → `/spec-kitti.implement`
