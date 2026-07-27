#!/bin/bash
set -e
export PATH="/opt/hermes/bin:/opt/hermes/.venv/bin:${PATH}"
export HOME="/home/agent"
HERMES_CLI="/opt/hermes/bin/hermes"

generate_secret() {
  /usr/local/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))'
}

export HERMES_API_KEY="${HERMES_API_KEY:-${API_SERVER_KEY:-$(generate_secret)}}"
export API_SERVER_KEY="${HERMES_API_KEY}"
: "${WRIGHT_API_TOKEN:?WRIGHT_API_TOKEN must be set to a unique installation secret}"
export WRIGHT_API_TOKEN

echo "=== Agent Container Starting ==="
echo "  Timestamp   : $(date -u)"

# 1. Validate LLM_API_URL
if [ -z "${LLM_API_URL}" ]; then
  echo "Warning: LLM_API_URL environment variable is not set. Please configure it via the Setup Web UI." >&2
fi

# 2. Export CONTAINER_MANIFEST
if [ -f "/container-manifest.md" ]; then
  export CONTAINER_MANIFEST=$(cat /container-manifest.md)
else
  echo "Warning: /container-manifest.md is missing. CONTAINER_MANIFEST will be empty." >&2
  export CONTAINER_MANIFEST=""
fi

# 3. Create Wright-owned data directories
mkdir -p /home/agent/.local/share/wright || echo "Warning: Failed to create Wright state directory" >&2
mkdir -p /home/agent/.config/wright || echo "Warning: Failed to create Wright config directory" >&2

# 4. Bootstrap Hermes Agent (first-run only)
HERMES_HOME="/home/agent/.hermes"
export HERMES_HOME
export HERMES_PROFILE="wright"

ensure_wright_profile() {
  mkdir -p "${HERMES_HOME}"
  if [ ! -d "${HERMES_HOME}/profiles/wright" ]; then
    echo "Creating Hermes profile: wright"
    "${HERMES_CLI}" profile create wright || true
  fi
  mkdir -p "${HERMES_HOME}/profiles/wright/sessions"
  mkdir -p "${HERMES_HOME}/profiles/wright/skills"
  mkdir -p "${HERMES_HOME}/webui/sessions"
  mkdir -p "${HERMES_HOME}/webui/workspace"
}

write_hermes_config() {
  export WRIGHT_HERMES_CONFIG="${HERMES_HOME}/config.yaml"
  /opt/hermes/.venv/bin/python <<'PY'
import os
import pathlib
import tempfile
import yaml

path = pathlib.Path(os.environ["WRIGHT_HERMES_CONFIG"])
try:
    existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
except FileNotFoundError:
    existing = {}
if not isinstance(existing, dict):
    raise SystemExit("Hermes configuration must be a mapping")
url = os.environ.get("LLM_API_URL") or "http://localhost:8000/v1"
model = os.environ.get("LLM_API_MODEL") or "default"
key = os.environ.get("LLM_API_KEY") or "NotNeeded"
existing["model"] = {
    "base_url": url,
    "context_length": 131072,
    "default": model,
    "provider": "custom",
}
providers = existing.get("custom_providers")
if not isinstance(providers, list):
    providers = []
owned = {"api_key": key, "base_url": url, "model": model, "name": "wright-llm"}
providers = [item for item in providers if not isinstance(item, dict) or item.get("name") != "wright-llm"]
existing["custom_providers"] = [*providers, owned]
existing.setdefault("toolsets", ["hermes-cli"])
existing["terminal"] = {
    **(existing.get("terminal") if isinstance(existing.get("terminal"), dict) else {}),
    "backend": "local",
    "persistent_shell": True,
    "cwd": "/home/agent/workspace",
    "timeout": 300,
}
path.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
    yaml.safe_dump(existing, handle, sort_keys=False)
    handle.flush()
    os.fsync(handle.fileno())
    temporary = handle.name
os.replace(temporary, path)
PY

  cp --no-preserve=mode,ownership "${HERMES_HOME}/config.yaml" "${HERMES_HOME}/profiles/wright/config.yaml.tmp"
  mv "${HERMES_HOME}/profiles/wright/config.yaml.tmp" "${HERMES_HOME}/profiles/wright/config.yaml"

  "${HERMES_CLI}" -p wright config set API_SERVER_ENABLED true
  "${HERMES_CLI}" -p wright config set API_SERVER_HOST "${API_SERVER_HOST:-127.0.0.1}"
  "${HERMES_CLI}" -p wright config set API_SERVER_KEY "${HERMES_API_KEY}"
  "${HERMES_CLI}" -p wright config set API_SERVER_PORT "${API_SERVER_PORT:-8642}"
}

ensure_wright_profile
write_hermes_config

if [ ! -f "${HERMES_HOME}/profiles/wright/SOUL.md" ]; then
  # Write SOUL.md with Wright agent instructions
  cat > "${HERMES_HOME}/profiles/wright/SOUL.md" <<'EOF'
# Hermes Agent Persona

You are Wright, a professional engineering and 3D design assistant.

## File Organization Rules
1. **Deliverables & Final Assets**: When creating, modifying, or exporting final files requested by the user (such as `.scad` OpenSCAD source files, `.stl`/`.3mf` 3D print exports, or final `.png`/`.jpg` rendering images), always place them directly in the main workspace root directory (which is the current working directory, e.g. `./`), or inside user-visible folders there (e.g. `./models/`, `./exports/`, or `./renders/`).
   - For OpenSCAD model tools (`create_model`, `update_model` etc.), specify the `workspace` parameter pointing to the workspace root directory (the current working directory `.` or the absolute path).
   - For OpenSCAD export tools (`export_model`), specify the `output_path` parameter pointing to the workspace root or a subfolder (e.g. `./cube.stl`) so they do not default to temporary directories.
   - For any image render output files, write/save them directly to a user-accessible path in the workspace root or `./renders/` instead of storing them in the `tmp/` directory.
2. **Intermediate & Working Files**: Only use the `tmp/` folder (which maps to the workspace's local `tmp/` folder) for transient internal renders, scratch files, build outputs, cache files, and logs. Do NOT put final files, exports, or requested images in `tmp/`.
EOF

  echo "Hermes profile bootstrapped."
else
  echo "Hermes profile ready at ${HERMES_HOME}/profiles/wright."
fi

# 5. Create default workspace directory
mkdir -p /home/agent/workspace

# 6. Log startup event
if echo "$(date -u) | Container started" >> /var/log/agent-startup.log 2>/dev/null; then
  : # Log succeeded
else
  echo "Warning: /var/log/agent-startup.log is not writable. Continuing without startup logging." >&2
fi

# 7. Start the requested command (typically supervisord)
echo "=== Starting services ==="
exec "$@"
