# Data Model: Mejoras de Usabilidad en Escrituras y Marca

**Feature**: `004-escrituras-ui-mejoras`  
**Date**: 2026-07-20  
**Source**: spec.md + research.md  
**Extends**: `001-plataforma-contaduria/data-model.md` (sin cambios de persistencia)

---

## Database / Backend Delta

**Ninguno.** No se crean tablas, columnas ni migraciones Alembic.

---

## API Delta

**Ninguno.** Se consumen contratos existentes:

| Endpoint | Uso en esta feature |
|---|---|
| `GET /escrituras` | Listado con query `escribano_id`, `estado` |
| `GET /escribanos` | Población de píldoras de escribano (`include_inactive=true`) |

Campos relevantes de `EscrituraListItem` (ya expuestos):

| Campo | Tipo | Uso UI |
|---|---|---|
| `id` | UUID | Link al detalle |
| `nombre` | string | Columna + búsqueda cliente |
| `estado` | enum | Columna + filtro estado |
| `escribano_id` | UUID | Filtro escribano |
| `escribano_nombre` | string | Columna |
| `created_at` | datetime | Columna + orden cliente |
| `costo_total` | MoneyStr | Columna |
| `total_pagado` | MoneyStr | Columna |
| `saldo_pendiente` | MoneyStr | Columna |
| `pagada_al_100` | bool | Badge cobro |
| `sobrepago` | bool | Badge cobro |

---

## Frontend State Model (nuevo)

### EscriturasListSessionState

Estado persistido en `sessionStorage` (clave `escrituras-list-state`).

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `escribanoFilter` | `'todas' \| string` | `'todas'` | UUID del escribano o todas |
| `estadoFilter` | `'todas' \| 'abierta' \| 'cerrada'` | `'todas'` | Filtro de estado |
| `searchQuery` | string | `''` | Texto de búsqueda por nombre |
| `sortDirection` | `'asc' \| 'desc'` | `'desc'` | Orden por `created_at` |

**Reglas**:
- Se serializa/deserializa como JSON; validar forma al leer (fallback a defaults).
- Se escribe en cada cambio de filtro/búsqueda/orden.
- Se ignora si `sessionStorage` no disponible (SSR/tests).

### EscritanoFilterOption (derivado, no persistido)

| Campo | Tipo | Fuente |
|---|---|---|
| `id` | UUID | `EscribanoResponse.id` |
| `label` | string | `EscribanoResponse.nombre` (+ sufijo inactivo si aplica) |

Construido por intersección escribanos API ∩ `escribano_id` distintos en listado.

---

## UI Layout Model (detalle escritura)

```
EscrituraDetail
├── header (nombre, acciones)
├── Saldo (card, full width)
├── Datos de la escritura (card, full width)
└── escritura-detail__grid  [≥1024px: 2 cols]
    ├── col-left: Factura principal
    │   └── factura-detalle [2-col subsecciones]
    └── col-right: stack
        ├── Pagos del cliente
        └── Pagos de la escribanía  (label renombrado)
```

---

## Terminology Mapping (UI only)

| Concepto interno | Label anterior | Label nuevo |
|---|---|---|
| Marca app | Contaduría Escribanía | Escribanía Barat |
| PagoColegio (dominio) | Pagos al Colegio | Pagos de la escribanía |

Identificadores de código/API **sin cambio**: `PagoColegio`, `pagos_colegio`, `/pagos-colegio`, `pago_colegio.created`.
