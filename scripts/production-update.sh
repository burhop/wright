#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REF="origin/main"
ALLOW_DIRTY=0
PULL=0
SKIP_CI=0
COMPOSE_FILE="docker-compose.minimal.yml"

usage() {
  cat <<'USAGE'
Usage: scripts/production-update.sh [options]

Checks that a production update is deploying exactly origin/main or a selected
release tag, then runs docker compose up.

Options:
  --ref <ref>          Git ref to deploy. Default: origin/main. Use v* tags for releases.
  --pull              Fast-forward the current branch before deploying origin/main.
  --allow-dirty       Permit a dirty working tree.
  --skip-ci-checks    Skip GitHub check-run verification even if gh auth is available.
  --compose-file <f>  Compose file to deploy. Default: docker-compose.minimal.yml.
  -h, --help          Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ref)
      REF="${2:?--ref requires a value}"
      shift
      ;;
    --pull)
      PULL=1
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
      ;;
    --skip-ci-checks)
      SKIP_CI=1
      ;;
    --compose-file)
      COMPOSE_FILE="${2:?--compose-file requires a value}"
      shift
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

if [ "$ALLOW_DIRTY" != "1" ] && [ -n "$(git status --porcelain --untracked-files=normal)" ]; then
  echo "Working tree is dirty. Commit, stash, clean, or rerun with --allow-dirty." >&2
  git status --short
  exit 1
fi

echo "Fetching origin and tags..."
git fetch --tags origin

CURRENT_BRANCH="$(git branch --show-current || true)"
if [ "$REF" = "origin/main" ] || [ "$REF" = "main" ]; then
  if [ "$PULL" = "1" ]; then
    if [ "$CURRENT_BRANCH" != "main" ]; then
      echo "--pull requires the current branch to be main." >&2
      exit 1
    fi
    git pull --ff-only origin main
  fi

  BEHIND_COUNT="$(git rev-list --count HEAD..origin/main)"
  if [ "$BEHIND_COUNT" != "0" ]; then
    echo "Local branch is behind origin/main by $BEHIND_COUNT commit(s)." >&2
    echo "Run scripts/production-update.sh --pull after reviewing the remote changes." >&2
    exit 1
  fi
fi

TARGET_COMMIT="$(git rev-parse "${REF}^{commit}")"
HEAD_COMMIT="$(git rev-parse HEAD)"

if [ "$HEAD_COMMIT" != "$TARGET_COMMIT" ]; then
  echo "Refusing to deploy $HEAD_COMMIT." >&2
  echo "Expected checked-out commit to match $REF ($TARGET_COMMIT)." >&2
  exit 1
fi

if [ "$SKIP_CI" != "1" ] && command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "Checking required GitHub checks for $TARGET_COMMIT..."
  REQUIRED_CHECKS=(
    "python-quality"
    "frontend-quality"
    "public-alpha-safety"
    "docs"
    "Docker Build CI"
  )

  for CHECK in "${REQUIRED_CHECKS[@]}"; do
    CONCLUSION="$(gh run list --commit "$TARGET_COMMIT" --workflow "$CHECK" --status completed --limit 1 --json conclusion --jq '.[0].conclusion // ""')"
    if [ "$CONCLUSION" != "success" ]; then
      echo "Required check '$CHECK' is not green for $TARGET_COMMIT (conclusion: ${CONCLUSION:-missing})." >&2
      exit 1
    fi
  done
else
  echo "GitHub CLI credentials unavailable or CI checks skipped; relying on local freshness checks."
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

echo "Deploying $TARGET_COMMIT with $COMPOSE_FILE..."
docker compose -f "$COMPOSE_FILE" pull
docker compose -f "$COMPOSE_FILE" up -d --build
docker compose -f "$COMPOSE_FILE" ps
