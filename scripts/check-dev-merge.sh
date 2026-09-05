#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNBOOK="docs/contributing/dev-push-runbook.md"
API_PORT="${WRIGHT_GATE_API_PORT:-18000}"
UI_PORT="${WRIGHT_GATE_UI_PORT:-15173}"
GATE_VENV="${WRIGHT_GATE_VENV:-$ROOT_DIR/.venv-dev-gate}"
export UV_PROJECT_ENVIRONMENT="$GATE_VENV"
export UV_PYTHON="${WRIGHT_GATE_PYTHON:-3.13}"
if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  GATE_PYTHON="$GATE_VENV/Scripts/python.exe"
else
  GATE_PYTHON="$GATE_VENV/bin/python"
fi
PYTHON_WORKSPACE_PATHS=(
  src/wright_engineering
  scripts/release
  scripts/validate-engineering-process-program.py
  scripts/program_control
  tests/program_control_plane
  scripts/build-native-runtime.py
  scripts/test-native-hermes-install.py
  scripts/test-published-native-hermes.py
  scripts/activate-hermes-package-channel.py
  apps/api
  packages/core
  packages/agent_adapters
  packages/tool_registry
  packages/data_vault
  packages/workspace_service
)

run() {
  echo
  echo "==> $*"
  "$@"
}

assert_port_available() {
  local port="$1"
  local label="$2"
  if ! "$GATE_PYTHON" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
probe = socket.socket()
try:
    probe.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    probe.close()
PY
  then
    echo "Gate $label port $port is already in use. Set WRIGHT_GATE_${label}_PORT to an unused port."
    exit 1
  fi
}

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${TMP_DB:-}" ]]; then
    rm -f "$TMP_DB"
  fi
  if [[ -n "${BACKEND_LOG:-}" ]]; then
    rm -f "$BACKEND_LOG"
  fi
}
trap cleanup EXIT

cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-$GATE_PYTHON}"

echo "Running Wright dev merge gate from $ROOT_DIR"
echo "Set SKIP_PLAYWRIGHT=1 only for a documented local browser/runtime limitation."
echo "Required reading: $RUNBOOK"
echo "Isolated live gate: API $API_PORT, UI $UI_PORT"

run git diff --check
# Rivet assets are force-included from integrations/, outside the Python package root.
run uv sync --all-packages --all-groups --reinstall-package wright-engineering
run "$GATE_PYTHON" -m scripts.release.scan_image --allow-unavailable-local-host

if [[ "${SKIP_PLAYWRIGHT:-0}" != "1" ]]; then
  echo
  echo "==> Checking Playwright live gate ports"
  assert_port_available "$API_PORT" API
  assert_port_available "$UI_PORT" UI
fi

run uv run ruff check "${PYTHON_WORKSPACE_PATHS[@]}"
run uv run ruff format --check "${PYTHON_WORKSPACE_PATHS[@]}"

run npx -w apps/web eslint .
if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  run npx prettier --check apps/web/ --end-of-line auto
else
  run npx prettier --check apps/web/
fi
run npx tsc --noEmit -p apps/web/tsconfig.app.json

run uv run --with mypy mypy scripts/release scripts/program_control src/wright_engineering --ignore-missing-imports
run uv run --with mypy mypy "${PYTHON_WORKSPACE_PATHS[@]}" --ignore-missing-imports || {
  echo "::warning::Mypy type checks failed with warning mode enabled."
}

run env PYTHON="$PYTHON_BIN" scripts/build-python-distributions.sh --dry-run packages/core packages/tool_registry
run uv run python -c "from pathlib import Path; from scripts.release.workflow_policy import validate_scoped_workflows; validate_scoped_workflows(Path('.'))"
run uv run --extra runtime python -m pytest -q tests/program_control_plane
run uv run python -m pytest -q tests/release
run uv run python -m pytest -q \
  tests/native_runtime \
  tests/release/test_native_release_evidence.py \
  tests/release/test_native_release_rehearsal.py \
  tests/release/test_native_workflow_policy.py \
  tests/test_public_python_distribution.py
run uv run --with pytest-cov python -m pytest -q tests/release tests/native_runtime --cov=scripts.release --cov=wright_engineering --cov-report=term --cov-fail-under=85
# Build once with the developer's installed lockfile dependencies. Native packaging
# reuses the fresh dist without running npm ci against a live Wright node_modules.
run npm run build --workspace=apps/web
run env WRIGHT_NATIVE_SKIP_FRONTEND_BUILD=1 PYTHON="$PYTHON_BIN" scripts/build-python-distributions.sh --dist-root "$ROOT_DIR/dist/dev-merge-python" .
run uv run python -c "from pathlib import Path; from scripts.release.python_artifacts import validate_native_distribution; artifacts=[p for p in Path('dist/dev-merge-python').rglob('*') if p.suffix == '.whl' or p.name.endswith('.tar.gz')]; assert len(artifacts) == 2; [validate_native_distribution(p) for p in artifacts]"

# Keep the request-to-cookie, request-to-filesystem/process, and exception-to-response
# regression boundaries visible as a dedicated gate. GitHub CodeQL remains the
# whole-program data-flow authority, while these tests provide an equivalent local
# behavioral check for the security paths that previously escaped this script.
run uv run python -m pytest -q \
  apps/api/tests/test_security.py \
  apps/api/tests/test_gateway_api.py \
  packages/workspace_service/tests/test_files.py \
  packages/workspace_service/tests/test_workspace_path.py \
  packages/workspace_service/tests/test_workspace_service.py

# Keep the Loops 068-073 program findings visible as one deterministic tranche.
# Full suites below remain authoritative; this early slice gives maintainers a
# direct failure for compatibility, diagnostics, persistence, offline, evidence,
# packaging, accessibility, and Gate E regressions.
run uv run --extra runtime python -m pytest -q \
  tests/program_hardening \
  tests/native_runtime/test_program_state_compatibility.py \
  tests/native_runtime/test_rollback.py \
  tests/native_runtime/test_security.py \
  tests/e2e/test_engineering_program_offline.py \
  tests/e2e/test_engineering_program_journey.py \
  packages/workspace_service/tests/test_engineering_program_recovery.py \
  packages/workspace_service/tests/test_engineering_scenario_performance.py \
  packages/workspace_service/tests/test_rivet_mcp_cancellation.py \
  packages/workspace_service/tests/test_support_diagnostics.py \
  packages/workspace_service/tests/test_support_diagnostic_service.py \
  packages/workspace_service/tests/test_support_diagnostics_performance.py \
  apps/api/tests/test_support_diagnostics_api.py \
  tests/release/test_program_compatibility_evidence.py \
  tests/packaging/test_program_hardening_contents.py
run npm run test --workspace=apps/web -- --run \
  CapabilityLibrary \
  RivetScenarioReport \
  SupportDiagnosticsPanel \
  workspace-service \
  ToolRegistryLayout

# The whole workspace includes the optional NumPy-backed engineering-model
# slice and several package-local test roots with intentionally repeated module
# and conftest names. Exercise every configured root in an isolated pytest
# process with both reviewed extras so collection cannot leak between packages.
for python_suite in \
  apps/api/tests \
  packages/agent_adapters/tests \
  packages/core/tests \
  packages/data_vault/tests \
  packages/model_registry/tests \
  packages/tool_registry/tests \
  packages/workspace_service/tests \
  tests; do
  python_suite_args=()
  if [[ "$python_suite" == "packages/model_registry/tests" ]]; then
    python_suite_args+=(-m "not performance")
  fi
  if [[ "$python_suite" == "tests" ]]; then
    python_suite_args+=(
      --ignore=tests/program_control_plane
      --ignore=tests/native_runtime
    )
  fi
  run uv run --extra runtime --extra engineering-models \
    python -m pytest "$python_suite" "${python_suite_args[@]}"
done
run uv run --isolated --reinstall-package hermes-plugin-wright \
  --package hermes-plugin-wright --with pytest --with pytest-asyncio --with respx --with PyYAML \
  python -m pytest hermes-plugin-wright/tests
run npm run test --workspace=apps/web
run uv run --with mkdocs-material mkdocs build --strict

if [[ "${SKIP_PLAYWRIGHT:-0}" == "1" ]]; then
  echo
  echo "==> Skipping Playwright live gate because SKIP_PLAYWRIGHT=1"
else

  TMP_DB="$(mktemp "${TMPDIR:-/tmp}/wright-dev-merge.XXXXXX.db")"
  BACKEND_LOG="$(mktemp "${TMPDIR:-/tmp}/wright-dev-merge-api.XXXXXX.log")"
  echo
  echo "==> Starting backend for Playwright live gate"
  LLM_API_URL="${LLM_API_URL:-http://127.0.0.1:${API_PORT}/v1}" \
  DATABASE_PATH="$TMP_DB" \
  WRIGHT_AUTH_MODE=compat \
  WRIGHT_API_MCP_AUTOSTART=1 \
  WRIGHT_BIND_HOST=127.0.0.1 \
    "$GATE_PYTHON" -m uvicorn api.main:app --host 127.0.0.1 --port "$API_PORT" >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!

  for attempt in {1..30}; do
    if curl --fail --silent --show-error --max-time 2 "http://127.0.0.1:${API_PORT}/api/health" >/dev/null; then
      echo "Backend is ready"
      break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      echo "Backend exited before becoming ready. Log follows:"
      cat "$BACKEND_LOG"
      exit 1
    fi
    if [[ "$attempt" == "30" ]]; then
      echo "Backend did not become ready. Log follows:"
      cat "$BACKEND_LOG"
      exit 1
    fi
    sleep 2
  done

  run env -u PLAYWRIGHT_BASE_URL \
    CI=1 \
    PLAYWRIGHT_INCLUDE_LIVE=1 \
    WRIGHT_PLAYWRIGHT_PORT="$UI_PORT" \
    WRIGHT_WEB_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}" \
    npx playwright test
fi

echo
echo "Dev merge gate passed."
