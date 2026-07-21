# Research: Impuestos por Escritura

**Feature**: `006-impuestos-escrituras`  
**Date**: 2026-07-20  
**Source**: spec.md + clarify session 2026-07-20 + codebase analysis (003, 004)

---

## R-001 — Persistencia: impuesto + pagos 1:1

**Decision**: Tres tablas: `impuestos_escritura` (cabecera del impuesto), `pagos_impuesto_cliente` y `pagos_impuesto_escribania` (máximo uno por impuesto, FK única `impuesto_id`).

**Rationale**: Modela FR-014/FR-018 (un pago por lado), permite editar pagos (clarify Q3) sin polimorfismo, y separa el monto de referencia del período de los montos efectivos de caja.

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Pagos embebidos como columnas en `impuestos_escritura` | Dificulta historial y libros derivados por fecha de pago |
| Tabla única `pagos_impuesto` con `tipo` cliente/escribanía | Menos explícito; validación de unicidad más frágil |
| Reutilizar `pagos_cliente` / `pagos_colegio` | Mezcla honorarios con impuestos; rompe FR-020 y cierre condicionado |

**Migración**: `007_impuestos_escritura` (siguiente después de `006_pagos_cliente`).

---

## R-002 — Prorrateo lineal por días

**Decision**: Módulo puro `impuesto_prorrateo.py` con:

```text
dias_periodo = inclusive_days(fecha_inicio, fecha_fin)
tramo_atras  = inclusive_days(fecha_inicio, fecha_corte)
tramo_adelante = inclusive_days(fecha_corte + 1 día, fecha_fin)
monto_sugerido = monto_total * (dias_tramo / dias_periodo)
```

Redondeo: `quantize(Decimal("0.01"), ROUND_HALF_UP)`; tests fijan casos del spec ($10.000 × 46/61).

**Rationale**: Clarify Q5 (sin solapamiento en fecha de corte); P6 (función pura testeable con TDD).

**Alternatives considered**:
- Mes contable por inicio/fin de período → descartado tras clarify del usuario (libros usan fecha de pago).
- Prorrateo mensual en lugar de diario → no coincide con regla de negocio.

---

## R-003 — Libros contables

**Decision**: Extender `libros_service` para incluir líneas de `pagos_impuesto_cliente` (entrada) y `pagos_impuesto_escribania` (salida), filtradas por `fecha` del pago en el mes. Discriminador `origen: "impuesto"` + `tipo_impuesto` en `LibroLineaResponse`.

**Rationale**: Caja real por fecha de pago (FR-010c); trazabilidad P8.

**Alternatives considered**:
- Líneas derivadas del monto prorrateado sin pago registrado → contradice principio de caja real.

---

## R-004 — Liquidación y Pago de Salarios

**Decision**: Extender `LiquidacionEscrituraItem` con campo `neto_impuestos` (puede ser negativo). Por mes y escritura:

```text
neto_impuestos = SUM(pagos_impuesto_cliente.fecha en mes)
               - SUM(pagos_impuesto_escribania.fecha en mes)
```

Total escribano del mes = `SUM(monto_cobrado) + SUM(neto_impuestos)` sobre sus escrituras con movimiento en el mes. Escrituras solo con impuestos (sin honorarios en el mes) **sí** aparecen si `neto_impuestos ≠ 0`.

**Rationale**: FR-020b, US6; asimetrías mensuales permitidas; cierre mensual no exige balance = 0.

**Alternatives considered**:
| Alternativa | Por qué se descartó |
|---|---|
| Línea separada solo a nivel escribano (sin escritura) | Rompe P8 traceability |
| No mostrar impuestos en liquidación | Contradice clarify corregido |

**Breaking change (menor)**: `LiquidacionEscrituraItem` gana `neto_impuestos`; frontend Liquidación/PagoSalarios muestra desglose o total combinado.

---

## R-005 — Cierre de escritura

**Decision**: Extender `close_escritura` con dos validaciones adicionales independientes del saldo de honorarios:

1. `balance_impuestos = Σ pagos cliente impuestos − Σ pagos escribanía impuestos` debe ser `0`.
2. Cada `ImpuestoEscritura` cargado debe tener ambos pagos registrados.

Nuevas excepciones: `EscrituraImpuestosBalanceError`, `EscrituraImpuestosPagosPendientesError` → HTTP 409 con `detail` estructurado.

**Rationale**: US5, FR-025/FR-025b; honorarios e impuestos son flujos separados (FR-020).

---

## R-006 — Edición vs. append-only (desviación de 003)

**Decision**: Impuestos y sus pagos son **editables y eliminables** mientras la escritura esté abierta (PATCH/DELETE en API). Al editar fecha/monto de pago, actualizar la línea existente en libros (no duplicar).

**Rationale**: Clarify Q3 opción B; distinto del modelo append-only de `pagos_cliente`/`pagos_colegio` de feature 003.

**Implicación**: Servicios usan `update` + `delete` con republicación SSE; tests de no-duplicación en libros.

---

## R-007 — Catálogo de tipos de impuesto

**Decision**: Enum PostgreSQL `tipo_impuesto` con valores fijos: `API`, `TGI`, `AGUAS_SANTAFESINAS`, `EPE`, `EXPENSAS`, `LITORAL_GAS`. Expuesto en API como strings con etiquetas legibles en UI.

**Rationale**: FR-002; sin tabla de configuración dinámica (assumption spec).

---

## R-008 — UI sin Figma

**Decision**: Reutilizar patrones de `PagoClienteForm` / `PagoColegioForm` y layout de columna derecha de feature 004. Sección "Impuestos" debajo de pagos cliente y escribanía.

**Rationale**: Assumption spec; constitution P10 no aplica (sin nodo Figma).

---

## R-009 — SSE y cache invalidation

**Decision**: Nuevos eventos:

- `impuesto.created` / `impuesto.updated` / `impuesto.deleted`
- `pago_impuesto_cliente.created` / `.updated` / `.deleted`
- `pago_impuesto_escribania.created` / `.updated` / `.deleted`

Todos publican también `liquidacion.updated` y `libros_updated` cuando afectan caja.

**Rationale**: P5; alineado con `pago_cliente_service` existente.

---

## R-010 — Testing (TDD completo)

**Decision**: Orden TDD por capas:

1. `test_impuesto_prorrateo.py` (puro)
2. `test_impuesto_balance.py` (balance acumulado, elegibilidad cierre)
3. `test_impuesto_service.py` + tests de pagos
4. `test_libros_service.py` / `test_liquidacion.py` (extensiones)
5. `test_escrituras_api.py` (409 cierre)
6. Integration API + migration `007`
7. Frontend Vitest para formulario y balance display (opcional en WU UI)

**Rationale**: Testing Strategy en spec.md; superficies financieras críticas.
