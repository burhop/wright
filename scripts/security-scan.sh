#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INCLUDE_UNTRACKED=0
SKIP_GITLEAKS=0
SKIP_TRUFFLEHOG=0

GITLEAKS_IMAGE="${GITLEAKS_IMAGE:-ghcr.io/gitleaks/gitleaks:v8.30.1}"
TRUFFLEHOG_IMAGE="${TRUFFLEHOG_IMAGE:-ghcr.io/trufflesecurity/trufflehog:3.95.7}"

usage() {
  cat <<'USAGE'
Usage: scripts/security-scan.sh [--include-untracked] [--skip-gitleaks] [--skip-trufflehog]

Runs Wright's public-alpha leak scan plus Dockerized Gitleaks and TruffleHog
history scans. Requires Docker for the dedicated scanners.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --include-untracked)
      INCLUDE_UNTRACKED=1
      ;;
    --skip-gitleaks)
      SKIP_GITLEAKS=1
      ;;
    --skip-trufflehog)
      SKIP_TRUFFLEHOG=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

cd "$ROOT_DIR"

PYTHON_CMD=()
if command -v python >/dev/null 2>&1; then
  PYTHON_CMD=(python)
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=(python3)
elif command -v py >/dev/null 2>&1; then
  PYTHON_CMD=(py -3)
else
  echo "Could not find python, python3, or py on PATH." >&2
  exit 1
fi

echo "== Wright public-alpha leak scan =="
if [ "$INCLUDE_UNTRACKED" = "1" ]; then
  "${PYTHON_CMD[@]}" scripts/check-public-alpha-leaks.py --include-untracked
else
  "${PYTHON_CMD[@]}" scripts/check-public-alpha-leaks.py
fi

if [ "$SKIP_GITLEAKS" != "1" ]; then
  echo
  echo "== Gitleaks history scan =="
  docker run --rm \
    -v "$ROOT_DIR:/repo" \
    "$GITLEAKS_IMAGE" \
    git /repo \
    --config /repo/.gitleaks.toml \
    --no-banner \
    --redact \
    --verbose
fi

if [ "$SKIP_TRUFFLEHOG" != "1" ]; then
  echo
  echo "== TruffleHog history scan =="
  docker run --rm \
    -v "$ROOT_DIR:/repo" \
    -w /repo \
    "$TRUFFLEHOG_IMAGE" \
    git file:///repo \
    --no-update \
    --fail \
    --results=verified,unknown \
    --no-verification \
    --exclude-globs=uv.lock,package-lock.json
fi

echo
echo "Security scans passed."
