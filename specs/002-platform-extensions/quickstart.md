# Quickstart (Delta): Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Feature**: `002-platform-extensions`  
**Date**: 2026-07-18  
**Base**: `specs/001-plataforma-contaduria/quickstart.md`

This document covers only the **new setup steps and validations** introduced by feature 002.
For the full environment setup (Docker, DB, auth, AWS deployment), refer to the base quickstart.

---

## New Environment Variables

Add these to `.env` (and `.env.example`) before starting the stack:

```bash
# --- Feature 002: Dollar Exchange Rate API ---
COTIZACION_API_URL=https://api.argentinadatos.com
COTIZACION_FALLBACK_URL=https://dolarapi.com
COTIZACION_CACHE_TTL_HOURS=8
```

These are the only required additions. All other variables are inherited from feature 001.

---

## Database Migration

After pulling the feature 002 branch, run the new migration:

```bash
# Option A — Makefile
make migrate

# Option B — Docker Compose
docker compose exec backend alembic upgrade head
```

Migration `004_platform_extensions` will:
1. Create `escribano`, `empleado`, `sueldo_historico` tables
2. Seed Escribanos: Costanza, Gabriel, Victoria
3. Seed Empleados: Graciela ($1,000,000), Guadalupe ($1,000,000)
4. Migrate `Escritura.escribano` ENUM → `escribano_id` FK + `escribano_nombre` snapshot
5. Drop the old `escribano` ENUM column

**Expected output**:
```
Running upgrade ... -> 004_platform_extensions
Seeded 3 escribanos: Costanza, Gabriel, Victoria
Seeded 2 empleados: Graciela ($1,000,000), Guadalupe ($1,000,000)
Migrated N escrituras: escribano ENUM → FK
OK
```

---

## Validating the Migration

```bash
# Confirm all escrituras have escribano_id populated
docker compose exec db psql -U escribania escribania_db \
  -c "SELECT count(*) FROM escritura WHERE escribano_id IS NULL;"
# Expected: 0

# Confirm escribanos were seeded
docker compose exec db psql -U escribania escribania_db \
  -c "SELECT nombre, deleted_at FROM escribano;"
# Expected: Costanza, Gabriel, Victoria — all with deleted_at = NULL

# Confirm empleados were seeded
docker compose exec db psql -U escribania escribania_db \
  -c "SELECT nombre, sueldo FROM empleado;"
# Expected: Graciela 1000000.00, Guadalupe 1000000.00
```

---

## Running New Tests (TDD)

All new test files follow TDD — write failing tests first, then implement.

```bash
# Unit tests for new services
docker compose exec backend python -m pytest tests/unit/test_cotizacion_service.py -v
docker compose exec backend python -m pytest tests/unit/test_libros_service.py -v
docker compose exec backend python -m pytest tests/unit/test_empleado_service.py -v

# Integration tests for new endpoints
docker compose exec backend python -m pytest tests/integration/test_cotizacion_api.py -v
docker compose exec backend python -m pytest tests/integration/test_escribanos_api.py -v
docker compose exec backend python -m pytest tests/integration/test_empleados_api.py -v
docker compose exec backend python -m pytest tests/integration/test_libros_api.py -v

# All tests (feature 001 + 002 combined)
make test
```

---

## Validating the Cotización API

With the backend running:

```bash
# Get today's MEP rate
curl -b cookies.txt \
  "http://localhost:8000/api/v1/cotizacion?casa=bolsa"

# Get Banco Nación rate for a specific historical date
curl -b cookies.txt \
  "http://localhost:8000/api/v1/cotizacion?casa=oficial&fecha=2026-07-01"

# Expected response:
# {"casa":"bolsa","fecha":"2026-07-18","compra":1190.5,"venta":1195.0,"source":"api"}
# Second call to same date → "source": "cache"
```

**Testing cache behavior**:
```bash
# First call — source should be "api"
curl -b cookies.txt "http://localhost:8000/api/v1/cotizacion?casa=bolsa&fecha=2026-07-01"
# Second call (same date) — source should be "cache"
curl -b cookies.txt "http://localhost:8000/api/v1/cotizacion?casa=bolsa&fecha=2026-07-01"
```

**Testing error handling** (simulate API failure):
```bash
# Set an invalid API URL to force error
COTIZACION_API_URL=https://invalid.nonexistent.example.com docker compose up backend
# Then:
curl -b cookies.txt "http://localhost:8000/api/v1/cotizacion?casa=bolsa"
# Expected: HTTP 503 with descriptive error message (not a 500)
```

---

## Validating Escribano Configuration

```bash
# List active escribanos
curl -b cookies.txt http://localhost:8000/api/v1/configuracion/escribanos

# Add a new escribano
curl -b cookies.txt -X POST http://localhost:8000/api/v1/configuracion/escribanos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Martínez"}'

# Try to add duplicate — should return 409
curl -b cookies.txt -X POST http://localhost:8000/api/v1/configuracion/escribanos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Martínez"}'

# Deactivate without force (if no escrituras) — should succeed with 204
curl -b cookies.txt -X DELETE http://localhost:8000/api/v1/configuracion/escribanos/<id>

# Deactivate with escrituras, no force — should return 409
# Deactivate with escrituras, with force — should succeed
curl -b cookies.txt -X DELETE \
  "http://localhost:8000/api/v1/configuracion/escribanos/<id>?force=true"
```

---

## Validating Libros

```bash
# Get Libro de Entrada for current month
curl -b cookies.txt http://localhost:8000/api/v1/libros/entrada

# Get Libro de Salida for a specific month
curl -b cookies.txt "http://localhost:8000/api/v1/libros/salida?anio=2026&mes=7"

# Expected: each line has escritura_id, escritura_nombre, concepto, monto
# Expected: Libro de Entrada contains only honorarios/certificación/gastos-entrada
# Expected: Libro de Salida contains impuestos/sellos/aportes/gastos-salida
```

**Validating traceability (SC-002, SC-003)**:
```bash
# Create a test escritura and verify it appears in both libros
curl -b cookies.txt -X POST http://localhost:8000/api/v1/escrituras \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test Trazabilidad",
    "usd_value": 105000,
    "dolar_mep": 1450.34,
    "dolar_nacion": 1425.00,
    "escribano_id": "<costanza-uuid>"
  }'

# Libro entrada should now contain lines for this escritura
curl -b cookies.txt http://localhost:8000/api/v1/libros/entrada
# Verify: lines with escritura_nombre = "Test Trazabilidad" and
#         concepto = "Honorarios Profesionales" / "Certificación"
```

---

## Validating Real-Time Updates (Libros + SSE)

Open two browser tabs:
1. **Tab 1** → Libro de Entrada page (current month)
2. **Tab 2** → Create a new Escritura

After saving the escritura in Tab 2, the Libro de Entrada totals in Tab 1 should update
within 2 seconds without page reload (SC-007).

---

## New UI Sections

After deploying the frontend, these sections are accessible:

| Section | URL | Description |
|---|---|---|
| Libro de Entrada | `/libro-entrada` | Monthly incoming cash flows |
| Libro de Salida | `/libro-salida` | Monthly outgoing payments |
| Configuración > Escribanos | `/configuracion?tab=escribanos` | Manage notaries |
| Configuración > Empleados | `/configuracion?tab=empleados` | Manage employees + salaries |

The `EscrituraForm` now includes:
- Date picker (default: today)
- "Consultar cotización" button that auto-fills MEP and Banco Nación fields
- Fields remain manually editable after auto-fill

---

## Common Issues (Feature 002)

| Problem | Likely cause | Fix |
|---|---|---|
| Migration fails: `column "escribano" does not exist` | Migration already partially applied | Run `alembic downgrade 003` then `alembic upgrade head` |
| `GET /cotizacion` returns 503 | ArgentinaDatos unreachable | Check `COTIZACION_API_URL` env var; test manually with `curl https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/2026/07/01` |
| Cotización button returns "Sin datos para esa fecha" | Weekend or market holiday | Normal behavior; enter rate manually |
| Libro de Entrada is empty | No escrituras for selected month | Create a test escritura for the current month |
| Escribano not showing in selector | Escribano is soft-deleted | Re-activate from Configuración > Escribanos or create a new one |
