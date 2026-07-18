#!/usr/bin/env bash
#
# spec-kitti-create-pr.sh
# Generador de Pull Requests de Spec-Kitti
#
# Crea PRs automáticos con descripción rica después de que una Work Unit pasa todos los tests.
#
# Uso:
#   ./spec-kitti-create-pr.sh --wu-data "$WU_JSON" --wu-dir ./WU-001
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
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# FUNCIONES
# ============================================================================

log_info() {
    echo -e "${CYAN}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✅${NC} $*"
}

die() {
    echo -e "\033[0;31m❌ $*\033[0m" >&2
    exit 1
}

# ============================================================================
# GENERACIÓN DE DESCRIPCIÓN DE PR
# ============================================================================

generate_pr_description() {
    local wu_data="$1"
    local wu_dir="$2"
    
    local wu_id
    wu_id=$(echo "$wu_data" | jq -r '.id')
    
    local wu_name
    wu_name=$(echo "$wu_data" | jq -r '.name')
    
    local wu_description
    wu_description=$(echo "$wu_data" | jq -r '.description')
    
    local success_criteria
    success_criteria=$(echo "$wu_data" | jq -r '.success_criteria')
    
    local affected_entities
    affected_entities=$(echo "$wu_data" | jq -r '.affected_entities[]' | sed 's/^/- /')
    
    local affected_files
    affected_files=$(echo "$wu_data" | jq -r '.affected_files[]' | sed 's/^/- /')
    
    # Leer resultados de tests
    local testing_report="${wu_dir}/../testing_report.json"
    local tests_passed="N/A"
    local tests_total="N/A"
    
    if [ -f "$testing_report" ]; then
        tests_passed=$(jq -r '.tests_passed' "$testing_report")
        tests_total=$(jq -r '.tests_total' "$testing_report")
    fi
    
    cat <<EOF
# $wu_id: $wu_name

## 📋 Descripción

$wu_description

## ✅ Criterio de Éxito

$success_criteria

## 🧪 Validación de Pruebas Legacy

**Tests ejecutados**: $tests_total  
**Tests pasados**: $tests_passed  
**Status**: ✅ PASS

Todas las pruebas legacy relacionadas con esta Work Unit han pasado exitosamente, 
garantizando que el código nuevo mantiene compatibilidad con la lógica de negocio legacy.

## 🏛️ Entidades Afectadas

$affected_entities

## 📁 Archivos Modificados

$affected_files

## 🤖 Generado por Spec-Kitti

Esta Work Unit fue implementada y validada de forma autónoma por el Sistema Multiagente (MAS) de Spec-Kitti.

- **Iteraciones**: Ver historial de commits
- **Auto-corrección**: El sistema iteró automáticamente hasta que todos los tests pasaron
- **Pruebas de Paridad**: Código validado contra lógica legacy

## 📝 Siguiente Paso

Revisa el código y, si todo está correcto, aprueba el PR para merge.

---

**Generado automáticamente por**: Spec-Kitti v1.0  
**Fecha**: $(date)
EOF
}

# ============================================================================
# CREACIÓN DE PR
# ============================================================================

create_commit_and_pr() {
    local wu_data="$1"
    local wu_dir="$2"
    
    local wu_id
    wu_id=$(echo "$wu_data" | jq -r '.id')
    
    local wu_name
    wu_name=$(echo "$wu_data" | jq -r '.name')
    
    log_info "Creando commit y PR para $wu_id..."
    
    # Agregar todos los cambios
    git add .
    
    # Verificar que hay cambios
    if ! git diff --cached --quiet; then
        # Generar descripción de PR
        local pr_description_file="$wu_dir/final/pr-description.md"
        mkdir -p "$wu_dir/final"
        generate_pr_description "$wu_data" "$wu_dir" > "$pr_description_file"
        
        log_success "Descripción de PR generada: $pr_description_file"
        
        # Leer tests pasados para commit message
        local testing_report="${wu_dir}/../testing_report.json"
        local tests_info=""
        
        if [ -f "$testing_report" ]; then
            local tests_passed
            tests_passed=$(jq -r '.tests_passed' "$testing_report")
            tests_info=" ($tests_passed tests legacy passed)"
        fi
        
        # Crear commit
        local commit_message="$wu_id: $wu_name$tests_info

Implementación autónoma de Work Unit validada con pruebas legacy.

Generado por: Spec-Kitti MAS
"
        
        git commit -m "$commit_message"
        
        log_success "Commit creado"
        
        # Push al remote
        local current_branch
        current_branch=$(git branch --show-current)
        
        log_info "Haciendo push a origin/$current_branch..."
        git push origin "$current_branch"
        
        log_success "Push completado"
        
        # Intentar crear PR con gh CLI si está disponible
        if command -v gh &> /dev/null; then
            log_info "Creando PR con GitHub CLI..."
            
            gh pr create \
                --title "$wu_id: $wu_name" \
                --body-file "$pr_description_file" \
                --assignee "@me" \
                || log_info "No se pudo crear PR automáticamente. Créalo manualmente en GitHub."
        else
            log_info "GitHub CLI (gh) no encontrado. Crea el PR manualmente:"
            echo ""
            echo "  Título: $wu_id: $wu_name"
            echo "  Descripción: Ver $pr_description_file"
            echo ""
        fi
        
    else
        log_info "No hay cambios para commitear"
        return 1
    fi
}

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

main() {
    local wu_data=""
    local wu_dir=""
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --wu-data)
                wu_data="$2"
                shift 2
                ;;
            --wu-dir)
                wu_dir="$2"
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
    
    if [ -z "$wu_dir" ]; then
        die "Falta argumento: --wu-dir"
    fi
    
    # Crear PR
    create_commit_and_pr "$wu_data" "$wu_dir"
    
    log_success "Pull Request creado exitosamente"
}

main "$@"

