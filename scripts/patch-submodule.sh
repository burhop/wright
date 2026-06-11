#!/usr/bin/env bash
set -euo pipefail

# Find directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SUBMODULE_DIR="$REPO_DIR/packages/freecad_mcp"
PATCH_FILE="$SCRIPT_DIR/freecad_mcp.patch"

if [ ! -d "$SUBMODULE_DIR" ] || [ ! -f "$SUBMODULE_DIR/pyproject.toml" ]; then
    echo "Warning: Submodule directory packages/freecad_mcp is empty or not initialized."
    exit 0
fi

# Check if the submodule is modified or if the patch is already applied
if git -C "$SUBMODULE_DIR" diff --quiet; then
    echo "Applying freecad_mcp patch..."
    # Apply patch from the parent repository directory
    git -C "$REPO_DIR" apply --directory=packages/freecad_mcp "$PATCH_FILE"
    echo "Patch applied successfully!"
else
    echo "Submodule already contains modifications. Skipping patch application."
fi
