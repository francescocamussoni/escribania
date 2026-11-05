# Data Model: Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Feature**: `009-pagos-colegio-factura`  
**Date**: 2026-07-26  
**Source**: spec.md + research.md  
**Extends**: `007-refactor-factura-montos`, `008-factura-vencimiento-monotributo`

---

## Entity Relationship Overview (delta)

```
FacturaPrincipal (EXTENDED)
    └── lineas_deshabilitadas: string[]  (JSONB)

PagoColegio (MODIFIED)
    ├── tipo: enum colegio | otros     (replaces imputacion)
    └── concepto: detalle obligatorio si otros

PlazoColegio (DERIVED — uses total_impuestos_efectivo)

LibroSalidaLinea (DERIVED — only pagos_colegio)
```

No new tables.

---

## FacturaPrincipal (`facturas_principales`) — delta

### New column (migration `012`)

| Column | Type | Constraints | Default |
|---|---|---|---|
| `lineas_deshabilitadas` | JSONB | NOT NULL | `'[]'::jsonb` |

### Semantics

- Array de claves de `FACTURA_LINEA_KEYS` deshabilitadas para cobro al cliente.
- `[]` = todas habilitadas (comportamiento actual post-migración).
- Montos calculados en columnas persisten valores **canónicos** de fórmula; montos **efectivos** se
  derivan en servicio/API aplicando máscara.

### Business rules

- **BR-FAC-001**: Mínimo una línea habilitada al guardar escritura abierta (FR-018).
- **BR-FAC-002**: Escritura cerrada — `lineas_deshabilitadas` inmutable (FR-019).
- **BR-FAC-003**: Deshabilitar línea impuesto reduce `total_impuestos_efectivo` y plazo colegio
  (clarify Q5).
- **BR-FAC-004**: Deshabilitar honorarios/gastos admin no altera `total_impuestos_efectivo`
  (FR-017b).

### API fields (FacturaResponse delta)

| Field | Type | Description |
|---|---|---|
| `lineas_deshabilitadas` | string[] | Keys deshabilitadas |
| `lineas` | FacturaLineaItem[] | Cada línea con `habilitada: bool`, `monto`, `monto_efectivo` |
| `total_impuestos_efectivo` | decimal | Suma impuestos habilitados |
| `costo_total` | decimal | `total_factura` efectivo (reemplaza lectura directa de columna) |

---

## PagoColegio (`pagos_colegio`) — delta

### Replace enum

**Remove**: `imputacion_pago_colegio` (`total_impuestos`, `honorarios_varios`, `otro`)

**Add**: `tipo_pago_escribania`

| DB value | UI label | concepto |
|---|---|---|
| `colegio` | Pago al colegio de escribanos | opcional (default "") |
| `otros` | Otros | **obligatorio** (detalle, min 1 char) |

### Column change

| Column | Action |
|---|---|
| `imputacion` | DROP after backfill |
| `tipo` | ADD NOT NULL |

### Migration backfill

```sql
UPDATE pagos_colegio SET tipo = 'colegio'
WHERE imputacion IN ('total_impuestos', 'honorarios_varios');

UPDATE pagos_colegio SET tipo = 'otros'
WHERE imputacion = 'otro';
```

### Validation

- `monto > 0`
- `tipo` required on create
- `tipo = otros` → `trim(concepto) != ""`
- Solo escrituras `abierta`
- Append-only (sin delete/edit — heredado 003)

---

## PlazoColegio (derived — adjusted)

| Field | Before (008) | After (009) |
|---|---|---|
| `monto_referencia` | `factura.total_impuestos` | `total_impuestos_efectivo` |
| `monto_pagado` | SUM pagos `imputacion=total_impuestos` | SUM pagos `tipo=colegio` |
| `monto_pendiente` | `max(0, ref - pagado)` | unchanged formula |

Estado `no_aplica` cuando `total_impuestos_efectivo == 0` (todos impuestos deshabilitados).

---

## LibroSalida (derived — narrowed)

**Source query**: solo `pagos_colegio` WHERE `fecha` en mes.

| Field | Value |
|---|---|
| `tipo_pago` | `colegio` \| `otros` |
| `concepto` | Label fijo o detalle |
| `escritura_id` | siempre presente |
| `monto`, `fecha_pago` | del pago |

**Excluded sources** (breaking vs current):

- `pagos_impuesto_escribania`
- `gastos_extraordinarios`

---

## BulkPagoColegio (API-only)

### Preview request

```json
{ "escritura_ids": ["uuid", ...] }
```

### Preview item

| Field | Type |
|---|---|
| `escritura_id` | uuid |
| `escritura_nombre` | string |
| `pendiente` | decimal |
| `elegible` | bool |
| `motivo` | string? — `cerrada`, `sin_pendiente` |

### Confirm request

```json
{
  "fecha": "2026-07-26",
  "items": [
    { "escritura_id": "uuid", "monto": "80000.00" }
  ]
}
```

**Rules**:

- Una `fecha` para todos los ítems
- Cada item crea `PagoColegio(tipo=colegio)`
- Skip o reject `elegible=false` en server (defensa en profundidad)

---

## FACTURA_LINEA_KEYS (catalog)

```text
# Honorarios
honorario_principal, certificacion, aporte_12pct, cinco_pct_hon, firma_honorarios

# Honorarios varios (cobrables al cliente; NO pagables vía colegio)
art2_a, art12_a, art12_c, art12_f

# Impuestos (afectan total_impuestos_efectivo)
tasa_3pm, sellos, tasa_75pm, firma_impuestos

# Gastos admin
inscripcion, protocolo, ii_certificados, municipio, fotocopias_urgentes,
certificaciones_extra, catastro, testimonio, concuerda, informes_notariales,
extracto, fotocopias_simples, tasas_minimas
```

Subtotales (`subtotal_honorarios`, `total_leyes_notariales`, `total_impuestos`, `total_gastos_admin`,
`dif_honorarios`, `total_parcial`, `total_sin_iva`, `iva`, `total_factura`) se **recalculan**; no
tienen casillero propio.
