# Quickstart (Delta): Vencimiento de pago al Colegio y régimen Monotributo

**Feature**: `008-factura-vencimiento-monotributo`  
**Date**: 2026-07-26  
**Base**: `specs/001-plataforma-contaduria/quickstart.md`  
**Requires**: feature `007-refactor-factura-montos` merged (migration `009`)

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

Migration `011` (`011_plazo_colegio_imputacion.py`) will:

1. Create enum `imputacion_pago_colegio`
2. Add `pagos_colegio.imputacion` (backfill existing → `honorarios_varios`)
3. Add `escribano.monotributista` (set Costanza → `true`)

**Expected**: `Running upgrade ... -> 011`

---

## TDD Workflow (mandatory)

```bash
# 1. Plazo colegio pure logic — write tests FIRST
cd backend && pytest tests/unit/test_plazo_colegio.py -v

# 2. Monotributo IVA in totales
pytest tests/unit/test_calcular_totales_factura.py -v -k monotribut

# 3. Pago colegio imputacion validation
pytest tests/unit/test_pago_colegio_service.py -v

# 4. Escribano PATCH + recalc open escrituras
pytest tests/integration/test_escribanos_api.py -v

# 5. Escrituras list/detail plazo_colegio fields
pytest tests/integration/test_escrituras_api.py -v -k plazo

# 6. Full backend suite
pytest tests/ -v

# 7. Frontend (optional Vitest)
cd frontend && npm test -- --run escrituraList PlazoColegioBadge
```

---

## Demo Seed Regeneration

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

Expect `DEMO_SEED_VERSION=5`:

- Costanza `monotributista=true`, IVA cero en sus escrituras
- Escrituras con fechas escalonadas para bandas verde/amarillo/rojo
- Pagos colegio demo con imputaciones mixtas

---

## Manual Validation Checklist

Ejecutar `./scripts/validate_quickstart_008.sh` contra stack local, luego validar UI en navegador si se desea.
Resultados documentados en `checklists/manual-validation.md`.

### Listado Escrituras

1. Columna **Plazo Colegio** muestra días + color (verde/amarillo/rojo) o estados Pagado / No aplica / Vencido.
2. Click header **Vencimiento** ordena por fecha límite (asc = más urgentes primero).
3. Escrituras Pagado / No aplica al final del sort por vencimiento.

### Detalle Escritura

4. Encabezado muestra mismo badge y fecha de vencimiento que el listado.
5. Registrar pago Colegio **sin** imputación → error de validación.
6. Pago imputado **Honorarios varios** → countdown sigue.
7. Pago imputado **Total impuestos** cubriendo monto → estado **Pagado**.

### Configuración Escribanos

8. Toggle **Monotributista** en Costanza (ya true en seed).
9. Desmarcar monotributista → todas escrituras abiertas de Costanza recalculan IVA > 0.
10. Volver a marcar → IVA = 0, Total + IVA = Total.

### Canonical monotributo (create escritura con Costanza)

| Input | Value |
|---|---|
| USD | 105_000 |
| MEP | 1_450.34 |
| Nación | 1_425.00 |

| Output | Monotributo |
|---|---|
| `iva` | 0.00 |
| `total_sin_iva` | 9_674_809.01 |
| `total_factura` | 9_674_809.01 |

---

## SSE Events

- `pago_colegio.created` — refresca plazo en list/detail
- `escribano.updated` (new) — refresca escrituras tras cambio monotributista
