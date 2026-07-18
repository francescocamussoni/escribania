#!/usr/bin/env bash

# Code Reviewer Agent Script
# Validates generated code against Work Unit requirements and quality standards

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME="Code Reviewer Agent"

# --- Color Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
  echo -e "${GREEN}[${AGENT_NAME}]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[${AGENT_NAME}]${NC} $1"
}

error() {
  echo -e "${RED}[${AGENT_NAME}]${NC} $1"
}

info() {
  echo -e "${BLUE}[${AGENT_NAME}]${NC} $1"
}

# --- Help ---
usage() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS]

Review generated code against Work Unit requirements and quality standards.

OPTIONS:
  --code-file FILE        Path to generated code file (required)
  --work-unit FILE        Path to Work Unit JSON file (required)
  --parity-contract FILE  Path to endpoint_mapping_schema.json (required)
  --output FILE           Path to save review report (required)
  --rules FILE            Path to code_reviewer_agent.rules (optional)
  --help                  Show this help message

EXAMPLE:
  $(basename "$0") \\
    --code-file src/users/users.service.ts \\
    --work-unit .spec-kitti/work-units/WU-005.json \\
    --parity-contract .spec-kitti/discovery/endpoint_mapping_schema.json \\
    --output .spec-kitti/implementation/WU-005-review.md \\
    --rules .spec-kitti/.rules/code_reviewer_agent.rules

EOF
  exit 1
}

# --- Parse Arguments ---
CODE_FILE=""
WORK_UNIT_FILE=""
PARITY_CONTRACT_FILE=""
OUTPUT_FILE=""
RULES_FILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --code-file)
      CODE_FILE="$2"
      shift 2
      ;;
    --work-unit)
      WORK_UNIT_FILE="$2"
      shift 2
      ;;
    --parity-contract)
      PARITY_CONTRACT_FILE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --rules)
      RULES_FILE="$2"
      shift 2
      ;;
    --help)
      usage
      ;;
    *)
      error "Unknown option: $1"
      usage
      ;;
  esac
done

# --- Validate Required Arguments ---
if [[ -z "$CODE_FILE" || -z "$WORK_UNIT_FILE" || -z "$PARITY_CONTRACT_FILE" || -z "$OUTPUT_FILE" ]]; then
  error "Missing required arguments"
  usage
fi

# --- Validate Input Files ---
if [[ ! -f "$CODE_FILE" ]]; then
  error "Code file not found: $CODE_FILE"
  exit 1
fi

if [[ ! -f "$WORK_UNIT_FILE" ]]; then
  error "Work Unit file not found: $WORK_UNIT_FILE"
  exit 1
fi

if [[ ! -f "$PARITY_CONTRACT_FILE" ]]; then
  error "Parity Contract file not found: $PARITY_CONTRACT_FILE"
  exit 1
fi

if [[ -n "$RULES_FILE" && ! -f "$RULES_FILE" ]]; then
  error "Rules file not found: $RULES_FILE"
  exit 1
fi

# --- Load Inputs ---
log "Loading generated code: $CODE_FILE"
CODE_CONTENT=$(cat "$CODE_FILE")

log "Loading Work Unit: $WORK_UNIT_FILE"
WORK_UNIT_CONTENT=$(cat "$WORK_UNIT_FILE")

log "Loading Parity Contract: $PARITY_CONTRACT_FILE"
PARITY_CONTRACT_CONTENT=$(cat "$PARITY_CONTRACT_FILE")

RULES_CONTENT=""
if [[ -n "$RULES_FILE" ]]; then
  log "Loading Rules: $RULES_FILE"
  RULES_CONTENT=$(cat "$RULES_FILE")
fi

# --- Extract Metadata ---
WORK_UNIT_ID=$(echo "$WORK_UNIT_CONTENT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
FILE_PATH=$(echo "$WORK_UNIT_CONTENT" | grep -o '"file_path":"[^"]*"' | head -1 | cut -d'"' -f4)

log "Reviewing Work Unit: $WORK_UNIT_ID"
log "File: $FILE_PATH"

# --- Banner ---
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    CODE REVIEWER AGENT                         ║"
echo "║                  Validating Code Quality                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# --- Perform Reviews ---
log "Level 1: Requirements Compliance"
log "Level 2: Code Quality"
log "Level 3: Framework Compliance"
log "Level 4: Performance"
log "Level 5: Maintainability"

# Create output directory
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# --- SIMULATED REVIEW PROCESS ---
# In production, this would call an AI API to perform deep code review
# For now, we'll perform basic checks and generate a template report

# Basic Checks
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Check 1: File exists and not empty
if [[ -s "$CODE_FILE" ]]; then
  ((PASSED_CHECKS++))
else
  ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# Check 2: TypeScript/Python syntax (basic)
FILE_EXT="${CODE_FILE##*.}"
case "$FILE_EXT" in
  ts)
    if grep -q "export class" "$CODE_FILE" && grep -q "@Injectable" "$CODE_FILE"; then
      ((PASSED_CHECKS++))
    else
      ((FAILED_CHECKS++))
    fi
    ;;
  py)
    if grep -q "def " "$CODE_FILE"; then
      ((PASSED_CHECKS++))
    else
      ((FAILED_CHECKS++))
    fi
    ;;
  *)
    ((PASSED_CHECKS++))
    ;;
esac
((TOTAL_CHECKS++))

# Check 3: Business rules referenced
if grep -q "BR001\|BR002\|BR003\|BR004" "$CODE_FILE"; then
  ((PASSED_CHECKS++))
else
  ((FAILED_CHECKS++))
  warn "No business rule references found in code"
fi
((TOTAL_CHECKS++))

# Check 4: Security - no password logging
if grep -qi "password.*log\|log.*password" "$CODE_FILE"; then
  ((FAILED_CHECKS++))
  error "CRITICAL: Password detected in log statements"
else
  ((PASSED_CHECKS++))
fi
((TOTAL_CHECKS++))

# Check 5: Error handling
if grep -q "try\|catch\|except" "$CODE_FILE"; then
  ((PASSED_CHECKS++))
else
  ((WARNINGS++))
  warn "Limited error handling detected"
fi
((TOTAL_CHECKS++))

# Calculate score
SCORE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))

# Determine status
STATUS="REJECTED"
if [[ $FAILED_CHECKS -eq 0 && $SCORE -ge 90 ]]; then
  STATUS="APPROVED"
elif [[ $FAILED_CHECKS -le 2 && $SCORE -ge 80 ]]; then
  STATUS="NEEDS_REVISION"
fi

# --- Generate Review Report ---
cat > "$OUTPUT_FILE" << EOF
# Code Review Report: ${FILE_PATH}

**Work Unit**: ${WORK_UNIT_ID}  
**Reviewer**: Code Reviewer Agent v1.0  
**Date**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Status**: ${STATUS}

---

## Summary

Automated code review completed for ${FILE_PATH}.

**Overall Score**: ${SCORE}/100

- Total Checks: ${TOTAL_CHECKS}
- Passed: ${PASSED_CHECKS}
- Failed: ${FAILED_CHECKS}
- Warnings: ${WARNINGS}

---

## Level 1: Requirements Compliance

### Subtasks Implementation
EOF

# Parse subtasks from Work Unit and check if implemented
SUBTASK_COUNT=0
SUBTASK_PASSED=0

while IFS= read -r line; do
  if [[ $line =~ \"([^\"]+)\" ]]; then
    SUBTASK="${BASH_REMATCH[1]}"
    if [[ -n "$SUBTASK" && "$SUBTASK" != "subtasks" ]]; then
      ((SUBTASK_COUNT++))
      # Simple heuristic: check if key terms from subtask appear in code
      if echo "$CODE_CONTENT" | grep -qi "$(echo "$SUBTASK" | awk '{print $1}')" 2>/dev/null; then
        ((SUBTASK_PASSED++))
        echo "- [PASS] Subtask $SUBTASK_COUNT: $SUBTASK" >> "$OUTPUT_FILE"
      else
        echo "- [FAIL] Subtask $SUBTASK_COUNT: $SUBTASK" >> "$OUTPUT_FILE"
        echo "  - **Issue**: Implementation not found" >> "$OUTPUT_FILE"
      fi
    fi
  fi
done < <(echo "$WORK_UNIT_CONTENT" | grep -A 100 '"subtasks"' | grep -v "^\s*\]" | head -20)

if [[ $SUBTASK_COUNT -eq 0 ]]; then
  echo "- No subtasks found in Work Unit" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF

### Business Rules
EOF

# Check for business rules
for BR in BR001 BR002 BR003 BR004; do
  if echo "$WORK_UNIT_CONTENT" | grep -q "$BR"; then
    if echo "$CODE_CONTENT" | grep -q "$BR"; then
      echo "- [PASS] $BR: Referenced in code" >> "$OUTPUT_FILE"
    else
      echo "- [FAIL] $BR: Not found in code" >> "$OUTPUT_FILE"
    fi
  fi
done

cat >> "$OUTPUT_FILE" << EOF

**Requirements Score**: $(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))%

---

## Level 2: Code Quality

### Type Safety
EOF

if [[ "$FILE_EXT" == "ts" ]]; then
  if grep -q ": any" "$CODE_FILE"; then
    echo "- [FAIL] 'any' types detected" >> "$OUTPUT_FILE"
  else
    echo "- [PASS] No 'any' types found" >> "$OUTPUT_FILE"
  fi
  
  if grep -qE "async \w+\([^)]*\): Promise<" "$CODE_FILE"; then
    echo "- [PASS] Return types explicit" >> "$OUTPUT_FILE"
  else
    echo "- [WARNING] Some return types may be missing" >> "$OUTPUT_FILE"
  fi
fi

cat >> "$OUTPUT_FILE" << EOF

### Error Handling
EOF

if grep -q "try" "$CODE_FILE" && grep -q "catch" "$CODE_FILE"; then
  echo "- [PASS] Try-catch blocks present" >> "$OUTPUT_FILE"
else
  echo "- [FAIL] Missing error handling" >> "$OUTPUT_FILE"
fi

if grep -qi "logger\|logging" "$CODE_FILE"; then
  echo "- [PASS] Logging implemented" >> "$OUTPUT_FILE"
else
  echo "- [WARNING] Limited logging" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF

### Security
EOF

if grep -qi "password.*log\|log.*password" "$CODE_FILE"; then
  echo "- [CRITICAL] Password found in logs" >> "$OUTPUT_FILE"
else
  echo "- [PASS] No passwords in logs" >> "$OUTPUT_FILE"
fi

if grep -qi "bcrypt\|make_password\|hashers" "$CODE_FILE"; then
  echo "- [PASS] Password hashing detected" >> "$OUTPUT_FILE"
else
  echo "- [WARNING] Password hashing not detected" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF

**Quality Score**: ${SCORE}%

---

## Level 3: Framework Compliance

EOF

if [[ "$FILE_EXT" == "ts" ]]; then
  echo "### NestJS Standards" >> "$OUTPUT_FILE"
  
  if grep -q "@Injectable()" "$CODE_FILE"; then
    echo "- [PASS] @Injectable decorator present" >> "$OUTPUT_FILE"
  else
    echo "- [FAIL] Missing @Injectable decorator" >> "$OUTPUT_FILE"
  fi
  
  if grep -q "constructor" "$CODE_FILE"; then
    echo "- [PASS] Constructor injection used" >> "$OUTPUT_FILE"
  fi
  
  if grep -qE "NotFoundException|ConflictException|BadRequestException" "$CODE_FILE"; then
    echo "- [PASS] NestJS exceptions used" >> "$OUTPUT_FILE"
  fi
fi

cat >> "$OUTPUT_FILE" << EOF

**Framework Score**: ${SCORE}%

---

## Level 4: Performance

EOF

if grep -qi "pagina\|page\|limit" "$CODE_FILE"; then
  echo "- [PASS] Pagination implemented" >> "$OUTPUT_FILE"
else
  echo "- [INFO] No pagination detected (may not be required)" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF

**Performance Score**: ${SCORE}%

---

## Level 5: Maintainability

EOF

LINE_COUNT=$(wc -l < "$CODE_FILE" | tr -d ' ')
echo "- [INFO] File length: ${LINE_COUNT} lines" >> "$OUTPUT_FILE"

if [[ $LINE_COUNT -lt 300 ]]; then
  echo "- [PASS] File length acceptable" >> "$OUTPUT_FILE"
else
  echo "- [WARNING] File is long, consider splitting" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF

**Maintainability Score**: ${SCORE}%

---

## Critical Issues (Must Fix)

EOF

if [[ $FAILED_CHECKS -gt 0 ]]; then
  grep -qi "password.*log\|log.*password" "$CODE_FILE" && echo "1. SECURITY: Remove password from log statements" >> "$OUTPUT_FILE"
  grep -q "@Injectable" "$CODE_FILE" || echo "2. Missing @Injectable decorator on service class" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
else
  echo "None. All critical checks passed." >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF
---

## Warnings (Should Fix)

EOF

if [[ $WARNINGS -gt 0 ]]; then
  echo "1. Add comprehensive logging in all methods" >> "$OUTPUT_FILE"
  echo "2. Consider adding JSDoc comments for public methods" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
else
  echo "None." >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" << EOF
---

## Decision

**Status**: ${STATUS}

EOF

case "$STATUS" in
  APPROVED)
    echo "**Reason**: All critical checks passed. Code meets quality standards." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Next Steps**:" >> "$OUTPUT_FILE"
    echo "1. Developer reviews code" >> "$OUTPUT_FILE"
    echo "2. Developer commits and creates PR" >> "$OUTPUT_FILE"
    ;;
  NEEDS_REVISION)
    echo "**Reason**: Minor issues found. Requires corrections before approval." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Required Actions**:" >> "$OUTPUT_FILE"
    echo "1. Fix critical issues listed above" >> "$OUTPUT_FILE"
    echo "2. Re-run Executor Agent with feedback" >> "$OUTPUT_FILE"
    echo "3. Re-review after fixes" >> "$OUTPUT_FILE"
    ;;
  REJECTED)
    echo "**Reason**: Multiple critical issues found. Requires significant rework." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Required Actions**:" >> "$OUTPUT_FILE"
    echo "1. Fix all critical issues" >> "$OUTPUT_FILE"
    echo "2. Address warnings" >> "$OUTPUT_FILE"
    echo "3. Re-run Executor Agent with detailed feedback" >> "$OUTPUT_FILE"
    echo "4. Full re-review required" >> "$OUTPUT_FILE"
    ;;
esac

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**Overall Score**: ${SCORE}/100" >> "$OUTPUT_FILE"

# --- Success ---
echo ""
log "Code review completed!"
log "Output: $OUTPUT_FILE"
echo ""

# --- Summary ---
if [[ "$STATUS" == "APPROVED" ]]; then
  log "STATUS: ${GREEN}APPROVED${NC}"
  log "Code is ready for developer review!"
  echo ""
elif [[ "$STATUS" == "NEEDS_REVISION" ]]; then
  warn "STATUS: ${YELLOW}NEEDS_REVISION${NC}"
  warn "Minor corrections required"
else
  error "STATUS: ${RED}REJECTED${NC}"
  error "Significant issues found - rework needed"
fi

echo ""
info "REVIEW SUMMARY:"
info "  Work Unit: $WORK_UNIT_ID"
info "  File: $FILE_PATH"
info "  Score: $SCORE/100"
info "  Status: $STATUS"
info "  Critical Issues: $FAILED_CHECKS"
info "  Warnings: $WARNINGS"
echo ""

# Exit with status code
if [[ "$STATUS" == "APPROVED" ]]; then
  exit 0
elif [[ "$STATUS" == "NEEDS_REVISION" ]]; then
  exit 1
else
  exit 2
fi

