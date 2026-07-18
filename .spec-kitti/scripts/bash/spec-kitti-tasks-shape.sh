#!/usr/bin/env bash
#
# spec-kitti-tasks-shape.sh
# Generador de Work Units de Spec-Kitti
#
# Lee el Plan Jerárquico y genera Work Units estructuradas,
# reduciendo 120+ tareas atómicas a 5-10 unidades de trabajo funcionales.
#
# Uso:
#   ./spec-kitti-tasks-shape.sh --json
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
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración
MAX_WUS="${ITTI_MAX_WUS:-10}"
MIN_SUBTASKS_PER_WU="${ITTI_MIN_SUBTASKS_PER_WU:-3}"
MAX_SUBTASKS_PER_WU="${ITTI_MAX_SUBTASKS_PER_WU:-15}"

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

die() {
    echo -e "\033[0;31m❌ $*\033[0m" >&2
    exit 1
}

# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

detect_feature_directory() {
    local current_branch
    current_branch=$(git branch --show-current)
    
    local feature_dir
    feature_dir=$(echo "$current_branch" | grep -oE '[0-9]+-[^/]+' | head -1)
    
    if [ -z "$feature_dir" ]; then
        die "No estás en una rama de feature (formato esperado: NNN-nombre-feature)"
    fi
    
    echo "$feature_dir"
}

validate_plan_file() {
    local plan_file="$1"
    
    if [ ! -f "$plan_file" ]; then
        die "Plan file no encontrado: $plan_file\nEjecuta /plan primero."
    fi
    
    # Verificar que tenga sección jerárquica
    if ! grep -q -E "## (Plan Jerárquico|Implementation Phases|Work Units)" "$plan_file"; then
        log_warning "Plan no contiene sección jerárquica clara"
        log_warning "Buscando cualquier estructura de plan..."
    fi
    
    log_success "Plan file válido"
}

generate_work_units_template() {
    local feature_dir="$1"
    local output_file="$2"
    
    log_info "Generando Work Units desde plan jerárquico..."
    
    cat <<EOF > "$output_file"
{
  "metadata": {
    "feature": "$feature_dir",
    "generated_at": "$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")",
    "total_work_units": 0,
    "estimated_hours": 0
  },
  "work_units": []
}
EOF
    
    log_info "📝 Template de Work Units creado: $output_file"
    echo ""
    
    cat <<EOF

${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${YELLOW}🎯 GENERACIÓN DE WORK UNITS${NC}
${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

El archivo work-units.json ha sido inicializado en:
  ${CYAN}$output_file${NC}

${YELLOW}SIGUIENTE PASO:${NC}

El agente de IA debe analizar el plan jerárquico y generar Work Units
estructuradas siguiendo estas pautas:

📋 **Estructura de Work Unit:**
{
  "id": "WU-001",
  "name": "Nombre descriptivo de alto nivel",
  "description": "Descripción completa de la funcionalidad",
  "priority": 1,
  "estimated_hours": 4,
  "affected_entities": ["Entity1", "Entity2"],
  "affected_files": ["src/path/file1.py", "src/path/file2.py"],
  "legacy_tests": ["tests/legacy/test_*.py"],
  "subtasks": [
    "Subtarea concreta 1",
    "Subtarea concreta 2",
    ...
  ],
  "success_criteria": "Descripción de cuándo está completa",
  "dependencies": [],
  "parallel_safe": true/false
}

🎯 **Objetivos:**
- Generar entre 5-10 Work Units (no más de $MAX_WUS)
- Cada WU debe tener 3-15 subtareas
- Cada WU debe ser funcionalmente completa y testeable
- Identificar pruebas legacy relevantes
- Establecer dependencias explícitas

📖 **Leer de:**
- Plan jerárquico en: specs/$feature_dir/plan.md
- Spec en: specs/$feature_dir/spec.md

✏️  **Escribir en:**
- $output_file

${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

Usa tu agente de IA (Cursor, Copilot, Claude) para analizar el plan
y llenar el archivo work-units.json con Work Units estructuradas.

Presiona ENTER cuando hayas completado la generación...
EOF
    
    read -p "" -r
}

validate_work_units() {
    local wu_file="$1"
    
    log_info "Validando Work Units generadas..."
    
    # Verificar que sea JSON válido
    if ! jq empty "$wu_file" 2>/dev/null; then
        die "work-units.json no es un JSON válido"
    fi
    
    # Contar Work Units
    local total_wus
    total_wus=$(jq -r '.work_units | length' "$wu_file")
    
    if [ "$total_wus" -eq 0 ]; then
        die "No se generaron Work Units. Revisa el archivo: $wu_file"
    fi
    
    if [ "$total_wus" -gt "$MAX_WUS" ]; then
        log_warning "Se generaron $total_wus Work Units (recomendado: máx $MAX_WUS)"
        log_warning "Considera consolidar algunas WUs relacionadas"
    fi
    
    # Validar cada WU
    local errors=0
    
    for i in $(seq 0 $((total_wus - 1))); do
        local wu_id
        wu_id=$(jq -r ".work_units[$i].id" "$wu_file")
        
        local wu_name
        wu_name=$(jq -r ".work_units[$i].name" "$wu_file")
        
        local subtasks_count
        subtasks_count=$(jq -r ".work_units[$i].subtasks | length" "$wu_file")
        
        # Validar subtasks
        if [ "$subtasks_count" -lt "$MIN_SUBTASKS_PER_WU" ]; then
            log_warning "$wu_id tiene solo $subtasks_count subtareas (mín: $MIN_SUBTASKS_PER_WU)"
            errors=$((errors + 1))
        fi
        
        if [ "$subtasks_count" -gt "$MAX_SUBTASKS_PER_WU" ]; then
            log_warning "$wu_id tiene $subtasks_count subtareas (máx: $MAX_SUBTASKS_PER_WU)"
            errors=$((errors + 1))
        fi
        
        # Validar campos requeridos
        local required_fields=("name" "description" "success_criteria")
        for field in "${required_fields[@]}"; do
            local value
            value=$(jq -r ".work_units[$i].$field" "$wu_file")
            
            if [ -z "$value" ] || [ "$value" = "null" ]; then
                log_warning "$wu_id falta campo requerido: $field"
                errors=$((errors + 1))
            fi
        done
    done
    
    if [ $errors -gt 0 ]; then
        log_warning "Se encontraron $errors advertencias. Revisa y ajusta si es necesario."
    else
        log_success "Todas las Work Units son válidas"
    fi
    
    echo "$total_wus"
}

analyze_execution_order() {
    local wu_file="$1"
    
    log_info "Analizando orden de ejecución y paralelización..."
    
    local total_wus
    total_wus=$(jq -r '.work_units | length' "$wu_file")
    
    local parallel_safe_count=0
    local with_dependencies_count=0
    
    for i in $(seq 0 $((total_wus - 1))); do
        local wu_id
        wu_id=$(jq -r ".work_units[$i].id" "$wu_file")
        
        local parallel_safe
        parallel_safe=$(jq -r ".work_units[$i].parallel_safe // false" "$wu_file")
        
        local dependencies
        dependencies=$(jq -r ".work_units[$i].dependencies | length" "$wu_file")
        
        if [ "$parallel_safe" = "true" ] && [ "$dependencies" -eq 0 ]; then
            parallel_safe_count=$((parallel_safe_count + 1))
        fi
        
        if [ "$dependencies" -gt 0 ]; then
            with_dependencies_count=$((with_dependencies_count + 1))
        fi
    done
    
    echo ""
    log_info "📊 Análisis de Paralelización:"
    echo "   • Total Work Units: $total_wus"
    echo "   • Ejecutables en paralelo: $parallel_safe_count"
    echo "   • Con dependencias: $with_dependencies_count"
    echo ""
}

generate_execution_recommendations() {
    local wu_file="$1"
    
    echo "🔄 Orden de ejecución recomendado:"
    echo ""
    
    # Ordenar por prioridad y dependencias
    # (simplificado - en producción usaríamos topological sort)
    local wu_ids
    wu_ids=$(jq -r '.work_units | sort_by(.priority) | .[].id' "$wu_file")
    
    local counter=1
    for wu_id in $wu_ids; do
        local wu_name
        wu_name=$(jq -r ".work_units[] | select(.id==\"$wu_id\") | .name" "$wu_file")
        
        local legacy_tests_count
        legacy_tests_count=$(jq -r ".work_units[] | select(.id==\"$wu_id\") | .legacy_tests | length" "$wu_file")
        
        local dependencies
        dependencies=$(jq -r ".work_units[] | select(.id==\"$wu_id\") | .dependencies | length" "$wu_file")
        
        local info=""
        if [ "$dependencies" -gt 0 ]; then
            local deps
            deps=$(jq -r ".work_units[] | select(.id==\"$wu_id\") | .dependencies | join(\", \")" "$wu_file")
            info=" (depende de: $deps)"
        fi
        
        echo "   $counter. $wu_id - $wu_name ($legacy_tests_count tests)$info"
        counter=$((counter + 1))
    done
    
    echo ""
}

output_json_info() {
    local feature_dir="$1"
    local wu_file="$2"
    
    if [ "${JSON_OUTPUT:-0}" -eq 1 ]; then
        # Output JSON para parsing por scripts
        jq -c "{
            feature: \"$feature_dir\",
            work_units_file: \"$wu_file\",
            total_work_units: (.work_units | length)
        }" "$wu_file"
    fi
}

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

main() {
    local json_output=0
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --json)
                json_output=1
                JSON_OUTPUT=1
                shift
                ;;
            *)
                die "Argumento desconocido: $1"
                ;;
        esac
    done
    
    # Detectar feature directory
    local feature_dir
    feature_dir=$(detect_feature_directory)
    
    local spec_dir="$REPO_ROOT/specs/$feature_dir"
    local plan_file="$spec_dir/plan.md"
    local wu_file="$spec_dir/work-units.json"
    
    # Validar plan
    validate_plan_file "$plan_file"
    
    # Generar template de Work Units
    generate_work_units_template "$feature_dir" "$wu_file"
    
    # Validar Work Units generadas
    local total_wus
    total_wus=$(validate_work_units "$wu_file")
    
    # Analizar orden de ejecución
    analyze_execution_order "$wu_file"
    
    # Mostrar recomendaciones
    generate_execution_recommendations "$wu_file"
    
    # Mostrar siguiente paso
    echo ""
    log_success "Work Units generadas exitosamente"
    echo ""
    echo "📁 Archivo generado:"
    echo "   $wu_file"
    echo ""
    log_info "📝 Siguiente paso:"
    echo "   Ejecuta: /implement.unit WU-001"
    echo ""
    echo "   Para ejecutar varias en paralelo:"
    echo "   /implement.unit WU-001 WU-003"
    echo ""
    
    # Output JSON si se solicitó
    output_json_info "$feature_dir" "$wu_file"
}

main "$@"

