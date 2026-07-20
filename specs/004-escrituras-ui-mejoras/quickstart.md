# Quickstart (Delta): Mejoras de Usabilidad en Escrituras y Marca

**Feature**: `004-escrituras-ui-mejoras`  
**Date**: 2026-07-20  
**Base**: `specs/003-pagos-cliente/quickstart.md`

This document covers only validations for feature 004. No migrations, env vars, or backend
changes are required.

---

## Prerequisites

- Feature 003 (`pagos-cliente`) merged and demo data seeded (recommended for filter testing).
- Stack running per base quickstart:

```bash
docker compose up --build
# or: make dev
```

Frontend: http://localhost:5173  
Login: credentials from `backend/scripts/create_user.py` / demo setup.

---

## Build & Test (frontend)

```bash
cd frontend
npm install
npm run test        # Vitest — escrituraList + session helpers
npm run build
```

---

## Manual Validation Checklist

### Listado de escrituras (`/escrituras`)

- [ ] **Toolbar superior**: barra de búsqueda a la izquierda y chips de escribano a la derecha (misma fila en desktop).
- [ ] **Filtro escribano**: solo nombres con escrituras (sin botón "Todas"); click selecciona, click de nuevo deselecciona; sin selección = todas.
- [ ] **Filtro estado**: segunda fila izquierda con píldoras Todas / Abiertas / Cerradas.
- [ ] **Filtro fecha de creación**: segunda fila derecha — selects Mes y Año; al cambiar cualquiera aplica ambos vía API; **Eliminar filtro** vuelve a mostrar todas las fechas.
- [ ] Columna **Fecha de creación** visible; click en header alterna orden asc/desc (default: más recientes primero).
- [ ] Barra de búsqueda filtra por nombre (case-insensitive) sin resetear filtros.
- [ ] Combinación escribano + estado + período + búsqueda aplica AND.
- [ ] Mensaje claro cuando no hay resultados con filtros activos.
- [ ] Abrir detalle y volver: filtros, búsqueda y orden conservados (misma pestaña).
- [ ] Cerrar pestaña y reabrir: estado reiniciado a defaults.

### Detalle de escritura (`/escrituras/:id`)

- [ ] Saldo y Datos arriba a ancho completo; debajo grid en desktop (≥1024px).
- [ ] Proporción columnas **~60% factura / ~40% pagos**; contenido principal usa más ancho (max ~1360px).
- [ ] Izquierda: Factura principal con subsecciones en dos columnas internas.
- [ ] Derecha: Pagos del cliente, luego Pagos de la escribanía (apilados).
- [ ] En viewport estrecho: saldo → datos → factura → pagos cliente → pagos escribanía.

### Marca y terminología

- [ ] Navbar, login y título de pestaña muestran **Escribanía Barat**.
- [ ] Detalle, libro de salida, formularios y mensajes vacíos usan **Pagos de la escribanía** / **pago de la escribanía**.
- [ ] Rutas `/pagos-colegio` y funcionalidad de registro sin cambios (solo copy visible).

### Regresión (SC-005)

- [ ] Crear escritura, registrar pagos cliente/escribanía, cerrar con saldo $0.
- [ ] Liquidación, salarios y libros siguen operativos.

---

## Automated Tests

```bash
cd frontend && npm run test
```

Expected: unit tests green for `filterByNombre`, `sortByCreatedAt`, `buildEscribanoFilterOptions`, and `useEscriturasListSession` helpers (19 tests total as of feature completion).
