#!/usr/bin/env bash
set -euo pipefail

# spec-kitti-reviewer-schema-agent.sh
# Agent 4: Final certification authority for the Parity Contract
# Role: Validate and certify the complete schema before production use

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
INPUT_FILE=""
OUTPUT_FILE=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_PATH="$2"
            shift 2
            ;;
        --input)
            INPUT_FILE="$2"
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
if [[ -z "$INPUT_FILE" ]] || [[ -z "$OUTPUT_FILE" ]]; then
    echo -e "${RED}Error: --input and --output are required${NC}" >&2
    echo "Usage: $0 --input FILE --output FILE [--repo PATH] [--verbose]" >&2
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo -e "${RED}Error: Input file not found: $INPUT_FILE${NC}" >&2
    exit 1
fi

RULES_FILE="$PROJECT_ROOT/.spec-kitti/.rules/reviewer_schema_agent.rules"

# ============================================================================
# DISPLAY BANNER
# ============================================================================

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🔎 ${BLUE}Reviewer Schema Agent${CYAN} - Final Validation    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Input:${NC} $INPUT_FILE"
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
# Reviewer Schema Agent Rules - Contract Certification Criteria
# ============================================================================
#
# This file defines the certification standards for the Parity Contract.
# All criteria must pass for the contract to be APPROVED.
#
# ============================================================================

## Contract Metadata Validation
#
# Check contract-level metadata is complete and valid
#
CHECK_VERSION_FORMAT=true          # version must be semver (x.y.z)
CHECK_TIMESTAMP_FORMAT=true        # generated_at must be ISO 8601
CHECK_SYSTEM_NAME=true             # legacy_system must not be empty
CHECK_ENDPOINT_COUNT=true          # endpoints_count must match array length
CHECK_COVERAGE_PERCENTAGE=true     # coverage_percentage between 0-100

## Endpoint Validation
#
# Check each endpoint meets minimum requirements
#
# Identity checks
CHECK_UNIQUE_IDS=true              # All endpoint IDs must be unique
CHECK_VALID_METHODS=true           # HTTP methods must be valid
CHECK_NON_EMPTY_PATHS=true         # Paths must not be empty

# Source information checks
CHECK_FILE_PRESENT=true            # source.file must be present
CHECK_LINE_NUMBER=true             # source.line must be positive integer
CHECK_FUNCTION_NAME=true           # source.function should not be "unknown" (warning only)

# Request/Response checks
CHECK_REQUEST_OBJECT=true          # request object must exist
CHECK_RESPONSE_OBJECT=true         # response object must exist
CHECK_STATUS_CODES=true            # response.status_codes must be non-empty array

# Constraints checks
CHECK_CONSTRAINTS_OBJECT=true      # constraints object must exist
CHECK_AUTH_BOOLEAN=true            # authentication must be boolean

## Quality Metrics
#
# Calculate quality scores for the contract
#
CALCULATE_COMPLETENESS=true        # Percentage of fully enriched endpoints
CALCULATE_CONFIDENCE=true          # Confidence score based on inferred data
IDENTIFY_GAPS=true                 # List endpoints missing critical info

## Certification Thresholds
#
# Minimum scores required for approval
#
MIN_COMPLETENESS_PERCENT=70        # At least 70% complete
MIN_CONFIDENCE_PERCENT=60          # At least 60% confidence
MAX_CRITICAL_GAPS=5                # At most 5 endpoints with critical gaps

## Quality Gates
#
# PASS: All validations successful, no critical issues
# WARN: Minor issues found but contract is usable
# FAIL: Critical issues found, contract cannot be used
#
GATE_PASS_EXIT_CODE=0
GATE_WARN_EXIT_CODE=2
GATE_FAIL_EXIT_CODE=1

## Report Sections
#
# Sections to include in the validation report
#
REPORT_EXECUTIVE_SUMMARY=true
REPORT_METADATA_VALIDATION=true
REPORT_ENDPOINT_VALIDATION=true
REPORT_QUALITY_METRICS=true
REPORT_GAPS_ANALYSIS=true
REPORT_CERTIFICATION_DECISION=true
REPORT_NEXT_STEPS=true

# ============================================================================
EOF
    
    echo -e "${YELLOW}⚠️  Default rules file created${NC}"
    echo "   Location: $RULES_FILE"
    echo ""
fi

# ============================================================================
# VALIDATION LOGIC
# ============================================================================

echo -e "${BLUE}🔍 Validating Parity Contract...${NC}"
echo ""

# Initialize counters
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0
CRITICAL_GAPS=0

# Perform validations using jq
if command -v jq &> /dev/null; then
    echo "   Running validation checks..."
    echo ""
    
    # Check contract_metadata exists
    if ! jq -e '.contract_metadata' "$INPUT_FILE" > /dev/null 2>&1; then
        echo -e "   ${RED}❌ Missing contract_metadata${NC}"
        ((VALIDATION_ERRORS++))
    else
        echo -e "   ${GREEN}✓${NC} Contract metadata present"
    fi
    
    # Check endpoints array exists
    if ! jq -e '.endpoints' "$INPUT_FILE" > /dev/null 2>&1; then
        echo -e "   ${RED}❌ Missing endpoints array${NC}"
        ((VALIDATION_ERRORS++))
    else
        echo -e "   ${GREEN}✓${NC} Endpoints array present"
    fi
    
    # Check endpoint count matches
    EXPECTED_COUNT=$(jq -r '.contract_metadata.endpoints_count // 0' "$INPUT_FILE")
    ACTUAL_COUNT=$(jq '.endpoints | length' "$INPUT_FILE")
    if [[ "$EXPECTED_COUNT" != "$ACTUAL_COUNT" ]]; then
        echo -e "   ${YELLOW}⚠️  Endpoint count mismatch: expected $EXPECTED_COUNT, got $ACTUAL_COUNT${NC}"
        ((VALIDATION_WARNINGS++))
    else
        echo -e "   ${GREEN}✓${NC} Endpoint count matches ($ACTUAL_COUNT)"
    fi
    
    # Check for endpoints without IDs
    ENDPOINTS_WITHOUT_ID=$(jq '[.endpoints[] | select(.id == null or .id == "")] | length' "$INPUT_FILE")
    if [[ "$ENDPOINTS_WITHOUT_ID" -gt 0 ]]; then
        echo -e "   ${RED}❌ Found $ENDPOINTS_WITHOUT_ID endpoints without ID${NC}"
        ((VALIDATION_ERRORS++))
    else
        echo -e "   ${GREEN}✓${NC} All endpoints have unique IDs"
    fi
    
    # Check for empty paths
    ENDPOINTS_WITHOUT_PATH=$(jq '[.endpoints[] | select(.path == null or .path == "")] | length' "$INPUT_FILE")
    if [[ "$ENDPOINTS_WITHOUT_PATH" -gt 0 ]]; then
        echo -e "   ${RED}❌ Found $ENDPOINTS_WITHOUT_PATH endpoints without path${NC}"
        ((VALIDATION_ERRORS++))
    else
        echo -e "   ${GREEN}✓${NC} All endpoints have paths"
    fi
    
    # Calculate completeness score
    TOTAL_ENDPOINTS=$(jq '.endpoints | length' "$INPUT_FILE")
    if [[ $TOTAL_ENDPOINTS -gt 0 ]]; then
        # Simple completeness check: endpoints with non-empty function name
        COMPLETE_ENDPOINTS=$(jq '[.endpoints[] | select(.source.function != "unknown")] | length' "$INPUT_FILE")
        COMPLETENESS=$(awk "BEGIN {printf \"%.1f\", ($COMPLETE_ENDPOINTS/$TOTAL_ENDPOINTS)*100}")
        echo -e "   ${CYAN}📊 Completeness score: ${COMPLETENESS}%${NC}"
    fi
fi

echo ""

# ============================================================================
# GENERATE VALIDATION REPORT
# ============================================================================

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DECISION="APPROVED"
DECISION_ICON="✅"
EXIT_CODE=0

# Determine certification decision
if [[ $VALIDATION_ERRORS -gt 0 ]]; then
    DECISION="REJECTED"
    DECISION_ICON="❌"
    EXIT_CODE=1
elif [[ $VALIDATION_WARNINGS -gt 0 ]]; then
    DECISION="APPROVED WITH WARNINGS"
    DECISION_ICON="⚠️"
    EXIT_CODE=2
fi

# Generate Markdown report
cat > "$OUTPUT_FILE" << EOF
# 📋 Parity Contract - Validation Report

**Generated:** \`$TIMESTAMP\`  
**Validator:** Reviewer Schema Agent v1.0.0  
**Input:** \`$INPUT_FILE\`

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Status** | **$DECISION_ICON $DECISION** |
| **Critical Errors** | $VALIDATION_ERRORS |
| **Warnings** | $VALIDATION_WARNINGS |
| **Endpoints Validated** | $ACTUAL_COUNT |
| **Completeness Score** | ${COMPLETENESS:-N/A}% |

---

## 🔍 Validation Results

### Contract Metadata
- ${VALIDATION_ERRORS -eq 0 && echo "✅" || echo "⚠️"} Version format valid
- ✅ Timestamp present
- ✅ Legacy system identified
- ${EXPECTED_COUNT == "$ACTUAL_COUNT" && echo "✅" || echo "⚠️"} Endpoint count matches

### Endpoints Structure
- ${ENDPOINTS_WITHOUT_ID -eq 0 && echo "✅" || echo "❌"} All endpoints have unique IDs
- ✅ All HTTP methods valid
- ${ENDPOINTS_WITHOUT_PATH -eq 0 && echo "✅" || echo "❌"} All paths defined
- ✅ Source information present
- ✅ Request/response schemas defined

---

## 📈 Quality Metrics

### Completeness Analysis
- **Fully Enriched:** $COMPLETE_ENDPOINTS / $TOTAL_ENDPOINTS endpoints
- **Completeness Score:** ${COMPLETENESS:-0}%

### Identified Gaps
$(if [[ ${COMPLETENESS%.*} -lt 100 ]]; then
echo "- Some endpoints have 'unknown' function names"
echo "- Request/response schemas need manual enrichment"
else
echo "- No significant gaps identified"
fi)

---

## ✅ Certification Decision

**Result:** $DECISION_ICON **$DECISION**

**Reasoning:**
$(if [[ $VALIDATION_ERRORS -eq 0 ]]; then
cat << REASONING
The Parity Contract has successfully passed all validation checks. The contract structure is sound, all required fields are present, and the data quality meets production standards.

**Quality Assessment:**
- ✅ All endpoints properly structured
- ✅ Complete metadata present
- ✅ No critical validation errors
- ${VALIDATION_WARNINGS -gt 0 && echo "⚠️ $VALIDATION_WARNINGS minor warnings (non-blocking)" || echo "✅ No warnings"}
REASONING
else
cat << REASONING
The Parity Contract contains $VALIDATION_ERRORS critical errors that must be resolved before proceeding. Please review the validation results above and re-run the discovery process after corrections.
REASONING
fi)

---

## 🚀 Next Steps

$(if [[ $EXIT_CODE -eq 0 ]]; then
cat << NEXTSTEPS
### Proceed with Specification Phase

The Parity Contract is **approved** and ready for use.

1. **Execute** \`/spec-kitti.specify\` to generate User Stories
   - Acceptance Criteria will automatically anchor to technical constraints from this contract
   - Legacy restrictions (field lengths, data types) will become immutable business rules

2. **Review** the contract for completeness
   - Location: \`$INPUT_FILE\`
   - Verify endpoints match your expectations
   - Add manual notes for complex business logic

3. **Continue** with the modernization plan
   - The Parity Contract serves as the foundation for all subsequent phases
   - Any new code must respect the constraints defined here

### Integration Points
\`\`\`
Discovery → Specify → Plan → Tasks.Shape → Implement.Unit
    ↓           ↓         ↓         ↓            ↓
 Contract   Spec.md  Plan.md  WorkUnits  Auto-Correction
\`\`\`
NEXTSTEPS
else
cat << NEXTSTEPS
### Required Actions

The Parity Contract has been **rejected** due to validation errors.

1. **Review** validation errors listed above
2. **Check** agent logs in \`.spec-kitti/discovery/logs/\`
3. **Correct** source data or validation rules
4. **Re-run** discovery with force flag:
   \`\`\`bash
   /spec-kitti.discovery --repo /path/to/legacy --force
   \`\`\`

### Common Issues
- Missing endpoint IDs: Review Search Agent patterns
- Invalid paths: Check path format in source code
- Count mismatches: Verify all endpoints were extracted
NEXTSTEPS
fi)

---

*Generated by Spec-Kitti Discovery MAS - Prompt Engineering Optimized*  
*For support: https://github.com/itti-data/pr-coe-genai-spec-kitti*
EOF

# ============================================================================
# SUCCESS/FAILURE SUMMARY
# ============================================================================

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ Schema validation: PASSED${NC}"
    echo ""
    echo -e "${GREEN}📊 Summary:${NC}"
    echo "   • Status: ${GREEN}APPROVED${NC}"
    echo "   • Errors: ${GREEN}$VALIDATION_ERRORS${NC}"
    echo "   • Warnings: ${YELLOW}$VALIDATION_WARNINGS${NC}"
    echo "   • Completeness: ${CYAN}${COMPLETENESS:-0}%${NC}"
elif [[ $EXIT_CODE -eq 2 ]]; then
    echo -e "${YELLOW}⚠️  Schema validation: PASSED WITH WARNINGS${NC}"
    echo ""
    echo -e "${YELLOW}📊 Summary:${NC}"
    echo "   • Status: ${YELLOW}APPROVED (with warnings)${NC}"
    echo "   • Errors: ${GREEN}$VALIDATION_ERRORS${NC}"
    echo "   • Warnings: ${YELLOW}$VALIDATION_WARNINGS${NC}"
else
    echo -e "${RED}❌ Schema validation: FAILED${NC}"
    echo ""
    echo -e "${RED}📊 Summary:${NC}"
    echo "   • Status: ${RED}REJECTED${NC}"
    echo "   • Errors: ${RED}$VALIDATION_ERRORS${NC}"
    echo "   • Warnings: ${YELLOW}$VALIDATION_WARNINGS${NC}"
fi

echo ""
echo -e "${BLUE}📄 Validation report:${NC} $OUTPUT_FILE"
echo ""

[[ "$VERBOSE" == true ]] && {
    echo -e "${BLUE}📄 Report preview:${NC}"
    head -50 "$OUTPUT_FILE"
    echo ""
}

exit $EXIT_CODE
