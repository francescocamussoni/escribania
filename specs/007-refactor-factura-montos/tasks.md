# Tasks: Refactorización de montos de Factura Principal

**Feature Branch**: `007-refactor-factura-montos`  
**Input**: `specs/007-refactor-factura-montos/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)  
**Testing**: TDD-first — tests en estado FAILING antes de cada implementación (spec § Testing Strategy)  
**UI / Figma**: **No se usa Figma** en esta feature (research R-004, plan Technical Context). Reorganización de `FacturaDetalle` y tokens existentes en `index.css`. El campo `figma:` **no aplica** — `/spec-kitti.implement` no debe bloquear por ausencia de referencia Figma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario (US1–US3)
- TDD: tests marcados con `⚠️ FAIL FIRST` deben fallar antes de implementar

---

## Phase 1: Setup — Preparación

**Purpose**: Verificar artefactos de diseño y preparar tipos frontend.

- [ ] T001 Revisar alineación entre `specs/007-refactor-factura-montos/contracts/openapi-delta.yaml` y `specs/007-refactor-factura-montos/data-model.md`
- [ ] T002 [P] Agregar campos stub en `frontend/src/types/api.ts`: `dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva` en `FacturaPrincipalResponse`

**Checkpoint**: Contratos y data-model alineados. Tipos TS listos para UI.

---

## Phase 2: User Story 2 — Totales recalculados automáticamente (Priority: P1) 🎯 MVP backend

**Goal**: Nuevas fórmulas de Totales en `calculo_factura`, persistencia en DB, `total_factura` = Total + IVA.

**Independent Test**: Fixture canónico (USD 105_000, MEP 1_450.34, Nación 1_425.00) → `dif_honorarios` 3_618_308.23, `total_parcial` 3_683_421.00, `total_sin_iva` 9_674_809.01, `iva` 1_875_257.52, `total_factura` 11_550_066.53; ítems de línea idénticos a constitución §5.

**⚠️ CRITICAL**: Bloquea US1 (sección Totales en UI) y US3 (saldo cliente).

### Tests TDD — US2 (⚠️ FAIL FIRST)

- [x] T003 [US2] ⚠️ FAIL FIRST Crear `backend/tests/unit/test_calcular_totales_factura.py`: asserts fixture canónico (research.md R-003), gastos excluidos del total parcial, redondeo por paso, SC-005 (line items unchanged vs constitution)
- [x] T004 [US2] ⚠️ FAIL FIRST Actualizar `backend/tests/unit/test_calculo_factura.py`: extender `test_calcular_factura_completa_canonical_fixture` con totales nuevos y `total_factura` = 11_550_066.53 (no suma legacy)
- [x] T005 [P] [US2] ⚠️ FAIL FIRST Crear `backend/tests/integration/test_migration_009_factura_totales.py`: columnas `dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva` NOT NULL tras upgrade; backfill coherente

### Implementación — US2

- [x] T006 [US2] Implementar `calcular_totales_factura()` y constantes `IVA_PCT`, `GASTOS_EXCLUIDOS_TOTAL_PARCIAL` en `backend/src/services/calculo_factura.py` hasta que `T003` pase
- [x] T007 [US2] Integrar totales en `calcular_factura_completa()`; reemplazar fórmula antigua de `total_factura` hasta que `T004` pase
- [x] T008 [US2] Crear migración `backend/alembic/versions/009_factura_totales.py`: ADD 4 columnas, backfill vía recálculo, SET NOT NULL
- [x] T009 [P] [US2] Extender `backend/src/models/factura_principal.py` con `dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva`
- [x] T010 [P] [US2] Extender `backend/src/schemas/factura.py` (`FacturaPrincipalResponse`) con los 4 campos nuevos
- [x] T011 [US2] Actualizar `FACTURA_FIELDS` en `backend/src/services/escritura_service.py` y `backend/tests/helpers/escritura_factory.py`
- [x] T012 [US2] Ejecutar `alembic upgrade head` y verificar que `T005` pasa

**Checkpoint**: Motor de cálculo y persistencia listos. API GET escritura expone totales.

---

## Phase 3: User Story 1 — Ver factura reorganizada por secciones (Priority: P1)

**Goal**: Cinco secciones en UI, etiquetas nuevas, resaltado Colegio en Honorarios, sección Totales.

**Independent Test**: Abrir escritura canónica → orden Bases → Honorarios → Honorarios varios → Corresponde → Totales; labels "Precio base Valor", "Total honorarios varios"; ítems Colegio visualmente distintos.

### Implementación — US1

- [x] T013 [P] [US1] Actualizar `frontend/src/types/api.ts` con campos definitivos (reemplazar stubs de T002)
- [x] T014 [US1] Reorganizar `buildSections()` en `frontend/src/components/escrituras/FacturaDetalle.tsx`: 5 secciones, Corresponde fusionado con subtotales impuestos/gastos, sección Totales (5 líneas + Total + IVA)
- [x] T015 [US1] Agregar estilo `.factura-row--colegio` en `frontend/src/index.css` y aplicarlo a Aporte 12%, 5% honorarios, Firma honorarios y Subtotal honorarios en `FacturaDetalle.tsx`
- [x] T016 [US1] Renombrar labels UI: "Precio base Valor", "Honorarios", "Honorarios varios", "Total honorarios varios"; eliminar footer duplicado `factura-total` si Totales ya muestra Total + IVA

**Checkpoint**: SC-001 y SC-003 verificables manualmente (quickstart § Factura UI).

---

## Phase 4: User Story 3 — Consistencia con pagos y libros (Priority: P2)

**Goal**: `costo_total` / `saldo_pendiente` y resumen deudas libro entrada = Total + IVA; referencia Honorarios varios para pagos Colegio.

**Independent Test**: Crear escritura → `costo_total` y `saldo_pendiente` = 11_550_066.53; pago parcial reduce saldo; resumen deudas coherente; label "Honorarios varios proyectados" en detalle.

### Tests TDD — US3 (⚠️ FAIL FIRST)

- [x] T017 [P] [US3] ⚠️ FAIL FIRST Actualizar `EXPECTED_FACTURA` y asserts en `backend/tests/integration/test_escrituras_api.py`: totales nuevos, `costo_total` / `saldo_pendiente` = `total_factura`
- [x] T018 [P] [US3] ⚠️ FAIL FIRST Revisar/actualizar `backend/tests/unit/test_pago_cliente_service.py` si asserta `total_factura` legacy (11_620_603.68)
- [x] T019 [P] [US3] ⚠️ FAIL FIRST Extender `backend/tests/unit/test_libros_service.py`: `resumen_deudas.costo_total` coincide con nuevo `total_factura` en escritura abierta con deuda

### Implementación — US3

- [x] T020 [US3] Verificar que `build_saldo_fields` en `backend/src/services/escritura_service.py` usa `factura.total_factura` sin cambio de código (solo nuevos montos); ajustar si hace falta
- [x] T021 [US3] Actualizar label en `frontend/src/pages/EscrituraDetail.tsx`: "Honorarios varios proyectados" (campo `total_leyes_notariales_proyectadas` sin cambio API)
- [x] T022 [US3] Ejecutar `T017`, `T018`, `T019` hasta verde

**Checkpoint**: SC-004 cumplido. Pagos cliente y libro entrada alineados.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Seed demo, labels residuales, validación final.

- [x] T023 [P] Bump `DEMO_SEED_VERSION` a 4 y regenerar `FACTURA_FIELDS` en `backend/scripts/seed_demo_data.py`; wipe/recreate `[DEMO]` con totales consistentes
- [x] T024 [P] Actualizar labels "Leyes notariales" → "Honorarios varios" en `frontend/src/pages/ConfiguracionPage.tsx` si aplica
- [x] T025 [P] Actualizar `backend/scripts/demo_calculo.py` para imprimir sección Totales
- [x] T026 Ejecutar checklist manual de `specs/007-refactor-factura-montos/quickstart.md` y suite `pytest tests/ -v`
- [x] T027 Documentar enmienda propuesta constitución §2.2 / §5 (totales canónicos) en `specs/007-refactor-factura-montos/research.md` R-007 o issue de seguimiento

**Checkpoint**: Demo seed v4 operativo. Suite completa verde.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias
- **US2 backend (Phase 2)**: Depende de Setup — **bloquea US1 y US3**
- **US1 UI (Phase 3)**: Depende de Phase 2 (campos API)
- **US3 integración (Phase 4)**: Depende de Phase 2
- **Polish (Phase 5)**: Depende de Phases 2–4

### User Story Dependencies

| Story | Depende de | Entregable independiente |
|---|---|---|
| US2 (P1) | Setup | pytest unit calculo + migración |
| US1 (P1) | US2 | UI 5 secciones con datos reales |
| US3 (P2) | US2 | saldo + libro entrada |

### Within Each Story

- Tests FAIL FIRST → implementación → verde
- US2: cálculo puro antes de migración (T006–T007 antes de T008–T012)
- US1: tipos antes de componente

### Parallel Opportunities

- T002 + T001 en paralelo
- T005, T009, T010 en paralelo tras T008 planificado
- T013 + T015 en paralelo (distintos archivos) tras Phase 2
- T017, T018, T019 en paralelo
- T023, T024, T025 en paralelo

---

## Parallel Example: User Story 2

```bash
# Tests en paralelo (tras T002):
pytest backend/tests/unit/test_calcular_totales_factura.py -v
pytest backend/tests/integration/test_migration_009_factura_totales.py -v

# Model + schema en paralelo (tras T008):
# factura_principal.py + schemas/factura.py
```

---

## Parallel Example: User Story 3

```bash
# Integración en paralelo:
pytest backend/tests/integration/test_escrituras_api.py -v
pytest backend/tests/unit/test_pago_cliente_service.py -v
pytest backend/tests/unit/test_libros_service.py -v
```

---

## Implementation Strategy

### MVP First (US2 backend + US1 UI)

1. Phase 1 Setup
2. Phase 2 US2 — cálculo y persistencia (MVP funcional en API)
3. Phase 3 US1 — factura visible para secretaria
4. **VALIDAR**: quickstart fixture canónico + UI checklist
5. Phase 4 US3 — saldo y libros
6. Phase 5 Polish — seed y regresión completa

### Incremental Delivery

| Incremento | Fases | Valor |
|---|---|---|
| MVP | 1 + 2 + 3 | Factura reorganizada con totales correctos |
| +Pagos | 4 | Saldo cliente y libro coherente |
| +Demo | 5 | Entorno local consistente |

---

## Task Summary

| Métrica | Valor |
|---|---|
| **Total tasks** | 27 |
| **US1** | 4 (T013–T016) |
| **US2** | 10 (T003–T012) |
| **US3** | 6 (T017–T022) |
| **Setup** | 2 (T001–T002) |
| **Polish** | 5 (T023–T027) |
| **Parallel-marked [P]** | 12 |
| **TDD FAIL FIRST** | 6 |

**Suggested MVP scope**: Phases 1–3 (T001–T016) — factura con totales en UI.  
**Next command**: `/spec-kitti.tasks.shape` o `/spec-kitti.implement` por Work Unit.

---

## Notes

- `total_factura` cambia de ~11_620_603.68 a 11_550_066.53 en fixture canónico (breaking change documentado en quickstart).
- Columna DB `total_leyes_notariales` sin rename; solo label UI "Total honorarios varios".
- Honorarios varios **no** entra en Total + IVA; sigue como referencia pagos Colegio.
