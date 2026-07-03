# =============================================================================
# Wright — Developer Makefile for Docker Containerization
# =============================================================================

.PHONY: help docker-build docker-test docker-clean docker-logs docker-shell docker-test-e2e lint format typecheck test test-external-freecad check check-dev-merge check-prod-merge security-scan docker-smoke hermes-plugin-install-test hermes-plugin-uninstall-test hermes-plugin-update-test hermes-plugin-lifecycle-test alpha-release-check python-package-build-check hermes-plugin-mirror-sync-dry-run hermes-plugin-mirror-validate hermes-plugin-root-lifecycle-test

PYTHON_WORKSPACE_PATHS := apps/api packages/core packages/agent_adapters packages/tool_registry packages/data_vault packages/workspace_service

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
	@echo "  test-external-freecad - Run opt-in FreeCAD MCP package tests"
	@echo "  check           - Execute all local quality gates (lint + format + typecheck + test)"
	@echo "  check-dev-merge - Run the CI-equivalent gate before merging to dev"
	@echo "  check-prod-merge - Run the release gate before merging dev to main"
	@echo "  security-scan   - Run public-alpha, Gitleaks, and TruffleHog secret scans"
	@echo "  alpha-release-check - Run final alpha release gates including Docker smoke"
	@echo "  python-package-build-check - Validate Wright package metadata for PyPI/TestPyPI"
	@echo "  hermes-plugin-mirror-sync-dry-run - Preview thin Hermes plugin mirror contents"
	@echo "  hermes-plugin-mirror-validate - Generate and validate a local thin plugin mirror"
	@echo "  hermes-plugin-root-lifecycle-test - Test Hermes install/update/remove from the mirror root"

docker-build:
	docker build -t wright-agent:latest -f docker/Dockerfile .

docker-smoke:
	./scripts/docker-smoke-test.sh

hermes-plugin-install-test:
	./scripts/test-hermes-plugin-install.sh

hermes-plugin-uninstall-test:
	./scripts/test-hermes-plugin-uninstall.sh

hermes-plugin-update-test:
	./scripts/test-hermes-plugin-update.sh

hermes-plugin-lifecycle-test: hermes-plugin-install-test hermes-plugin-uninstall-test hermes-plugin-update-test

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
	uv run ruff check $(PYTHON_WORKSPACE_PATHS)
	npx -w apps/web eslint .

format:
	uv run ruff format $(PYTHON_WORKSPACE_PATHS)
	npx prettier --write apps/web/

typecheck:
	uv run pip install mypy --quiet
	uv run mypy $(PYTHON_WORKSPACE_PATHS) --ignore-missing-imports || echo "Mypy checks failed (warning only)"
	npx tsc --noEmit -p apps/web/tsconfig.app.json

test:
	uv run pytest
	uv run --package hermes-plugin-wright pytest hermes-plugin-wright/tests
	npm run test --workspace=apps/web

test-external-freecad:
	cd packages/freecad_mcp && uv run pytest

check:
	uv run ruff check $(PYTHON_WORKSPACE_PATHS)
	npx -w apps/web eslint .
	uv run ruff format --check $(PYTHON_WORKSPACE_PATHS)
	npx prettier --check apps/web/
	uv run pip install mypy --quiet
	uv run mypy $(PYTHON_WORKSPACE_PATHS) --ignore-missing-imports || echo "Mypy checks failed (warning only)"
	npx tsc --noEmit -p apps/web/tsconfig.app.json
	uv run pytest
	uv run --package hermes-plugin-wright pytest hermes-plugin-wright/tests
	npm run test --workspace=apps/web

check-dev-merge:
	./scripts/check-dev-merge.sh

check-prod-merge:
	./scripts/check-prod-merge.sh

security-scan:
	./scripts/security-scan.sh --include-untracked

alpha-release-check:
	./scripts/alpha-release-check.sh


python-package-build-check:
	./scripts/build-python-distributions.sh --dry-run packages/core packages/tool_registry

hermes-plugin-mirror-sync-dry-run:
	./scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --dry-run

hermes-plugin-mirror-validate:
	@tmp_dir=$$(mktemp -d "$${TMPDIR:-/tmp}/wright-plugin-mirror.XXXXXX"); \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	./scripts/sync-hermes-plugin-mirror.sh --source hermes-plugin-wright --mirror-url https://github.com/burhop/hermes-plugin-wright --branch dev --channel development --output-dir "$$tmp_dir"; \
	./scripts/validate-hermes-plugin-mirror.sh --mirror-dir "$$tmp_dir" --channel development

hermes-plugin-root-lifecycle-test:
	./scripts/test-hermes-plugin-install.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
	./scripts/test-hermes-plugin-update.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
	./scripts/test-hermes-plugin-uninstall.sh --mirror-root --repo-url https://github.com/burhop/hermes-plugin-wright --ref dev
