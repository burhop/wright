#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNBOOK="docs/contributing/dev-push-runbook.md"
BASE_REF="${WRIGHT_DEV_BASE_REF:-}"
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
if [[ -z "$BASE_REF" ]]; then
  BASE_REF="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  BASE_REF="${BASE_REF:-origin/dev}"
fi
echo "Required reading: $RUNBOOK"
echo "Fast gate change base: $BASE_REF"

if [[ "$(git branch --show-current)" == "dev" ]]; then
  echo "Direct pushes to dev are not supported. Push a feature branch and merge a pull request."
  exit 1
fi

run git diff --check

if git show-ref --verify --quiet refs/remotes/origin/dev &&
  ! git merge-base --is-ancestor origin/dev HEAD; then
  echo "::warning::origin/dev is not an ancestor of HEAD. Refresh the branch before the full merge gate."
fi

CHANGED_FILES="$({
  git diff --name-only "$BASE_REF"...HEAD 2>/dev/null || git diff --name-only HEAD~1...HEAD
  git diff --name-only
  git diff --cached --name-only
  git ls-files --others --exclude-standard
} | sort -u)"

CHECK_FRONTEND=0
CHECK_PYTHON=0
CHECK_DOCS=0
PYTHON_TEST_TARGETS=()
PLAYWRIGHT_TARGETS=()
while IFS= read -r changed_file; do
  [[ -z "$changed_file" ]] && continue
  case "$changed_file" in
    .github/workflows/*|scripts/check-dev-*|Makefile|AGENTS.md)
      CHECK_FRONTEND=1
      CHECK_PYTHON=1
      CHECK_DOCS=1
      ;;
    apps/web/*|playwright*.ts|package.json|package-lock.json)
      CHECK_FRONTEND=1
      ;;
    docs/*|specs/*|mkdocs.yml)
      CHECK_DOCS=1
      ;;
    scripts/*.md)
      CHECK_DOCS=1
      ;;
    tests/ui-integration/*.spec.ts|tests/ui-integration/*/*.spec.ts)
      CHECK_FRONTEND=1
      PLAYWRIGHT_TARGETS+=("$changed_file")
      ;;
    apps/api/*)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=(apps/api/tests)
      ;;
    packages/*/*)
      CHECK_PYTHON=1
      IFS=/ read -r package_parent package_name _ <<<"$changed_file"
      package_root="$package_parent/$package_name"
      [[ -d "$package_root/tests" ]] && PYTHON_TEST_TARGETS+=("$package_root/tests")
      ;;
    scripts/release/*)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=(tests/release)
      ;;
    tests/release/*.py)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=("$changed_file")
      ;;
    hermes-plugin-wright/*)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=(hermes-plugin-wright/tests)
      ;;
    tests/*.py|tests/*/*.py)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=("$changed_file")
      ;;
    *.py|pyproject.toml|uv.lock|src/*|scripts/*)
      CHECK_PYTHON=1
      PYTHON_TEST_TARGETS+=(tests)
      ;;
  esac
done <<<"$CHANGED_FILES"

echo "Selected scopes: python=$CHECK_PYTHON frontend=$CHECK_FRONTEND docs=$CHECK_DOCS"
if [[ "${#PYTHON_TEST_TARGETS[@]}" -gt 0 ]]; then
  printf 'Selected Python target: %s\n' "${PYTHON_TEST_TARGETS[@]}"
fi
if [[ "${#PLAYWRIGHT_TARGETS[@]}" -gt 0 ]]; then
  printf 'Selected Playwright target: %s\n' "${PLAYWRIGHT_TARGETS[@]}"
fi

if [[ "$CHECK_PYTHON" == "1" ]]; then
  run uv sync --all-packages --all-groups
  run uv run ruff check "${PYTHON_WORKSPACE_PATHS[@]}"
  run uv run ruff format --check "${PYTHON_WORKSPACE_PATHS[@]}"
  run uv run --with mypy mypy scripts/release src/wright_engineering --ignore-missing-imports

  mapfile -t PYTHON_TEST_TARGETS < <(printf '%s\n' "${PYTHON_TEST_TARGETS[@]}" | sed '/^$/d' | sort -u)
  for python_suite in "${PYTHON_TEST_TARGETS[@]}"; do
    run uv run --extra runtime --extra engineering-models \
      python -m pytest -q "$python_suite"
  done
fi

if [[ "$CHECK_FRONTEND" == "1" ]]; then
  run npm ci --dry-run
  run npx -w apps/web eslint .
  if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
    run npx prettier --check apps/web/ --end-of-line auto
  else
    run npx prettier --check apps/web/
  fi
  run npx tsc --noEmit -p apps/web/tsconfig.app.json
  run npm run test --workspace=apps/web -- --changed "$BASE_REF"
  run npm run build --workspace=apps/web

  if [[ "$CHECK_PYTHON" == "0" ]]; then
    run uv sync --all-packages --all-groups
  fi

  GATE_API_PORT="${WRIGHT_GATE_API_PORT:-18001}"
  GATE_UI_PORT="${WRIGHT_GATE_UI_PORT:-15174}"
  if curl --fail --silent --show-error --max-time 1 "http://127.0.0.1:${GATE_API_PORT}/api/health" >/dev/null 2>&1; then
    echo "Gate API port $GATE_API_PORT is already in use. Set WRIGHT_GATE_API_PORT to an unused port."
    exit 1
  fi
  if curl --fail --silent --show-error --max-time 1 "http://127.0.0.1:${GATE_UI_PORT}" >/dev/null 2>&1; then
    echo "Gate UI port $GATE_UI_PORT is already in use. Set WRIGHT_GATE_UI_PORT to an unused port."
    exit 1
  fi
  TMP_DB="$(mktemp "${TMPDIR:-/tmp}/wright-dev-push.XXXXXX.db")"
  BACKEND_LOG="$(mktemp "${TMPDIR:-/tmp}/wright-dev-push-api.XXXXXX.log")"
  echo "==> Starting isolated API on port $GATE_API_PORT"
  LLM_API_URL="${LLM_API_URL:-http://127.0.0.1:${GATE_API_PORT}/v1}" \
  DATABASE_PATH="$TMP_DB" \
  WRIGHT_AUTH_MODE=compat \
  WRIGHT_API_MCP_AUTOSTART=0 \
  WRIGHT_BIND_HOST=127.0.0.1 \
    "$GATE_PYTHON" -m uvicorn api.main:app --host 127.0.0.1 --port "$GATE_API_PORT" >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!

  for attempt in {1..30}; do
    if curl --fail --silent --show-error --max-time 2 "http://127.0.0.1:${GATE_API_PORT}/api/health" >/dev/null; then
      echo "Isolated API is ready"
      break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      echo "Isolated API exited before becoming ready. Log follows:"
      cat "$BACKEND_LOG"
      exit 1
    fi
    if [[ "$attempt" == "30" ]]; then
      echo "Isolated API did not become ready. Log follows:"
      cat "$BACKEND_LOG"
      exit 1
    fi
    sleep 2
  done

  if [[ "${#PLAYWRIGHT_TARGETS[@]}" == "0" ]]; then
    PLAYWRIGHT_TARGETS=(
      tests/ui-integration/navigation.spec.ts
      tests/ui-integration/workspace-surfaces/focus-layout.spec.ts
      tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts
    )
  fi
  mapfile -t PLAYWRIGHT_TARGETS < <(printf '%s\n' "${PLAYWRIGHT_TARGETS[@]}" | sort -u)
  run env -u PLAYWRIGHT_BASE_URL \
    CI=1 \
    WRIGHT_PLAYWRIGHT_PORT="$GATE_UI_PORT" \
    WRIGHT_WEB_API_PROXY_TARGET="http://127.0.0.1:${GATE_API_PORT}" \
    npx playwright test "${PLAYWRIGHT_TARGETS[@]}" --project=chromium
fi

if [[ "$CHECK_DOCS" == "1" ]]; then
  run uv run --with mkdocs-material mkdocs build --strict
fi

if [[ "$CHECK_FRONTEND" == "0" && "$CHECK_PYTHON" == "0" && "$CHECK_DOCS" == "0" ]]; then
  echo "No changed files selected a language gate. Review the diff before pushing."
fi

echo
echo "Dev push fast gate passed."
