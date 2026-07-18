#!/usr/bin/env bash
# Smoke test end-to-end del backend (sin frontend).
#
# Uso:
#   ./scripts/smoke_test.sh
#   SMOKE_PASSWORD=admin123 ./scripts/smoke_test.sh
#   SMOKE_BASE_URL=http://localhost:8000 make smoke
#
# Variables:
#   SMOKE_BASE_URL   default: http://localhost:8000
#   SMOKE_USER       default: admin
#   SMOKE_PASSWORD   default: tu-password  (ver `make user` en backend/Makefile)
#   SMOKE_SKIP_SSE   setear a 1 para omitir prueba SSE

set -euo pipefail

BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
API="${BASE_URL}/api/v1"
USER="${SMOKE_USER:-admin}"
PASS="${SMOKE_PASSWORD:-tu-password}"

COOKIE_JAR="$(mktemp)"
BODY_FILE="$(mktemp)"
SSE_FILE="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$BODY_FILE" "$SSE_FILE"' EXIT

PASS_COUNT=0
FAIL_COUNT=0

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red() { printf '\033[31m%s\033[0m\n' "$*" >&2; }

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  green "  ✓ $*"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  red "  ✗ $*"
  exit 1
}

json_get() {
  local expr="$1"
  python3 -c "import json,sys; data=json.load(sys.stdin); print($expr)" <"$BODY_FILE"
}

request() {
  local method="$1"
  local url="$2"
  local expected="${3:-200}"

  if (( $# >= 3 )); then
    shift 3
  else
    shift 2
  fi

  local code
  code="$(
    curl -sS -o "$BODY_FILE" -w "%{http_code}" -X "$method" \
      -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
      -H "Content-Type: application/json" \
      "$@" \
      "$url"
  )"

  if [[ "$code" != "$expected" ]]; then
    echo "Response body:" >&2
    cat "$BODY_FILE" >&2
    fail "$method $url → esperado HTTP $expected, obtuvo $code"
  fi
}

section() {
  echo ""
  echo "── $* ──"
}

section "Configuración"
echo "  Base URL : $BASE_URL"
echo "  Usuario  : $USER"

section "1. Health"
if ! curl -sS -o /dev/null --connect-timeout 2 "${API}/health" 2>/dev/null; then
  red "No hay API en ${BASE_URL}"
  red "Levantá el servidor en otra terminal: make run"
  exit 1
fi
request GET "${API}/health"
[[ "$(json_get "data['status']")" == "ok" ]] || fail "health status"
pass "GET /health"

section "2. Auth"
request POST "${API}/auth/login" 401 -d '{"username":"'"$USER"'","password":"wrong-password"}'
pass "login con contraseña incorrecta → 401"

request POST "${API}/auth/login" 200 -d '{"username":"'"$USER"'","password":"'"$PASS"'"}'
pass "login exitoso"

request GET "${API}/auth/me"
[[ -n "$(json_get "data['username']")" ]] || fail "/auth/me sin username"
pass "GET /auth/me → $(json_get "data['username']")"

section "3. Configuración"
request GET "${API}/configuracion"
CONFIG_VERSION="$(json_get "data['version']")"
CONFIG_ID="$(json_get "data['id']")"
pass "GET /configuracion → versión $CONFIG_VERSION"

request GET "${API}/configuracion/history"
pass "GET /configuracion/history"

section "4. Escritura (fixture canónico)"
request POST "${API}/escrituras" 201 -d '{
  "nombre": "Smoke Test Escritura",
  "escribano": "costanza",
  "usd_value": "105000.00",
  "dolar_mep": "1450.34",
  "dolar_nacion": "1425.00"
}'
ESCRITURA_ID="$(json_get "data['id']")"
TOTAL_FACTURA="$(json_get "data['factura']['total_factura']")"
[[ "$TOTAL_FACTURA" == "11731403.68" ]] || fail "total_factura esperado 11731403.68, obtuvo $TOTAL_FACTURA"
pass "POST /escrituras → id=$ESCRITURA_ID, total_factura=$TOTAL_FACTURA"

request GET "${API}/escrituras?escribano=costanza"
pass "GET /escrituras?escribano=costanza"

request GET "${API}/escrituras/${ESCRITURA_ID}"
pass "GET /escrituras/{id}"

section "5. Gasto adicional"
request POST "${API}/escrituras/${ESCRITURA_ID}/gastos" 201 -d '{
  "concepto": "Timbre smoke test",
  "monto": "50000.00",
  "direccion": "salida",
  "fecha": "2026-07-18"
}'
pass "POST /escrituras/{id}/gastos"

section "6. Liquidación y salarios (mes actual)"
YEAR="$(date +%Y)"
MONTH="$(date +%-m 2>/dev/null || date +%m | sed 's/^0//')"
CANONICAL_SUBTOTAL="4111713.90"

request GET "${API}/liquidacion?anio=${YEAR}&mes=${MONTH}"
python3 - "$ESCRITURA_ID" "$CANONICAL_SUBTOTAL" "$BODY_FILE" <<'PY' || fail "liquidación no incluye la escritura smoke con subtotal canónico"
import json
import sys

escritura_id, expected_subtotal, body_file = sys.argv[1:4]
with open(body_file, encoding="utf-8") as handle:
    data = json.load(handle)

costanza = next((e for e in data["por_escribano"] if e["escribano"] == "costanza"), None)
if costanza is None:
    raise SystemExit("escribano costanza no encontrado")

item = next((i for i in costanza["escrituras"] if i["escritura_id"] == escritura_id), None)
if item is None:
    raise SystemExit(f"escritura {escritura_id} no está en liquidación de costanza")

if item["subtotal"] != expected_subtotal:
    raise SystemExit(
        f"subtotal esperado {expected_subtotal}, obtuvo {item['subtotal']}"
    )
PY
LIQ_TOTAL="$(json_get "data['total_costanza']")"
pass "GET /liquidacion?anio=${YEAR}&mes=${MONTH} → costanza incluye smoke ($CANONICAL_SUBTOTAL), total=$LIQ_TOTAL"

request GET "${API}/salarios?anio=${YEAR}&mes=${MONTH}"
python3 - "$ESCRITURA_ID" "$CANONICAL_SUBTOTAL" "$BODY_FILE" <<'PY' || fail "salarios no incluye la escritura smoke con subtotal canónico"
import json
import sys

escritura_id, expected_subtotal, body_file = sys.argv[1:4]
with open(body_file, encoding="utf-8") as handle:
    data = json.load(handle)

costanza = next((e for e in data["escribanos"] if e["nombre"] == "Costanza"), None)
if costanza is None:
    raise SystemExit("pago Costanza no encontrado")

item = next((i for i in costanza["escrituras"] if i["escritura_id"] == escritura_id), None)
if item is None:
    raise SystemExit(f"escritura {escritura_id} no está en salarios de Costanza")

if item["subtotal"] != expected_subtotal:
    raise SystemExit(
        f"subtotal esperado {expected_subtotal}, obtuvo {item['subtotal']}"
    )
PY
pass "GET /salarios?anio=${YEAR}&mes=${MONTH}"

section "7. Cierre y escritura inmutable"
request POST "${API}/escrituras/${ESCRITURA_ID}/close" 200
[[ "$(json_get "data['estado']")" == "cerrada" ]] || fail "estado tras close"
pass "POST /escrituras/{id}/close → cerrada"

request PATCH "${API}/escrituras/${ESCRITURA_ID}" 409 -d '{"nombre":"No debe actualizarse"}'
pass "PATCH escritura cerrada → 409"

section "8. Protección sin sesión"
rm -f "$COOKIE_JAR"
touch "$COOKIE_JAR"
request GET "${API}/escrituras" 401
pass "GET /escrituras sin cookie → 401"

# Restaurar sesión para logout
request POST "${API}/auth/login" 200 -d '{"username":"'"$USER"'","password":"'"$PASS"'"}'

if [[ "${SMOKE_SKIP_SSE:-0}" != "1" ]]; then
  section "9. SSE (evento escritura.created)"
  ESCRITURA_SSE_PAYLOAD='{
    "nombre": "Smoke SSE Escritura",
    "escribano": "gabriel",
    "usd_value": "105000.00",
    "dolar_mep": "1450.34",
    "dolar_nacion": "1425.00"
  }'

  curl -sS -N -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    -H "Accept: text/event-stream" \
    "${API}/events" >"$SSE_FILE" 2>/dev/null &
  SSE_PID=$!

  sleep 1
  request POST "${API}/escrituras" 201 -d "$ESCRITURA_SSE_PAYLOAD"
  sleep 2
  kill "$SSE_PID" 2>/dev/null || true
  wait "$SSE_PID" 2>/dev/null || true

  if grep -q "escritura.created" "$SSE_FILE"; then
    pass "SSE recibió escritura.created"
  else
    echo "  (stream recibido:)" >&2
    head -20 "$SSE_FILE" >&2 || true
    fail "SSE no recibió escritura.created (usar SMOKE_SKIP_SSE=1 para omitir)"
  fi
else
  section "9. SSE omitido (SMOKE_SKIP_SSE=1)"
fi

section "10. Logout"
request POST "${API}/auth/logout" 204
pass "POST /auth/logout → 204"

request GET "${API}/auth/me" 401
pass "GET /auth/me tras logout → 401"

echo ""
green "════════════════════════════════════════"
green "  Smoke test OK ($PASS_COUNT checks)"
green "════════════════════════════════════════"
