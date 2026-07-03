#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_WORKSPACE_PATHS=(
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
}
trap cleanup EXIT

cd "$ROOT_DIR"

echo "Running Wright dev merge gate from $ROOT_DIR"
echo "Set SKIP_PLAYWRIGHT=1 only for a documented local browser/runtime limitation."

run git diff --check
run uv run ruff check "${PYTHON_WORKSPACE_PATHS[@]}"
run uv run ruff format --check "${PYTHON_WORKSPACE_PATHS[@]}"

run npx -w apps/web eslint .
run npx prettier --check apps/web/
run npx tsc --noEmit -p apps/web/tsconfig.app.json

run uv pip install mypy --quiet
run uv run mypy "${PYTHON_WORKSPACE_PATHS[@]}" --ignore-missing-imports || {
  echo "::warning::Mypy type checks failed with warning mode enabled."
}

run scripts/build-python-distributions.sh --dry-run packages/core packages/tool_registry

run uv run pytest
run uv run --package hermes-plugin-wright pytest hermes-plugin-wright/tests
run npm run test --workspace=apps/web
run npm run build --workspace=apps/web
run uv run --with mkdocs-material mkdocs build --strict

if [[ "${SKIP_PLAYWRIGHT:-0}" == "1" ]]; then
  echo
  echo "==> Skipping Playwright live gate because SKIP_PLAYWRIGHT=1"
else
  TMP_DB="$(mktemp "${TMPDIR:-/tmp}/wright-dev-merge.XXXXXX.db")"
  BACKEND_LOG="$(mktemp "${TMPDIR:-/tmp}/wright-dev-merge-api.XXXXXX.log")"
  echo
  echo "==> Starting backend for Playwright live gate"
  LLM_API_URL="${LLM_API_URL:-http://127.0.0.1:8000/v1}" \
  DATABASE_PATH="$TMP_DB" \
    uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!

  for attempt in {1..30}; do
    if curl --fail --silent --show-error --max-time 2 http://127.0.0.1:8000/api/health >/dev/null; then
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

  run env PLAYWRIGHT_INCLUDE_LIVE=1 npx playwright test
fi

echo
echo "Dev merge gate passed."
