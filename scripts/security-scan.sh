#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INCLUDE_UNTRACKED=0
SKIP_GITLEAKS=0
SKIP_TRUFFLEHOG=0

GITLEAKS_IMAGE="${GITLEAKS_IMAGE:-ghcr.io/gitleaks/gitleaks:v8.30.1}"
TRUFFLEHOG_IMAGE="${TRUFFLEHOG_IMAGE:-ghcr.io/trufflesecurity/trufflehog:3.95.7}"

# Git for Windows rewrites POSIX-looking arguments before invoking Windows
# executables. Give Docker Desktop an explicit Windows bind source and disable
# conversion so both the host path and in-container /repo paths stay correct.
DOCKER_ROOT_DIR="$ROOT_DIR"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) DOCKER_ROOT_DIR="$(cygpath -w "$ROOT_DIR")" ;;
esac

SCAN_ROOT_DIR="$ROOT_DIR"
DOCKER_SCAN_ROOT_DIR="$DOCKER_ROOT_DIR"
TEMP_SCAN_PARENT=""

cleanup() {
  if [ -n "$TEMP_SCAN_PARENT" ] && [ -d "$TEMP_SCAN_PARENT" ]; then
    rm -rf -- "$TEMP_SCAN_PARENT"
  fi
}
trap cleanup EXIT

prepare_history_scan_root() {
  # Docker cannot resolve a linked worktree's .git file because it names the
  # host-only common Git directory. Normalize only history scans into a local
  # full clone; the public-alpha scan above still covers the live worktree and
  # its optional untracked files.
  if [ -f "$ROOT_DIR/.git" ]; then
    TEMP_SCAN_PARENT="$(mktemp -d "${TMPDIR:-/tmp}/wright-security-scan.XXXXXX")"
    SCAN_ROOT_DIR="$TEMP_SCAN_PARENT/repo"
    git clone --no-hardlinks --no-checkout "$ROOT_DIR" "$SCAN_ROOT_DIR" >/dev/null
    HEAD_COMMIT="$(git -C "$ROOT_DIR" rev-parse --verify HEAD)"
    git -C "$SCAN_ROOT_DIR" checkout --detach "$HEAD_COMMIT" >/dev/null
  fi

  SCAN_COMMIT_COUNT="$(git -C "$SCAN_ROOT_DIR" rev-list --count HEAD)"
  if ! [[ "$SCAN_COMMIT_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "History scan root contains no commits; refusing a false-green scan." >&2
    exit 1
  fi

  DOCKER_SCAN_ROOT_DIR="$SCAN_ROOT_DIR"
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) DOCKER_SCAN_ROOT_DIR="$(cygpath -w "$SCAN_ROOT_DIR")" ;;
  esac
  echo "History scan coverage: $SCAN_COMMIT_COUNT commits reachable from HEAD."
}

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

if [ "$SKIP_GITLEAKS" != "1" ] || [ "$SKIP_TRUFFLEHOG" != "1" ]; then
  prepare_history_scan_root
fi

if [ "$SKIP_GITLEAKS" != "1" ]; then
  echo
  echo "== Gitleaks history scan =="
  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "$DOCKER_SCAN_ROOT_DIR:/repo" \
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
  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "$DOCKER_SCAN_ROOT_DIR:/repo" \
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
