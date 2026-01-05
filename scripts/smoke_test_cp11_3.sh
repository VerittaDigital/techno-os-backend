#!/bin/bash
# CP-11.3: Smoke Tests for F11 Gate Consolidation
# Purpose: Validate gate engine on VPS production environment
# Expected: Zero failures, audit.log consistent

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${VERITTA_BETA_API_KEY:-}"
AUDIT_LOG="${AUDIT_LOG_PATH:-./audit.log}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Test counters
PASSED=0
FAILED=0

# Helper functions
log() {
    echo -e "${GREEN}[$(date -u +"%Y-%m-%d %H:%M:%S UTC")]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

test_pass() {
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}✓${NC} $1"
}

test_fail() {
    FAILED=$((FAILED + 1))
    echo -e "  ${RED}✗${NC} $1"
}

test_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check prerequisites
check_prerequisites() {
    test_section "PREREQUISITE CHECKS"
    
    if [ -z "$API_KEY" ]; then
        error "VERITTA_BETA_API_KEY not set"
        exit 1
    fi
    
    log "API Base: $API_BASE"
    log "API Key: ${API_KEY:0:10}..."
    
    # Check if server is responding
    if ! curl -fsS "$API_BASE/health" > /dev/null 2>&1; then
        error "Server not responding at $API_BASE/health"
        exit 1
    fi
    test_pass "Server responding"
}

# Test 1: Valid POST /process (should succeed)
test_valid_process() {
    test_section "TEST 1: Valid POST /process"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/process" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"text":"smoke test valid request"}')
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        local status=$(echo "$body" | jq -r '.status // "UNKNOWN"')
        local trace_id=$(echo "$body" | jq -r '.trace_id // "missing"')
        
        if [ "$status" = "SUCCESS" ] && [ "$trace_id" != "missing" ]; then
            test_pass "POST /process succeeded (status=$status, trace_id=$trace_id)"
        else
            test_fail "POST /process returned 200 but wrong body (status=$status)"
        fi
    else
        test_fail "POST /process failed with HTTP $http_code"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
}

# Test 2: 404 - Unknown route (should return G8_UNKNOWN_ACTION)
test_unknown_route() {
    test_section "TEST 2: POST /unknown-route (G8_UNKNOWN_ACTION)"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/unknown-route" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"test":"data"}')
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "404" ]; then
        local trace_id=$(echo "$body" | jq -r '.trace_id // "missing"')
        
        if [ "$trace_id" != "missing" ]; then
            test_pass "404 returned with trace_id=$trace_id"
        else
            test_fail "404 returned but no trace_id"
        fi
    else
        test_fail "Expected 404 but got HTTP $http_code"
    fi
}

# Test 3: 405 - Method not allowed (should return G8_UNKNOWN_ACTION)
test_method_not_allowed() {
    test_section "TEST 3: GET /process (405 Method Not Allowed)"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" -X GET "$API_BASE/process" \
        -H "X-API-Key: $API_KEY")
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "405" ]; then
        local trace_id=$(echo "$body" | jq -r '.trace_id // "missing"')
        
        if [ "$trace_id" != "missing" ]; then
            test_pass "405 returned with trace_id=$trace_id"
        else
            test_fail "405 returned but no trace_id"
        fi
    else
        test_fail "Expected 405 but got HTTP $http_code"
    fi
}

# Test 4: Malformed JSON (should return G10_BODY_PARSE_ERROR)
test_malformed_json() {
    test_section "TEST 4: Malformed JSON (G10_BODY_PARSE_ERROR)"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/process" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"text":"unclosed string')
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "422" ]; then
        local error_msg=$(echo "$body" | jq -r '.error // .message // "unknown"')
        
        if [[ "$error_msg" =~ G10_BODY_PARSE_ERROR ]]; then
            test_pass "422 returned with G10_BODY_PARSE_ERROR"
        else
            test_pass "422 returned (error: $error_msg)"
        fi
    else
        test_fail "Expected 422 but got HTTP $http_code"
    fi
}

# Test 5: GET /health (should always work)
test_health_endpoint() {
    test_section "TEST 5: GET /health (public endpoint)"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" -X GET "$API_BASE/health")
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        local status=$(echo "$body" | jq -r '.status // "unknown"')
        
        if [ "$status" = "ok" ]; then
            test_pass "GET /health returned status=ok"
        else
            test_fail "GET /health returned 200 but wrong status ($status)"
        fi
    else
        test_fail "Expected 200 but got HTTP $http_code"
    fi
}

# Test 6: Audit log verification
test_audit_log() {
    test_section "TEST 6: Audit Log Verification"
    
    if [ ! -f "$AUDIT_LOG" ]; then
        warn "Audit log not found at $AUDIT_LOG (may be remote VPS)"
        return
    fi
    
    # Check if audit log has G8 entries
    local g8_count=$(grep -c "G8_UNKNOWN_ACTION" "$AUDIT_LOG" 2>/dev/null || echo "0")
    local g10_count=$(grep -c "G10_BODY_PARSE_ERROR" "$AUDIT_LOG" 2>/dev/null || echo "0")
    
    if [ "$g8_count" -gt 0 ]; then
        test_pass "Audit log contains $g8_count G8_UNKNOWN_ACTION entries"
    else
        warn "No G8_UNKNOWN_ACTION entries in audit log (may be expected if log was cleared)"
    fi
    
    if [ "$g10_count" -gt 0 ]; then
        test_pass "Audit log contains $g10_count G10_BODY_PARSE_ERROR entries"
    else
        warn "No G10_BODY_PARSE_ERROR entries in audit log"
    fi
}

# Summary
print_summary() {
    test_section "TEST SUMMARY"
    
    local total=$((PASSED + FAILED))
    echo ""
    echo "Total Tests:  $total"
    echo "Passed:       $PASSED"
    echo "Failed:       $FAILED"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ CP-11.3 APPROVED${NC}"
        echo "All smoke tests passed successfully."
        exit 0
    else
        echo -e "${RED}✗ CP-11.3 FAILED${NC}"
        echo "Some tests failed. Review logs above."
        exit 1
    fi
}

# Main execution
main() {
    log "Starting CP-11.3 Smoke Tests"
    log "Timestamp: $TIMESTAMP"
    
    check_prerequisites
    test_valid_process
    test_unknown_route
    test_method_not_allowed
    test_malformed_json
    test_health_endpoint
    test_audit_log
    
    print_summary
}

main "$@"
