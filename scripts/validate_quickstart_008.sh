#!/usr/bin/env bash
# Validates quickstart manual checklist (feature 008) against a running stack.
set -euo pipefail

BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
API="${BASE_URL}/api/v1"
USER="${SMOKE_USER:-admin}"
PASS="${SMOKE_PASSWORD:-tu-password}"

COOKIE_JAR="$(mktemp)"
BODY_FILE="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$BODY_FILE"' EXIT

PASS_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '  ✓ %s\n' "$*"; }
fail() { printf '  ✗ %s\n' "$*" >&2; exit 1; }

json_field() {
  python3 -c "import json,sys; data=json.load(sys.stdin); print($1)" <"$BODY_FILE"
}

request() {
  local method="$1" url="$2" expected=200
  shift 2
  if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
    expected="$1"
    shift
  fi
  local code
  code="$(curl -sS -o "$BODY_FILE" -w "%{http_code}" -X "$method" \
    -b "$COOKIE_JAR" -c "$COOKIE_JAR" -H "Content-Type: application/json" "$@" "$url")"
  [[ "$code" == "$expected" ]] || { cat "$BODY_FILE" >&2; fail "$method $url → $code (expected $expected)"; }
}

echo "── Login ──"
request POST "${API}/auth/login" 200 -d "{\"username\":\"${USER}\",\"password\":\"${PASS}\"}"

echo "── Item 1: plazo_colegio en listado ──"
request GET "${API}/escrituras"
python3 - "$BODY_FILE" <<'PY'
import json, sys
items = json.load(open(sys.argv[1]))
assert items, "listado vacío"
assert all("plazo_colegio" in i for i in items), "falta plazo_colegio"
estados = {i["plazo_colegio"]["estado"] for i in items}
assert estados <= {"no_aplica", "pendiente", "vencido", "pagado"}, estados
demo = [i for i in items if "Plazo colegio" in i.get("nombre", "")]
assert demo, "faltan escrituras demo plazo showcase (seed v5)"
PY
pass "Listado con plazo_colegio, estados válidos y demo showcase"

echo "── Item 4: detalle plazo_colegio = listado ──"
ESC_ID="$(python3 -c "import json; print(json.load(open('$BODY_FILE'))[0]['id'])")"
LIST_PLAZO="$(python3 -c "import json; print(json.dumps(json.load(open('$BODY_FILE'))[0]['plazo_colegio']))")"
request GET "${API}/escrituras/${ESC_ID}"
DETAIL_PLAZO="$(python3 -c "import json; print(json.dumps(json.load(open('$BODY_FILE'))['plazo_colegio']))")"
[[ "$LIST_PLAZO" == "$DETAIL_PLAZO" ]] || fail "plazo_colegio difiere list vs detail"
pass "Detalle plazo_colegio idéntico al listado"

echo "── Item 5: pago sin imputación → 422 ──"
request POST "${API}/escrituras/${ESC_ID}/pagos-colegio" 422 \
  -d '{"monto":"100.00","fecha":"2026-07-26","concepto":"sin imputacion"}'
pass "POST sin imputación devuelve 422"

echo "── Items 6–7: imputaciones ──"
request GET "${API}/escrituras"
DEMO_ID="$(python3 -c "
import json
for i in json.load(open('$BODY_FILE')):
    if 'banda verde' in i.get('nombre', ''):
        print(i['id']); break
")"
[[ -n "$DEMO_ID" ]] || fail "no se encontró escritura demo plazo verde"

request GET "${API}/escrituras/${DEMO_ID}"
REF="$(python3 -c "import json; print(json.load(open('$BODY_FILE'))['plazo_colegio']['monto_referencia'])")"

request POST "${API}/escrituras/${DEMO_ID}/pagos-colegio" 201 \
  -d '{"monto":"1000.00","fecha":"2026-07-26","concepto":"honorarios test","imputacion":"honorarios_varios"}'
request GET "${API}/escrituras/${DEMO_ID}"
ESTADO_HV="$(python3 -c "import json; print(json.load(open('$BODY_FILE'))['plazo_colegio']['estado'])")"
[[ "$ESTADO_HV" != "pagado" ]] || fail "honorarios_varios no debería cerrar plazo"
pass "Pago honorarios_varios mantiene countdown (estado=$ESTADO_HV)"

request POST "${API}/escrituras/${DEMO_ID}/pagos-colegio" 201 \
  -d "{\"monto\":\"${REF}\",\"fecha\":\"2026-07-26\",\"concepto\":\"total impuestos\",\"imputacion\":\"total_impuestos\"}"
request GET "${API}/escrituras/${DEMO_ID}"
ESTADO_TI="$(python3 -c "import json; print(json.load(open('$BODY_FILE'))['plazo_colegio']['estado'])")"
[[ "$ESTADO_TI" == "pagado" ]] || fail "esperado pagado, got $ESTADO_TI"
pass "Pago total_impuestos completo → estado pagado"

echo "── Items 8–10 + canonical: monotributista Costanza ──"
request GET "${API}/configuracion/escribanos"
COSTANZA_ID="$(python3 -c "import json; print(next(r['id'] for r in json.load(open('$BODY_FILE')) if r['nombre']=='Costanza'))")"
MONO="$(python3 -c "import json; print(next(r['monotributista'] for r in json.load(open('$BODY_FILE')) if r['nombre']=='Costanza'))")"
[[ "$MONO" == "True" ]] && pass "Costanza monotributista=true (item 8)"

request POST "${API}/escrituras" 201 -d "{
  \"nombre\": \"[T044] Canonical monotributo\",
  \"escribano_id\": \"${COSTANZA_ID}\",
  \"usd_value\": \"105000.00\",
  \"dolar_mep\": \"1450.34\",
  \"dolar_nacion\": \"1425.00\"
}"
CANON_ID="$(python3 -c "import json; d=json.load(open('$BODY_FILE')); print(d['id'])")"
python3 <<PY
import json
d=json.load(open("$BODY_FILE"))
f=d["factura"]
assert f["iva"]=="0.00", f["iva"]
assert f["total_sin_iva"]=="9674809.01", f["total_sin_iva"]
assert f["total_factura"]=="9674809.01", f["total_factura"]
PY
pass "Canonical monotributo Costanza (iva=0, total=9674809.01)"

request PATCH "${API}/configuracion/escribanos/${COSTANZA_ID}" 200 -d '{"monotributista": false}'
request GET "${API}/escrituras/${CANON_ID}"
python3 -c "import json; iva=json.load(open('$BODY_FILE'))['factura']['iva']; assert iva!='0.00', iva"
pass "Desmarcar monotributista → IVA > 0 (item 9)"

request PATCH "${API}/configuracion/escribanos/${COSTANZA_ID}" 200 -d '{"monotributista": true}'
request GET "${API}/escrituras/${CANON_ID}"
python3 <<PY
import json
f=json.load(open("$BODY_FILE"))["factura"]
assert f["iva"]=="0.00"
assert f["total_factura"]==f["total_sin_iva"]
PY
pass "Re-marcar monotributista → IVA=0 (item 10)"

echo ""
echo "API validation: ${PASS_COUNT} checks passed"
echo "Items 2–3 (sort Vencimiento UI): validados por escrituraList.test.ts (16 tests)"
