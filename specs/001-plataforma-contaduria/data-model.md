# Data Model: Plataforma Contable — Escribanía

**Feature**: `001-plataforma-contaduria`  
**Date**: 2026-07-18  
**Source**: spec.md + research.md

---

## Entity Relationship Overview

```
ConfiguracionFinanciera (versioned, immutable rows)
        │
        │ FK (version used at creation)
        ▼
    Escritura ──────────────────────────────┐
        │ (1:1)                             │ (1:N)
        ▼                                   ▼
  FacturaPrincipal                   GastoAdicional
        │
        │ (aggregated by)
        ▼
  LiquidacionMensual ──────────────── PagoSalario (1:N)
        │
        │ references
        ▼
    Escritura (many-to-many via snapshot)

Usuario (standalone — auth only)
```

---

## Entities

### Escritura

Central entity. Living document until explicitly closed.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `nombre` | VARCHAR(255) | not null | Free-text name entered by secretary |
| `estado` | ENUM('abierta', 'cerrada') | not null, default 'abierta' | |
| `escribano` | ENUM('costanza', 'gabriel', 'victoria') | not null | |
| `usd_value` | NUMERIC(15,2) | not null, > 0 | Property value in USD |
| `dolar_mep` | NUMERIC(10,4) | not null, > 0 | MEP exchange rate at creation |
| `dolar_nacion` | NUMERIC(10,4) | not null, > 0 | Banco Nación exchange rate at creation |
| `config_version_id` | UUID | FK → ConfiguracionFinanciera.id, not null | Config snapshot used |
| `created_at` | TIMESTAMPTZ | not null, default now() | Month scoping anchor |
| `closed_at` | TIMESTAMPTZ | nullable | Set when estado → cerrada |
| `updated_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- `usd_value`, `dolar_mep`, `dolar_nacion` MUST be > 0 (validated server-side)
- Once `estado = cerrada`, no UPDATE is allowed on any field
- `created_at` is the canonical anchor for monthly scoping (never overwritten)

**Indexes**: `created_at` (btree), `escribano` (btree), `estado` (btree)

---

### FacturaPrincipal

Auto-generated 1:1 with Escritura. Stores all calculated monetary amounts as a
mutable snapshot while open; frozen when Escritura is closed.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `escritura_id` | UUID | FK → Escritura.id, unique, not null | 1:1 |
| `monto_base_mep` | NUMERIC(18,2) | not null | USD × dolar_mep |
| `precio_base_nacion` | NUMERIC(18,2) | not null | USD × dolar_nacion |
| `honorario_principal` | NUMERIC(18,2) | not null | 2.4% of monto, min configurable |
| `certificacion` | NUMERIC(18,2) | not null | 0.3% of monto |
| `suma_hon_cert` | NUMERIC(18,2) | not null | honorario + certificacion |
| `aporte_12pct` | NUMERIC(18,2) | not null | 12% of suma_hon_cert |
| `cinco_pct_hon` | NUMERIC(18,2) | not null | 5% of honorario, min configurable |
| `firma_honorarios` | NUMERIC(18,2) | not null | Fixed amount from config |
| `subtotal_honorarios` | NUMERIC(18,2) | not null | aporte_12pct + cinco_pct_hon + firma |
| `art2_a` | NUMERIC(18,2) | not null | 0.48% of monto |
| `art12_a` | NUMERIC(18,2) | not null | 0.40% of monto, min configurable |
| `art12_c` | NUMERIC(18,2) | not null | 0.12% of monto |
| `art12_f` | NUMERIC(18,2) | not null | Fixed amount from config |
| `total_leyes_notariales` | NUMERIC(18,2) | not null | Sum of art2_a..art12_f |
| `tasa_3pm` | NUMERIC(18,2) | not null | 3‰ of precio |
| `sellos` | NUMERIC(18,2) | not null | ~2.5% of precio with fixed adj. |
| `tasa_75pm` | NUMERIC(18,2) | not null | 7.5‰ of precio |
| `firma_impuestos` | NUMERIC(18,2) | not null | Fixed amount from config |
| `total_impuestos` | NUMERIC(18,2) | not null | Sum of tasa_3pm..firma_impuestos |
| `inscripcion` | NUMERIC(18,2) | not null | Fixed from config |
| `protocolo` | NUMERIC(18,2) | not null | Fixed from config |
| `ii_certificados` | NUMERIC(18,2) | not null | Fixed from config |
| `municipio` | NUMERIC(18,2) | not null | Fixed from config |
| `fotocopias_urgentes` | NUMERIC(18,2) | not null | Fixed from config |
| `certificaciones_extra` | NUMERIC(18,2) | not null | Fixed from config |
| `catastro` | NUMERIC(18,2) | not null | Fixed from config |
| `testimonio` | NUMERIC(18,2) | not null | Fixed from config |
| `concuerda` | NUMERIC(18,2) | not null | Fixed from config |
| `informes_notariales` | NUMERIC(18,2) | not null | Fixed from config |
| `extracto` | NUMERIC(18,2) | not null | Fixed from config |
| `fotocopias_simples` | NUMERIC(18,2) | not null | Fixed from config |
| `tasas_minimas` | NUMERIC(18,2) | not null | Fixed from config |
| `total_gastos_admin` | NUMERIC(18,2) | not null | Sum of all gastos fijos |
| `total_factura` | NUMERIC(18,2) | not null | Grand total |
| `updated_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- Recalculated on every save of an open Escritura
- Frozen (no UPDATE) when parent Escritura is closed
- All amounts use `NUMERIC(18,2)` to avoid floating-point errors

---

### GastoAdicional

Ad-hoc expense entries associated with an Escritura.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `escritura_id` | UUID | FK → Escritura.id, not null | |
| `concepto` | VARCHAR(500) | not null | Description of expense |
| `monto` | NUMERIC(18,2) | not null, > 0 | |
| `direccion` | ENUM('entrada', 'salida') | not null | Cash flow direction |
| `fecha` | DATE | not null | Date of expense |
| `created_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- Can only be added to open Escrituras
- Immutable once created (no edit/delete — append-only log)

**Indexes**: `escritura_id` (btree), `fecha` (btree)

---

### ConfiguracionFinanciera

Versioned, immutable rows. Never UPDATE in place — insert a new row for each change.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `version` | INTEGER | not null | Increments on each new config |
| `descripcion` | VARCHAR(255) | nullable | Optional label for this version |
| `honorario_pct` | NUMERIC(7,5) | not null, default 0.024 | 2.4% |
| `honorario_min` | NUMERIC(18,2) | not null | Minimum honorario amount |
| `certificacion_pct` | NUMERIC(7,5) | not null, default 0.003 | 0.3% |
| `aporte_pct` | NUMERIC(7,5) | not null, default 0.12 | 12% |
| `cinco_pct_hon_pct` | NUMERIC(7,5) | not null, default 0.05 | 5% |
| `cinco_pct_hon_min` | NUMERIC(18,2) | not null | Minimum 5% hon amount |
| `firma_honorarios` | NUMERIC(18,2) | not null | Fixed fee |
| `art2_a_pct` | NUMERIC(7,5) | not null, default 0.0048 | |
| `art12_a_pct` | NUMERIC(7,5) | not null, default 0.004 | |
| `art12_a_min` | NUMERIC(18,2) | not null | |
| `art12_c_pct` | NUMERIC(7,5) | not null, default 0.0012 | |
| `art12_f` | NUMERIC(18,2) | not null | Fixed |
| `tasa_3pm_pct` | NUMERIC(7,5) | not null, default 0.003 | |
| `sellos_pct` | NUMERIC(7,5) | not null, default 0.025 | |
| `sellos_ajuste_fijo` | NUMERIC(18,2) | not null, default 250 | Fixed deduction |
| `tasa_75pm_pct` | NUMERIC(7,5) | not null, default 0.0075 | |
| `firma_impuestos` | NUMERIC(18,2) | not null | Fixed |
| `inscripcion` | NUMERIC(18,2) | not null | |
| `protocolo` | NUMERIC(18,2) | not null | |
| `ii_certificados` | NUMERIC(18,2) | not null | |
| `municipio` | NUMERIC(18,2) | not null | |
| `fotocopias_urgentes` | NUMERIC(18,2) | not null | |
| `certificaciones_extra` | NUMERIC(18,2) | not null | |
| `catastro` | NUMERIC(18,2) | not null | |
| `testimonio` | NUMERIC(18,2) | not null | |
| `concuerda` | NUMERIC(18,2) | not null | |
| `informes_notariales` | NUMERIC(18,2) | not null | |
| `extracto` | NUMERIC(18,2) | not null | |
| `fotocopias_simples` | NUMERIC(18,2) | not null | |
| `tasas_minimas` | NUMERIC(18,2) | not null | |
| `salario_secretarias_total` | NUMERIC(18,2) | not null | e.g. 2,000,000 ARS |
| `created_at` | TIMESTAMPTZ | not null, default now() | |
| `created_by` | UUID | FK → Usuario.id, nullable | Audit: who changed config |

**Business rules**:
- Never updated — a new row is inserted for each configuration change
- The row with the highest `version` number is the active configuration
- Escrituras FK to the version active at their creation time

---

### LiquidacionMensual

Monthly settlement snapshot. Created when closing a month.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `anio` | INTEGER | not null | |
| `mes` | INTEGER | not null, 1–12 | |
| `fecha_generacion` | TIMESTAMPTZ | not null, default now() | |
| `total_costanza` | NUMERIC(18,2) | not null | |
| `total_gabriel` | NUMERIC(18,2) | not null | |
| `total_victoria` | NUMERIC(18,2) | not null | |
| `total_global` | NUMERIC(18,2) | not null | |
| `created_by` | UUID | FK → Usuario.id, nullable | |

**Unique constraint**: (`anio`, `mes`) — one liquidación per month

---

### PagoSalario

Monthly payment record per person (escribanos + secretarias).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `liquidacion_id` | UUID | FK → LiquidacionMensual.id, not null | |
| `persona` | VARCHAR(100) | not null | Name: Costanza, Gabriel, Victoria, Graciela, Guadalupe |
| `tipo` | ENUM('escribano', 'secretaria') | not null | |
| `monto` | NUMERIC(18,2) | not null | |
| `detalle_json` | JSONB | nullable | Array of {escritura_id, nombre, honorario, certificacion} |

**Business rules**:
- For escribanos: monto = sum(honorario_principal + certificacion) per escritura in month
- For secretarias: monto = salario_secretarias_total / 2 (from active config)
- `detalle_json` stores the traceable breakdown linking to each Escritura

---

### Usuario

Authentication entity. Single profile — full access.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `username` | VARCHAR(100) | unique, not null | |
| `hashed_password` | VARCHAR(255) | not null | Argon2id hash |
| `nombre_display` | VARCHAR(100) | nullable | Shown in UI |
| `activo` | BOOLEAN | not null, default true | |
| `created_at` | TIMESTAMPTZ | not null, default now() | |
| `last_login_at` | TIMESTAMPTZ | nullable | |

---

## State Transitions

### Escritura lifecycle

```
         [created]
             │
             ▼
          ABIERTA  ◄──── editable (inputs, gastos adicionales)
             │            recalculates FacturaPrincipal on every save
             │
       [secretaria closes]
             │
             ▼
          CERRADA  ──── immutable; included in liquidación of its creation month
```

### ConfiguracionFinanciera versioning

```
  version N (active)
       │
  [admin saves new config]
       │
       ▼
  version N+1 (new active)   ← old version N never deleted; FK from old escrituras preserved
```

---

## Scoping Rules (Monthly Queries)

```sql
-- Escrituras belonging to month M for liquidación
WHERE created_at >= date_trunc('month', M)
  AND created_at <  date_trunc('month', M) + interval '1 month'

-- Active config at any given moment
SELECT * FROM configuracion_financiera
ORDER BY version DESC
LIMIT 1
```
