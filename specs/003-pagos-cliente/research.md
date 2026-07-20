# Research: Pagos del Cliente y Libros Contables Basados en Caja Real

**Feature**: `003-pagos-cliente`  
**Date**: 2026-07-20  
**Source**: spec.md + clarify session 2026-07-20 + codebase analysis (001, 002)

---

## R-001 — Modelo de persistencia: reemplazo de GastoAdicional

**Decision**: Crear dos tablas nuevas `pagos_cliente` y `pagos_colegio` con estructura paralela; migrar datos desde `gastos_adicionales`; eliminar tabla y enum `direccion_gasto` al final de la migración.

**Rationale**:
- Alinea el modelo con las entidades de dominio `PagoCliente` y `PagoColegio` de la spec.
- Elimina el concepto de `direccion` (entrada/salida) que mezclaba flujos disconexos.
- Permite reglas de validación distintas por tipo (pago cliente valida saldo; pago colegio no).
- Facilita índices por `fecha` para libros filtrados por mes de pago.

**Alternatives considered**:
| Alternativa | Por qué se descartó |
|---|---|
| Renombrar tabla a `pagos` con columna `tipo` | Menos explícito en código; mezcla reglas en un solo servicio |
| Mantener `gastos_adicionales` y solo cambiar UI | No refleja el cambio semántico; `direccion` seguiría confundiendo |
| Tabla única polimórfica sin migración | Rompe datos históricos sin trazabilidad clara |

**Schema propuesto** (ambas tablas):

| Columna | Tipo | Notas |
|---|---|---|
| `id` | UUID PK | |
| `escritura_id` | UUID FK → escrituras | |
| `monto` | NUMERIC(18,2) | > 0 |
| `fecha` | DATE | Usada para filtro mensual en libros/liquidación |
| `concepto` | VARCHAR(500) | Opcional en API; default `""` en DB |
| `created_at` | TIMESTAMPTZ | Append-only audit |

Índices: `(escritura_id)`, `(fecha)`.

---

## R-002 — Cálculo de saldo pendiente

**Decision**: Función pura `calc_saldo(costo_total, total_pagado) -> Decimal` en módulo `pago_saldo.py`; `saldo_pendiente = max(costo_total - total_pagado, 0)`; flag `sobrepago = total_pagado > costo_total`.

**Rationale**: Cumple FR-003 y edge case de sobrepago tras recálculo de factura. Función pura testeable con TDD (P6).

**Alternatives considered**:
- Persistir `saldo_pendiente` en DB → riesgo de desincronización al recalcular factura.
- Rechazar pagos que causen sobrepago → contradice spec (permite sobrepago y cierre).

---

## R-003 — Liquidación y Pago de Salarios basados en caja real

**Decision**: Reemplazar scoping por `Escritura.created_at` con scoping por `PagoCliente.fecha` en el mes. Cada escritura con pagos en el mes aporta **una línea** con `monto_cobrado = SUM(pagos del mes)`. Total escribano = suma de `monto_cobrado`.

**Rationale**: Implementa FR-026, FR-026b, FR-028 y decisión de clarify (montón único + pagos reales).

**Alternatives considered**:
| Alternativa | Por qué se descartó |
|---|---|
| Mantener honorario+certificación proyectados | Contradice clarify Q1 |
| Distribución proporcional por sección | Rechazado en clarify Q2 |
| Incluir escrituras sin pagos del mes | Contradice FR-027 |

**Breaking change**: `LiquidacionEscrituraItem` pierde `honorario_principal`, `certificacion`, `subtotal`; adopta `monto_cobrado`. Frontend de Liquidación y Pago de Salarios debe actualizarse.

---

## R-004 — Libro de Entrada y Libro de Salida

**Decision**:
- **Entrada**: query `pagos_cliente` WHERE `fecha` en mes; cada pago = una línea. Agregar sección `resumen_deudas` con escrituras abiertas que tengan `saldo_pendiente > 0` (sin filtro de mes en deuda — deuda es estado actual).
- **Salida**: query `pagos_colegio` WHERE `fecha` en mes; cada pago = una línea. Sin derivación de `FacturaPrincipal`.

**Rationale**: Libros reflejan caja real (FR-010, FR-021). Filtro por fecha de pago, no fecha de escritura (edge cases spec).

**Alternatives considered**:
- Derivar salida de `total_leyes_notariales` al cierre → rechazado en clarify Q4 (registro manual).
- Incluir escrituras sin pagos en líneas del libro → contradice spec.

**DTO delta**: `LibroLineaResponse` usa `fecha_pago: date` (reemplaza `fecha_escritura`). `LibroEntradaResponse` agrega `resumen_deudas: list[DeudaResumenItem]`.

---

## R-005 — Pagos al Colegio: referencia informativa

**Decision**: En `GET /escrituras/{id}` y sección UI, exponer `total_leyes_notariales_proyectadas` desde `FacturaPrincipal.total_leyes_notariales` (o suma de art2_a..art12_f). Solo lectura; sin validación al registrar `PagoColegio`.

**Rationale**: Clarify Q5 — referencia informativa sin bloqueo.

---

## R-006 — Cierre de escritura condicionado

**Decision**: `close_escritura()` valida `saldo_pendiente == 0` antes de cambiar estado; si `> 0`, lanza `EscrituraSaldoPendienteError` con monto pendiente (HTTP 409).

**Rationale**: FR-007, FR-008. Encaja con flujo existente de `close_escritura` en `escritura_service.py`.

---

## R-007 — Migración de datos históricos

**Decision**: Migración Alembic idempotente `006_pagos_cliente`:
1. Crear `pagos_cliente`, `pagos_colegio`.
2. `INSERT INTO pagos_cliente SELECT ... FROM gastos_adicionales WHERE direccion = 'entrada'`.
3. `INSERT INTO pagos_colegio SELECT ... FROM gastos_adicionales WHERE direccion = 'salida'`.
4. Para escrituras `cerrada` sin filas en `pagos_cliente`: insertar pago implícito con `monto = factura.total_factura`, `fecha = closed_at::date`, `concepto = 'Migración: pago implícito al cierre'`.
5. Drop `gastos_adicionales`; drop enum `direccion_gasto`.

**Rationale**: FR-033, FR-034, FR-035.

---

## R-008 — Eventos SSE

**Decision**: Emitir `pago_cliente.created` y `pago_colegio.created` además de invalidar caches existentes (`liquidacion.updated`, `libros_updated`, `escritura.updated`). Frontend invalida queries de escrituras, libros, liquidación, salarios.

**Rationale**: P5 — push-based, sin polling. Patrón ya usado en feature 001/002.

---

## R-009 — Constitución §2.3 / §2.4 (Gastos Adicionales y Libros derivados)

**Decision**: Proceder con el cambio de dominio documentado en Complexity Tracking del plan. Al mergear la feature, actualizar constitución (MINOR bump) para reemplazar §2.3 Gastos Adicionales por Pagos del Cliente / Pagos al Colegio y actualizar §2.4 sobre libros basados en pagos reales.

**Rationale**: La spec 003 y las decisiones de clarify superseden el modelo ficticio de la constitución v1.0.0. No bloquea implementación; se registra como deuda de governance.

---

## R-010 — Salarios de secretarias

**Decision**: Sin cambio — `SalarioService` sigue leyendo sueldos de `Empleado` activo para la sección secretarias. Solo cambia el bloque de escribanos (pagos reales del mes).

**Rationale**: Fuera de scope explícito de la spec; sueldos fijos no dependen de caja de clientes.
