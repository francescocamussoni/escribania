# Implementation Plan: Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Branch**: `009-pagos-colegio-factura` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/009-pagos-colegio-factura/spec.md`

---

## Summary

Refinar **Pagos de la escribanía** a dos tipos (**Colegio** / **Otros**), eliminando la imputación 008
(honorarios varios). **Libro de Salida** solo agrega `pagos_colegio` (Colegio y Otros con detalle).
**Factura**: casillero por ítem de línea con `lineas_deshabilitadas`; `total_impuestos_efectivo` y
`costo_total` recalculados con una sola lectura. **Pago masivo** desde listado Escrituras con fecha
única. **TDD-first** (migration `012`).

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic; React + Vite, TanStack Query — no new packages  
**Storage**: PostgreSQL 16 — migration `012` (`lineas_deshabilitadas`, `pagos_colegio.tipo`)  
**Testing**: pytest + pytest-asyncio (**TDD-first**); Vitest for bulk UI + factura toggles  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: Bulk preview ≤ 500ms for 50 escrituras (local); libro salida query unchanged complexity  
**Constraints**: SSE invalidation; depends on 007 totales + 008 plazo UI (badge/sort retained)  
**Scale/Scope**: ~20 backend files, ~12 frontend files, 1 migration

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | Migration `012` + Docker/RDS |
| P2 — Cost-conscious AWS | ✅ Pass | No new services |
| P3 — Python backend | ✅ Pass | `factura_lineas.py`, `pago_colegio_bulk_service.py` |
| P4 — Frontend UX | ✅ Pass | Toggles en factura; bulk en listado; 2-option payment form |
| P5 — Real-time via SSE | ✅ Pass | `pago_colegio.created` + `escritura.updated` on line toggles |
| P6 — Formula integrity | ✅ Pass | Pure `aplicar_lineas_habilitadas`; canonical fixture tests |
| P7 — Security baseline | ✅ Pass | DTOs; `extra=forbid`; bulk max 100 items; auth unchanged |
| P8 — Traceability | ✅ Pass | Libro líneas → escritura + pago id |

**Post-design re-check**: ✅ All gates pass.

**Note (constitution §2.4)**: Libro de Salida ahora incluye pagos **Otros** además de Colegio — alineado
con operación real (spec clarify); impuestos 006 y gastos 005 fuera del libro.

---

## Project Structure

### Documentation (this feature)

```text
specs/009-pagos-colegio-factura/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/openapi-delta.yaml
├── checklists/requirements.md
└── tasks.md                    # Phase 2 (/spec-kitti.tasks)
```

### Source Code — New and Modified Files

```text
backend/
├── alembic/versions/
│   └── 012_pagos_colegio_factura_lineas.py          # NEW
├── src/
│   ├── models/
│   │   ├── pago_colegio.py                          # MODIFY — TipoPagoEscribania
│   │   └── factura_principal.py                     # MODIFY — lineas_deshabilitadas
│   ├── schemas/
│   │   ├── pago_colegio.py                          # MODIFY — tipo, drop imputacion
│   │   ├── pago_colegio_bulk.py                     # NEW
│   │   ├── factura.py                               # MODIFY — lineas + efectivos
│   │   ├── escritura.py                             # MODIFY — lineas_deshabilitadas input
│   │   └── libros.py                                # MODIFY — tipo_pago on linea
│   ├── services/
│   │   ├── factura_lineas.py                        # NEW — catalog + mask (TDD)
│   │   ├── calculo_factura.py                       # MODIFY — accept disabled keys
│   │   ├── plazo_colegio.py                         # MODIFY — sum colegio tipo
│   │   ├── pago_colegio_service.py                  # MODIFY — tipo validation
│   │   ├── pago_colegio_bulk_service.py             # NEW
│   │   ├── escritura_service.py                     # MODIFY — saldo efectivo, plazo
│   │   └── libros_service.py                        # MODIFY — salida solo colegio
│   ├── api/routes/
│   │   ├── pagos_colegio.py                         # MODIFY
│   │   └── escrituras.py                            # MODIFY — bulk routes
│   └── scripts/
│       └── seed_demo_data.py                        # MODIFY — v6
├── tests/
│   ├── unit/
│   │   ├── test_factura_lineas.py                   # NEW — TDD first
│   │   ├── test_plazo_colegio.py                    # MODIFY
│   │   ├── test_libros_service.py                   # MODIFY
│   │   ├── test_pago_colegio_service.py             # MODIFY
│   │   └── test_pago_colegio_bulk.py                # NEW
│   └── integration/
│       ├── test_pagos_colegio_bulk_api.py           # NEW
│       └── test_escrituras_api.py                   # MODIFY

frontend/
├── src/
│   ├── components/escrituras/
│   │   ├── PagoColegioForm.tsx                      # MODIFY — tipo Colegio/Otros
│   │   ├── PagoColegioList.tsx                      # MODIFY — show tipo
│   │   ├── FacturaDetalle.tsx                       # MODIFY — line toggles
│   │   ├── EscrituraList.tsx                        # MODIFY — checkboxes + bulk action
│   │   └── PagoColegioBulkModal.tsx                 # NEW
│   ├── components/libros/
│   │   └── LibroSalidaTable.tsx                     # MODIFY — tipo + detalle
│   ├── api/
│   │   └── pagosColegio.ts                          # MODIFY — bulk + tipo
│   ├── types/api.ts                                 # MODIFY
│   └── utils/
│       └── tipoPagoEscribania.ts                     # NEW (replaces imputacionColegio.ts)
```

**Structure Decision**: Monorepo existente `backend/` + `frontend/`; sin nuevos módulos top-level.

---

## Plan Jerárquico (para Spec-Kitti)

### Work Unit 1: Líneas de factura habilitables (backend core)

**Propósito**: Persistir y calcular montos efectivos por ítem de línea; recalcular costo_total y
total_impuestos_efectivo.

**Entidades afectadas**: `FacturaPrincipal`, `Escritura` (saldo derivado)

**Archivos**:
- `backend/src/services/factura_lineas.py` — NEW
- `backend/src/services/calculo_factura.py` — MODIFY
- `backend/src/services/escritura_service.py` — MODIFY
- `backend/alembic/versions/012_*.py` — column `lineas_deshabilitadas`
- `backend/tests/unit/test_factura_lineas.py` — NEW (TDD first)

**Criterio de éxito**: Fixture constitución — deshabilitar `municipio` reduce costo_total exacto;
deshabilitar `sellos` reduce total_impuestos_efectivo y no afecta honorarios.

**Estimación**: 6h

---

### Work Unit 2: Tipo Colegio/Otros en pagos_colegio

**Propósito**: Reemplazar imputación 008; validar detalle obligatorio en Otros; migración datos.

**Entidades afectadas**: `PagoColegio`

**Archivos**:
- `backend/src/models/pago_colegio.py`
- `backend/src/schemas/pago_colegio.py`
- `backend/src/services/pago_colegio_service.py`
- `backend/tests/unit/test_pago_colegio_service.py`

**Criterio de éxito**: API rechaza otros sin concepto; pagos colegio reducen pendiente; migración
012 backfill correcto.

**Dependencias**: WU-1 (pendiente usa total_impuestos_efectivo)

**Estimación**: 4h

---

### Work Unit 3: Plazo colegio + Libro de Salida

**Propósito**: Ajustar plazo a tipo colegio + referencia efectiva; libro solo pagos_colegio.

**Entidades afectadas**: PlazoColegio (derived), LibroSalida

**Archivos**:
- `backend/src/services/plazo_colegio.py`
- `backend/src/services/libros_service.py`
- `backend/src/schemas/libros.py`
- `backend/tests/unit/test_plazo_colegio.py`
- `backend/tests/unit/test_libros_service.py`

**Criterio de éxito**: Libro salida excluye impuesto escribanía y gastos extraordinarios; línea Otros
muestra detalle; SC-005 plazo Pagado tras cubrir efectivo.

**Dependencias**: WU-1, WU-2

**Estimación**: 4h

---

### Work Unit 4: Pago masivo al Colegio (API)

**Propósito**: Preview + confirm bulk con fecha única.

**Archivos**:
- `backend/src/services/pago_colegio_bulk_service.py` — NEW
- `backend/src/api/routes/escrituras.py` — bulk routes
- `backend/tests/unit/test_pago_colegio_bulk.py`
- `backend/tests/integration/test_pagos_colegio_bulk_api.py`

**Criterio de éxito**: POST bulk crea N pagos colegio misma fecha; preview excluye cerradas/sin pendiente.

**Dependencias**: WU-2, WU-3

**Estimación**: 5h

---

### Work Unit 5: Frontend — Factura toggles + formulario pagos

**Propósito**: UI casilleros por línea; form Colegio/Otros; lista pagos.

**Archivos**:
- `frontend/src/components/escrituras/FacturaDetalle.tsx`
- `frontend/src/components/escrituras/PagoColegioForm.tsx`
- `frontend/src/components/escrituras/PagoColegioList.tsx`
- `frontend/src/types/api.ts`

**Criterio de éxito**: Toggles persisten vía PATCH escritura; form sin imputación; otros exige detalle.

**Dependencias**: WU-1, WU-2 (API)

**Estimación**: 6h

---

### Work Unit 6: Frontend — Listado bulk + Libro Salida

**Propósito**: Selección múltiple, modal bulk, tabla libro con tipo/detalle.

**Archivos**:
- `frontend/src/components/escrituras/EscrituraList.tsx`
- `frontend/src/components/escrituras/PagoColegioBulkModal.tsx` — NEW
- `frontend/src/components/libros/LibroSalidaTable.tsx`
- `frontend/src/api/pagosColegio.ts`

**Criterio de éxito**: Flujo masivo end-to-end; libro muestra solo pagos escribanía; SSE refresh.

**Dependencias**: WU-4, WU-5

**Estimación**: 5h

---

### Work Unit 7: Seed demo + documentación delta

**Propósito**: `DEMO_SEED_VERSION=6`; validar quickstart manual.

**Archivos**:
- `backend/scripts/seed_demo_data.py`
- `specs/009-pagos-colegio-factura/quickstart.md` (validado)

**Criterio de éxito**: Demo carga sin error; checklist manual quickstart pasable.

**Dependencias**: WU-1–6

**Estimación**: 2h

---

### Notas para Spec-Kitti

**Total Work Units**: 7  
**Tiempo estimado**: ~32h  
**Paralelo posible**: WU-5 puede iniciar mocks tras WU-1 contratos; WU-6 tras WU-4.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Libro Salida ya no incluye egresos 006/005 | Spec FR-007 — libro = solo solapa escribanía | Mantener mezcla contradice operación acordada |
| JSONB `lineas_deshabilitadas` | ~30 flags por factura, default all-enabled | Tabla normalizada añade joins sin beneficio |

---

## Phase 0 / Phase 1 Artifacts

| Artifact | Path | Status |
|---|---|---|
| Research | [research.md](./research.md) | ✅ Complete |
| Data model | [data-model.md](./data-model.md) | ✅ Complete |
| API contract | [contracts/openapi-delta.yaml](./contracts/openapi-delta.yaml) | ✅ Complete |
| Quickstart | [quickstart.md](./quickstart.md) | ✅ Complete |

**Next command**: `/spec-kitti.tasks`
