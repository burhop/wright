#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITLEAKS_IMAGE="${GITLEAKS_IMAGE:-ghcr.io/gitleaks/gitleaks:v8.30.1}"
FIXTURE_ROOT="$ROOT_DIR/test-results/.gitleaks-program-status-contract.$$"
FIXTURE_PATH="$FIXTURE_ROOT/docs/programs/engineering-process-platform/test-run-ledger.json"
DOCKER_ROOT_DIR="$ROOT_DIR"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) DOCKER_ROOT_DIR="$(cygpath -w "$ROOT_DIR")" ;;
esac

cleanup() {
  rm -rf "$FIXTURE_ROOT"
}
trap cleanup EXIT

mkdir -p "$(dirname "$FIXTURE_PATH")"
run_key="$(printf 'program-status-run-key' | sha256sum | cut -d' ' -f1)"
printf '{"run_key":"%s"}\n' "$run_key" >"$FIXTURE_PATH"

MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$DOCKER_ROOT_DIR:/repo" \
  "$GITLEAKS_IMAGE" \
  dir /repo/test-results/"$(basename "$FIXTURE_ROOT")" \
  --config /repo/.gitleaks.toml \
  --no-banner \
  --redact >/dev/null

fixture_secret="$(printf 'program-status-negative-control' | sha256sum | cut -d' ' -f1)"
printf '{"run_key":"%s","api_key":"%s"}\n' "$run_key" "$fixture_secret" >"$FIXTURE_PATH"
if MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$DOCKER_ROOT_DIR:/repo" \
  "$GITLEAKS_IMAGE" \
  dir /repo/test-results/"$(basename "$FIXTURE_ROOT")" \
  --config /repo/.gitleaks.toml \
  --no-banner \
  --redact >/dev/null 2>&1; then
  echo "Gitleaks failed to detect a second API-key match beside an allowed run_key." >&2
  exit 1
fi

printf '{"run_key":"%sa"}\n' "$run_key" >"$FIXTURE_PATH"
if MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$DOCKER_ROOT_DIR:/repo" \
  "$GITLEAKS_IMAGE" \
  dir /repo/test-results/"$(basename "$FIXTURE_ROOT")" \
  --config /repo/.gitleaks.toml \
  --no-banner \
  --redact >/dev/null 2>&1; then
  echo "Gitleaks failed to detect a run_key longer than one SHA-256 identity." >&2
  exit 1
fi

echo "Program-status Gitleaks allowlist contract passed."

python "$ROOT_DIR/scripts/test-gitleaks-native-evidence.py"
