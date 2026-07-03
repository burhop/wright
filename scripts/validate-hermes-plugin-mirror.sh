#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/validate-hermes-plugin-mirror.sh --mirror-dir DIR [--channel stable|development]

Validate a generated root-level Wright Hermes plugin mirror.

Options:
  --mirror-dir DIR   Mirror directory to validate.
  --channel NAME     stable or development (default: development).
  -h, --help         Show this help message.
USAGE
}

MIRROR_DIR=""
CHANNEL="development"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mirror-dir)
      MIRROR_DIR="$2"
      shift 2
      ;;
    --channel)
      CHANNEL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$CHANNEL" in stable|development) ;; *) echo "--channel must be stable or development" >&2; exit 2 ;; esac
[ -n "$MIRROR_DIR" ] || { echo "--mirror-dir is required" >&2; exit 2; }
[ -d "$MIRROR_DIR" ] || { echo "Mirror directory not found: $MIRROR_DIR" >&2; exit 1; }

failures=()
fail() { failures+=("$1"); }

required=(plugin.yaml __init__.py bridge.py catalog.py catalog.yaml commands.py schemas.py pyproject.toml README.md verify_plugin.py tests)
for path in "${required[@]}"; do
  [ -e "$MIRROR_DIR/$path" ] || fail "missing required root path: $path"
done
[ -f "$MIRROR_DIR/LICENSE" ] || [ -f "$MIRROR_DIR/LICENSE.md" ] || fail "missing license file"
[ -f "$MIRROR_DIR/PROVENANCE.md" ] || [ -f "$MIRROR_DIR/provenance.json" ] || fail "missing provenance file"

prohibited=(apps packages docker specs registry node_modules .venv __pycache__ .pytest_cache)
for path in "${prohibited[@]}"; do
  [ ! -e "$MIRROR_DIR/$path" ] || fail "prohibited path present: $path"
done
while IFS= read -r path; do
  [ -z "$path" ] && continue
  fail "prohibited generated file present: ${path#$MIRROR_DIR/}"
done < <(find "$MIRROR_DIR" \( -name '*.pyc' -o -name '.env' -o -name '.env.*' \) -print)

readme="$MIRROR_DIR/README.md"
if [ -f "$readme" ]; then
  for token in \
    "official thin Wright Hermes plugin mirror" \
    "Stable install" \
    "Development install" \
    "hermes plugins update wright" \
    "hermes plugins remove wright" \
    "Migration" \
    "https://github.com/burhop/wright" \
    "https://github.com/burhop/wright/issues" \
    "https://github.com/burhop/wright/releases" \
    "https://pypi.org/project/wright-engineering/" \
    "Hermes plugin" \
    "Provenance"; do
    grep -qi "$token" "$readme" || fail "README missing required content: $token"
  done
fi

pyproject="$MIRROR_DIR/pyproject.toml"
if [ -f "$pyproject" ]; then
  if [ "$CHANNEL" = "stable" ]; then
    grep -q '\[tool\.uv\.sources\]' "$pyproject" && fail "stable mirror pyproject must not contain [tool.uv.sources]"
    grep -q 'workspace *= *true' "$pyproject" && fail "stable mirror pyproject must not contain workspace sources"
    grep -Eq 'git\+|@[[:space:]]*git' "$pyproject" && fail "stable mirror pyproject must not contain Git dependencies"
    grep -Eq 'wright-tool-registry[><=~!]' "$pyproject" || fail "stable pyproject must pin a versioned wright-tool-registry dependency"
  else
    grep -Eq 'wright-core @ git\+https://github\.com/burhop/wright\.git@[0-9a-f]{40}#subdirectory=packages/core' "$pyproject" || fail "development pyproject must pin wright-core to a source Git commit"
    grep -Eq 'wright-tool-registry @ git\+https://github\.com/burhop/wright\.git@[0-9a-f]{40}#subdirectory=packages/tool_registry' "$pyproject" || fail "development pyproject must pin wright-tool-registry to a source Git commit"
  fi
fi

if [ -f "$MIRROR_DIR/provenance.json" ]; then
  python3 - "$MIRROR_DIR/provenance.json" <<'PY' || fail "provenance.json must include a full 40-character commit_sha"
import json, re, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
sha = data.get("commit_sha", "")
if not re.fullmatch(r"[0-9a-f]{40}", sha):
    raise SystemExit(1)
for key in ("main_repo_url", "plugin_version", "wright_core_version", "wright_tool_registry_version", "source_paths"):
    if not data.get(key):
        raise SystemExit(1)
PY
elif [ -f "$MIRROR_DIR/PROVENANCE.md" ]; then
  grep -Eq '[0-9a-f]{40}' "$MIRROR_DIR/PROVENANCE.md" || fail "PROVENANCE.md must include a full commit SHA"
fi

if [ "${#failures[@]}" -gt 0 ]; then
  printf 'Mirror validation failed for %s (%s):\n' "$MIRROR_DIR" "$CHANNEL" >&2
  printf ' - %s\n' "${failures[@]}" >&2
  exit 1
fi

echo "Mirror validation passed for $MIRROR_DIR ($CHANNEL)."
