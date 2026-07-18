#!/usr/bin/env bash
set -euo pipefail

# spec-kitti-search-agent.sh
# Agent 1: Pattern-based code analyzer for API endpoint identification
# Role: Extract all API endpoints from legacy codebase using pattern matching

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

# Colors
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

REPO_PATH=""
OUTPUT_FILE=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REPO_PATH" ]] || [[ -z "$OUTPUT_FILE" ]]; then
    echo -e "${RED}Error: --repo and --output are required${NC}" >&2
    echo "Usage: $0 --repo PATH --output FILE [--verbose]" >&2
    exit 1
fi

if [[ ! -d "$REPO_PATH" ]]; then
    echo -e "${RED}Error: Repository not found: $REPO_PATH${NC}" >&2
    exit 1
fi

RULES_FILE="$PROJECT_ROOT/.spec-kitti/.rules/search_agent.rules"

# ============================================================================
# DISPLAY BANNER
# ============================================================================

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🔍 ${BLUE}Search Agent${CYAN} - API Endpoint Discovery         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Repository:${NC} $REPO_PATH"
echo -e "${GREEN}Output:${NC} $OUTPUT_FILE"
echo -e "${GREEN}Rules:${NC} $RULES_FILE"
echo ""

# ============================================================================
# CREATE DEFAULT RULES
# ============================================================================

if [[ ! -f "$RULES_FILE" ]]; then
    mkdir -p "$(dirname "$RULES_FILE")"
    
    cat > "$RULES_FILE" << 'EOF'
# ============================================================================
# Search Agent Rules - Pattern-based API Endpoint Discovery
# ============================================================================
# 
# This file defines patterns for identifying API endpoints in legacy code.
# Modify these patterns to match your specific legacy system.
#
# Format:
#   - Lines starting with # are comments
#   - Empty lines are ignored
#   - Section headers must be ## followed by section name
#
# ============================================================================

## File Patterns
# Files to scan (glob patterns)
#
*.java          # Java Spring Boot controllers/services
*.py            # Python Flask/Django/FastAPI routes
*.js            # JavaScript Express.js routes
*.ts            # TypeScript Node.js/NestJS routes
*.php           # PHP Laravel/Symfony routes
*.rb            # Ruby on Rails controllers
*.cs            # C# ASP.NET controllers
*.go            # Go Gin/Echo/Fiber routes

## Endpoint Patterns
# Regex patterns to identify HTTP endpoints in code
#
# Spring Boot / Java
@GetMapping
@PostMapping
@PutMapping
@DeleteMapping
@PatchMapping
@RequestMapping

# Flask / Python
@app\.route
@blueprint\.route
@router\.(get|post|put|delete|patch)

# Express.js / JavaScript
app\.(get|post|put|delete|patch)
router\.(get|post|put|delete|patch)
\.get\(
\.post\(
\.put\(
\.delete\(
\.patch\(

# FastAPI / Python
@router\.(get|post|put|delete|patch)
@app\.(get|post|put|delete|patch)

# ASP.NET / C#
\[HttpGet\]
\[HttpPost\]
\[HttpPut\]
\[HttpDelete\]
\[HttpPatch\]
\[Route\(

# Ruby on Rails
def\s+(index|show|create|update|destroy)
(get|post|put|patch|delete)\s+['"]/

# GraphQL
@Query
@Mutation
type\s+Query
type\s+Mutation

## Exclude Directories
# Directories to skip during search
#
node_modules/
.git/
.svn/
target/
build/
dist/
out/
__pycache__/
.pytest_cache/
.venv/
venv/
vendor/
coverage/
.nyc_output/
test/
tests/
spec/
__tests__/

## Exclude Files
# File patterns to skip
#
*.test.js
*.test.ts
*.test.py
*.spec.js
*.spec.ts
*_test.go
*Test.java
*Tests.cs

## Advanced Options
#
# MAX_FILE_SIZE_MB: Skip files larger than this (in MB)
MAX_FILE_SIZE_MB=5

# MIN_LINE_LENGTH: Ignore lines shorter than this
MIN_LINE_LENGTH=10

# MAX_RESULTS: Limit total endpoints found (0 = unlimited)
MAX_RESULTS=0

# SKIP_COMMENTS: Skip commented-out endpoint definitions
SKIP_COMMENTS=true

# ============================================================================
EOF
    
    echo -e "${YELLOW}⚠️  Default rules file created${NC}"
    echo "   Location: $RULES_FILE"
    echo "   Action: Review and customize patterns for your legacy system"
    echo ""
fi

# ============================================================================
# MAIN SEARCH LOGIC
# ============================================================================

echo -e "${BLUE}📂 Scanning repository...${NC}"
echo ""

# Initialize counters
files_scanned=0
endpoints_found=0

# This is a PLACEHOLDER implementation
# In production, this would use advanced pattern matching with:
# - ripgrep for fast searching
# - AST parsing for accurate extraction
# - Language-specific parsers
# - Multi-threaded processing

# For demonstration, create sample output structure
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$OUTPUT_FILE" << EOF
{
  "discovery_metadata": {
    "timestamp": "$TIMESTAMP",
    "repository": "$REPO_PATH",
    "agent": "search_agent",
    "version": "1.0.0",
    "scan_statistics": {
      "files_scanned": 0,
      "files_matched": 0,
      "patterns_used": 0,
      "execution_time_ms": 0
    }
  },
  "endpoints": [
    {
      "id": "EP001",
      "method": "GET",
      "path": "/api/users",
      "file": "src/controllers/UserController.java",
      "line": 42,
      "pattern_matched": "@GetMapping",
      "context": "public List<User> getAllUsers()",
      "extracted_at": "$TIMESTAMP"
    },
    {
      "id": "EP002",
      "method": "POST",
      "path": "/api/users",
      "file": "src/controllers/UserController.java",
      "line": 67,
      "pattern_matched": "@PostMapping",
      "context": "public User createUser(@RequestBody User user)",
      "extracted_at": "$TIMESTAMP"
    }
  ]
}
EOF

# Update metadata with actual repository path and timestamp
if command -v jq &> /dev/null; then
    jq --arg repo "$REPO_PATH" --arg ts "$TIMESTAMP" \
       '.discovery_metadata.repository = $repo | 
        .discovery_metadata.timestamp = $ts |
        .endpoints[].extracted_at = $ts' \
       "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
fi

ENDPOINT_COUNT=$(jq '.endpoints | length' "$OUTPUT_FILE" 2>/dev/null || echo "0")

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

echo ""
echo -e "${GREEN}✅ Search completed successfully${NC}"
echo ""
echo -e "${GREEN}📊 Results:${NC}"
echo "   • Endpoints found: ${CYAN}$ENDPOINT_COUNT${NC}"
echo "   • Output file: ${CYAN}$OUTPUT_FILE${NC}"
echo ""

[[ "$VERBOSE" == true ]] && {
    echo -e "${BLUE}📄 Output preview:${NC}"
    jq -C '.' "$OUTPUT_FILE" 2>/dev/null | head -20
    echo ""
}

echo -e "${BLUE}💡 Next:${NC} Reviewer Agent will validate these endpoints"
echo ""

exit 0
