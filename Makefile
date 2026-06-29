# =============================================================================
# Wright — Developer Makefile for Docker Containerization
# =============================================================================

.PHONY: help docker-build docker-test docker-clean docker-logs docker-shell docker-test-e2e lint format typecheck test check security-scan docker-smoke alpha-release-check

# Default target displays help
help:
	@echo "Available Makefile targets:"
	@echo "  docker-build    - Build the production Docker image"
	@echo "  docker-test     - Start the container in test/dev mode (bind mounts enabled)"
	@echo "  docker-clean    - Stop containers and destroy test volumes"
	@echo "  docker-logs     - Follow the logs from the test container"
	@echo "  docker-shell    - Open an interactive shell inside the running container"
	@echo "  docker-test-e2e - Run Playwright UI tests against the built Docker image"
	@echo "  docker-smoke    - Build and smoke-test the production Docker image"
	@echo ""
	@echo "Local Developer Targets (Non-Docker):"
	@echo "  lint            - Run Ruff and ESLint checkers"
	@echo "  format          - Apply Ruff and Prettier code formatting"
	@echo "  typecheck       - Run Mypy and TSC type check validation"
	@echo "  test            - Run pytest and frontend vitest suites"
	@echo "  check           - Execute all local quality gates (lint + format + typecheck + test)"
	@echo "  security-scan   - Run public-alpha, Gitleaks, and TruffleHog secret scans"
	@echo "  alpha-release-check - Run final alpha release gates including Docker smoke"

docker-build:
	docker build -t wright-agent:latest -f docker/Dockerfile .

docker-smoke:
	./scripts/docker-smoke-test.sh

docker-test:
	@if [ ! -f docker/.env ]; then \
		echo "Warning: docker/.env does not exist. Copying from docker/.env.example..."; \
		cp docker/.env.example docker/.env; \
		echo "Please edit docker/.env with your LLM API credentials before running."; \
	fi
	docker compose -f docker-compose.test.yml up -d --build

docker-clean:
	docker compose -f docker-compose.test.yml down -v

docker-logs:
	docker compose -f docker-compose.test.yml logs -f

docker-shell:
	docker compose -f docker-compose.test.yml exec agent bash

docker-test-e2e:
	@echo "Setting up clean test environment..."
	docker compose -f docker-compose.test.yml down -v || true
	@if [ -f apps/api/state.db ]; then sqlite3 apps/api/state.db "DELETE FROM system_settings WHERE key = 'llm_api_url';"; fi
	@if [ -f docker/.env ]; then mv docker/.env docker/.env.bak; fi
	@echo "=== PHASE 1: Setup wizard test (unconfigured) ==="
	@cp docker/.env.example docker/.env
	@sed -i 's/^LLM_API_URL=.*/LLM_API_URL=/' docker/.env
	@echo "Starting container stack..."
	docker compose -f docker-compose.test.yml up -d --build
	@echo "Waiting for backend API to be ready..."
	@for i in {1..30}; do curl -s http://localhost:8080/api/health >/dev/null && break || sleep 1; done
	@echo "Waiting for Hermes agent service to be ready..."
	@for i in {1..30}; do curl -s http://localhost:8080/api/agent/health | grep -q '"state":"connected"' && break || sleep 1; done
	@echo "Running Playwright Setup Flow test..."
	@PLAYWRIGHT_BASE_URL=http://localhost:8080 npx playwright test tests/ui-integration/setup.spec.ts || (EXIT_VAL=$$?; make docker-clean; if [ -f docker/.env.bak ]; then mv docker/.env.bak docker/.env; fi; exit $$EXIT_VAL)
	@echo "=== PHASE 2: All other tests (configured) ==="
	docker compose -f docker-compose.test.yml down -v || true
	@sed -i 's/^LLM_API_URL=.*/LLM_API_URL=http:\/\/127.0.0.1:8080\/api\/health/' docker/.env
	@echo "Starting container stack with LLM_API_URL..."
	docker compose -f docker-compose.test.yml up -d --build
	@echo "Waiting for backend API to be ready..."
	@for i in {1..30}; do curl -s http://localhost:8080/api/health >/dev/null && break || sleep 1; done
	@echo "Waiting for Hermes agent service to be ready..."
	@for i in {1..30}; do curl -s http://localhost:8080/api/agent/health | grep -q '"state":"connected"' && break || sleep 1; done
	@echo "Running remaining Playwright integration tests..."
	@PLAYWRIGHT_BASE_URL=http://localhost:8080 npx playwright test --grep-invert "LLM Setup Flow" || (EXIT_VAL=$$?; make docker-clean; if [ -f docker/.env.bak ]; then mv docker/.env.bak docker/.env; fi; exit $$EXIT_VAL)
	@echo "Restoring original .env..."
	@make docker-clean
	@if [ -f docker/.env.bak ]; then mv docker/.env.bak docker/.env; fi
	@echo "E2E tests passed."

docker-test-live:
	@echo "Setting up unmocked live test environment..."
	docker compose -f docker-compose.test.yml down -v || true
	@if [ -f apps/api/state.db ]; then sqlite3 apps/api/state.db "DELETE FROM system_settings WHERE key = 'llm_api_url';"; fi
	@if [ -f docker/.env ]; then mv docker/.env docker/.env.bak; fi
	@cp docker/.env.example docker/.env
	@sed -i 's|^LLM_API_URL=.*|LLM_API_URL=http://promaxgb10-5c88:8000/v1|' docker/.env
	@echo "Starting container stack with Real LLM URL..."
	docker compose -f docker-compose.test.yml up -d --build
	@echo "Waiting for containers to be ready..."
	@for i in {1..30}; do curl -s http://127.0.0.1:8080/api/health >/dev/null && break || sleep 1; done
	@echo "Running Live Unmocked E2E test..."
	@PLAYWRIGHT_BASE_URL=http://127.0.0.1:8080 npx playwright test --config=playwright.live.config.ts tests/e2e-live/live-chat.spec.ts
	@echo "Cleaning up..."
	@make docker-clean
	@if [ -f docker/.env.bak ]; then mv docker/.env.bak docker/.env; fi
	@echo "Live E2E tests passed!"

# Local Developer Targets (Non-Docker)
lint:
	uv run ruff check apps/api/ packages/
	npx -w apps/web eslint .

format:
	uv run ruff format apps/api/ packages/
	npx prettier --write apps/web/

typecheck:
	uv run pip install mypy --quiet
	uv run mypy apps/api/ packages/ --ignore-missing-imports || echo "Mypy checks failed (warning only)"
	npx tsc --noEmit -p apps/web/tsconfig.app.json

test:
	uv run pytest
	npm run test --workspace=apps/web

check:
	uv run ruff check apps/api/ packages/
	npx -w apps/web eslint .
	uv run ruff format --check apps/api/ packages/
	npx prettier --check apps/web/
	uv run pip install mypy --quiet
	uv run mypy apps/api/ packages/ --ignore-missing-imports || echo "Mypy checks failed (warning only)"
	npx tsc --noEmit -p apps/web/tsconfig.app.json
	uv run pytest
	npm run test --workspace=apps/web

security-scan:
	./scripts/security-scan.sh --include-untracked

alpha-release-check:
	./scripts/alpha-release-check.sh

