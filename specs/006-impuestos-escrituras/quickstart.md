# Quickstart (Delta): Impuestos por Escritura

**Feature**: `006-impuestos-escrituras`  
**Date**: 2026-07-20  
**Base**: `specs/003-pagos-cliente/quickstart.md`

This document covers setup and validation steps introduced by feature 006.
For full environment setup, refer to the base quickstart.

---

## New Environment Variables

No new environment variables required.

---

## Database Migration

```bash
make migrate
# or
docker compose exec backend alembic upgrade head
```

Migration `007_impuestos_escritura` will:

1. Create enums `tipo_impuesto`, `direccion_prorrateo`
2. Create `impuestos_escritura`
3. Create `pagos_impuesto_cliente` and `pagos_impuesto_escribania` (UNIQUE per impuesto)
4. Add indexes on `escritura_id` and `fecha`

**Expected**: `Running upgrade ... -> 007_impuestos_escritura`

---

## TDD Workflow (mandatory)

```bash
# 1. Prorrateo puro (write tests first)
cd backend && pytest tests/unit/test_impuesto_prorrateo.py -v

# 2. Balance y cierre
pytest tests/unit/test_impuesto_balance.py -v

# 3. Services + API
pytest tests/unit/test_impuesto_service.py tests/integration/test_impuestos_api.py -v

# 4. Libros y liquidación
pytest tests/unit/test_libros_service.py tests/unit/test_liquidacion.py -v
```

---

## Manual Validation Checklist

### Prorrateo

1. Open an escritura → Impuestos → create API impuesto:
   - Monto total: `10000`
   - Período: `2026-05-01` → `2026-06-30`
   - Fecha corte: `2026-06-15`
   - Dirección: **hacia atrás**
2. Verify suggested amount ≈ `10000 × 46/61` = `8196.72` (rounded)
3. Switch direction to **hacia adelante** → suggested ≈ `10000 × 15/61` = `2459.02`

### Pagos y libros

1. Register **Pago cliente** with suggested amount, fecha `2026-07-10`
2. Libro de Entrada julio 2026 shows impuesto line
3. Register **Pago escribanía** same amount, fecha `2026-07-15`
4. Libro de Salida julio shows matching line

### Liquidación (asimetría mensual OK)

1. With only client payment in July → Liquidación julio shows `+neto_impuestos` for escribano
2. Month close still allowed
3. Add escribanía payment in August → net shifts accordingly

### Cierre escritura

1. With balance impuestos ≠ 0 → `POST /escrituras/{id}/close` returns **409**
2. With impuesto missing a payment → **409** with pending list
3. When balance = 0 and all impuestos complete → close succeeds (plus honorarios saldo = 0)

---

## Frontend

After backend is running:

```bash
cd frontend && npm run dev
```

Navigate to `/escrituras/{id}` — Impuestos section appears below Pagos del cliente and Pagos de la escribanía.

SSE: registering/editing impuestos invalidates `libros`, `liquidacion`, `salarios`, `escritura` queries.

---

## API Smoke Test

```bash
# Create impuesto
curl -b cookies.txt -X POST "http://localhost:8000/api/v1/escrituras/{id}/impuestos" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "API",
    "monto_total": "10000.00",
    "periodo_inicio": "2026-05-01",
    "periodo_fin": "2026-06-30",
    "fecha_corte": "2026-06-15",
    "direccion_prorrateo": "hacia_atras"
  }'

# Register pago cliente
curl -b cookies.txt -X POST "http://localhost:8000/api/v1/escrituras/{id}/impuestos/{impuesto_id}/pago-cliente" \
  -H "Content-Type: application/json" \
  -d '{"monto": "8196.72", "fecha": "2026-07-10"}'
```

---

## Dependencies

- Feature **004** (layout detalle dos columnas) should be deployed for optimal UI placement.
- Feature **003** (pagos cliente/colegio, libros por caja real) must be present.
