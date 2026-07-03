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

if [[ "${SKIP_HERMES_PLUGIN_LIFECYCLE:-0}" == "1" ]]; then
  echo
  echo "==> Skipping Hermes plugin root lifecycle gate because SKIP_HERMES_PLUGIN_LIFECYCLE=1"
else
  run make hermes-plugin-root-lifecycle-test
fi

echo
echo "Production merge gate passed."
