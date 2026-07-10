#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/build-python-distributions.sh [--dry-run] [--skip-clean-install] [--dist-root DIR] PACKAGE_DIR...

Build and validate Wright Python package release candidates.

Options:
  --dry-run             Validate package metadata without building artifacts.
  --skip-clean-install  Build artifacts but skip isolated pip install/import validation.
  --dist-root DIR       Directory for built artifacts (default: dist/python-packages).
  -h, --help            Show this help message.
USAGE
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_ROOT="$ROOT_DIR/dist/python-packages"
DRY_RUN=0
SKIP_CLEAN_INSTALL="${WRIGHT_SKIP_CLEAN_INSTALL:-0}"
PACKAGES=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-clean-install)
      SKIP_CLEAN_INSTALL=1
      shift
      ;;
    --dist-root)
      if [ "$#" -lt 2 ]; then
        echo "--dist-root requires a directory" >&2
        exit 2
      fi
      DIST_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      PACKAGES+=("$1")
      shift
      ;;
  esac
done

if [ "${#PACKAGES[@]}" -eq 0 ]; then
  echo "At least one package directory is required." >&2
  usage >&2
  exit 2
fi

python_bin="${PYTHON:-python3}"

validate_metadata() {
  local package_dir="$1"
  "$python_bin" - "$package_dir" <<'PY'
from __future__ import annotations

import pathlib
import sys

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

package_dir = pathlib.Path(sys.argv[1])
pyproject = package_dir / "pyproject.toml"
if not pyproject.exists():
    raise SystemExit(f"{package_dir}: missing pyproject.toml")

with pyproject.open("rb") as fh:
    data = tomllib.load(fh)
project = data.get("project", {})
required = ["name", "version", "description", "readme", "requires-python", "license", "dependencies"]
missing = [key for key in required if key not in project]
if missing:
    raise SystemExit(f"{pyproject}: missing required metadata fields: {', '.join(missing)}")

readme = package_dir / str(project["readme"])
if not readme.exists():
    raise SystemExit(f"{pyproject}: readme file does not exist: {readme}")

urls = project.get("urls", {})
for key in ("Homepage", "Source", "Issues", "Documentation", "Releases"):
    if key not in urls or not str(urls[key]).startswith("https://"):
        raise SystemExit(f"{pyproject}: missing https project URL {key}")

deps = [str(dep) for dep in project.get("dependencies", [])]
name = project.get("name")
if name == "wright-tool-registry":
    if not any(dep.startswith("wright-core>=") and ",<" in dep for dep in deps):
        raise SystemExit("wright-tool-registry must depend on a bounded wright-core release")

print(f"metadata ok: {name} {project.get('version')}")
PY
}

built_wheels=()
built_import_modules=()
for package in "${PACKAGES[@]}"; do
  package_dir="$package"
  if [ ! -d "$package_dir" ]; then
    package_dir="$ROOT_DIR/$package"
  fi
  if [ ! -d "$package_dir" ]; then
    echo "Package directory not found: $package" >&2
    exit 1
  fi

  validate_metadata "$package_dir"
  if [ "$DRY_RUN" = "1" ]; then
    continue
  fi

  package_name="$($python_bin - "$package_dir/pyproject.toml" <<'PY'
from __future__ import annotations
import pathlib, re, sys
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
with pathlib.Path(sys.argv[1]).open('rb') as fh:
    data = tomllib.load(fh)
print(re.sub(r'[^A-Za-z0-9_.-]+', '-', data['project']['name']))
PY
)"
  case "$package_name" in
    wright-engineering) built_import_modules+=("wright_engineering") ;;
    wright-core) built_import_modules+=("core") ;;
    wright-tool-registry) built_import_modules+=("tool_registry") ;;
    wright-data-vault) built_import_modules+=("data_vault") ;;
    wright-agent-adapters) built_import_modules+=("agent_adapters") ;;
    wright-workspace-service) built_import_modules+=("workspace_service") ;;
    *) built_import_modules+=("${package_name//-/_}") ;;
  esac

  out_dir="$DIST_ROOT/$package_name"
  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  "$python_bin" -m build --sdist --wheel --outdir "$out_dir" "$package_dir"

  wheel="$(find "$out_dir" -maxdepth 1 -type f -name '*.whl' | sort | tail -1)"
  sdist="$(find "$out_dir" -maxdepth 1 -type f \( -name '*.tar.gz' -o -name '*.zip' \) | sort | tail -1)"
  if [ -z "$wheel" ] || [ -z "$sdist" ]; then
    echo "Expected both wheel and source distribution in $out_dir" >&2
    exit 1
  fi
  built_wheels+=("$wheel")
done

if [ "$DRY_RUN" = "1" ]; then
  echo "Dry run completed. Package metadata is release-ready."
  exit 0
fi

if [ "$SKIP_CLEAN_INSTALL" = "1" ]; then
  echo "Built distributions in $DIST_ROOT; clean install skipped."
  exit 0
fi

tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/wright-package-install.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT
"$python_bin" -m venv "$tmp_dir/venv"
if [ -x "$tmp_dir/venv/bin/python" ]; then
  venv_python="$tmp_dir/venv/bin/python"
elif [ -x "$tmp_dir/venv/Scripts/python.exe" ]; then
  venv_python="$tmp_dir/venv/Scripts/python.exe"
else
  echo "Unable to locate Python in clean-install virtual environment." >&2
  exit 1
fi
"$venv_python" -m pip install --upgrade pip >/dev/null
"$venv_python" -m pip install "${built_wheels[@]}"
"$venv_python" - "${built_import_modules[@]}" <<'PY'
import importlib
import sys
for module_name in sys.argv[1:]:
    importlib.import_module(module_name)
print("clean install imports ok")
PY

echo "Built and validated distributions in $DIST_ROOT."
