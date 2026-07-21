# Data Model: Gastos Extraordinarios de la Escribanía

**Feature**: `005-gastos-extraordinarios`  
**Date**: 2026-07-20  
**Source**: spec.md + research.md  
**Extends**: libros y salarios existentes (sin cambio a `escrituras`)

---

## Entity Relationship Overview (delta)

```
GastoExtraordinario (NEW)
        │
        ▼
  Libro de Salida (línea derivada por fecha, origen=extraordinario)
        │
        ▼
  Pago de Salarios (deducción mensual ÷ escribanos activos)
```

**Sin relación** con `Escritura`, `Liquidacion`, `Libro de Entrada`.

---

## New Entity

### GastoExtraordinario (`gastos_extraordinarios`)

Gasto puntual de la escribanía no vinculado a una escritura.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `concepto` | VARCHAR(500) | not null, min length 1 | FR-003, FR-006 |
| `monto` | NUMERIC(18,2) | not null, > 0 | FR-003, FR-006 |
| `fecha` | DATE | not null | Determina mes contable |
| `created_at` | TIMESTAMPTZ | not null | |
| `updated_at` | TIMESTAMPTZ | not null | Editable |

**Business rules**:
- CRUD libre (no depende de estado de escritura)
- Mes contable = mes calendario de `fecha`
- Un registro = una línea en Libro de Salida del mes de `fecha`

**Indexes**: `(fecha)` para consultas mensuales

---

## Extended Schemas (API responses)

### LibroLineaResponse (delta)

| Field | Change |
|---|---|
| `origen` | Añadir literal `"extraordinario"` |
| `escritura_id` | Opcional `null` para origen extraordinario |
| `escritura_nombre` | Opcional `null` |
| `gasto_extraordinario_id` | UUID opcional (trazabilidad) |

### PagoSalariosResumen (delta)

| Field | Type | Notes |
|---|---|---|
| `total_gastos_extraordinarios` | MoneyStr | Suma del mes |
| `advertencia_reparto` | string \| null | Si no hay escribanos activos |

### PagoEscribano (delta)

| Field | Type | Notes |
|---|---|---|
| `deduccion_gastos_extraordinarios` | MoneyStr | Cuota del escribano |
| `monto_neto` | MoneyStr | `monto_total - deduccion` |

`monto_total` conserva el significado actual (cobros + neto impuestos por escrituras).

---

## Computed: DeduccionGastoExtraordinario

No persistido. Calculado en `salario_service` por mes:

```text
total_mes = SUM(gastos_extraordinarios WHERE fecha in month)
n = COUNT(escribanos activos)
cuotas = reparto_equitativo(total_mes, n)  # ver gasto_extraordinario_reparto.py
```

---

## Validation Rules (API boundary)

| Input | Rule |
|---|---|
| `concepto` | `min_length=1`, `max_length=500` |
| `monto` | `> 0`, 2 decimales |
| `fecha` | date válida |
| PATCH | al menos un campo; mismas reglas parciales |

---

## SSE Payload

```json
{
  "gasto_extraordinario_id": "uuid",
  "anio": 2026,
  "mes": 7
}
```

Eventos: `gasto_extraordinario.created`, `.updated`, `.deleted`, más `libros_updated`.
