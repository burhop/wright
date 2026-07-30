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

# 1. Validate LLM provider seed
if [ -z "${LLM_API_URL}" ] && [ -z "${WRIGHT_LLM_PROVIDER}" ] && [ -z "${WRIGHT_LLM_CONFIG_FILE}" ]; then
  echo "Warning: no LLM provider is configured. Use the Setup Web UI, WRIGHT_LLM_CONFIG_FILE, or WRIGHT_LLM_PROVIDER." >&2
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
  "${HERMES_CLI}" -p wright config set API_SERVER_KEY -- "${HERMES_API_KEY}"
  "${HERMES_CLI}" -p wright config set API_SERVER_PORT "${API_SERVER_PORT:-8642}"
}

apply_llm_provider_seed() {
  local profile_config="${HERMES_HOME}/profiles/wright/config.yaml"
  local profile_auth="${HERMES_HOME}/profiles/wright/auth.json"
  local status_path="/home/agent/.config/wright/llm-provider-status.json"
  local python_cmd=("/workspace/.venv/bin/python")
  if [ ! -x "${python_cmd[0]}" ]; then
    python_cmd=(/usr/local/bin/uv run --project /workspace python)
  fi

  if "${python_cmd[@]}" -m agent_adapters.llm_seed \
      --config-path "${profile_config}" \
      --auth-path "${profile_auth}" \
      --status-path "${status_path}"; then
    echo "LLM provider seed processed."
  else
    echo "Warning: failed to apply LLM provider seed. Continuing so the Setup Web UI can repair it." >&2
  fi
}

materialize_mcp_bundle_config() {
  local generated_config="${WRIGHT_MCP_HERMES_CONFIG:-}"
  local generated_status="${WRIGHT_MCP_STATUS:-}"
  if [ -z "${generated_config}" ] || [ ! -f "${generated_config}" ]; then
    return 0
  fi

  export WRIGHT_MCP_GENERATED_CONFIG="${generated_config}"
  export WRIGHT_MCP_PROFILE_CONFIG="${HERMES_HOME}/profiles/wright/config.yaml"
  /opt/hermes/.venv/bin/python <<'PY'
import os
import pathlib
import tempfile
import yaml

source = pathlib.Path(os.environ["WRIGHT_MCP_GENERATED_CONFIG"])
path = pathlib.Path(os.environ["WRIGHT_MCP_PROFILE_CONFIG"])
generated = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
if not isinstance(generated, dict):
    raise SystemExit("generated MCP configuration must be a mapping")
generated_servers = generated.get("mcp_servers")
if not isinstance(generated_servers, dict):
    raise SystemExit("generated MCP configuration must include mcp_servers")
existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
if not isinstance(existing, dict):
    raise SystemExit("Hermes profile configuration must be a mapping")
servers = existing.get("mcp_servers")
if not isinstance(servers, dict):
    servers = {}
for name, config in generated_servers.items():
    servers[name] = config
existing["mcp_servers"] = servers
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
    yaml.safe_dump(existing, handle, sort_keys=False)
    handle.flush()
    os.fsync(handle.fileno())
    temporary = handle.name
os.replace(temporary, path)
PY

  mkdir -p /home/agent/.config/wright
  cp --no-preserve=mode,ownership "${generated_config}" /home/agent/.config/wright/mcp-bundle.generated.yaml
  if [ -n "${generated_status}" ] && [ -f "${generated_status}" ]; then
    cp --no-preserve=mode,ownership "${generated_status}" /home/agent/.config/wright/mcp-bundle-status.json
  fi
  echo "MCP bundle configuration materialized."
}

ensure_wright_profile
write_hermes_config
apply_llm_provider_seed
materialize_mcp_bundle_config

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
