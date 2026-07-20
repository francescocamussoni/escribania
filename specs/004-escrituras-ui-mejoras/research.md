# Research: Mejoras de Usabilidad en Escrituras y Marca

**Feature**: `004-escrituras-ui-mejoras`  
**Date**: 2026-07-20  
**Source**: spec.md + clarify session 2026-07-20 + codebase analysis (001–003)

---

## R-001 — Alcance de cambios en backend

**Decision**: **Sin cambios de API ni base de datos.** La feature es exclusivamente frontend (UI, utilidades cliente, copy).

**Rationale**:
- `GET /escrituras` ya expone `created_at`, `escribano_id`, filtros `estado` y `escribano_id` (`backend/src/api/routes/escrituras.py`).
- `EscrituraListItem` ya incluye todos los campos del listado (spec FR-001).
- Búsqueda por nombre y orden por fecha son responsabilidad del cliente (assumption de clarify).
- Renombrar labels de UI no requiere renombrar rutas `pagos-colegio` ni eventos SSE `pago_colegio.created` (FR-010).

**Alternatives considered**:

| Alternativa | Por qué se descartó |
|---|---|
| Agregar `?q=` y `?sort=created_at` al API | Volumen operativo bajo; evita trabajo backend innecesario |
| Migración DB para renombrar `pagos_colegio` | Fuera de alcance; identificadores internos intactos |

---

## R-002 — Arquitectura de filtrado en el listado

**Decision**: Pipeline de dos etapas:

1. **Servidor** — `GET /escrituras?escribano_id=&estado=` según píldoras activas.
2. **Cliente** — sobre el array devuelto: `filterByNombre()` + `sortByCreatedAt()`.

**Rationale**: Alineado con assumptions de spec y clarify; reutiliza `EscrituraListFilters` existente en `frontend/src/api/escrituras.ts`.

**Alternatives considered**:
- Todo en cliente con una sola carga → más datos transferidos sin beneficio.
- Todo en servidor → requiere extender OpenAPI sin necesidad.

---

## R-003 — Píldoras de escribano en fila superior

**Decision**: Construir opciones desde `GET /escribanos?include_inactive=true` **intersectado** con `escribano_id` distintos presentes en una carga inicial `GET /escrituras` sin filtros (cacheada en TanStack Query con `staleTime` alto en la página).

**Rationale**: Cumple FR-003 (“activos e inactivos **con escrituras asociadas**”) sin nuevo endpoint. Escribanos inactivos sin trámites no aparecen como píldora.

**Alternatives considered**:
- Mostrar todos los escribanos configurados → incluiría píldoras que siempre devuelven vacío.
- Endpoint dedicado `GET /escribanos?con_escrituras=true` → over-engineering para esta feature.

---

## R-004 — Persistencia de estado del listado

**Decision**: `sessionStorage` con clave `escrituras-list-state` (JSON serializado). Hook dedicado `useEscriturasListSession()`.

**Campos persistidos**: `escribanoFilter`, `estadoFilter`, `searchQuery`, `sortDirection`.

**Rationale**: Sobrevive desmontaje del componente al navegar a detalle u otras rutas; se borra al cerrar pestaña (FR-008a). Sin impacto de rendimiento.

**Alternatives considered**:
| Alternativa | Por qué se descartó |
|---|---|
| Solo estado React en layout padre | Se pierde al desmontar rutas actuales |
| URL query params | Más complejo; no requerido por spec |
| localStorage | Persistiría entre sesiones; contradice edge case de spec |

---

## R-005 — Ordenamiento por fecha de creación

**Decision**: Cabecera de columna “Fecha de creación” clickeable; alterna `desc` ↔ `asc`. Default: `desc` (assumption spec).

**Implementación**: Función pura `sortEscriturasByCreatedAt(items, direction)` en `frontend/src/utils/escrituraList.ts`; indicador visual `↑` / `↓` en header.

**Rationale**: FR-002 exige control visible; patrón estándar en tablas.

---

## R-006 — Layout de detalle en dos columnas

**Decision**: CSS Grid en `index.css`:

- `.escritura-detail__grid` — 2 columnas ≥1024px (`1fr 1fr`), 1 columna en mobile.
- Columna izquierda: `FacturaDetalle`.
- Columna derecha: `PagoClienteList` + `PagoColegioList` apilados.
- `.factura-detalle` — `grid-template-columns: 1fr 1fr` para subsecciones; total de factura full-width al pie.

**Rationale**: FR-011, FR-012, FR-013; sin nuevas dependencias; coherente con tokens existentes en `index.css`.

**Alternatives considered**:
- CSS columns (`column-count`) → orden de lectura menos predecible.
- Librería de layout (MUI Grid) → no está en el stack actual.

---

## R-007 — Rebranding y terminología

**Decision**: Buscar y reemplazar strings visibles en `frontend/src/` (grep confirmado):

| Antes | Después | Archivos |
|---|---|---|
| `Contaduría Escribanía` | `Escribanía Barat` | `Navbar.tsx`, `LoginPage.tsx` |
| `Pagos al Colegio` / `pago al Colegio` | `Pagos de la escribanía` / `pago de la escribanía` | `EscrituraDetail.tsx`, `PagoColegioForm.tsx`, `PagoColegioList.tsx`, `LibroSalidaPage.tsx`, `LibroSalidaTable.tsx` |

**No modificar**: nombres de archivos/componentes (`PagoColegio*`), rutas API, tipos TS, eventos SSE.

**Rationale**: FR-009, FR-010; minimize diff y riesgo de regresión.

---

## R-008 — Estrategia de testing (Hybrid)

**Decision**: Vitest unit tests para módulo `escrituraList.ts` y hook de session (si lógica extraída). Sin tests obligatorios de CSS/layout. Sin cambios en suite backend.

**Archivos de test nuevos**:
- `frontend/src/utils/escrituraList.test.ts`
- (opcional) `frontend/src/hooks/useEscriturasListSession.test.ts`

**Rationale**: Testing Strategy de spec; patrón existente en `format.test.ts`.

---

## R-009 — Figma / diseño

**Decision**: No hay referencia Figma para esta feature. Reutilizar tokens y clases existentes (`.filter-tabs`, `.detail-card`, `.factura-detalle`). Layout validado manualmente en viewport ≥1024px y <1024px.

**Rationale**: Constitution P10 aplica cuando hay nodo Figma; spec no lo provee. Cambios son reorganización de contenido existente, no nuevo diseño visual.
