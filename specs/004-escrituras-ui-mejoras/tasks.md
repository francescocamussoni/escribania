# Tasks: Mejoras de Usabilidad en Escrituras y Marca

**Feature Branch**: `004-escrituras-ui-mejoras`  
**Input**: `specs/004-escrituras-ui-mejoras/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: Hybrid — unit tests obligatorios para lógica de listado (`escrituraList.ts`, session); sin TDD estricto en layout/CSS (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature (research R-009, plan Constitution P10 N/A). Reutilizar tokens y componentes existentes (`index.css`, `.filter-tabs`, `.detail-card`). El campo `figma:` **no aplica** — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario correspondiente (US1–US3)
- **Backend**: Sin cambios de API ni migraciones (contracts/openapi-delta.yaml documenta consumo existente)

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar contexto de diseño y entorno frontend antes de implementar.

- [x] T001 Revisar alineación entre `specs/004-escrituras-ui-mejoras/spec.md`, `plan.md` y `contracts/openapi-delta.yaml` (sin cambios de API esperados)
- [x] T002 Confirmar que `GET /escrituras` expone `created_at`, `escribano_id` y query params `estado`/`escribano_id` en `backend/src/api/routes/escrituras.py`
- [x] T003 [P] Verificar que `cd frontend && npm run test` ejecuta Vitest correctamente antes de agregar nuevos tests

**Checkpoint**: Documentación alineada. API existente confirmada. Toolchain frontend operativa.

---

## Phase 2: Foundational — Utilidades de listado y sesión (BLOCKING)

**Purpose**: Lógica pura testeable y persistencia de estado del listado. Bloquea US1.

**⚠️ CRITICAL**: US1 no puede completarse hasta que esta fase esté verde.

### Tests — Foundational (Hybrid)

- [x] T004 [P] Escribir `frontend/src/utils/escrituraList.test.ts`: `filterByNombre` (case-insensitive, parcial, vacío)
- [x] T005 [P] Extender `frontend/src/utils/escrituraList.test.ts`: `sortByCreatedAt` (asc/desc, estabilidad)
- [x] T006 [P] Extender `frontend/src/utils/escrituraList.test.ts`: `buildEscribanoFilterOptions` (intersección escribanos ∩ escrituras)
- [x] T007 [P] Escribir tests de `useEscriturasListSession` (o helpers exportados): serialización, defaults, JSON inválido → fallback

### Implementación — Foundational

- [x] T008 Crear `frontend/src/utils/escrituraList.ts` con `filterByNombre`, `sortByCreatedAt`, `buildEscribanoFilterOptions`, tipos `SortDirection`
- [x] T009 Crear `frontend/src/hooks/useEscriturasListSession.ts`: leer/escribir `sessionStorage` clave `escrituras-list-state` (`escribanoFilter`, `estadoFilter`, `searchQuery`, `sortDirection`); defaults según data-model.md
- [x] T010 Ejecutar `cd frontend && npm run test -- escrituraList` hasta verde; ajustar implementación si fallan T004–T007

**Checkpoint**: Utilidades y hook de sesión listos. Tests unitarios verdes.

---

## Phase 3: User Story 1 — Encontrar y Filtrar Escrituras (Priority: P1) 🎯 MVP

**Goal**: Listado con fecha de creación, orden, dos filas de píldoras (escribano + estado), búsqueda por nombre y persistencia en sesión.

**Independent Test**: En `/escrituras`, aplicar filtros escribano+estado, buscar por nombre, ordenar por fecha, abrir detalle y volver — criterios conservados (spec US1 escenarios 1–9).

### Implementación — US1

- [x] T011 [US1] Modificar `frontend/src/pages/EscriturasPage.tsx`: reemplazar tabs únicos por fila escribano (`Todas` + píldoras por escribano) y fila estado (`Todas`/`Abiertas`/`Cerradas`); conectar `useEscriturasListSession`
- [x] T012 [US1] Modificar `frontend/src/pages/EscriturasPage.tsx`: pasar `escribano_id` y `estado` a `useEscrituras` según filtros activos; cargar escribanos con `useEscribanos(true)` y `buildEscribanoFilterOptions`
- [x] T013 [US1] Modificar `frontend/src/pages/EscriturasPage.tsx`: agregar barra de búsqueda; aplicar `filterByNombre` y `sortByCreatedAt` en cliente sobre datos del query
- [x] T014 [US1] Modificar `frontend/src/components/escrituras/EscrituraList.tsx`: agregar columna Fecha de creación con `formatDate(item.created_at)`
- [x] T015 [US1] Modificar `frontend/src/components/escrituras/EscrituraList.tsx`: header clickeable de fecha con indicador asc/desc; callback `onSortToggle` desde página
- [x] T016 [US1] Modificar `frontend/src/components/escrituras/EscrituraList.tsx`: mensaje explícito cuando `items.length === 0` y hay filtros/búsqueda activos (FR-008)
- [x] T017 [P] [US1] Modificar `frontend/src/index.css`: ampliar grid `.escritura-list--saldo` para columna fecha; estilos `.escrituras-page__search` y segunda fila `.filter-tabs`
- [x] T018 [US1] Validar persistencia: navegar a `/escrituras/:id` y volver; cambiar a liquidación y regresar — estado conservado en misma pestaña (FR-008a)

**Checkpoint**: US1 completa. MVP funcional en listado de escrituras.

---

## Phase 4: User Story 2 — Detalle con Menos Desplazamiento (Priority: P2)

**Goal**: Layout en dos columnas bajo Saldo/Datos; factura principal compacta en 2 columnas internas.

**Independent Test**: En `/escrituras/:id` en desktop ≥1024px, ver Saldo + inicio de factura o pagos con ≤1 pantalla de scroll; en mobile, secciones apiladas (spec US2).

**Dependencia**: Puede iniciarse en paralelo con US1 tras Phase 2 (archivos distintos salvo `index.css` — coordinar merges).

### Implementación — US2

- [x] T019 [P] [US2] Modificar `frontend/src/pages/EscrituraDetail.tsx`: envolver Factura principal y columna de pagos en contenedor `.escritura-detail__grid` (izq. factura, der. pagos cliente + pagos escribanía apilados)
- [x] T020 [P] [US2] Modificar `frontend/src/components/escrituras/FacturaDetalle.tsx`: aplicar clase/layout para subsecciones en dos columnas; total factura full-width al pie
- [x] T021 [US2] Modificar `frontend/src/index.css`: reglas `.escritura-detail__grid` (2 cols ≥1024px, 1 col mobile) y `.factura-detalle` grid 2 columnas
- [x] T022 [US2] Verificar orden de apilado mobile: saldo → datos → factura → pagos cliente → pagos escribanía (FR-013)

**Checkpoint**: US2 completa. Detalle más compacto en desktop sin pérdida de información.

---

## Phase 5: User Story 3 — Marca y Terminología (Priority: P3)

**Goal**: "Escribanía Barat" en toda la app; "Pagos de la escribanía" en toda UI visible (sin renombrar APIs/tipos).

**Independent Test**: Revisar login, navbar, detalle, libro salida — sin strings "Contaduría Escribanía" ni "Pagos al Colegio" en JSX visible (spec US3, SC-004).

### Implementación — US3

- [x] T023 [P] [US3] Modificar `frontend/src/components/layout/Navbar.tsx`: reemplazar marca por "Escribanía Barat"
- [x] T024 [P] [US3] Modificar `frontend/src/pages/LoginPage.tsx`: reemplazar título por "Escribanía Barat"
- [x] T025 [P] [US3] Modificar `frontend/src/pages/EscrituraDetail.tsx`: título sección "Pagos de la escribanía" (mantener componentes `PagoColegio*`)
- [x] T026 [P] [US3] Modificar `frontend/src/components/escrituras/PagoColegioForm.tsx`: labels y mensajes de error con "pago de la escribanía"
- [x] T027 [P] [US3] Modificar `frontend/src/components/escrituras/PagoColegioList.tsx`: mensaje vacío "Pagos de la escribanía"
- [x] T028 [P] [US3] Modificar `frontend/src/pages/LibroSalidaPage.tsx` y `frontend/src/components/libros/LibroSalidaTable.tsx`: terminología "Pagos de la escribanía"
- [x] T029 [US3] Grep en `frontend/src/`: confirmar ausencia de strings visibles antiguos; excluir tipos API, rutas `/pagos-colegio`, eventos SSE

**Checkpoint**: US3 completa. Rebranding y terminología consistentes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validación final, regresión y documentación.

- [x] T030 [P] Ejecutar `cd frontend && npm run test` — suite completa verde
- [x] T031 [P] Ejecutar `cd frontend && npm run build` — sin errores TypeScript
- [ ] T032 Validar checklist manual en `specs/004-escrituras-ui-mejoras/quickstart.md` (listado, detalle, marca, regresión SC-005)
- [x] T033 [P] Actualizar `specs/004-escrituras-ui-mejoras/quickstart.md` si algún paso de validación difiere del comportamiento final

**Checkpoint**: Feature lista para merge. Sin regresiones en flujos críticos.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) — BLOCKS US1
    ↓
    ├── Phase 3 (US1) — MVP
    ├── Phase 4 (US2) — paralelo tras Phase 2 (cuidado con index.css)
    └── Phase 5 (US3) — paralelo; T025 toca EscrituraDetail tras T019
    ↓
Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depende de | Independiente para probar |
|-------|------------|---------------------------|
| US1 (P1) | Phase 2 | ✅ Listado `/escrituras` |
| US2 (P2) | Phase 2 | ✅ Detalle `/escrituras/:id` |
| US3 (P3) | Ninguna (salvo T025 + T019 mismo archivo) | ✅ Copy en rutas principales |

### Within Each User Story

- Foundational: tests T004–T007 antes o junto con T008–T009 (Hybrid, no bloqueante estricto)
- US1: T011–T013 (página) antes de T014–T016 (lista); T017 CSS en paralelo
- US2: T019–T020 en paralelo; T021 CSS después
- US3: T023–T028 todos [P] excepto T029 verificación final

---

## Parallel Execution Examples

### Foundational (tras T001–T003)

```bash
# Tests en paralelo:
T004 filterByNombre tests
T005 sortByCreatedAt tests
T006 buildEscribanoFilterOptions tests
T007 session tests
```

### User Story 1 (tras Phase 2)

```bash
T017 index.css list styles   # [P] con T014–T016 si coordinan grid columns
```

### User Story 2 + US3 (tras Phase 2)

```bash
# Diferentes archivos en paralelo:
T019 EscrituraDetail layout
T023 Navbar brand
T024 LoginPage brand
T026 PagoColegioForm labels
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1)
3. **STOP and VALIDATE** — quickstart checklist sección listado
4. Demo/deploy si aplica

### Incremental Delivery

1. Setup + Foundational → utilidades listas
2. US1 → MVP listado mejorado
3. US2 → layout detalle
4. US3 → marca y terminología
5. Polish → regresión completa

### Suggested MVP Scope

**Phases 1–3 (T001–T018)** — entrega valor inmediato en pantalla principal sin depender de layout detalle ni rebranding.

---

## Task Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| Setup | T001–T003 (3) | — |
| Foundational | T004–T010 (7) | — |
| US1 — Listado | T011–T018 (8) | P1 🎯 |
| US2 — Detalle layout | T019–T022 (4) | P2 |
| US3 — Marca | T023–T029 (7) | P3 |
| Polish | T030–T033 (4) | — |
| **Total** | **33 tasks** | |

**Parallel opportunities**: 18 tasks marcadas `[P]`  
**Independent test criteria**: US1 → listado; US2 → detalle layout; US3 → copy en rutas principales

---

## Notes

- No modificar `backend/`, `swagger/openapi.yaml`, nombres `PagoColegio*`, rutas `/pagos-colegio` ni eventos `pago_colegio.created`
- Orden default listado: `created_at` descendente (spec Assumptions)
- Filtros servidor: `escribano_id` + `estado`; búsqueda y orden: cliente (research R-002)
- Conflictos probables en `index.css` y `EscrituraDetail.tsx` si US2 y US3 corren en paralelo — serializar merges en esos archivos
