#!/usr/bin/env bash
#
# spec-kitti-orchestrator.sh
# Motor de Orquestación Principal de Spec-Kitti
#
# Ejecuta Work Units de forma autónoma con bucle de auto-corrección:
# 1. Agente Executor genera código
# 2. Agente de Pruebas valida contra tests legacy
# 3. Si FAIL, reenvía reporte al Executor
# 4. Repite hasta PASS o MAX_ITERATIONS
# 5. Crea PR automático
#
# Uso:
#   ./spec-kitti-orchestrator.sh WU-001
#   ./spec-kitti-orchestrator.sh WU-001 --max-iterations 10
#   ./spec-kitti-orchestrator.sh --all
#

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración por defecto (sobreescribible con env vars)
MAX_ITERATIONS="${ITTI_MAX_ITERATIONS:-5}"
TIMEOUT_PER_ITERATION="${ITTI_TIMEOUT_PER_ITERATION:-600}"
MAX_DIFF_LINES="${ITTI_MAX_WU_DIFF_LINES:-5000}"
VERBOSE="${ITTI_VERBOSE:-0}"
DRY_RUN="${ITTI_DRY_RUN:-0}"

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC}  $*"
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

log_step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$*${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

log_iteration() {
    local current=$1
    local max=$2
    echo -e "\n${MAGENTA}╔════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║  🔄 ITERACIÓN ${current}/${max}                       ║${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════╝${NC}\n"
}

verbose() {
    if [ "$VERBOSE" -eq 1 ]; then
        echo -e "${CYAN}[VERBOSE]${NC} $*"
    fi
}

die() {
    log_error "$*"
    exit 1
}

# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

check_prerequisites() {
    log_step "Verificando prerequisitos"
    
    local missing=0
    
    # Verificar jq
    if ! command -v jq &> /dev/null; then
        log_error "jq no está instalado. Instala con: brew install jq"
        missing=1
    else
        log_success "jq encontrado"
    fi
    
    # Verificar git
    if ! command -v git &> /dev/null; then
        log_error "git no está instalado"
        missing=1
    else
        log_success "git encontrado"
    fi
    
    # Verificar pytest (si hay tests de Python)
    if ! command -v pytest &> /dev/null; then
        log_warning "pytest no encontrado. Si usas tests Python, instala: pip install pytest"
    else
        log_success "pytest encontrado"
    fi
    
    # Verificar que estamos en un repo git
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        die "No estás en un repositorio git"
    fi
    
    if [ $missing -eq 1 ]; then
        die "Faltan prerequisitos. Instálalos antes de continuar."
    fi
}

validate_work_unit_file() {
    local wu_file="$1"
    
    if [ ! -f "$wu_file" ]; then
        die "Archivo work-units.json no encontrado en: $wu_file\nEjecuta /tasks.shape primero."
    fi
    
    # Validar que sea JSON válido
    if ! jq empty "$wu_file" 2>/dev/null; then
        die "work-units.json no es un JSON válido"
    fi
    
    verbose "work-units.json válido"
}

load_work_unit() {
    local wu_id="$1"
    local wu_file="$2"
    
    verbose "Cargando Work Unit: $wu_id"
    
    local wu_data
    wu_data=$(jq ".work_units[] | select(.id==\"$wu_id\")" "$wu_file")
    
    if [ -z "$wu_data" ] || [ "$wu_data" = "null" ]; then
        die "Work Unit $wu_id no encontrada en work-units.json"
    fi
    
    echo "$wu_data"
}

check_dependencies() {
    local wu_data="$1"
    local wu_status_file="$2"
    
    local deps
    deps=$(echo "$wu_data" | jq -r '.dependencies[]?' 2>/dev/null || echo "")
    
    if [ -z "$deps" ]; then
        verbose "Work Unit no tiene dependencias"
        return 0
    fi
    
    log_info "Verificando dependencias..."
    
    for dep in $deps; do
        local dep_status
        dep_status=$(jq -r ".work_units.\"$dep\".status // \"PENDING\"" "$wu_status_file" 2>/dev/null || echo "PENDING")
        
        if [ "$dep_status" != "COMPLETED" ]; then
            log_error "Dependencia no satisfecha: $dep (status: $dep_status)"
            echo ""
            echo "Ejecuta primero: /implement.unit $dep"
            return 1
        fi
        
        log_success "Dependencia $dep satisfecha"
    done
    
    return 0
}

# ============================================================================
# FUNCIONES DE EJECUCIÓN
# ============================================================================

create_execution_directory() {
    local wu_id="$1"
    local spec_dir="$2"
    
    local wu_dir="$spec_dir/$wu_id"
    mkdir -p "$wu_dir"
    
    echo "$wu_dir"
}

execute_executor_agent() {
    local wu_data="$1"
    local iteration="$2"
    local wu_dir="$3"
    local spec_dir="$4"
    
    log_info "🤖 Agente Executor: Generando código..."
    
    local executor_script="$SCRIPT_DIR/spec-kitti-executor-agent.sh"
    
    if [ ! -f "$executor_script" ]; then
        die "Script del Executor Agent no encontrado: $executor_script"
    fi
    
    local mode="INITIAL_IMPLEMENTATION"
    local extra_args=""
    
    if [ "$iteration" -gt 0 ]; then
        mode="ERROR_CORRECTION"
        extra_args="--testing-report $spec_dir/testing_report.md"
    fi
    
    local iteration_dir="$wu_dir/iteration-$(printf '%02d' $((iteration + 1)))"
    mkdir -p "$iteration_dir"
    
    if [ "$DRY_RUN" -eq 1 ]; then
        log_info "[DRY RUN] Ejecutaría: $executor_script --mode $mode $extra_args"
        return 0
    fi
    
    # Ejecutar con timeout
    if timeout "$TIMEOUT_PER_ITERATION" "$executor_script" \
        --wu-data "$wu_data" \
        --mode "$mode" \
        --iteration "$iteration" \
        --output-dir "$iteration_dir" \
        $extra_args; then
        
        log_success "Código generado exitosamente"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "Executor Agent timeout después de $TIMEOUT_PER_ITERATION segundos"
        else
            log_error "Executor Agent falló con código: $exit_code"
        fi
        return 1
    fi
}

execute_test_agent() {
    local wu_data="$1"
    local wu_dir="$2"
    local spec_dir="$3"
    local iteration="$4"
    
    log_info "🧪 Agente de Pruebas: Ejecutando tests legacy..."
    
    local test_script="$SCRIPT_DIR/spec-kitti-test-agent.sh"
    
    if [ ! -f "$test_script" ]; then
        die "Script del Test Agent no encontrado: $test_script"
    fi
    
    local wu_id
    wu_id=$(echo "$wu_data" | jq -r '.id')
    
    local iteration_dir="$wu_dir/iteration-$(printf '%02d' $((iteration + 1)))"
    
    if [ "$DRY_RUN" -eq 1 ]; then
        log_info "[DRY RUN] Ejecutaría: $test_script --wu-id $wu_id"
        return 0
    fi
    
    # Ejecutar tests
    if "$test_script" \
        --wu-data "$wu_data" \
        --output-dir "$iteration_dir" \
        --report-file "$spec_dir/testing_report.md"; then
        
        log_success "Todos los tests pasaron"
        return 0
    else
        log_warning "Algunos tests fallaron"
        return 1
    fi
}

analyze_results() {
    local spec_dir="$1"
    local testing_report="$spec_dir/testing_report.json"
    
    if [ ! -f "$testing_report" ]; then
        log_error "testing_report.json no encontrado"
        return 1
    fi
    
    local status
    status=$(jq -r '.status' "$testing_report")
    
    local total_tests
    total_tests=$(jq -r '.tests_passed + .tests_failed' "$testing_report")
    
    local passed_tests
    passed_tests=$(jq -r '.tests_passed' "$testing_report")
    
    local failed_tests
    failed_tests=$(jq -r '.tests_failed' "$testing_report")
    
    echo ""
    log_step "📊 Análisis de Resultados"
    echo "  • Tests ejecutados: $total_tests"
    echo "  • Tests pasados: $passed_tests"
    echo "  • Tests fallados: $failed_tests"
    
    if [ "$status" = "PASS" ]; then
        echo -e "  • Status: ${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "  • Status: ${RED}❌ FAIL${NC}"
        echo ""
        log_info "Ver detalles en: $spec_dir/testing_report.md"
        return 1
    fi
}

create_pull_request() {
    local wu_data="$1"
    local wu_dir="$2"
    
    log_step "📝 Creando Pull Request"
    
    local wu_id
    wu_id=$(echo "$wu_data" | jq -r '.id')
    
    local wu_name
    wu_name=$(echo "$wu_data" | jq -r '.name')
    
    local total_tests
    if [ -f "$wu_dir/../testing_report.json" ]; then
        total_tests=$(jq -r '.tests_passed' "$wu_dir/../testing_report.json")
    else
        total_tests="N/A"
    fi
    
    local pr_script="$SCRIPT_DIR/spec-kitti-create-pr.sh"
    
    if [ ! -f "$pr_script" ]; then
        log_warning "Script de PR no encontrado: $pr_script"
        log_info "Crea el commit manualmente con:"
        echo ""
        echo "  git add ."
        echo "  git commit -m \"$wu_id: $wu_name ($total_tests tests legacy passed)\""
        echo "  git push origin \$(git branch --show-current)"
        return 0
    fi
    
    if [ "$DRY_RUN" -eq 1 ]; then
        log_info "[DRY RUN] Crearía PR: $wu_id: $wu_name"
        return 0
    fi
    
    "$pr_script" --wu-data "$wu_data" --wu-dir "$wu_dir"
}

update_work_unit_status() {
    local wu_id="$1"
    local status="$2"
    local wu_status_file="$3"
    local iterations="$4"
    
    verbose "Actualizando status de $wu_id a $status"
    
    local timestamp
    timestamp=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")
    
    # Crear archivo de status si no existe
    if [ ! -f "$wu_status_file" ]; then
        echo '{"work_units":{}}' > "$wu_status_file"
    fi
    
    # Actualizar status
    local temp_file
    temp_file=$(mktemp)
    
    jq ".work_units.\"$wu_id\" = {
        \"status\": \"$status\",
        \"updated_at\": \"$timestamp\",
        \"iterations\": $iterations
    }" "$wu_status_file" > "$temp_file"
    
    mv "$temp_file" "$wu_status_file"
}

# ============================================================================
# BUCLE PRINCIPAL DE EJECUCIÓN
# ============================================================================

execute_work_unit() {
    local wu_id="$1"
    local wu_file="$2"
    local spec_dir="$3"
    
    log_step "🚀 Iniciando Motor de Orquestación Spec-Kitti"
    echo "  Work Unit: $wu_id"
    echo "  Feature: $(basename "$spec_dir")"
    echo "  Max Iterations: $MAX_ITERATIONS"
    echo ""
    
    # Cargar Work Unit
    local wu_data
    wu_data=$(load_work_unit "$wu_id" "$wu_file")
    
    local wu_name
    wu_name=$(echo "$wu_data" | jq -r '.name')
    
    local legacy_tests_count
    legacy_tests_count=$(echo "$wu_data" | jq -r '.legacy_tests | length')
    
    log_info "📁 $wu_name"
    log_info "🎯 Objetivo: $legacy_tests_count tests legacy deben pasar"
    
    # Verificar dependencias
    local wu_status_file="$spec_dir/work-units-status.json"
    if ! check_dependencies "$wu_data" "$wu_status_file"; then
        die "Dependencias no satisfechas"
    fi
    
    # Crear directorio de ejecución
    local wu_dir
    wu_dir=$(create_execution_directory "$wu_id" "$spec_dir")
    
    # Bucle de auto-corrección
    local iteration=0
    local status="FAIL"
    local start_time
    start_time=$(date +%s)
    
    while [ $iteration -lt "$MAX_ITERATIONS" ] && [ "$status" = "FAIL" ]; do
        log_iteration $((iteration + 1)) "$MAX_ITERATIONS"
        
        # FASE 1: Generación de código
        if ! execute_executor_agent "$wu_data" "$iteration" "$wu_dir" "$spec_dir"; then
            log_error "Executor Agent falló en iteración $((iteration + 1))"
            update_work_unit_status "$wu_id" "FAILED" "$wu_status_file" "$((iteration + 1))"
            return 1
        fi
        
        # FASE 2: Validación con pruebas
        if execute_test_agent "$wu_data" "$wu_dir" "$spec_dir" "$iteration"; then
            status="PASS"
        else
            status="FAIL"
        fi
        
        # FASE 3: Análisis de resultados
        if analyze_results "$spec_dir"; then
            status="PASS"
            break
        fi
        
        iteration=$((iteration + 1))
        
        if [ $iteration -lt "$MAX_ITERATIONS" ] && [ "$status" = "FAIL" ]; then
            log_warning "Reintentando con correcciones..."
            sleep 2
        fi
    done
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    log_step "RESULTADO FINAL"
    
    if [ "$status" = "PASS" ]; then
        log_success "¡Work Unit $wu_id completada exitosamente!"
        echo "  • Iteraciones: $((iteration + 1))/$MAX_ITERATIONS"
        echo "  • Tiempo total: $((duration / 60))m $((duration % 60))s"
        echo ""
        
        update_work_unit_status "$wu_id" "COMPLETED" "$wu_status_file" "$((iteration + 1))"
        
        create_pull_request "$wu_data" "$wu_dir"
        return 0
    else
        log_error "Work Unit $wu_id falló después de $MAX_ITERATIONS intentos"
        echo "  • Tiempo total: $((duration / 60))m $((duration % 60))s"
        echo ""
        log_info "📝 Revisa manualmente: $spec_dir/testing_report.md"
        
        update_work_unit_status "$wu_id" "FAILED" "$wu_status_file" "$MAX_ITERATIONS"
        return 1
    fi
}

# ============================================================================
# FUNCIONES DE UTILIDADES (STATUS, ALL, ETC)
# ============================================================================

show_status() {
    local wu_file="$1"
    local wu_status_file="$2"
    
    log_step "📊 Estado de Work Units"
    
    if [ ! -f "$wu_status_file" ]; then
        log_info "No hay Work Units ejecutadas todavía"
        return
    fi
    
    local total_wus
    total_wus=$(jq -r '.work_units | length' "$wu_file")
    
    echo "Total Work Units: $total_wus"
    echo ""
    
    jq -r '.work_units[] | "\(.id) - \(.name)"' "$wu_file" | while IFS= read -r wu_line; do
        local wu_id
        wu_id=$(echo "$wu_line" | cut -d' ' -f1)
        
        local wu_status
        wu_status=$(jq -r ".work_units.\"$wu_id\".status // \"PENDING\"" "$wu_status_file")
        
        local icon
        case "$wu_status" in
            COMPLETED)
                icon="${GREEN}✅${NC}"
                ;;
            IN_PROGRESS)
                icon="${YELLOW}🔄${NC}"
                ;;
            FAILED)
                icon="${RED}❌${NC}"
                ;;
            PENDING)
                icon="${CYAN}⏳${NC}"
                ;;
            *)
                icon="  "
                ;;
        esac
        
        echo -e "$icon $wu_line (${wu_status})"
    done
}

execute_all_work_units() {
    local wu_file="$1"
    local spec_dir="$2"
    
    log_step "🔄 Ejecutando todas las Work Units"
    
    # TODO: Implementar ejecución con respeto a dependencias (topological sort)
    # Por ahora, ejecutar en orden secuencial
    
    local wu_ids
    wu_ids=$(jq -r '.work_units[].id' "$wu_file")
    
    local total_wus
    total_wus=$(echo "$wu_ids" | wc -l | tr -d ' ')
    
    local completed=0
    local failed=0
    
    for wu_id in $wu_ids; do
        echo ""
        log_info "[$((completed + failed + 1))/$total_wus] Procesando $wu_id..."
        
        if execute_work_unit "$wu_id" "$wu_file" "$spec_dir"; then
            completed=$((completed + 1))
        else
            failed=$((failed + 1))
            log_warning "Continuando con siguiente Work Unit..."
        fi
    done
    
    echo ""
    log_step "RESUMEN FINAL"
    log_success "Completadas: $completed/$total_wus"
    if [ $failed -gt 0 ]; then
        log_error "Fallidas: $failed/$total_wus"
    fi
}

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

main() {
    # Parse argumentos
    local wu_id=""
    local show_status_only=0
    local execute_all=0
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-iterations)
                MAX_ITERATIONS="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT_PER_ITERATION="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=1
                shift
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --status)
                show_status_only=1
                shift
                ;;
            --all)
                execute_all=1
                shift
                ;;
            WU-*)
                wu_id="$1"
                shift
                ;;
            *)
                die "Argumento desconocido: $1"
                ;;
        esac
    done
    
    # Validar prerequisitos
    check_prerequisites
    
    # Detectar branch y spec directory
    local current_branch
    current_branch=$(git branch --show-current)
    
    local feature_dir
    feature_dir=$(echo "$current_branch" | grep -oE '[0-9]+-[^/]+' | head -1)
    
    if [ -z "$feature_dir" ]; then
        die "No estás en una rama de feature (formato esperado: NNN-nombre-feature)"
    fi
    
    local spec_dir="$REPO_ROOT/specs/$feature_dir"
    local wu_file="$spec_dir/work-units.json"
    local wu_status_file="$spec_dir/work-units-status.json"
    
    # Validar work-units.json
    validate_work_unit_file "$wu_file"
    
    # Modos de operación
    if [ $show_status_only -eq 1 ]; then
        show_status "$wu_file" "$wu_status_file"
        exit 0
    fi
    
    if [ $execute_all -eq 1 ]; then
        execute_all_work_units "$wu_file" "$spec_dir"
        exit 0
    fi
    
    if [ -z "$wu_id" ]; then
        die "Debes especificar un Work Unit ID (ej: WU-001) o usar --all"
    fi
    
    # Ejecutar Work Unit específica
    execute_work_unit "$wu_id" "$wu_file" "$spec_dir"
}

# Ejecutar
main "$@"

