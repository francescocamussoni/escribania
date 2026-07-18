#!/usr/bin/env bash
#
# spec-kitti-test-agent.sh
# Agente de Pruebas de Spec-Kitti
#
# Responsabilidades:
# - Aislar y ejecutar pruebas legacy relevantes a la Work Unit
# - Generar testing_report.md estructurado con detalles de fallos
# - Generar testing_report.json para parsing automático
# - Analizar errores y proporcionar contexto accionable
#
# Uso:
#   ./spec-kitti-test-agent.sh --wu-data "$WU_JSON" --output-dir ./iteration-01 --report-file ./testing_report.md
#

set -e
set -o pipefail

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración de tests
TEST_PARALLEL="${ITTI_TEST_PARALLEL:-0}"
TEST_TIMEOUT="${ITTI_TEST_TIMEOUT:-300}"

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

log_info() {
    echo -e "${CYAN}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✅${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $*"
}

log_error() {
    echo -e "${RED}❌${NC} $*" >&2
}

die() {
    log_error "$*"
    exit 1
}

# ============================================================================
# EJECUCIÓN DE PRUEBAS
# ============================================================================

detect_test_framework() {
    # Detectar framework de testing basándose en archivos del proyecto
    if command -v pytest &> /dev/null && [ -f "$REPO_ROOT/pytest.ini" ] || [ -f "$REPO_ROOT/pyproject.toml" ]; then
        echo "pytest"
    elif command -v python -m unittest &> /dev/null; then
        echo "unittest"
    elif command -v npm &> /dev/null && [ -f "$REPO_ROOT/package.json" ]; then
        echo "jest"
    elif command -v go &> /dev/null && [ -f "$REPO_ROOT/go.mod" ]; then
        echo "gotest"
    else
        echo "unknown"
    fi
}

run_pytest_tests() {
    local test_file="$1"
    local output_file="$2"
    
    local pytest_args=(
        "$test_file"
        "--tb=short"           # Traceback corto
        "--no-header"          # Sin header
        "-v"                   # Verbose
        "--color=yes"          # Con colores
        "--junit-xml=$output_file.xml"  # JUnit XML para parsing
    )
    
    if [ "$TEST_PARALLEL" -eq 1 ]; then
        pytest_args+=("-n" "auto")  # Requiere pytest-xdist
    fi
    
    if timeout "$TEST_TIMEOUT" pytest "${pytest_args[@]}" > "$output_file" 2>&1; then
        return 0
    else
        return 1
    fi
}

run_unittest_tests() {
    local test_file="$1"
    local output_file="$2"
    
    # Convertir path a módulo Python
    local module_path
    module_path=$(echo "$test_file" | sed 's/\//./g' | sed 's/\.py$//')
    
    if timeout "$TEST_TIMEOUT" python -m unittest "$module_path" -v > "$output_file" 2>&1; then
        return 0
    else
        return 1
    fi
}

run_jest_tests() {
    local test_file="$1"
    local output_file="$2"
    
    if timeout "$TEST_TIMEOUT" npm test -- "$test_file" --verbose > "$output_file" 2>&1; then
        return 0
    else
        return 1
    fi
}

run_single_test() {
    local test_file="$1"
    local output_file="$2"
    local framework="$3"
    
    case "$framework" in
        pytest)
            run_pytest_tests "$test_file" "$output_file"
            ;;
        unittest)
            run_unittest_tests "$test_file" "$output_file"
            ;;
        jest)
            run_jest_tests "$test_file" "$output_file"
            ;;
        *)
            log_error "Framework de testing no soportado: $framework"
            return 1
            ;;
    esac
}

# ============================================================================
# ANÁLISIS DE ERRORES
# ============================================================================

analyze_test_failure() {
    local test_log="$1"
    
    # Intentar usar analizador Python si existe
    local analyzer_script="$SCRIPT_DIR/../python/analyze_test_failure.py"
    
    if [ -f "$analyzer_script" ] && command -v python &> /dev/null; then
        python "$analyzer_script" "$test_log" 2>/dev/null || echo "Análisis automático no disponible"
    else
        # Análisis básico con grep
        local error_type
        error_type=$(grep -oE "(AssertionError|AttributeError|TypeError|ValueError|KeyError|ImportError)" "$test_log" | head -1 || echo "Unknown")
        
        echo "- **Tipo de Error**: $error_type"
        echo "- **Análisis**: Revisa el log completo arriba para detalles"
    fi
}

extract_failed_assertion() {
    local test_log="$1"
    
    # Extraer la línea de assertion que falló
    grep -A 2 "AssertionError" "$test_log" | head -5 || echo "No assertion found"
}

# ============================================================================
# GENERACIÓN DE REPORTES
# ============================================================================

generate_testing_report_header() {
    local wu_id="$1"
    local timestamp="$2"
    
    cat <<EOF
# Testing Report - $timestamp

## Work Unit: $wu_id

---

EOF
}

generate_testing_report_summary() {
    local total_tests="$1"
    local passed_tests="$2"
    local failed_tests="$3"
    local status="$4"
    
    local status_icon
    if [ "$status" = "PASS" ]; then
        status_icon="✅ PASS"
    else
        status_icon="❌ FAIL"
    fi
    
    cat <<EOF
## Resumen

- **Tests ejecutados**: $total_tests
- **Tests pasados**: $passed_tests
- **Tests fallados**: $failed_tests
- **Status**: $status_icon

---

EOF
}

generate_failed_test_section() {
    local test_name="$1"
    local test_log_file="$2"
    
    cat <<EOF
### $(basename "$test_name")

\`\`\`
$(cat "$test_log_file")
\`\`\`

**Análisis del Error**:

$(analyze_test_failure "$test_log_file")

**Aserción Fallida**:

\`\`\`
$(extract_failed_assertion "$test_log_file")
\`\`\`

---

EOF
}

generate_passed_tests_section() {
    local passed_tests_array=("$@")
    
    if [ ${#passed_tests_array[@]} -eq 0 ]; then
        return
    fi
    
    cat <<EOF
## Tests Pasados

EOF
    
    for test in "${passed_tests_array[@]}"; do
        echo "- ✅ $(basename "$test")"
    done
    
    echo ""
    echo "---"
    echo ""
}

generate_json_report() {
    local wu_id="$1"
    local total_tests="$2"
    local passed_tests="$3"
    local failed_tests="$4"
    local status="$5"
    local failed_tests_json="$6"
    local passed_tests_json="$7"
    local output_file="$8"
    
    local timestamp
    timestamp=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")
    
    cat > "$output_file" <<EOF
{
  "work_unit_id": "$wu_id",
  "timestamp": "$timestamp",
  "status": "$status",
  "tests_total": $total_tests,
  "tests_passed": $passed_tests,
  "tests_failed": $failed_tests,
  "failed_tests": $failed_tests_json,
  "passed_tests": $passed_tests_json
}
EOF
}

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

execute_test_suite() {
    local wu_data="$1"
    local output_dir="$2"
    local report_file="$3"
    
    log_info "Ejecutando suite de pruebas legacy..."
    
    # Extraer información de la Work Unit
    local wu_id
    wu_id=$(echo "$wu_data" | jq -r '.id')
    
    local legacy_tests
    mapfile -t legacy_tests < <(echo "$wu_data" | jq -r '.legacy_tests[]')
    
    if [ ${#legacy_tests[@]} -eq 0 ]; then
        log_warning "No hay tests legacy especificados para esta Work Unit"
        
        # Crear reporte vacío con status PASS (no hay tests que fallar)
        local timestamp
        timestamp=$(date)
        
        cat > "$report_file" <<EOF
# Testing Report - $timestamp

## Work Unit: $wu_id

⚠️  **Advertencia**: No hay tests legacy especificados para esta Work Unit.

**Status**: ✅ PASS (vacuamente verdadero)

**Recomendación**: Considera agregar tests de paridad para validar el comportamiento.
EOF
        
        generate_json_report "$wu_id" 0 0 0 "PASS" "[]" "[]" "${report_file%.md}.json"
        return 0
    fi
    
    # Detectar framework de testing
    local test_framework
    test_framework=$(detect_test_framework)
    
    log_info "Framework detectado: $test_framework"
    
    # Crear directorio de resultados
    local test_results_dir="$output_dir/test-results"
    mkdir -p "$test_results_dir"
    
    # Ejecutar cada test
    local passed_tests=()
    local failed_tests=()
    local total_tests=${#legacy_tests[@]}
    
    local counter=1
    for test_file in "${legacy_tests[@]}"; do
        local test_name
        test_name=$(basename "$test_file")
        
        log_info "[$counter/$total_tests] Ejecutando: $test_name"
        
        local test_log="$test_results_dir/${test_name}.log"
        
        if run_single_test "$REPO_ROOT/$test_file" "$test_log" "$test_framework"; then
            passed_tests+=("$test_file")
            log_success "$test_name - PASS"
        else
            failed_tests+=("$test_file")
            log_error "$test_name - FAIL"
        fi
        
        counter=$((counter + 1))
    done
    
    # Generar reporte
    log_info "Generando reporte de pruebas..."
    
    local timestamp
    timestamp=$(date)
    
    local status
    if [ ${#failed_tests[@]} -eq 0 ]; then
        status="PASS"
    else
        status="FAIL"
    fi
    
    # Generar reporte Markdown
    {
        generate_testing_report_header "$wu_id" "$timestamp"
        generate_testing_report_summary "$total_tests" "${#passed_tests[@]}" "${#failed_tests[@]}" "$status"
        
        if [ ${#failed_tests[@]} -gt 0 ]; then
            echo "## Tests Fallados"
            echo ""
            for test_file in "${failed_tests[@]}"; do
                local test_name
                test_name=$(basename "$test_file")
                local test_log="$test_results_dir/${test_name}.log"
                generate_failed_test_section "$test_name" "$test_log"
            done
        fi
        
        if [ ${#passed_tests[@]} -gt 0 ]; then
            generate_passed_tests_section "${passed_tests[@]}"
        fi
        
        cat <<EOF
## Siguiente Paso

EOF
        
        if [ "$status" = "FAIL" ]; then
            cat <<EOF
Los tests fallaron. El Agente Executor recibirá este reporte automáticamente
y generará correcciones en la próxima iteración.

**No se requiere intervención manual** - el sistema se auto-corregirá.
EOF
        else
            cat <<EOF
¡Todos los tests pasaron! 🎉

El sistema procederá a crear un Pull Request con el código validado.
EOF
        fi
        
    } > "$report_file"
    
    log_success "Reporte Markdown generado: $report_file"
    
    # Generar reporte JSON
    local failed_tests_json
    failed_tests_json=$(printf '%s\n' "${failed_tests[@]}" | jq -R . | jq -s .)
    
    local passed_tests_json
    passed_tests_json=$(printf '%s\n' "${passed_tests[@]}" | jq -R . | jq -s .)
    
    local json_report="${report_file%.md}.json"
    generate_json_report "$wu_id" "$total_tests" "${#passed_tests[@]}" "${#failed_tests[@]}" "$status" "$failed_tests_json" "$passed_tests_json" "$json_report"
    
    log_success "Reporte JSON generado: $json_report"
    
    # Retornar código apropiado
    if [ "$status" = "PASS" ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

main() {
    local wu_data=""
    local output_dir=""
    local report_file=""
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --wu-data)
                wu_data="$2"
                shift 2
                ;;
            --output-dir)
                output_dir="$2"
                shift 2
                ;;
            --report-file)
                report_file="$2"
                shift 2
                ;;
            *)
                die "Argumento desconocido: $1"
                ;;
        esac
    done
    
    # Validar argumentos
    if [ -z "$wu_data" ]; then
        die "Falta argumento: --wu-data"
    fi
    
    if [ -z "$output_dir" ]; then
        die "Falta argumento: --output-dir"
    fi
    
    if [ -z "$report_file" ]; then
        die "Falta argumento: --report-file"
    fi
    
    # Crear directorios
    mkdir -p "$output_dir"
    mkdir -p "$(dirname "$report_file")"
    
    # Ejecutar suite de tests
    execute_test_suite "$wu_data" "$output_dir" "$report_file"
}

main "$@"

