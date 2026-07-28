#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run() {
  echo
  echo "==> $*"
  "$@"
}

cd "$ROOT_DIR"

echo "Running Wright production merge gate from $ROOT_DIR"
echo "This includes the dev merge gate plus release, Docker, and Hermes plugin mirror checks."
echo "Use only documented SKIP_* overrides for local host limitations, never to hide a failure."

run scripts/check-dev-merge.sh
run scripts/security-scan.sh --include-untracked
run scripts/alpha-release-check.sh
run make hermes-plugin-mirror-validate
run uv run python -c "from scripts.release.hermes_capability import require_released_package_capability; require_released_package_capability()"

if grep -q -- '--base-only' .github/workflows/release.yml; then
  echo "Production release workflow must run the full published native lifecycle, not base-only acceptance."
  exit 1
fi
run uv run pytest -q \
  tests/release/test_native_release_evidence.py \
  tests/release/test_native_workflow_policy.py \
  tests/release/test_native_release_rehearsal.py

if [[ "${SKIP_HERMES_PLUGIN_LIFECYCLE:-0}" == "1" ]]; then
  echo
  echo "==> Skipping Hermes plugin root lifecycle gate because SKIP_HERMES_PLUGIN_LIFECYCLE=1"
else
  run make hermes-plugin-root-lifecycle-test
fi

echo
echo "Production merge gate passed."
