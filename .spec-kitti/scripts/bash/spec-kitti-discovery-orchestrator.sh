#!/usr/bin/env bash
set -euo pipefail

# spec-kitti-discovery-orchestrator.sh
# Orchestrates the 4-agent Multi-Agent System (MAS) for legacy reverse engineering
# Generates the Parity Contract (endpoint_mapping_schema.json)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

# Source common utilities
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    echo "Error: common.sh not found" >&2
    exit 1
fi

# ============================================================================
# CONFIGURATION
# ============================================================================

# Color codes for output
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Directory structure
readonly DISCOVERY_DIR="$PROJECT_ROOT/.spec-kitti/discovery"
readonly LOGS_DIR="$DISCOVERY_DIR/logs"
readonly CACHE_DIR="$DISCOVERY_DIR/.cache"
readonly RULES_DIR="$PROJECT_ROOT/.spec-kitti/.rules"

# Output files
readonly ENDPOINT_MAPPING="$DISCOVERY_DIR/endpoint_mapping.json"
readonly ENDPOINT_MAPPING_VALIDATED="$DISCOVERY_DIR/endpoint_mapping_validated.json"
readonly ENDPOINT_MAPPING_SCHEMA="$DISCOVERY_DIR/endpoint_mapping_schema.json"
readonly CONTRACT_REPORT="$DISCOVERY_DIR/contract_validation_report.md"

# Agent scripts
readonly SEARCH_AGENT="$SCRIPT_DIR/spec-kitti-search-agent.sh"
readonly ENDPOINT_REVIEWER_AGENT="$SCRIPT_DIR/spec-kitti-endpoint-reviewer-agent.sh"
readonly SCHEMA_AGENT="$SCRIPT_DIR/spec-kitti-schema-agent.sh"
readonly SCHEMA_REVIEWER_AGENT="$SCRIPT_DIR/spec-kitti-schema-reviewer-agent.sh"

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

DOCS_PATH=""
FORCE=false
AGENT_ONLY=""
VERBOSE=false

usage() {
    cat << EOF
Usage: $0 --docs PATH [OPTIONS]

Orchestrates a 4-agent MAS to generate the Parity Contract through multi-source analysis.

Required Arguments:
  --docs PATH           Path to documentation folder containing:
                        • interviews/ (transcriptions, endpoints.txt)
                        • har-files/ (browser network captures)
                        • application/ (legacy code repositories)

Optional Arguments:
  --force               Force re-execution (ignore cache)
  --agent NAME          Run only specific agent: search|reviewer|schema|reviewer-schema
  --verbose             Enable verbose logging with detailed diagnostics
  -h, --help            Show this help message

Examples:
  $0 --docs /docs/reverse-engineering
  $0 --docs /docs/reverse-engineering --force
  $0 --docs /docs/reverse-engineering --agent search --verbose

Documentation Structure:
  /docs/reverse-engineering/
    ├── interviews/
    │   ├── endpoints.txt              (list of URLs from meetings)
    │   ├── transcripcion_TL_*.txt     (Tech Lead interview notes)
    │   └── arquitectura.md            (architecture decisions)
    ├── har-files/
    │   ├── *.har                      (browser network captures)
    │   └── README.md                  (capture methodology)
    └── application/
        ├── frontend-repo/             (legacy frontend code)
        └── backend-repo/              (legacy backend code)

Exit Codes:
  0  Success - Parity Contract generated and approved
  1  Error - Pipeline failed (check logs)
  2  Warning - Contract generated with warnings

For more information: https://github.com/itti-data/pr-coe-genai-spec-kitti
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --docs)
            DOCS_PATH="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --agent)
            AGENT_ONLY="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

# ============================================================================
# VALIDATION
# ============================================================================

if [[ -z "$DOCS_PATH" ]]; then
    echo -e "${RED}Error: --docs argument is required${NC}" >&2
    echo ""
    usage
    exit 1
fi

if [[ ! -d "$DOCS_PATH" ]]; then
    echo -e "${RED}Error: Documentation path does not exist: $DOCS_PATH${NC}" >&2
    exit 1
fi

# Verify expected subdirectories exist
INTERVIEWS_DIR="$DOCS_PATH/interviews"
HAR_DIR="$DOCS_PATH/har-files"
APP_DIR="$DOCS_PATH/application"

if [[ ! -d "$INTERVIEWS_DIR" ]]; then
    echo -e "${YELLOW}Warning: interviews/ directory not found in $DOCS_PATH${NC}" >&2
    echo -e "${YELLOW}Expected structure: $DOCS_PATH/interviews/${NC}" >&2
fi

if [[ ! -d "$HAR_DIR" ]]; then
    echo -e "${YELLOW}Warning: har-files/ directory not found in $DOCS_PATH${NC}" >&2
    echo -e "${YELLOW}Expected structure: $DOCS_PATH/har-files/${NC}" >&2
fi

if [[ ! -d "$APP_DIR" ]]; then
    echo -e "${YELLOW}Warning: application/ directory not found in $DOCS_PATH${NC}" >&2
    echo -e "${YELLOW}Expected structure: $DOCS_PATH/application/${NC}" >&2
fi

# Validate agent name if provided
if [[ -n "$AGENT_ONLY" ]]; then
    case "$AGENT_ONLY" in
        search|reviewer|schema|reviewer-schema)
            ;;
        *)
            echo -e "${RED}Error: Invalid agent name: $AGENT_ONLY${NC}" >&2
            echo "Valid agents: search, reviewer, schema, reviewer-schema"
            exit 1
            ;;
    esac
fi

# ============================================================================
# SETUP
# ============================================================================

# Create directory structure
mkdir -p "$DISCOVERY_DIR" "$LOGS_DIR" "$CACHE_DIR" "$RULES_DIR"

# ============================================================================
# DISPLAY BANNER
# ============================================================================

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        ${CYAN}🔍 SPEC-KITTI DISCOVERY - MAS ORCHESTRATOR${BLUE}         ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║     Multi-Agent System for Legacy Reverse Engineering       ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📁 Documentation:${NC} $DOCS_PATH"
echo -e "${GREEN}📂 Output:${NC} $DISCOVERY_DIR"
[[ "$FORCE" == true ]] && echo -e "${YELLOW}⚡ Mode:${NC} Force re-execution"
[[ "$VERBOSE" == true ]] && echo -e "${CYAN}📝 Logging:${NC} Verbose"
[[ -n "$AGENT_ONLY" ]] && echo -e "${CYAN}🎯 Agent:${NC} $AGENT_ONLY only"
echo ""

# Display discovered sources
echo -e "${CYAN}📚 Discovered Sources:${NC}"
[[ -d "$INTERVIEWS_DIR" ]] && echo "   • Interviews: $(find "$INTERVIEWS_DIR" -type f | wc -l | tr -d ' ') files"
[[ -d "$HAR_DIR" ]] && echo "   • HAR files: $(find "$HAR_DIR" -name "*.har" | wc -l | tr -d ' ') captures"
[[ -d "$APP_DIR" ]] && echo "   • Applications: $(find "$APP_DIR" -maxdepth 1 -type d | tail -n +2 | wc -l | tr -d ' ') repositories"
echo ""

# ============================================================================
# CHECK EXISTING CONTRACT
# ============================================================================

if [[ -f "$ENDPOINT_MAPPING_SCHEMA" ]] && [[ "$FORCE" != true ]] && [[ -z "$AGENT_ONLY" ]]; then
    echo -e "${YELLOW}⚠️  Parity Contract already exists${NC}"
    echo ""
    echo "   📄 File: $ENDPOINT_MAPPING_SCHEMA"
    echo ""
    
    # Show file info
    if command -v jq &> /dev/null; then
        ENDPOINTS_COUNT=$(jq '.contract_metadata.endpoints_count // 0' "$ENDPOINT_MAPPING_SCHEMA" 2>/dev/null)
        GENERATED_AT=$(jq -r '.contract_metadata.generated_at // "unknown"' "$ENDPOINT_MAPPING_SCHEMA" 2>/dev/null)
        echo "   Endpoints: $ENDPOINTS_COUNT"
        echo "   Generated: $GENERATED_AT"
        echo ""
    fi
    
    echo "   Options:"
    echo "   1. Use ${CYAN}--force${NC} to regenerate"
    echo "   2. Use ${CYAN}--agent <name>${NC} to re-run specific agent"
    echo "   3. Review existing file"
    echo "   4. Delete file manually and re-run"
    echo ""
    exit 0
fi

# ============================================================================
# AGENT EXECUTION FUNCTION
# ============================================================================

run_agent() {
    local agent_name=$1
    local agent_script=$2
    local agent_input=$3
    local agent_output=$4
    local log_file="$LOGS_DIR/${agent_name// /-}.log"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🤖 Executing: ${agent_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Verify agent script exists
    if [[ ! -f "$agent_script" ]]; then
        echo -e "${RED}❌ Agent script not found: $agent_script${NC}"
        return 1
    fi
    
    # Make executable
    chmod +x "$agent_script" 2>/dev/null || true
    
    # Build command
    local cmd="$agent_script --docs \"$DOCS_PATH\""
    [[ -n "$agent_input" ]] && cmd="$cmd --input \"$agent_input\""
    [[ -n "$agent_output" ]] && cmd="$cmd --output \"$agent_output\""
    [[ "$VERBOSE" == true ]] && cmd="$cmd --verbose"
    
    echo -e "${GREEN}📝 Command:${NC} $cmd"
    echo -e "${GREEN}📄 Log:${NC} $log_file"
    echo ""
    
    # Record start time
    local start_time=$(date +%s)
    
    # Execute agent
    local exit_code=0
    if eval "$cmd" > "$log_file" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${GREEN}✅ ${agent_name} completed successfully${NC}"
        echo -e "${GREEN}⏱️  Duration: ${duration}s${NC}"
        echo ""
        
        # Show preview of output if verbose
        if [[ "$VERBOSE" == true ]] && [[ -n "$agent_output" ]] && [[ -f "$agent_output" ]]; then
            echo -e "${CYAN}📊 Output preview:${NC}"
            if command -v jq &> /dev/null && [[ "$agent_output" == *.json ]]; then
                jq -r '. | keys' "$agent_output" 2>/dev/null | head -5
            else
                head -3 "$agent_output"
            fi
            echo ""
        fi
        
        return 0
    else
        exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${RED}❌ ${agent_name} failed${NC}"
        echo -e "${RED}⏱️  Duration: ${duration}s${NC}"
        echo -e "${RED}🚨 Exit code: $exit_code${NC}"
        echo ""
        echo -e "${YELLOW}📄 Log file: $log_file${NC}"
        echo ""
        echo -e "${RED}Last 20 lines of log:${NC}"
        echo "────────────────────────────────────────"
        tail -20 "$log_file" 2>/dev/null || echo "(log file empty or not found)"
        echo "────────────────────────────────────────"
        echo ""
        
        return 1
    fi
}

# ============================================================================
# PIPELINE EXECUTION
# ============================================================================

echo -e "${CYAN}🚀 Starting Discovery Pipeline${NC}"
echo ""

START_TIME=$(date +%s)

# Agent 1: Search Agent
if [[ -z "$AGENT_ONLY" ]] || [[ "$AGENT_ONLY" == "search" ]]; then
    if ! run_agent "Search Agent" "$SEARCH_AGENT" "" "$ENDPOINT_MAPPING"; then
        echo -e "${RED}❌ Pipeline failed at Search Agent${NC}"
        echo -e "${RED}💡 Tip: Check search patterns in $RULES_DIR/search_agent.rules${NC}"
        exit 1
    fi
fi

# Agent 2: Reviewer Agent
if [[ -z "$AGENT_ONLY" ]] || [[ "$AGENT_ONLY" == "reviewer" ]]; then
    if ! run_agent "Endpoint Reviewer Agent" "$ENDPOINT_REVIEWER_AGENT" "$ENDPOINT_MAPPING" "$ENDPOINT_MAPPING_VALIDATED"; then
        echo -e "${RED}❌ Pipeline failed at Reviewer Agent${NC}"
        echo -e "${RED}💡 Tip: Check validation rules in $RULES_DIR/reviewer-agent.rules${NC}"
        exit 1
    fi
fi

# Agent 3: Schema Agent
if [[ -z "$AGENT_ONLY" ]] || [[ "$AGENT_ONLY" == "schema" ]]; then
    if ! run_agent "Schema Agent" "$SCHEMA_AGENT" "$ENDPOINT_MAPPING_VALIDATED" "$ENDPOINT_MAPPING_SCHEMA"; then
        echo -e "${RED}❌ Pipeline failed at Schema Agent${NC}"
        echo -e "${RED}💡 Tip: Check schema rules in $RULES_DIR/schema_agent.rules${NC}"
        exit 1
    fi
fi

# Agent 4: Reviewer Schema Agent
if [[ -z "$AGENT_ONLY" ]] || [[ "$AGENT_ONLY" == "reviewer-schema" ]]; then
    if ! run_agent "Schema Reviewer Agent" "$SCHEMA_REVIEWER_AGENT" "$ENDPOINT_MAPPING_SCHEMA" "$CONTRACT_REPORT"; then
        echo -e "${RED}❌ Pipeline failed at Reviewer Schema Agent${NC}"
        echo -e "${RED}💡 Tip: Review validation report: $CONTRACT_REPORT${NC}"
        exit 1
    fi
fi

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║        ✅ ${CYAN}PARITY CONTRACT GENERATED SUCCESSFULLY${GREEN}        ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Display statistics
if [[ -f "$ENDPOINT_MAPPING_SCHEMA" ]] && command -v jq &> /dev/null; then
    ENDPOINTS_COUNT=$(jq '.contract_metadata.endpoints_count // 0' "$ENDPOINT_MAPPING_SCHEMA" 2>/dev/null)
    LEGACY_SYSTEM=$(jq -r '.contract_metadata.legacy_system // "unknown"' "$ENDPOINT_MAPPING_SCHEMA" 2>/dev/null)
    VERSION=$(jq -r '.contract_metadata.version // "unknown"' "$ENDPOINT_MAPPING_SCHEMA" 2>/dev/null)
    
    echo -e "${GREEN}📊 Statistics:${NC}"
    echo "   • Endpoints discovered: ${CYAN}$ENDPOINTS_COUNT${NC}"
    echo "   • Legacy system: $LEGACY_SYSTEM"
    echo "   • Contract version: $VERSION"
    echo "   • Total duration: ${CYAN}${TOTAL_DURATION}s${NC}"
    echo ""
fi

# Display generated files
echo -e "${GREEN}📁 Generated Files:${NC}"
echo "   1. ${CYAN}$ENDPOINT_MAPPING_SCHEMA${NC}"
echo "      └─ Parity Contract (use in /spec-kitti.specify)"
echo ""
echo "   2. ${CYAN}$CONTRACT_REPORT${NC}"
echo "      └─ Validation report"
echo ""
echo "   3. ${CYAN}$LOGS_DIR/${NC}"
echo "      └─ Agent execution logs"
echo ""

# Next steps
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo "   1. Review the Parity Contract: ${CYAN}cat $ENDPOINT_MAPPING_SCHEMA${NC}"
echo "   2. Read validation report: ${CYAN}cat $CONTRACT_REPORT${NC}"
echo "   3. Proceed to specification: ${CYAN}/spec-kitti.specify${NC}"
echo ""

exit 0
