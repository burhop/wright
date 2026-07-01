#!/bin/bash
set -euo pipefail

export HOME="${HOME:-/home/agent}"
export HERMES_HOME="${HERMES_HOME:-/home/agent/.hermes}"
export HERMES_PROFILE="${HERMES_PROFILE:-wright}"
export WRIGHT_REPO_DIR="${WRIGHT_REPO_DIR:-/workspace}"
export DATABASE_PATH="${DATABASE_PATH:-/home/agent/.local/share/wright/state.db}"
export HERMES_API_KEY="${HERMES_API_KEY:-${API_SERVER_KEY:-wright-local-dev}}"
export API_SERVER_KEY="${API_SERVER_KEY:-$HERMES_API_KEY}"
export PATH="/home/agent/.local/bin:/home/agent/.hermes/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

case "${LLM_API_MODEL:-}" in
  ""|"your-default-model")
    export LLM_API_MODEL="${HERMES_DEFAULT_MODEL:-nemotron-nano}"
    ;;
esac

case "${LLM_API_URL:-}" in
  ""|"https://your-llm-endpoint/v1")
    export LLM_API_URL="${HERMES_DEFAULT_LLM_API_URL:-http://192.168.1.165:8000/v1}"
    ;;
esac

case "${LLM_API_KEY:-}" in
  ""|"sk-your-key-here")
    export LLM_API_KEY="${NVIDIA_API_KEY:-not-needed}"
    ;;
esac

HERMES_CLI="${HERMES_CLI:-$(command -v hermes || true)}"
SETUP_LOG="/var/log/hackathon-setup.log"

log_setup() {
  echo "$(date -u) | $*" >> "$SETUP_LOG" 2>/dev/null || true
}

echo "=== Wright Nous Hackathon Container Starting ==="
echo "  Wright repo : ${WRIGHT_REPO_DIR}"
echo "  Hermes home : ${HERMES_HOME}"
echo "  LLM URL     : ${LLM_API_URL:-<setup-pending>}"
echo "  Model       : ${LLM_API_MODEL:-${HERMES_DEFAULT_MODEL:-nemotron-nano}}"

mkdir -p \
  "${HERMES_HOME}/profiles/${HERMES_PROFILE}/sessions" \
  "${HERMES_HOME}/profiles/${HERMES_PROFILE}/skills" \
  "${HERMES_HOME}/webui/sessions" \
  "${HERMES_HOME}/webui/workspace" \
  /home/agent/.npm \
  /home/agent/.backups/etc \
  /home/agent/.local/share/wright \
  /home/agent/workspace

if command -v sudo >/dev/null 2>&1; then
  sudo chown -R "$(id -u):$(id -g)" /home/agent/.npm /home/agent/.local "$HERMES_HOME" 2>/dev/null || true
fi

if [ -f "/container-manifest.md" ]; then
  export CONTAINER_MANIFEST="$(cat /container-manifest.md)"
else
  export CONTAINER_MANIFEST=""
fi

write_hermes_config() {
  python3 - <<'PY'
import json
import os
from pathlib import Path

home = Path(os.environ.get("HERMES_HOME", "/home/agent/.hermes"))
profile = os.environ.get("HERMES_PROFILE", "wright")
repo = os.environ.get("WRIGHT_REPO_DIR", "/workspace")
llm_url = os.environ.get("LLM_API_URL") or "http://192.168.1.165:8000/v1"
llm_key = os.environ.get("LLM_API_KEY") or os.environ.get("NVIDIA_API_KEY") or "not-needed"
llm_model = os.environ.get("LLM_API_MODEL") or os.environ.get("HERMES_DEFAULT_MODEL") or "nemotron-nano"
api_key = os.environ.get("HERMES_API_KEY") or os.environ.get("API_SERVER_KEY") or "wright-local-dev"

config = {
    "model": {
        "base_url": llm_url,
        "context_length": 131072,
        "default": llm_model,
        "provider": "custom",
    },
    "custom_providers": [
        {
            "api_key": llm_key,
            "base_url": llm_url,
            "model": llm_model,
            "name": "hackathon-llm",
        }
    ],
    "mcp_servers": {
        "wrightgateway": {
            "command": "uv",
            "args": [
                "run",
                "--project",
                repo,
                "python",
                "-m",
                "tool_registry.gateway",
            ],
            "env": {
                "WRIGHT_API_BASE_URL": "http://127.0.0.1:8000",
                "WRIGHT_REPO_DIR": repo,
                "DATABASE_PATH": os.environ.get("DATABASE_PATH", "/home/agent/.local/share/wright/state.db"),
            },
            "timeout": 300,
            "tools": {"resources": False, "prompts": False},
        },
        "stripe-link": {
            "command": "npx",
            "args": ["-y", "@stripe/link-cli@0.8.1", "--mcp"],
            "enabled": False,
            "timeout": 300,
            "tools": {"resources": False, "prompts": False},
        },
    },
    "terminal": {
        "backend": "local",
        "persistent_shell": True,
        "cwd": "/home/agent/workspace",
        "timeout": 300,
    },
    "toolsets": ["hermes-cli"],
    "api_server": {
        "enabled": True,
        "host": os.environ.get("API_SERVER_HOST", "0.0.0.0"),
        "port": int(os.environ.get("API_SERVER_PORT", "8642")),
        "key": api_key,
    },
}

paths = [
    home / "config.yaml",
    home / "profiles" / profile / "config.yaml",
]
for path in paths:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
PY
}

write_hermes_soul() {
  local soul_path="${HERMES_HOME}/profiles/${HERMES_PROFILE}/SOUL.md"
  if [ -f "$soul_path" ]; then
    return
  fi

  cat > "$soul_path" <<'EOF'
# Wright Hackathon Agent

You are Wright running inside the Nous Hackathon prototype container.

Priorities:
1. Help run business operations for engineering teams using Wright.
2. Treat payment actions as real-world actions that require explicit user approval.
3. Keep secrets out of transcripts, logs, git, screenshots, and demo recordings.
4. Use the Wright gateway MCP for engineering operations and Stripe skills for payments.
5. Prefer safe read-only checks before mutating external services.

Use /home/agent/workspace for user-visible files and /tmp only for temporary scratch data.
EOF
}

install_runtime_integrations() {
  local hermes_python=""
  local candidate
  for candidate in \
    /usr/local/lib/hermes-agent/venv/bin/python \
    /usr/local/lib/hermes-agent/.venv/bin/python
  do
    if [ -x "$candidate" ]; then
      hermes_python="$candidate"
      break
    fi
  done

  if [ -n "$hermes_python" ] && [ -d "${WRIGHT_REPO_DIR}/hermes-plugin-wright" ]; then
    uv pip install --python "$hermes_python" -e "${WRIGHT_REPO_DIR}/hermes-plugin-wright" >> "$SETUP_LOG" 2>&1 || \
      log_setup "warning: failed to refresh editable Wright Hermes plugin"
  else
    log_setup "warning: Hermes Python environment or Wright Hermes plugin was not found"
  fi

  if command -v stripe >/dev/null 2>&1; then
    stripe plugin install projects >> "$SETUP_LOG" 2>&1 || \
      log_setup "warning: stripe projects plugin install did not complete"
  fi

  if [ -n "$HERMES_CLI" ]; then
    for skill in \
      official/payments/stripe-link-cli \
      official/payments/stripe-projects \
      official/payments/mpp-agent
    do
      printf 'y\n' | "$HERMES_CLI" -p "$HERMES_PROFILE" skills install "$skill" >> "$SETUP_LOG" 2>&1 || \
        log_setup "warning: failed to install Hermes skill $skill"
    done
  else
    log_setup "warning: hermes command not found on PATH"
  fi
}

write_hermes_config
write_hermes_soul
install_runtime_integrations

if echo "$(date -u) | Hackathon container started | repo=${WRIGHT_REPO_DIR}" >> /var/log/agent-startup.log 2>/dev/null; then
  :
else
  echo "Warning: /var/log/agent-startup.log is not writable. Continuing." >&2
fi

echo "=== Starting hackathon services ==="
exec "$@"
