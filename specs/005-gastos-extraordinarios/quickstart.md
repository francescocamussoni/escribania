# Quickstart: Gastos Extraordinarios (005)

**Branch**: `005-gastos-extraordinarios`  
**Prerequisites**: Backend con migración `008` aplicada; frontend con ruta `/gastos-extraordinarios`.

---

## 1. Migración y servidor

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/pytest tests/unit/test_gasto_extraordinario_reparto.py tests/integration/test_gastos_extraordinarios_api.py -v
```

Con Docker:

```bash
make db-down && docker compose up --build
# Verificar en logs: migración 008 aplicada
```

---

## 2. Flujo manual — Alta y Libro de Salida

1. Login como secretaria.
2. Navbar → **Gastos Extraordinarios** (2.ª posición, después de Escrituras).
3. Seleccionar mes/año (ej. julio 2026).
4. Registrar gasto: concepto `Celulares`, monto `150000`, fecha `2026-07-15`.
5. Verificar listado con total `$150.000,00`.
6. Ir a **Libro de Salida** → mismo mes → línea con badge **Extraordinario**, sin escritura.

---

## 3. Flujo manual — Pago de Salarios

1. Con 3 escribanos activos y `$300.000` en gastos del mes:
2. **Pago de Salarios** → julio 2026.
3. Cada escribano muestra deducción `$100.000,00` y `monto_neto = monto_total - 100000`.
4. Suma de deducciones = total gastos del mes (SC-003).

---

## 4. Edición y eliminación

1. En Gastos Extraordinarios, editar monto de un gasto.
2. Libro de Salida y Pago de Salarios reflejan el cambio (SSE o refresh).
3. Eliminar gasto → desaparece del listado y del libro.

---

## 5. Casos borde

| Caso | Resultado esperado |
|------|-------------------|
| Sin escribanos activos | Gasto se registra; salarios muestra `advertencia_reparto` |
| Monto $100 ÷ 3 escribanos | Suma cuotas = $100 (centavos al último alfabético) |
| Fecha en otro mes que selector al registrar | Gasto aparece en mes de la **fecha**, no del selector |
| Liquidación | Sin impacto |

---

## 6. Tests completos

```bash
cd backend && .venv/bin/pytest tests/ -q
cd frontend && npm test && npm run build
```
