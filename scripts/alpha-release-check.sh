#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Git whitespace check =="
git diff --check

echo
echo "== Python pytest =="
uv run pytest

echo
echo "== Frontend Vitest =="
npm run test --workspace=apps/web

echo
echo "== Frontend production build =="
npm run build --workspace=apps/web

echo
echo "== MkDocs strict build =="
uv run --with mkdocs-material mkdocs build --strict

echo
echo "== Security scans =="
scripts/security-scan.sh --include-untracked

echo
echo "== Docker smoke test =="
scripts/docker-smoke-test.sh

echo
echo "Alpha release check passed."
