# Quickstart (Delta): Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Feature**: `009-pagos-colegio-factura`  
**Date**: 2026-07-26  
**Base**: `specs/001-plataforma-contaduria/quickstart.md`  
**Requires**: features `007`, `008` merged (migrations `009`, `011`)

---

## New Environment Variables

None.

---

## Database Migration

```bash
make migrate
# or
docker compose exec backend alembic upgrade head
```

Migration `012` (`012_pagos_colegio_factura_lineas.py`) will:

1. Add `facturas_principales.lineas_deshabilitadas` JSONB default `[]`
2. Create enum `tipo_pago_escribania` (`colegio`, `otros`)
3. Add `pagos_colegio.tipo`, backfill from `imputacion`
4. Drop `pagos_colegio.imputacion` and enum `imputacion_pago_colegio`

---

## TDD Workflow (mandatory)

```bash
# 1. Líneas habilitables — write tests FIRST
cd backend && pytest tests/unit/test_factura_lineas.py -v

# 2. Plazo colegio con total_impuestos_efectivo + tipo colegio
pytest tests/unit/test_plazo_colegio.py -v

# 3. Libro salida solo pagos_colegio
pytest tests/unit/test_libros_service.py -v -k salida

# 4. Pago colegio tipo + detalle otros
pytest tests/unit/test_pago_colegio_service.py -v

# 5. Bulk preview + confirm
pytest tests/unit/test_pago_colegio_bulk.py -v
pytest tests/integration/test_pagos_colegio_bulk_api.py -v

# 6. Escritura update lineas_deshabilitadas + costo_total
pytest tests/integration/test_escrituras_api.py -v -k lineas

# 7. Full backend
pytest tests/ -v

# 8. Frontend (Vitest)
cd frontend && npm test -- --run PagoColegio FacturaDetalle EscrituraList
```

---

## Demo Seed

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

Expect `DEMO_SEED_VERSION=6`:

- Al menos una escritura con líneas deshabilitadas de demo
- Pagos colegio con `tipo` colegio/otros (sin imputación)
- Pendientes al Colegio coherentes con `total_impuestos_efectivo`

---

## Manual Validation Checklist

### Pagos de la escribanía (detalle escritura)

- [ ] Selector muestra solo **Colegio** (default) y **Otros**
- [ ] No aparece imputación honorarios varios
- [ ] Otros sin detalle → error de validación
- [ ] Pago Colegio reduce pendiente y actualiza badge vencimiento

### Libro de Salida

- [ ] Solo líneas de pagos Colegio y Otros del mes
- [ ] Líneas Otros muestran detalle en columna concepto
- [ ] No aparecen impuestos de servicios ni gastos extraordinarios
- [ ] Actualización en tiempo real al registrar pago (SSE)

### Factura — líneas habilitables

- [ ] Casillero por ítem de línea en factura abierta
- [ ] Deshabilitar gasto admin reduce costo al cliente, no Total impuestos
- [ ] Deshabilitar ítem impuesto reduce Total impuestos y pendiente Colegio
- [ ] No permite deshabilitar todas las líneas

### Pago masivo (listado Escrituras)

- [ ] Checkboxes por fila; acción con ≥1 selección
- [ ] Preview muestra pendiente por escritura
- [ ] Fecha única aplicada a todos los pagos
- [ ] Escrituras cerradas / sin pendiente no elegibles

---

## API Smoke (curl)

```bash
# Preview bulk (reemplazar TOKEN y UUIDs)
curl -s -X POST http://localhost:8000/api/v1/escrituras/pagos-colegio/bulk/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"escritura_ids":["<uuid1>","<uuid2>"]}' | jq

# Pago otros con detalle
curl -s -X POST http://localhost:8000/api/v1/escrituras/<id>/pagos-colegio \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"monto":"15000.00","fecha":"2026-07-26","tipo":"otros","concepto":"Tasa municipal imprevista"}' | jq
```
