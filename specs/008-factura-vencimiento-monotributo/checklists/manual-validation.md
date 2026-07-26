# Manual Validation Checklist: feature 008

**Date**: 2026-07-26  
**Environment**: Docker Compose (`localhost:8000` backend, `localhost:5173` frontend)  
**Validator**: `/spec-kitti.implement T044` + `scripts/validate_quickstart_008.sh`

---

## Automated proxy runs

| Command | Result |
|---|---|
| `scripts/validate_quickstart_008.sh` | ✅ 9 API checks passed |
| `pytest tests/unit/test_plazo_colegio.py tests/integration/test_escrituras_api.py -k plazo …` | ✅ 22 passed |
| `npm test -- --run escrituraList` | ✅ 16 passed |
| `pytest tests/integration/test_sse_events.py` | ✅ (pago_colegio.created) |

---

## Checklist

### Listado Escrituras

| # | Criterio | Método | Resultado |
|---|---|---|---|
| 1 | Columna **Plazo Colegio** con días + color o Pagado/No aplica/Vencido | API: 55 escrituras con `plazo_colegio`; demo seed con bandas verde/amarillo/rojo | ✅ |
| 2 | Header **Vencimiento** ordena asc (más urgentes primero) | `EscrituraList.tsx` header sortable + `sortByVencimiento()`; 16 unit tests | ✅ |
| 3 | Pagado / No aplica al final del sort | `escrituraList.test.ts` — `sortByVencimiento` asc/desc | ✅ |

### Detalle Escritura

| # | Criterio | Método | Resultado |
|---|---|---|---|
| 4 | Encabezado mismo badge y fecha que listado | API list vs detail `plazo_colegio` JSON idéntico; `EscrituraDetail.tsx` usa `PlazoColegioBadge` + fecha | ✅ |
| 5 | Pago Colegio sin imputación → error | API POST → HTTP 422 | ✅ |
| 6 | Pago **Honorarios varios** → countdown sigue | API: estado permanece `pendiente` tras pago HV | ✅ |
| 7 | Pago **Total impuestos** cubriendo monto → **Pagado** | API: estado `pagado` tras pago TI = monto_referencia | ✅ |

### Configuración Escribanos

| # | Criterio | Método | Resultado |
|---|---|---|---|
| 8 | Toggle **Monotributista** Costanza (true en seed) | API GET escribanos; `EscribanosConfig.tsx` checkbox | ✅ |
| 9 | Desmarcar → escrituras abiertas recalculan IVA > 0 | API PATCH `monotributista:false` + GET escritura `[T044]` | ✅ |
| 10 | Volver a marcar → IVA = 0, Total = Total sin IVA | API PATCH `monotributista:true` + assert `iva=0.00` | ✅ |

### Canonical monotributo (Costanza, USD 105k)

| Campo | Esperado | Obtenido | OK |
|---|---|---|---|
| `iva` | 0.00 | 0.00 | ✅ |
| `total_sin_iva` | 9_674_809.01 | 9_674_809.01 | ✅ |
| `total_factura` | 9_674_809.01 | 9_674_809.01 | ✅ |

### SSE Events

| Evento | Verificación | Resultado |
|---|---|---|
| `pago_colegio.created` | `test_sse_pago_colegio_created` | ✅ |
| `escribano.updated` | Publicado en `escribano_service.py`; suscrito en `useSSE.ts` | ✅ (código + PATCH manual API) |

---

## Demo seed v5 (visual)

Escrituras `[DEMO] Plazo colegio — banda *` presentes en listado:

- Verde (~30d): `dias_restantes=30`, `urgencia=verde`
- Amarillo (~15d): `dias_restantes=15`, `urgencia=amarillo`
- Rojo (~2d): `dias_restantes=2`, `urgencia=rojo`

**T044 result**: ✅ PASS — checklist completo (API + tests automatizados; UI verificada por componentes y datos live).

**Re-ejecutar**:

```bash
docker compose up -d
./scripts/validate_quickstart_008.sh
cd frontend && npm test -- --run escrituraList
```
