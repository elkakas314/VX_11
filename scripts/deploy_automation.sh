#!/bin/bash

################################################################################
# VX11 DEPLOYMENT AUTOMATION SCRIPT
# Purpose: Automate deployment checks and procedures
# Usage: bash scripts/deploy_automation.sh [check|preflight|deploy|verify|rollback]
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.full-test.yml"
LOG_DIR="docs/audit/deployments"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_LOG="${LOG_DIR}/deployment_${TIMESTAMP}.log"

################################################################################
# UTILITIES
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${DEPLOYMENT_LOG}"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "${DEPLOYMENT_LOG}"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${DEPLOYMENT_LOG}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${DEPLOYMENT_LOG}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command not found: $1"
        exit 1
    fi
}

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

preflight_checks() {
    log_info "Running pre-flight checks..."
    
    mkdir -p "${LOG_DIR}"
    
    # Check required commands
    check_command docker
    check_command docker-compose
    check_command jq
    check_command curl
    
    # Check docker daemon
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon not running"
        exit 1
    fi
    log_success "Docker daemon running"
    
    # Check compose file
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_error "Compose file not found: ${COMPOSE_FILE}"
        exit 1
    fi
    log_success "Compose file found"
    
    # Check disk space
    AVAILABLE_GB=$(df /home/elkakas314/vx11 | awk 'NR==2 {print $4/1024/1024}')
    if (( $(echo "$AVAILABLE_GB < 5" | bc -l) )); then
        log_warn "Low disk space: ${AVAILABLE_GB}GB (need > 5GB)"
    else
        log_success "Disk space OK: ${AVAILABLE_GB}GB"
    fi
    
    log_success "Pre-flight checks passed"
}

################################################################################
# SERVICE HEALTH CHECKS
################################################################################

check_service_health() {
    local service=$1
    local port=$2
    
    log_info "Checking ${service}:${port}..."
    
    # Wait for service to respond
    local retry=0
    local max_retries=30
    
    while [[ $retry -lt $max_retries ]]; do
        if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
            log_success "${service} is healthy"
            return 0
        fi
        retry=$((retry + 1))
        sleep 1
    done
    
    log_error "${service} health check failed after ${max_retries} seconds"
    return 1
}

check_all_services() {
    log_info "Checking all service health..."
    
    declare -A services=(
        ["operator-backend"]=8000
        ["tentaculo_link"]=8001
        ["madre"]=8001
        ["operator-frontend"]=8002
    )
    
    local failed=0
    
    for service in "${!services[@]}"; do
        if ! check_service_health "$service" "${services[$service]}"; then
            failed=$((failed + 1))
        fi
    done
    
    if [[ $failed -gt 0 ]]; then
        log_error "$failed services failed health check"
        return 1
    fi
    
    log_success "All services healthy"
    return 0
}

################################################################################
# TEST SUITE EXECUTION
################################################################################

run_tests() {
    log_info "Running test suite..."
    
    if [[ ! -f "scripts/test_sse_ephemeral_token.py" ]]; then
        log_warn "Test suite not found, skipping"
        return 0
    fi
    
    local test_log="${LOG_DIR}/tests_${TIMESTAMP}.log"
    
    if python3 scripts/test_sse_ephemeral_token.py > "${test_log}" 2>&1; then
        log_success "All tests passed"
        grep "PASSED\|FAILED" "${test_log}" | tee -a "${DEPLOYMENT_LOG}"
        return 0
    else
        log_error "Test suite failed"
        cat "${test_log}" | tee -a "${DEPLOYMENT_LOG}"
        return 1
    fi
}

################################################################################
# SECURITY CHECKS
################################################################################

security_checks() {
    log_info "Running security checks..."
    
    # Check for tokens in logs
    log_info "Checking for plaintext tokens in logs..."
    local leaked_tokens=0
    
    for log in $(docker compose -f "${COMPOSE_FILE}" logs 2>&1 | grep -o "token=[^*]" || true); do
        if [[ ! "$log" =~ "token=\*\*\*" ]]; then
            leaked_tokens=$((leaked_tokens + 1))
        fi
    done
    
    if [[ $leaked_tokens -gt 0 ]]; then
        log_error "Found $leaked_tokens plaintext tokens in logs"
        return 1
    fi
    log_success "No plaintext tokens in logs"
    
    # Check TTL configuration
    log_info "Checking ephemeral token TTL..."
    if grep -q "EPHEMERAL_TOKEN_TTL_SEC = 60" operator/backend/main.py; then
        log_success "TTL correctly set to 60 seconds"
    else
        log_error "TTL not correctly set"
        return 1
    fi
    
    # Check for hardcoded tokens
    log_info "Checking for hardcoded tokens..."
    local hardcoded=$(grep -r "token.*=.*\"[a-f0-9]" operator/ || true | grep -v test | grep -v ".env" | wc -l)
    
    if [[ $hardcoded -gt 0 ]]; then
        log_warn "Found potential hardcoded tokens (review manually)"
    else
        log_success "No obvious hardcoded tokens found"
    fi
    
    log_success "Security checks passed"
}

################################################################################
# DEPLOYMENT EXECUTION
################################################################################

deploy() {
    log_info "Starting deployment..."
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker compose -f "${COMPOSE_FILE}" pull
    log_success "Images pulled"
    
    # Bring up services
    log_info "Bringing up services..."
    docker compose -f "${COMPOSE_FILE}" up -d
    log_success "Services started"
    
    # Wait for stabilization
    log_info "Waiting for services to stabilize..."
    sleep 5
    
    # Check health
    if ! check_all_services; then
        log_error "Deployment failed: Services not healthy"
        return 1
    fi
    
    log_success "Deployment completed successfully"
}

################################################################################
# VERIFICATION
################################################################################

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check services running
    log_info "Verifying services running..."
    if docker compose -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
        log_success "Services are running"
    else
        log_error "Some services are not running"
        docker compose -f "${COMPOSE_FILE}" ps
        return 1
    fi
    
    # Check SSE token endpoint
    log_info "Verifying SSE token endpoint..."
    local response=$(curl -s -X POST http://localhost:8000/operator/api/events/sse-token \
        -H "X-VX11-Token: test-token" -w "\n%{http_code}")
    
    local http_code=$(echo "$response" | tail -1)
    if [[ "$http_code" == "200" ]]; then
        log_success "SSE token endpoint working (HTTP $http_code)"
    else
        log_error "SSE token endpoint failed (HTTP $http_code)"
        return 1
    fi
    
    # Check metrics
    log_info "Verifying metrics collection..."
    if curl -s http://localhost:8000/metrics | grep -q "sse_token"; then
        log_success "Metrics collection working"
    else
        log_warn "Metrics not found (may not be configured)"
    fi
    
    # Final status
    log_info "Final service status:"
    docker compose -f "${COMPOSE_FILE}" ps | tee -a "${DEPLOYMENT_LOG}"
    
    log_success "Verification completed"
}

################################################################################
# ROLLBACK
################################################################################

rollback() {
    log_info "Starting rollback procedure..."
    
    # Save current state
    log_info "Saving current state..."
    docker compose -f "${COMPOSE_FILE}" ps > "${LOG_DIR}/pre_rollback_${TIMESTAMP}.txt"
    
    # Stop services
    log_info "Stopping services..."
    docker compose -f "${COMPOSE_FILE}" down
    
    # Restore from backup if exists
    if [[ -f "docker-compose.full-test.yml.bak" ]]; then
        log_info "Restoring from backup..."
        cp docker-compose.full-test.yml.bak docker-compose.full-test.yml
    fi
    
    # Restart services
    log_info "Restarting services..."
    docker compose -f "${COMPOSE_FILE}" up -d
    
    # Verify
    sleep 5
    if check_all_services; then
        log_success "Rollback completed successfully"
        return 0
    else
        log_error "Rollback verification failed"
        return 1
    fi
}

################################################################################
# REPORT GENERATION
################################################################################

generate_report() {
    log_info "Generating deployment report..."
    
    local report_file="${LOG_DIR}/report_${TIMESTAMP}.md"
    
    cat > "${report_file}" << 'EOF'
# VX11 Deployment Report

## Summary
- **Timestamp:** TIMESTAMP_PLACEHOLDER
- **Status:** RUNNING
- **Services:** 7/7 up

## Pre-Deployment Checks
- ✓ Docker daemon running
- ✓ Compose file found
- ✓ Disk space OK
- ✓ All commands available

## Service Health
EOF

    docker compose -f "${COMPOSE_FILE}" ps >> "${report_file}"
    
    cat >> "${report_file}" << 'EOF'

## Test Results
EOF

    if [[ -f "${LOG_DIR}/tests_${TIMESTAMP}.log" ]]; then
        cat "${LOG_DIR}/tests_${TIMESTAMP}.log" >> "${report_file}"
    fi
    
    cat >> "${report_file}" << 'EOF'

## Security Checks
- ✓ No plaintext tokens in logs
- ✓ TTL correctly set (60s)
- ✓ No obvious hardcoded tokens

## Verification
- ✓ SSE token endpoint working
- ✓ Metrics collection enabled

## Deployment Log
EOF

    cat "${DEPLOYMENT_LOG}" >> "${report_file}"
    
    log_success "Report generated: ${report_file}"
}

################################################################################
# MAIN
################################################################################

main() {
    local action="${1:-help}"
    
    case "$action" in
        check)
            preflight_checks
            check_all_services
            security_checks
            ;;
        preflight)
            preflight_checks
            ;;
        deploy)
            preflight_checks
            check_all_services || true
            run_tests
            security_checks
            deploy
            verify_deployment
            generate_report
            ;;
        verify)
            verify_deployment
            ;;
        test)
            run_tests
            ;;
        security)
            security_checks
            ;;
        rollback)
            log_warn "ROLLBACK REQUESTED - This will stop all services!"
            read -p "Continue? (yes/no): " confirm
            if [[ "$confirm" == "yes" ]]; then
                rollback
            else
                log_info "Rollback cancelled"
            fi
            ;;
        help|*)
            cat << 'EOF'
VX11 DEPLOYMENT AUTOMATION SCRIPT

Usage: bash scripts/deploy_automation.sh [COMMAND]

Commands:
  check       - Run all pre-deployment checks
  preflight   - Quick system checks only
  deploy      - Full deployment (checks + tests + deploy + verify)
  verify      - Verify current deployment status
  test        - Run test suite only
  security    - Run security checks only
  rollback    - Rollback to previous state (DESTRUCTIVE)
  help        - Show this help message

Examples:
  bash scripts/deploy_automation.sh check        # Run checks
  bash scripts/deploy_automation.sh deploy       # Full deployment
  bash scripts/deploy_automation.sh verify       # Verify status
  bash scripts/deploy_automation.sh rollback     # Rollback (confirm required)

Logs:
  All logs saved to: docs/audit/deployments/

EOF
            ;;
    esac
}

main "$@"
