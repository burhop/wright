#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/sync-hermes-plugin-mirror.sh --source DIR --mirror-url URL --branch BRANCH [--output-dir DIR] [--channel stable|development] [--dry-run]

Generate a thin root-level Hermes plugin mirror from the monorepo plugin source.

Options:
  --source DIR       Source plugin directory (default: hermes-plugin-wright).
  --mirror-url URL   Public mirror repository URL.
  --branch BRANCH    Mirror branch being generated.
  --output-dir DIR   Local output directory for generated mirror files.
  --channel NAME     stable or development (default: development).
  --dry-run          Print the files that would be exported without writing.
  -h, --help         Show this help message.
USAGE
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/hermes-plugin-wright"
MIRROR_URL=""
BRANCH=""
OUTPUT_DIR=""
CHANNEL="development"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source)
      SOURCE_DIR="$2"
      case "$SOURCE_DIR" in /*) ;; *) SOURCE_DIR="$ROOT_DIR/$SOURCE_DIR" ;; esac
      shift 2
      ;;
    --mirror-url)
      MIRROR_URL="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --channel)
      CHANNEL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
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
[ -n "$MIRROR_URL" ] || { echo "--mirror-url is required" >&2; exit 2; }
[ -n "$BRANCH" ] || { echo "--branch is required" >&2; exit 2; }
[ -d "$SOURCE_DIR" ] || { echo "Source directory not found: $SOURCE_DIR" >&2; exit 1; }
if [ "$DRY_RUN" != "1" ] && [ -z "$OUTPUT_DIR" ]; then
  echo "--output-dir is required unless --dry-run is used" >&2
  exit 2
fi

allowlist=(
  plugin.yaml
  __init__.py
  bridge.py
  catalog.py
  catalog.yaml
  commands.py
  schemas.py
  pyproject.toml
  README.md
  PROVENANCE.md
  verify_plugin.py
  tests
)

if [ "$DRY_RUN" = "1" ]; then
  echo "Mirror dry run for $MIRROR_URL branch $BRANCH ($CHANNEL)"
  for path in "${allowlist[@]}"; do
    if [ -e "$SOURCE_DIR/$path" ]; then
      echo "$path"
    fi
  done
  if [ -f "$ROOT_DIR/LICENSE" ] || [ -f "$ROOT_DIR/LICENSE.md" ]; then
    echo "LICENSE"
  fi
  echo "provenance.json"
  exit 0
fi

mkdir -p "$OUTPUT_DIR"
rm -rf "$OUTPUT_DIR"/*

commit_sha="$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || printf 'unknown')"

copy_file() {
  local rel="$1"
  if [ -f "$SOURCE_DIR/$rel" ]; then
    mkdir -p "$OUTPUT_DIR/$(dirname "$rel")"
    cp "$SOURCE_DIR/$rel" "$OUTPUT_DIR/$rel"
  fi
}

copy_pyproject_without_workspace_sources() {
  python3 - "$SOURCE_DIR/pyproject.toml" "$OUTPUT_DIR/pyproject.toml" "$CHANNEL" "$commit_sha" <<'PYPROJECT_REWRITE'
from __future__ import annotations

from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
output = Path(sys.argv[2])
channel = sys.argv[3]
commit_sha = sys.argv[4]

lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
filtered: list[str] = []
skip_uv_sources = False
for line in lines:
    if line.strip() == "[tool.uv.sources]":
        skip_uv_sources = True
        continue
    if skip_uv_sources and line.startswith("["):
        skip_uv_sources = False
    if not skip_uv_sources:
        filtered.append(line)

text = "".join(filtered)
if channel == "development":
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise SystemExit("development mirror requires a full source commit SHA")
    replacement = (
        f'    "wright-core @ git+https://github.com/burhop/wright.git@{commit_sha}#subdirectory=packages/core",\n'
        f'    "wright-tool-registry @ git+https://github.com/burhop/wright.git@{commit_sha}#subdirectory=packages/tool_registry",\n'
    )
    text, count = re.subn(r'    "wright-tool-registry[^"\n]+",\n', replacement, text, count=1)
    if count != 1:
        raise SystemExit("could not rewrite wright-tool-registry dependency")

output.write_text(text, encoding="utf-8")
PYPROJECT_REWRITE
}

for path in "${allowlist[@]}"; do
  if [ "$path" = "pyproject.toml" ]; then
    copy_pyproject_without_workspace_sources
  elif [ -d "$SOURCE_DIR/$path" ]; then
    mkdir -p "$OUTPUT_DIR/$path"
    while IFS= read -r file; do
      rel="${file#$SOURCE_DIR/}"
      case "$rel" in
        *__pycache__*|*.pyc|*.pyo|*.pyd|*.pytest_cache*) continue ;;
      esac
      mkdir -p "$OUTPUT_DIR/$(dirname "$rel")"
      cp "$file" "$OUTPUT_DIR/$rel"
    done < <(find "$SOURCE_DIR/$path" -type f | sort)
  else
    copy_file "$path"
  fi
done

if [ ! -f "$OUTPUT_DIR/LICENSE" ] && [ ! -f "$OUTPUT_DIR/LICENSE.md" ]; then
  if [ -f "$ROOT_DIR/LICENSE" ]; then
    cp "$ROOT_DIR/LICENSE" "$OUTPUT_DIR/LICENSE"
  elif [ -f "$ROOT_DIR/LICENSE.md" ]; then
    cp "$ROOT_DIR/LICENSE.md" "$OUTPUT_DIR/LICENSE.md"
  else
    printf 'MIT License\n' > "$OUTPUT_DIR/LICENSE"
  fi
fi

generated_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
plugin_version="$(python3 - "$SOURCE_DIR/plugin.yaml" <<'PY'
import re, sys
text=open(sys.argv[1], encoding='utf-8').read()
match=re.search(r'^version:\s*["\']?([^"\'\n]+)', text, re.M)
print(match.group(1).strip() if match else 'unknown')
PY
)"
core_version="$(python3 - "$ROOT_DIR/packages/core/pyproject.toml" <<'PY'
import sys, tomllib
with open(sys.argv[1], 'rb') as fh:
    print(tomllib.load(fh)['project']['version'])
PY
)"
tool_registry_version="$(python3 - "$ROOT_DIR/packages/tool_registry/pyproject.toml" <<'PY'
import sys, tomllib
with open(sys.argv[1], 'rb') as fh:
    print(tomllib.load(fh)['project']['version'])
PY
)"

cat > "$OUTPUT_DIR/provenance.json" <<JSON
{
  "main_repo_url": "https://github.com/burhop/wright",
  "mirror_repo_url": "$MIRROR_URL",
  "commit_sha": "$commit_sha",
  "branch": "$BRANCH",
  "channel": "$CHANNEL",
  "generated_at": "$generated_at",
  "workflow_run_url": "${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-burhop/wright}/actions/runs/${GITHUB_RUN_ID:-local}",
  "plugin_version": "$plugin_version",
  "wright_core_version": "$core_version",
  "wright_tool_registry_version": "$tool_registry_version",
  "source_paths": ["${SOURCE_DIR#$ROOT_DIR/}"]
}
JSON

if [ ! -f "$OUTPUT_DIR/PROVENANCE.md" ]; then
  cat > "$OUTPUT_DIR/PROVENANCE.md" <<EOF_PROVENANCE
# Provenance

Main repository: https://github.com/burhop/wright
Mirror repository: $MIRROR_URL
Source branch: $BRANCH
Source commit: $commit_sha
Generated at: $generated_at
Plugin version: $plugin_version
wright-core version: $core_version
wright-tool-registry version: $tool_registry_version
EOF_PROVENANCE
fi

echo "Generated mirror files in $OUTPUT_DIR"
