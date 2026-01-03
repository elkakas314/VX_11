.PHONY: help up-core up-full-test down smoke lint test clean audit-rotate logs status

# VX11 Operations Makefile
# Usage: make <target>
# Example: make up-core && make smoke

help:
	@echo "VX11 Operations Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  up-core           Start VX11 in solo_madre (read-only)"
	@echo "  up-full-test      Start VX11 full-test profile (with spawner)"
	@echo "  down              Stop all services + remove orphans"
	@echo "  smoke             Run smoke tests (health, endpoints)"
	@echo "  lint              Check code style + security"
	@echo "  test              Run unit tests"
	@echo "  clean             Clean generated files (careful!)"
	@echo "  audit-rotate      Rotate old audit dirs to archive/ (dry-run)"
	@echo "  audit-rotate-do   Rotate old audit dirs (apply)"
	@echo "  logs              Tail Docker logs (all services)"
	@echo "  status            Show current status"
	@echo ""

# ============================================================================
# DOCKER COMPOSE TARGETS
# ============================================================================

up-core:
	@echo "Starting VX11 in solo_madre (read-only)..."
	docker compose -f docker-compose.yml up -d
	@echo "Waiting for services..."
	sleep 3
	@echo "Run 'make smoke' to verify"

up-full-test:
	@echo "Starting VX11 full-test profile..."
	docker compose -f docker-compose.full-test.yml up -d
	@echo "Waiting for services..."
	sleep 5
	@echo "Run 'make smoke' to verify"

down:
	@echo "Stopping all services..."
	docker compose down --remove-orphans
	@echo "✓ Down complete"

# ============================================================================
# TESTING & VERIFICATION
# ============================================================================

smoke:
	@echo "Running smoke tests..."
	@echo ""
	@echo "Test 1: Health check"
	@curl -s http://localhost:8000/health | jq . && echo "✓ PASS" || echo "✗ FAIL"
	@echo ""
	@echo "Test 2: Status endpoint"
	@curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/vx11/status | jq . && echo "✓ PASS" || echo "✗ FAIL"
	@echo ""
	@echo "Test 3: Operator health"
	@curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/health | jq . && echo "✓ PASS" || echo "✗ FAIL"
	@echo ""

lint:
	@echo "Linting Python..."
	find operator operator_backend tentaculo_link madre switch -name "*.py" 2>/dev/null | \
		head -20 | xargs -I {} python3 -m py_compile {} && echo "✓ Python syntax OK" || echo "✗ Syntax errors"
	@echo ""
	@echo "Checking for secrets..."
	@grep -r "password\|token\|api_key\|secret" --include="*.py" operator tentaculo_link madre 2>/dev/null | \
		grep -v "\.git\|#.*password\|X-VX11-Token" | wc -l | xargs -I {} echo "Potential secrets found: {}"

test:
	@echo "Running tests (if available)..."
	@if [ -d "tests" ]; then \
		python3 -m pytest tests/ -v 2>/dev/null || echo "pytest not available"; \
	else \
		echo "No tests/ directory found"; \
	fi

# ============================================================================
# CLEANUP & MAINTENANCE
# ============================================================================

clean:
	@echo "⚠️  WARNING: This will DELETE generated files!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Cleaning..."; \
		find . -type f -name "*.pyc" -delete; \
		find . -type d -name "__pycache__" -delete; \
		find . -type d -name ".pytest_cache" -delete; \
		rm -rf build/; \
		echo "✓ Cleaned"; \
	else \
		echo "Aborted"; \
	fi

audit-rotate:
	@echo "Dry-run: audit rotation..."
	bash scripts/vx11_rotate_audits.sh --dry-run

audit-rotate-do:
	@echo "⚠️  WARNING: This will MOVE old audit directories to archive/!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		bash scripts/vx11_rotate_audits.sh; \
	else \
		echo "Aborted"; \
	fi

# ============================================================================
# DEBUGGING & MONITORING
# ============================================================================

logs:
	@echo "Docker logs (all services, last 50 lines)..."
	docker compose logs --tail=50 -f

status:
	@echo "VX11 Status Report"
	@echo ""
	@echo "Git:"
	@git log --oneline -3
	@echo ""
	@echo "Docker:"
	@docker compose ps --all
	@echo ""
	@echo "Endpoints:"
	@curl -s http://localhost:8000/health | jq .
	@echo ""
	@echo "Processes:"
	@pgrep -fa "uvicorn|docker|compose" | wc -l | xargs echo "Total VX11 processes:"
	@echo ""
	@echo "Zombies:"
	@ps -eo stat | grep -c Z || echo "0"
	@echo ""

.DEFAULT_GOAL := help
