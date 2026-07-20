# Data Model: Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Feature**: `002-platform-extensions`  
**Date**: 2026-07-18  
**Source**: spec.md + research.md  
**Extends**: `001-plataforma-contaduria/data-model.md`

---

## Entity Relationship Overview (delta)

```
                    Escribano (NEW — soft delete)
                        │ FK (1:N)
                        ▼
                    Escritura  ◄─── escribano_nombre VARCHAR (snapshot)
                        │
                        │ (aggregated by — unchanged)
                        ▼
                  FacturaPrincipal
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      EntradaLibro (derived)  SalidaLibro (derived)
       [no persistence]        [no persistence]

Empleado (NEW — soft delete)
    │ (1:N, ordered by created_at DESC)
    ▼
SueldoHistorico (NEW — snapshot per month close)
```

Changes to existing entities:
- `Escritura.escribano` ENUM column → replaced by `escribano_id` FK + `escribano_nombre` VARCHAR snapshot
- `ConfiguracionFinanciera.salario_secretarias_total` → superseded by `Empleado.sueldo` per employee (kept for backward compat on old records)

---

## New Entities

### Escribano

Dynamic notary configuration. Replaces the hardcoded ENUM `('costanza', 'gabriel', 'victoria')`
on `Escritura`. Uses soft delete to preserve historical FK references.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `nombre` | VARCHAR(100) | not null | Display name, e.g. "Costanza" |
| `deleted_at` | TIMESTAMPTZ | nullable, default null | Soft delete; null = active |
| `created_at` | TIMESTAMPTZ | not null, default now() | |

**Business rules**:
- `nombre` unique among active rows only (partial unique index `WHERE deleted_at IS NULL`)
- A soft-deleted `Escribano` MUST NOT appear in the escribano selector for new/edited escrituras
- A soft-deleted `Escribano` with name "García" does NOT block creating a new active one with the same name
- Hard delete is forbidden; only soft delete is permitted

**Indexes**:
- `uq_escribano_nombre_active` — partial unique index: `UNIQUE (nombre) WHERE deleted_at IS NULL`
- `deleted_at` (btree) — for listing active escribanos

**Seed data** (migration `004`):
```
INSERT INTO escribano (nombre) VALUES ('Costanza'), ('Gabriel'), ('Victoria');
```

---

### Empleado

Employee (secretary) with configurable salary. Replaces the hardcoded split in
`ConfiguracionFinanciera.salario_secretarias_total`. Uses soft delete.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `nombre` | VARCHAR(100) | not null | Display name, e.g. "Graciela" |
| `sueldo` | NUMERIC(18,2) | not null, > 0 | Current monthly salary in ARS |
| `deleted_at` | TIMESTAMPTZ | nullable, default null | Soft delete; null = active |
| `created_at` | TIMESTAMPTZ | not null, default now() | |
| `updated_at` | TIMESTAMPTZ | not null, default now() | Updated on each sueldo change |

**Business rules**:
- `sueldo` MUST be > 0 (validated server-side, FR-016)
- Modifying `sueldo` updates `updated_at` and immediately affects the current month's Pago de Salarios calculation
- Does NOT modify `SueldoHistorico` of already-closed months (FR-017)
- Soft-deleted employees are excluded from Pago de Salarios for future months

**Indexes**:
- `uq_empleado_nombre_active` — partial unique index: `UNIQUE (nombre) WHERE deleted_at IS NULL`
- `deleted_at` (btree)

**Seed data** (migration `004`):
```
INSERT INTO empleado (nombre, sueldo)
VALUES ('Graciela', 1000000.00), ('Guadalupe', 1000000.00);
```

---

### SueldoHistorico

Immutable salary snapshot per employee per month. Generated automatically when a monthly
settlement is closed. Provides traceability for historical Pago de Salarios records.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, not null | |
| `empleado_id` | UUID | FK → Empleado.id, not null | References the employee (even if later soft-deleted) |
| `empleado_nombre` | VARCHAR(100) | not null | Snapshot of name at close time |
| `anio` | INTEGER | not null | |
| `mes` | INTEGER | not null, 1–12 | |
| `sueldo` | NUMERIC(18,2) | not null | Salary captured at month close |
| `created_at` | TIMESTAMPTZ | not null, default now() | When this snapshot was taken |

**Business rules**:
- One record per (`empleado_id`, `anio`, `mes`) — unique constraint
- NEVER updated after creation (append-only)
- `empleado_nombre` is snapshotted to preserve display even if employee is later soft-deleted

**Indexes**:
- Unique: (`empleado_id`, `anio`, `mes`)
- `(anio, mes)` (btree) — for month-based lookups

---

## Modified Entities

### Escritura (modified)

Replaces the hardcoded `escribano` ENUM with a FK to `Escribano` table.
Adds `escribano_nombre` snapshot for display resilience.

| Column | Change | Notes |
|---|---|---|
| `escribano` | **REMOVED** (ENUM column dropped after migration) | Was `ENUM('costanza', 'gabriel', 'victoria')` |
| `escribano_id` | **ADDED** — UUID, FK → Escribano.id, not null | Dynamic reference to Escribano entity |
| `escribano_nombre` | **ADDED** — VARCHAR(100), not null | Snapshot of name at creation time; ensures display even if Escribano is soft-deleted |

**Migration strategy** (in `004_platform_extensions.py`):
1. Add `escribano_id` nullable + `escribano_nombre` nullable
2. Seed `Escribano` table with Costanza, Gabriel, Victoria
3. `UPDATE escritura SET escribano_id = (SELECT id FROM escribano WHERE lower(nombre) = lower(escritura.escribano)), escribano_nombre = ...`
4. Set `escribano_id` and `escribano_nombre` NOT NULL
5. Drop `escribano` ENUM column

**New index**: `escribano_id` (btree)

---

## Derived Views (No Persistence)

### EntradaLibro (computed, not stored)

Derived at query time from `FacturaPrincipal` and `GastoAdicional` of escrituras
belonging to the requested month. Never persisted as a table.

**Composition per escritura**:

| Source field | Concepto label |
|---|---|
| `FacturaPrincipal.honorario_principal` | "Honorarios Profesionales" |
| `FacturaPrincipal.certificacion` | "Certificación" |
| `GastoAdicional` where `direccion = 'entrada'` | GastoAdicional.concepto (verbatim) |

**DTO shape** (one row per source item per escritura):

```
EntradaLibroDTO:
  escritura_id:    UUID
  escritura_nombre: str
  concepto:        str
  monto:           Decimal
  fecha_escritura: date   (Escritura.created_at date)
  escritura_url:   str    (client-side route: /escrituras/{id})
```

**Scoping**: same rule as Liquidación Mensual — all escrituras with `created_at` in the
requested month (both `abierta` and `cerrada`).

**Total**: sum of all `monto` values in the filtered set.

---

### SalidaLibro (computed, not stored)

| Source field | Concepto label |
|---|---|
| `FacturaPrincipal.tasa_3pm` | "Ing. Brutos (3‰)" |
| `FacturaPrincipal.sellos` | "Sellos Fiscales" |
| `FacturaPrincipal.tasa_75pm` | "Tasa 7.5‰" |
| `FacturaPrincipal.firma_impuestos` | "Firma Impuestos" |
| `FacturaPrincipal.art2_a` | "Leyes Notariales Art. 2 inc. a)" |
| `FacturaPrincipal.art12_a` | "Leyes Notariales Art. 12 inc. a)" |
| `FacturaPrincipal.art12_c` | "Leyes Notariales Art. 12 inc. c)" |
| `FacturaPrincipal.art12_f` | "Leyes Notariales Art. 12 inc. f)" |
| `FacturaPrincipal.inscripcion` | "Inscripción" |
| `FacturaPrincipal.protocolo` | "Protocolo" |
| `FacturaPrincipal.ii_certificados` | "I.I. Certificados" |
| `FacturaPrincipal.municipio` | "Municipio" |
| `FacturaPrincipal.fotocopias_urgentes` | "Fotocopias Urgentes" |
| `FacturaPrincipal.certificaciones_extra` | "Certificaciones Extra" |
| `FacturaPrincipal.catastro` | "Catastro" |
| `FacturaPrincipal.testimonio` | "Testimonio" |
| `FacturaPrincipal.concuerda` | "Concuerda" |
| `FacturaPrincipal.informes_notariales` | "Informes Notariales" |
| `FacturaPrincipal.extracto` | "Extracto" |
| `FacturaPrincipal.fotocopias_simples` | "Fotocopias Simples" |
| `FacturaPrincipal.tasas_minimas` | "Tasas Mínimas" |
| `GastoAdicional` where `direccion = 'salida'` | GastoAdicional.concepto (verbatim) |

**DTO shape**: identical structure to `EntradaLibroDTO`.

**Note**: `total_gastos_admin` column is **not** used directly — each admin expense item
is derived individually for traceability (FR-020).

---

## Soft Delete Infrastructure

All new entities that support soft delete (`Escribano`, `Empleado`) inherit from
`SoftDeleteMixin`. The global SQLAlchemy event listener registered in `database.py` ensures
soft-deleted rows are automatically excluded from all ORM queries unless explicitly bypassed.

```python
# Bypass for admin queries (never exposed to frontend):
await session.execute(
    select(Escribano).execution_options(include_deleted=True)
)
```

**FK preservation**: `Escritura.escribano_id` remains valid after `Escribano` is soft-deleted
because the row still exists physically. The `escribano_nombre` snapshot on `Escritura` ensures
the UI can always display the name without querying the possibly-soft-deleted `Escribano` row.

---

## Updated ERD (full picture)

```
ConfiguracionFinanciera (versioned immutable)
        │ FK
        ▼
    Escritura ──── escribano_id ──► Escribano (soft delete)
        │          escribano_nombre (snapshot)
        │ (1:1)
        ▼
  FacturaPrincipal ──► EntradaLibro (derived)
        │         ──► SalidaLibro (derived)
        │
    GastoAdicional (entrada | salida)

  LiquidacionMensual ──► PagoSalario (1:N)

  Empleado (soft delete) ──► SueldoHistorico (1:N, per month close)

  Usuario (auth, unchanged)
```

---

## Migration Checklist

Migration `004_platform_extensions.py` must:

- [ ] Create `escribano` table with partial unique index
- [ ] Create `empleado` table with partial unique index
- [ ] Create `sueldo_historico` table
- [ ] Register `SoftDeleteMixin` event listener in `database.py` (code change, not DB)
- [ ] Add `escribano_id UUID NULLABLE` and `escribano_nombre VARCHAR NULLABLE` to `escritura`
- [ ] Seed `Escribano`: Costanza, Gabriel, Victoria
- [ ] Seed `Empleado`: Graciela ($1,000,000), Guadalupe ($1,000,000)
- [ ] Populate `escritura.escribano_id` and `escritura.escribano_nombre` from existing ENUM values
- [ ] Set `escribano_id` and `escribano_nombre` NOT NULL on `escritura`
- [ ] Add FK constraint `escritura.escribano_id → escribano.id`
- [ ] Drop `escritura.escribano` ENUM column
- [ ] Add index on `escritura.escribano_id`
- [ ] Verify: zero rows have NULL `escribano_id` after migration
