# Quickstart (Delta): Pagos del Cliente y Libros Contables Basados en Caja Real

**Feature**: `003-pagos-cliente`  
**Date**: 2026-07-20  
**Base**: `specs/002-platform-extensions/quickstart.md`

This document covers only the **new setup steps and validations** introduced by feature 003.
For the full environment setup (Docker, DB, auth, AWS deployment), refer to the base quickstart.

---

## New Environment Variables

No new environment variables required for this feature.

---

## Database Migration

After pulling the feature 003 branch, run the new migration:

```bash
# Option A — Makefile
make migrate

# Option B — Docker Compose
docker compose exec backend alembic upgrade head
```

Migration `006_pagos_cliente` will:
1. Create `pagos_cliente` and `pagos_colegio` tables
2. Migrate `gastos_adicionales` WHERE `direccion = 'entrada'` → `pagos_cliente`
3. Migrate `gastos_adicionales` WHERE `direccion = 'salida'` → `pagos_colegio`
4. Insert implicit client payments for closed escrituras without payment history
5. Drop `gastos_adicionales` table and `direccion_gasto` enum

**Expected output**:
```
Running upgrade ... -> 006_pagos_cliente
Migrated N gastos entrada → pagos_cliente
Migrated M gastos salida → pagos_colegio
Inserted K implicit payments for closed escrituras
Dropped gastos_adicionales
OK
```

---

## Demo data (local / Docker Compose)

With `SEED_DEMO_DATA=true` and `ENVIRONMENT=local`, the backend seeds **12 demo escrituras**
(4 scenarios × Costanza, Gabriel, Victoria) on first startup. Idempotent: restarts skip if
`[DEMO]` escrituras already exist.

| Escenario | Descripción |
|-----------|-------------|
| C1 | Creada y cerrada en **junio 2026**, pagada en junio |
| C2 | **Abierta**, creada en junio, pagos junio+julio parciales + pago colegio |
| C3 | **Cerrada**, creada en junio, pagos junio+julio, saldada en julio |
| C4 | Creada y cerrada en **julio 2026**, pagada en julio |

Manual seed (local, DB running):

```bash
cd backend && SEED_DEMO_DATA=true make demo-data
```

Reset demo: `make db-down && make db-up` then `docker compose up`.

---

## Validating the Migration

```bash
# Confirm gastos_adicionales is gone
docker compose exec db psql -U escribania -d escribania -c "\dt pagos_*"

# Confirm closed escrituras have implicit payments
docker compose exec db psql -U escribania -d escribania -c \
  "SELECT e.nombre, COUNT(pc.id) FROM escrituras e \
   LEFT JOIN pagos_cliente pc ON pc.escritura_id = e.id \
   WHERE e.estado = 'cerrada' GROUP BY e.nombre LIMIT 5;"
```

---

## Running Tests (TDD)

```bash
# Unit tests — saldo, libros, liquidación
docker compose exec backend python -m pytest \
  tests/unit/test_pago_saldo.py \
  tests/unit/test_pago_cliente_service.py \
  tests/unit/test_pago_colegio_service.py \
  tests/unit/test_libros_service.py \
  tests/unit/test_liquidacion.py -v

# Integration tests — API
docker compose exec backend python -m pytest \
  tests/integration/test_pagos_cliente_api.py \
  tests/integration/test_pagos_colegio_api.py \
  tests/integration/test_libros_api.py \
  tests/integration/test_liquidacion_api.py \
  tests/integration/test_escrituras_api.py -v
```

---

## Validating Pagos del Cliente

```bash
# Create or use an open escritura
ESCRITURA_ID="<uuid>"

# Register partial payment
curl -b cookies.txt -X POST "http://localhost:8000/api/v1/escrituras/${ESCRITURA_ID}/pagos-cliente" \
  -H "Content-Type: application/json" \
  -d '{"monto": "400000.00", "fecha": "2026-07-20", "concepto": "Anticipo"}'

# Check saldo on escritura detail
curl -b cookies.txt "http://localhost:8000/api/v1/escrituras/${ESCRITURA_ID}"
# Expected: total_pagado=400000, saldo_pendiente=costo_total-400000

# Try to close with pending balance (should fail 409)
curl -b cookies.txt -X POST "http://localhost:8000/api/v1/escrituras/${ESCRITURA_ID}/close"
# Expected: 409 with saldo_pendiente in body
```

---

## Validating Pagos al Colegio

```bash
# Register colegio payment (works even if client has saldo pendiente)
curl -b cookies.txt -X POST "http://localhost:8000/api/v1/escrituras/${ESCRITURA_ID}/pagos-colegio" \
  -H "Content-Type: application/json" \
  -d '{"monto": "150000.00", "fecha": "2026-07-20"}'

# Check escritura shows total_leyes_notariales_proyectadas (informative only)
curl -b cookies.txt "http://localhost:8000/api/v1/escrituras/${ESCRITURA_ID}"
```

---

## Validating Libros (Caja Real)

```bash
# Libro de Entrada — only client payments in July 2026
curl -b cookies.txt "http://localhost:8000/api/v1/libros/entrada?anio=2026&mes=7"
# Expected: lineas = pagos del mes; resumen_deudas for open escrituras with debt

# Libro de Salida — only colegio payments in July 2026
curl -b cookies.txt "http://localhost:8000/api/v1/libros/salida?anio=2026&mes=7"
# Expected: lineas = pagos colegio del mes; NO factura-derived items
```

---

## Validating Liquidación y Pago de Salarios

```bash
# Liquidación — lump sum per escritura with payments in month
curl -b cookies.txt "http://localhost:8000/api/v1/liquidacion?anio=2026&mes=7"
# Expected: monto_cobrado per escritura (NOT honorario+certificación projected)

# Pago de Salarios — escribano total = sum of monto_cobrado
curl -b cookies.txt "http://localhost:8000/api/v1/salarios?anio=2026&mes=7"
```

---

## Validating Real-Time Updates (SSE)

1. **Tab 1** → Libro de Entrada page (current month)
2. **Tab 2** → Escritura detail → register a client payment
3. Tab 1 should update within 2 seconds (no page reload)

Repeat with Tab 1 on Liquidación page — totals should update on payment registration.

---

## Frontend Routes (unchanged paths, modified content)

| Route | Change |
|---|---|
| `/escrituras/:id` | Gastos Adicionales → Pagos del Cliente + Pagos al Colegio |
| `/escrituras` | List shows costo_total, total_pagado, saldo_pendiente |
| `/libro-entrada` | Client payments + debt summary |
| `/libro-salida` | Colegio payments only |
| `/liquidacion` | monto_cobrado lump sum per escritura |
| `/salarios` | Escribano totals from real payments |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Cannot close escritura | saldo_pendiente > 0 | Register remaining client payment |
| Libro Entrada empty | No payments in selected month | Register payment with fecha in that month |
| Liquidación missing escritura | No client payments in month | Expected — only escrituras with payments appear |
| 410 on POST /gastos | Endpoint deprecated | Use /pagos-cliente or /pagos-colegio |
| Migration fails on re-run | Non-idempotent script | Migration must use IF NOT EXISTS / skip existing |
