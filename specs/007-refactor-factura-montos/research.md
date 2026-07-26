# Research: Refactorización de montos de Factura Principal

**Feature**: `007-refactor-factura-montos`  
**Date**: 2026-07-26  
**Source**: spec.md + clarify session 2026-07-26 + codebase analysis

---

## R-001 — Semántica de `total_factura`

**Decision**: `FacturaPrincipal.total_factura` almacena **Total + IVA** (monto canónico de cobro al cliente). Se agregan columnas para los intermedios; `total_sin_iva` almacena el renglón UI "Total" (sin IVA).

**Rationale**: Clarify Q1; `costo_total` / `saldo_pendiente` ya leen `total_factura` en `escritura_service.build_saldo_fields` — un solo cambio de fórmula alimenta pagos cliente y resumen de deudas del libro de entrada.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Nuevo campo `total_mas_iva` y mantener `total_factura` legacy | Duplica el monto canónico; obligaría a cambiar todos los consumidores manualmente |
| Solo mostrar Total + IVA sin persistir intermedios | Contradice clarify Q4 (mismo ciclo que resto de secciones) |

---

## R-002 — Nuevas columnas y migración

**Decision**: Migración Alembic `009_factura_totales` agrega a `facturas_principales`:

| Columna | UI label |
|---|---|
| `dif_honorarios` | Dif Honorarios |
| `total_parcial` | Total parcial |
| `total_sin_iva` | Total |
| `iva` | IVA |

`total_factura` se recalcula como `total_sin_iva + iva` (Total + IVA).

**Rationale**: Patrón existente (todas las líneas persistidas); queries y libros sin recomputar en lectura.

**Migración de datos**: Para filas existentes en entornos no-demo, `upgrade()` recalcula vía `calcular_factura_completa` usando USD y TC de la escritura padre. Seed demo `[DEMO]` se regenera por versión (FR-020), no por SQL masivo.

**Alternatives considered**:
- Vista materializada solo en API → rechazado (clarify Q4).

---

## R-003 — Fórmulas de Totales (módulo puro)

**Decision**: Nueva función `calcular_totales_factura(honorarios, impuestos, gastos) -> dict` en `calculo_factura.py`, invocada al final de `calcular_factura_completa`. Constantes nombradas:

```text
IVA_PCT = Decimal("0.21")
GASTOS_EXCLUIDOS_TOTAL_PARCIAL = (
  "fotocopias_urgentes", "informes_notariales", "municipio",
  "ii_certificados", "catastro",
)
```

Fórmulas (redondeo `quantize(0.01, ROUND_HALF_UP)` en cada paso):

```text
dif_honorarios  = suma_hon_cert - aporte_12pct
gastos_neto     = total_gastos_admin - SUM(excluidos)
total_parcial   = dif_honorarios + gastos_neto
total_sin_iva   = total_parcial + subtotal_honorarios + total_impuestos
iva             = (dif_honorarios + total_impuestos) * IVA_PCT
total_factura   = total_sin_iva + iva   # Total + IVA
```

**Rationale**: P6 (funciones puras); ítems de línea sin cambio (SC-005); Honorarios varios (`total_leyes_notariales`) explícitamente fuera de Total/IVA (spec Assumptions).

**Canonical fixture** (USD 105_000, MEP 1_450.34, Nación 1_425.00):

| Campo | Valor |
|---|---|
| `dif_honorarios` | 3_618_308.23 |
| `total_parcial` | 3_683_421.00 |
| `total_sin_iva` | 9_674_809.01 |
| `iva` | 1_875_257.52 |
| `total_factura` (Total + IVA) | 11_550_066.53 |

Ítems de línea individuales permanecen iguales al fixture constitución §5.

---

## R-004 — UI: secciones y etiquetas

**Decision**: Solo cambios en `FacturaDetalle.tsx` + CSS; sin Figma node (spec-kitti-figma GATEKEEPER no aplica — reorganización de layout existente, no nuevo diseño).

- Renombrar secciones según FR-001–FR-008.
- `precio_base_nacion` → label **Precio base Valor** (campo API sin cambio).
- `total_leyes_notariales` → label **Total honorarios varios** (columna DB sin cambio).
- Resaltado Colegio: clase `factura-row--colegio` en Aporte 12%, 5% hon., Firma honorarios y Subtotal honorarios; color derivado de `--color-*` existentes o token secundario del theme (no hardcode hex sin design system).

**Rationale**: FR-004; minimizar breaking API; UI labels en frontend.

**EscrituraDetail**: texto "Leyes notariales proyectadas" → "Honorarios varios proyectados"; campo API `total_leyes_notariales_proyectadas` se mantiene (alias documentado en data-model).

---

## R-005 — Libros y liquidación

**Decision**: **Sin cambio de lógica** en `libros_service` para líneas de caja (siguen siendo pagos registrados). El resumen de deudas usa `build_saldo_fields` → automáticamente refleja nuevo `total_factura`.

Liquidación: actualizar **solo etiquetas** en agregaciones que mencionen "Leyes notariales" si existen en frontend (`LiquidacionPage`, `ConfiguracionPage` secciones de config). Desglose por ítem individual en libro salida mantiene labels canónicos por campo (`art2_a`, etc.).

**Rationale**: FR-018; P8 traceability a ítems individuales intacta.

---

## R-006 — Seed demo y tests

**Decision**: `DEMO_SEED_VERSION` 3 → **4**; al detectar versión/count inconsistente, borrar escrituras `[DEMO]` y recrear. Actualizar:

- `backend/tests/unit/test_calculo_factura.py`
- `backend/tests/integration/test_escrituras_api.py` (`EXPECTED_FACTURA`)
- `backend/tests/helpers/escritura_factory.py`
- Cualquier test que asserta `total_factura` antiguo (11_620_603.68 → 11_550_066.53)

**Rationale**: FR-020, FR-021; TDD-first (clarify Q2).

**TDD order**:

1. `test_calcular_totales_factura.py` (nuevos asserts fixture)
2. Actualizar `test_calcular_factura_completa_canonical_fixture`
3. Migración 009 + model
4. `test_escrituras_api` integración saldo/costo_total
5. Frontend smoke (Vitest opcional para `buildSections`)

---

## R-007 — Constitución §2.2 y §5 (seguimiento)

**Decision**: Tras implementación feature 007, aplicar enmienda **MINOR** a `constitution.md`:

- Tabla de secciones: Honorarios, Honorarios varios, Corresponde, Totales.
- §5: agregar bloque Totales con valores canónicos R-003; actualizar semántica de `total_factura` (= Total + IVA).

**Rationale**: Governance §6; P6 exige fixture actualizado.

**Status (2026-07-26)**: Feature 007 implementada. Pendiente PR separado de enmienda constitucional con:

| Bloque | Cambio propuesto |
|--------|------------------|
| §2.2 tabla | Reemplazar filas "Honorarios Profesionales / Leyes Notariales / Impuestos / Gastos" por layout de 5 secciones |
| §5 Totales | `dif_honorarios` 3_618_308.23; `total_parcial` 3_683_421.00; `total_sin_iva` 9_674_809.01; `iva` 1_875_257.52; `total_factura` 11_550_066.53 |
| §5 nota | `total_factura` ya no suma honorarios varios al cobro cliente |

**Alternatives considered**: Dejar constitución sin actualizar → rechazado (P6 drift).

---

## R-008 — OpenAPI / API surface

**Decision**: Delta OpenAPI extiende `FacturaPrincipalResponse` con cuatro campos nuevos; `total_factura` descripción actualizada. Sin nuevos endpoints.

**Alternatives considered**:
- Endpoint `/factura/breakdown` → innecesario; datos ya en GET escritura.
