# Implementation Plan: Pagos del Cliente y Libros Contables Basados en Caja Real

**Branch**: `003-pagos-cliente` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/003-pagos-cliente/spec.md`

---

## Summary

Refactor the Contaduría Escribanía platform from a **fictional cash-flow model** (auto-derived
libros and projected liquidación) to a **real cash model** where money only exists when recorded:

1. Replace `GastoAdicional` (entrada/salida) with **`PagoCliente`** and **`PagoColegio`** —
   append-only payment records per escritura.
2. Expose **saldo pendiente** (`costo_total − total_pagado`) on every escritura; block cierre
   unless `saldo_pendiente = 0`.
3. **Libro de Entrada** = client payments by payment date + debt summary.
4. **Libro de Salida** = manual colegio payments by payment date (disconnected from client cobro).
5. **Liquidación** and **Pago de Salarios** (escribanos) = lump-sum client payments received
   in the month (not projected factura totals).

Approach: extend existing FastAPI/PostgreSQL/React stack; Alembic migration; TDD throughout.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend) — unchanged  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic (backend); React + Vite, TanStack Query (frontend) — no new packages  
**Storage**: PostgreSQL 16 — new tables `pagos_cliente`, `pagos_colegio`; drop `gastos_adicionales`  
**Testing**: pytest + pytest-asyncio (TDD — tests before implementation per spec); Vitest (frontend)  
**Target Platform**: ECS Fargate + RDS (unchanged)  
**Project Type**: Web application — existing `backend/` + `frontend/`  
**Performance Goals**: Saldo update ≤ 3s (SC-001); SSE propagation ≤ 2s (SC-006)  
**Constraints**: No polling; append-only payments; migration must be idempotent; breaking API change on `LiquidacionEscrituraItem`  
**Scale/Scope**: < 10 concurrent users; migrates all historical `gastos_adicionales` data

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| P1 — Symmetric environments | ✅ Pass | No new external services; migration runs identically local/Docker/RDS |
| P2 — Cost-conscious AWS | ✅ Pass | No new AWS services |
| P3 — Python backend | ✅ Pass | All logic in Python services |
| P4 — Frontend UX | ✅ Pass | Escritura detail gains clear Pagos del Cliente / Pagos al Colegio sections; list shows saldo |
| P5 — Real-time via SSE | ✅ Pass | New events `pago_cliente.created`, `pago_colegio.created`; invalidate libros + liquidación |
| P6 — Formula integrity | ✅ Pass | `pago_saldo.py` pure functions; factura calc unchanged; new logic fully unit-tested |
| P7 — Security baseline | ✅ Pass | Server-side monto validation; DTOs only; auth on all endpoints |
| P8 — Traceability | ✅ Pass | Every libro/liquidación line includes `escritura_id` + `escritura_nombre` |

**Post-design re-check**: ✅ All gates pass.

**Governance note**: Constitution §2.3 (Gastos Adicionales) and §2.4 (libros derivados) are
superseded by this feature — see Complexity Tracking.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-pagos-cliente/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1 (delta)
├── contracts/
│   └── openapi-patch.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/spec-kitti.tasks)
```

### Source Code — New and Modified Files

```text
backend/
├── alembic/versions/
│   └── 006_pagos_cliente.py              # NEW — tables + data migration + drop gastos
├── src/
│   ├── models/
│   │   ├── pago_cliente.py               # NEW
│   │   ├── pago_colegio.py               # NEW
│   │   ├── escritura.py                  # MODIFY — relationships
│   │   └── gasto_adicional.py            # DELETE after migration
│   ├── schemas/
│   │   ├── pago_cliente.py               # NEW
│   │   ├── pago_colegio.py               # NEW
│   │   ├── escritura.py                  # MODIFY — saldo fields, pagos lists
│   │   ├── libros.py                     # MODIFY — DeudaResumen, fecha_pago
│   │   ├── liquidacion.py                # MODIFY — monto_cobrado
│   │   └── gasto.py                      # DELETE
│   ├── services/
│   │   ├── pago_saldo.py                 # NEW — pure functions
│   │   ├── pago_cliente_service.py       # NEW
│   │   ├── pago_colegio_service.py       # NEW
│   │   ├── escritura_service.py          # MODIFY — close guard, remove add_gasto
│   │   ├── libros_service.py             # MODIFY — payment-based derivation
│   │   ├── liquidacion_service.py        # MODIFY — payment-month scoping
│   │   └── salario_service.py            # MODIFY — use new liquidación items
│   ├── api/routes/
│   │   ├── pagos_cliente.py              # NEW — POST /escrituras/{id}/pagos-cliente
│   │   ├── pagos_colegio.py              # NEW — POST /escrituras/{id}/pagos-colegio
│   │   ├── gastos.py                     # DELETE or 410 Gone
│   │   └── router.py                     # MODIFY — wire new routes
│   └── services/
│       └── escritura_errors.py           # MODIFY — EscrituraSaldoPendienteError
├── tests/
│   ├── unit/
│   │   ├── test_pago_saldo.py            # NEW — TDD first
│   │   ├── test_pago_cliente_service.py  # NEW
│   │   ├── test_pago_colegio_service.py  # NEW
│   │   ├── test_libros_service.py        # MODIFY — rewrite derivation tests
│   │   └── test_liquidacion.py           # MODIFY — payment-based tests
│   └── integration/
│       ├── test_pagos_cliente_api.py     # NEW
│       ├── test_pagos_colegio_api.py     # NEW
│       ├── test_libros_api.py            # MODIFY
│       ├── test_liquidacion_api.py       # MODIFY
│       └── test_escrituras_api.py        # MODIFY — close guard, saldo fields

frontend/
├── src/
│   ├── api/
│   │   ├── pagosCliente.ts               # NEW
│   │   ├── pagosColegio.ts               # NEW
│   │   ├── escrituras.ts                 # MODIFY — saldo types
│   │   ├── libros.ts                     # MODIFY — resumen_deudas
│   │   └── gastos.ts                     # DELETE
│   ├── hooks/
│   │   ├── usePagosCliente.ts            # NEW
│   │   ├── usePagosColegio.ts            # NEW
│   │   ├── useSSE.ts                     # MODIFY — new event types
│   │   └── useLibros.ts                  # MODIFY
│   ├── components/
│   │   ├── escrituras/
│   │   │   ├── PagoClienteForm.tsx       # NEW (replaces GastoForm)
│   │   │   ├── PagoClienteList.tsx       # NEW
│   │   │   ├── PagoColegioForm.tsx       # NEW
│   │   │   ├── PagoColegioList.tsx       # NEW
│   │   │   ├── EscrituraForm.tsx         # MODIFY — remove gastos
│   │   │   └── EscrituraList.tsx         # MODIFY — saldo columns
│   │   ├── libros/
│   │   │   ├── LibroEntradaTable.tsx     # MODIFY — payments + debt summary
│   │   │   └── LibroSalidaTable.tsx      # MODIFY — colegio payments only
│   │   └── liquidacion/
│   │       └── EscribanoCard.tsx         # MODIFY — monto_cobrado
│   ├── pages/
│   │   ├── EscrituraDetail.tsx           # MODIFY — dual payment sections
│   │   ├── LibroEntradaPage.tsx          # MODIFY
│   │   ├── LibroSalidaPage.tsx           # MODIFY
│   │   └── LiquidacionPage.tsx           # MODIFY
│   └── types/
│       └── api.ts                        # MODIFY — new types, remove GastoAdicional
```

**Structure Decision**: Web application (Option 2) — extends existing `backend/` + `frontend/` from features 001/002.

---

## Plan Jerárquico (para Itti-Kit)

### Work Unit 1: Migración DB + Modelos PagoCliente / PagoColegio

**Propósito**: Fundación de datos — tablas nuevas, migración de `gastos_adicionales`, eliminación del modelo legacy.

**Entidades afectadas**:
- `PagoCliente` (NEW)
- `PagoColegio` (NEW)
- `GastoAdicional` (REMOVED)

**Archivos a crear/modificar**:
- `backend/alembic/versions/006_pagos_cliente.py`
- `backend/src/models/pago_cliente.py`
- `backend/src/models/pago_colegio.py`
- `backend/src/models/escritura.py` — relationships
- `backend/src/models/__init__.py`

**Subtareas internas**:
1. Escribir migration test / smoke script para idempotencia
2. Crear tablas con índices en `escritura_id` y `fecha`
3. Migrar datos entrada → `pagos_cliente`, salida → `pagos_colegio`
4. Insertar pagos implícitos para escrituras cerradas (FR-035)
5. Drop `gastos_adicionales` y enum `direccion_gasto`
6. Registrar modelos SQLAlchemy y relationships en Escritura

**Criterio de éxito**: `alembic upgrade head` idempotente; cero filas en `gastos_adicionales`; escrituras cerradas tienen al menos un `pago_cliente`.

**Estimación**: 4 horas

---

### Work Unit 2: Saldo + Pagos del Cliente (backend, TDD)

**Propósito**: Lógica core de caja entrante — registro de pagos, cálculo de saldo, guard de cierre.

**Entidades afectadas**: `PagoCliente`, `Escritura` (computed saldo)

**Archivos a crear/modificar**:
- `backend/src/services/pago_saldo.py`
- `backend/src/services/pago_cliente_service.py`
- `backend/src/schemas/pago_cliente.py`
- `backend/src/schemas/escritura.py` — saldo fields
- `backend/src/api/routes/pagos_cliente.py`
- `backend/src/services/escritura_service.py` — close guard, remove `add_gasto_adicional`
- `backend/tests/unit/test_pago_saldo.py`
- `backend/tests/unit/test_pago_cliente_service.py`
- `backend/tests/integration/test_pagos_cliente_api.py`
- `backend/tests/integration/test_escrituras_api.py` — close + saldo

**Subtareas internas**:
1. TDD: `calc_saldo`, `can_close`, sobrepago flag
2. TDD: registrar pago válido, rechazar monto > saldo, rechazar en cerrada
3. TDD: `close_escritura` bloquea con saldo > 0, éxito con saldo = 0
4. Implementar `POST /escrituras/{id}/pagos-cliente`
5. Extender `GET /escrituras/{id}` y list con `costo_total`, `total_pagado`, `saldo_pendiente`
6. SSE: `pago_cliente.created` + `liquidacion.updated` + `libros_updated`

**Criterio de éxito**: Todos los tests unit/integration pasan; SC-001 y SC-002 verificados.

**Estimación**: 6 horas

**Dependencias**: WU-1

---

### Work Unit 3: Pagos al Colegio (backend, TDD)

**Propósito**: Registro manual de egresos al Colegio, independiente del cobro al cliente.

**Entidades afectadas**: `PagoColegio`

**Archivos a crear/modificar**:
- `backend/src/services/pago_colegio_service.py`
- `backend/src/schemas/pago_colegio.py`
- `backend/src/api/routes/pagos_colegio.py`
- `backend/tests/unit/test_pago_colegio_service.py`
- `backend/tests/integration/test_pagos_colegio_api.py`

**Subtareas internas**:
1. TDD: registrar pago colegio en escritura con saldo pendiente del cliente (debe pasar)
2. TDD: rechazar monto ≤ 0, rechazar en escritura cerrada
3. TDD: no validar contra leyes notariales proyectadas
4. Implementar `POST /escrituras/{id}/pagos-colegio`
5. Exponer `total_leyes_notariales_proyectadas` en escritura detail (read-only)
6. SSE: `pago_colegio.created` + `libros_updated`
7. Eliminar o deprecar `POST /escrituras/{id}/gastos` (410 Gone)

**Criterio de éxito**: Pago colegio registrable sin pago del cliente; referencia informativa presente en response.

**Estimación**: 4 horas

**Dependencias**: WU-1

---

### Work Unit 4: Libros Contables — Caja Real (backend, TDD)

**Propósito**: Reescribir derivación de Libro de Entrada y Salida basada en pagos reales.

**Entidades afectadas**: `EntradaLibro`, `SalidaLibro` (derived)

**Archivos a crear/modificar**:
- `backend/src/services/libros_service.py` — full rewrite
- `backend/src/schemas/libros.py` — `DeudaResumenItem`, `fecha_pago`
- `backend/tests/unit/test_libros_service.py` — rewrite
- `backend/tests/integration/test_libros_api.py` — rewrite

**Subtareas internas**:
1. TDD: entrada solo contiene `PagoCliente` del mes (no honorarios derivados)
2. TDD: entrada incluye `resumen_deudas` para escrituras abiertas con saldo > 0
3. TDD: salida solo contiene `PagoColegio` del mes (no factura items)
4. TDD: filtro por `fecha` del pago, no `created_at` de escritura
5. Implementar endpoints actualizados
6. Verificar totales = suma de líneas

**Criterio de éxito**: SC-003, SC-004, SC-005 verificados en tests.

**Estimación**: 5 horas

**Dependencias**: WU-2, WU-3

---

### Work Unit 5: Liquidación y Pago de Salarios — Caja Real (backend, TDD)

**Propósito**: Recalcular liquidación y salarios de escribanos desde pagos reales del mes (montón único).

**Entidades afectadas**: `LiquidacionMensual`, `PagoSalario` (escribanos block)

**Archivos a crear/modificar**:
- `backend/src/services/liquidacion_service.py` — payment-month query
- `backend/src/services/salario_service.py` — use new items
- `backend/src/schemas/liquidacion.py` — `monto_cobrado` replaces subtotal fields
- `backend/tests/unit/test_liquidacion.py` — rewrite
- `backend/tests/integration/test_liquidacion_api.py` — rewrite
- `backend/tests/unit/test_salario.py` — update

**Subtareas internas**:
1. TDD: escritura con pago parcial aporta solo monto cobrado en mes
2. TDD: escritura sin pagos en mes excluida de liquidación
3. TDD: dos pagos en mes = una línea con suma (montón único)
4. TDD: total escribano = suma monto_cobrado de sus escrituras
5. Actualizar `SalarioService` para usar nuevos items
6. Secretarias block sin cambio (Empleado.sueldo)

**Criterio de éxito**: SC-008 verificado; liquidación no muestra honorarios proyectados.

**Estimación**: 5 horas

**Dependencias**: WU-2

---

### Work Unit 6: Frontend — Pagos, Saldo y Cierre

**Propósito**: UI de registro de pagos, visualización de saldo, secciones duales en detalle de escritura.

**Archivos a crear/modificar**:
- `frontend/src/components/escrituras/PagoClienteForm.tsx`
- `frontend/src/components/escrituras/PagoClienteList.tsx`
- `frontend/src/components/escrituras/PagoColegioForm.tsx`
- `frontend/src/components/escrituras/PagoColegioList.tsx`
- `frontend/src/pages/EscrituraDetail.tsx`
- `frontend/src/components/escrituras/EscrituraList.tsx`
- `frontend/src/api/pagosCliente.ts`, `pagosColegio.ts`
- `frontend/src/hooks/usePagosCliente.ts`, `usePagosColegio.ts`
- `frontend/src/hooks/useSSE.ts` — handle new events
- Eliminar `GastoForm.tsx`, `api/gastos.ts`

**Subtareas internas**:
1. Reemplazar Gastos Adicionales por sección Pagos del Cliente con resumen saldo
2. Agregar sección Pagos al Colegio con referencia informativa leyes notariales
3. Listado escrituras: columnas costo_total, total_pagado, saldo_pendiente, badge 100%
4. Botón cerrar deshabilitado con tooltip si saldo > 0
5. Indicador visual de sobrepago
6. SSE invalidation en pagos y cierre

**Criterio de éxito**: SC-001, SC-002, FR-030–032 verificados manualmente.

**Estimación**: 6 horas

**Dependencias**: WU-2, WU-3

---

### Work Unit 7: Frontend — Libros, Liquidación y Salarios

**Propósito**: Actualizar vistas agregadas para reflejar caja real.

**Archivos a crear/modificar**:
- `frontend/src/components/libros/LibroEntradaTable.tsx` — pagos + resumen deudas
- `frontend/src/components/libros/LibroSalidaTable.tsx` — pagos colegio
- `frontend/src/pages/LibroEntradaPage.tsx`, `LibroSalidaPage.tsx`
- `frontend/src/pages/LiquidacionPage.tsx`
- `frontend/src/components/liquidacion/EscribanoCard.tsx` — monto_cobrado
- `frontend/src/types/api.ts`

**Subtareas internas**:
1. Libro Entrada: líneas por pago + tabla resumen deudas
2. Libro Salida: solo pagos colegio del mes
3. Liquidación: mostrar monto_cobrado (sin desglose honorarios/leyes)
4. Pago Salarios: totales escribano desde pagos reales
5. Actualizar tipos TypeScript (breaking change liquidación item)

**Criterio de éxito**: SC-003, SC-004, SC-006, SC-008 verificados en UI.

**Estimación**: 5 horas

**Dependencias**: WU-4, WU-5, WU-6

---

### Notas para Itti-Kit

**Total estimado de Work Units**: 7  
**Tiempo total estimado**: ~35 horas  
**Work Units en paralelo**: WU-2 y WU-3 tras WU-1; WU-4 y WU-5 tras WU-2/WU-3; WU-6 tras WU-2+WU-3; WU-7 tras WU-4+WU-5+WU-6

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Constitution §2.3 Gastos Adicionales superseded | Real cash model requires distinct PagoCliente/PagoColegio instead of direction-tagged expenses | Keeping GastoAdicional with renamed labels preserves confusing `direccion` semantics |
| Constitution §2.4 "libros derivable from escritura data" | Libros now derive from payment records, not factura line items | Auto-deriving from factura was the fictional model this feature explicitly removes |
| Breaking API: `LiquidacionEscrituraItem` shape | Lump-sum cash model per clarify session | Keeping honorario+certificación fields would misrepresent liquidación as projected not real |
| Constitution amendment deferred to merge | Plan cannot block on governance doc update | Will PATCH constitution §2.3/§2.4 when feature ships (research R-009) |

---

## Phase 0 / Phase 1 Artifacts

| Artifact | Path | Status |
|---|---|---|
| Research | [research.md](./research.md) | ✅ Complete |
| Data Model | [data-model.md](./data-model.md) | ✅ Complete |
| API Contract | [contracts/openapi-patch.yaml](./contracts/openapi-patch.yaml) | ✅ Complete |
| Quickstart | [quickstart.md](./quickstart.md) | ✅ Complete |
| Tasks | tasks.md | ⏳ Next: `/spec-kitti.tasks` |

---

## Testing Strategy (from spec)

**Approach**: TDD — Test-Driven Development completo.

Every Work Unit starts with failing tests. Priority test surfaces:
1. `pago_saldo.py` — pure function edge cases (sobrepago, zero saldo)
2. Payment registration guards (amount, open state, immutability)
3. Libros derivation (no factura lines, correct month filter)
4. Liquidación lump-sum aggregation
5. Migration idempotency
6. SSE integration for real-time views
