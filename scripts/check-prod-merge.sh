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
wheel_path="$(find "$ROOT_DIR/dist/dev-merge-python" -type f -name '*.whl' -print -quit)"
if [[ -z "$wheel_path" ]]; then
  echo "Production wheel content check could not find the dev-gate wheel."
  exit 1
fi
run uv run --with check-wheel-contents==0.6.3 check-wheel-contents "$wheel_path"
run scripts/security-scan.sh --include-untracked
run scripts/alpha-release-check.sh

mirror_dir="$(mktemp -d "${TMPDIR:-/tmp}/wright-plugin-mirror.XXXXXX")"
cleanup_mirror() {
  rm -rf "$mirror_dir"
}
trap cleanup_mirror EXIT
run scripts/sync-hermes-plugin-mirror.sh \
  --source hermes-plugin-wright \
  --mirror-url https://github.com/burhop/hermes-plugin-wright \
  --branch dev \
  --channel development \
  --output-dir "$mirror_dir"
run scripts/validate-hermes-plugin-mirror.sh \
  --mirror-dir "$mirror_dir" \
  --channel development
cleanup_mirror
trap - EXIT

run uv run python -c "from scripts.release.hermes_capability import require_released_git_plugin_interface; require_released_git_plugin_interface()"

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
  run scripts/test-hermes-plugin-install.sh \
    --mirror-root \
    --repo-url https://github.com/burhop/hermes-plugin-wright \
    --ref dev
  run scripts/test-hermes-plugin-update.sh \
    --mirror-root \
    --repo-url https://github.com/burhop/hermes-plugin-wright \
    --ref dev
  run scripts/test-hermes-plugin-uninstall.sh \
    --mirror-root \
    --repo-url https://github.com/burhop/hermes-plugin-wright \
    --ref dev
fi

echo
echo "Production merge gate passed."
