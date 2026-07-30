#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-linux-arm64}"
HOST_PORT="${WRIGHT_MCP_HOST_PORT:-8080}"
TOKEN="${WRIGHT_API_TOKEN:?WRIGHT_API_TOKEN must be set}"
BIND_HOST="${WRIGHT_MCP_BIND:-127.0.0.1}"
PUBLIC_ORIGIN="${WRIGHT_MCP_PUBLIC_ORIGIN:-}"
if [ -z "$PUBLIC_ORIGIN" ] && [ -n "${WRIGHT_MCP_PUBLIC_HOST:-}" ]; then
  case "$WRIGHT_MCP_PUBLIC_HOST" in
    http://*|https://*) PUBLIC_ORIGIN="${WRIGHT_MCP_PUBLIC_HOST%/}" ;;
    *) PUBLIC_ORIGIN="http://${WRIGHT_MCP_PUBLIC_HOST}:${HOST_PORT}" ;;
  esac
fi

DEFAULT_ALLOWED_ORIGINS="http://127.0.0.1:${HOST_PORT},http://localhost:${HOST_PORT},http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5173,http://localhost:5173"
ALLOWED_ORIGINS="${WRIGHT_ALLOWED_ORIGINS:-$DEFAULT_ALLOWED_ORIGINS}"
if [ -n "$PUBLIC_ORIGIN" ]; then
  ALLOWED_ORIGINS="${PUBLIC_ORIGIN},${ALLOWED_ORIGINS}"
fi

case "$PROFILE" in
  linux-amd64)
    IMAGE="${WRIGHT_MCP_IMAGE:-wright:mcp-linux-amd64}"
    PLATFORM="${WRIGHT_MCP_DOCKER_PLATFORM:-linux/amd64}"
    PREFIX="${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp_linux_amd64}"
    ;;
  linux-arm64)
    IMAGE="${WRIGHT_MCP_IMAGE:-wright:mcp-linux-arm64}"
    PLATFORM="${WRIGHT_MCP_DOCKER_PLATFORM:-linux/arm64}"
    PREFIX="${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp_linux_arm64}"
    ;;
  *)
    echo "Usage: $0 [linux-amd64|linux-arm64]" >&2
    exit 64
    ;;
esac

docker run --rm \
  --platform "$PLATFORM" \
  --user root \
  --entrypoint /bin/sh \
  -v "${PREFIX}_data:/home/agent/.local/share/wright" \
  -v "${PREFIX}_workspaces:/home/agent/workspace" \
  -v "${PREFIX}_config:/home/agent/.config/wright" \
  -v "${PREFIX}_hermes:/home/agent/.hermes" \
  -v "${PREFIX}_logs:/var/log" \
  "$IMAGE" \
  -c 'mkdir -p /home/agent/.local/share/wright /home/agent/workspace /home/agent/.config/wright /home/agent/.hermes /var/log && chown -R agent:agent /home/agent/.local/share/wright /home/agent/workspace /home/agent/.config/wright /home/agent/.hermes /var/log'

docker run -d \
  --name "${WRIGHT_MCP_CONTAINER:-${PREFIX}_agent}" \
  --platform "$PLATFORM" \
  -p "${BIND_HOST}:${HOST_PORT}:8000" \
  -e WRIGHT_AUTH_MODE="${WRIGHT_AUTH_MODE:-enforced}" \
  -e WRIGHT_BIND_HOST="${WRIGHT_BIND_HOST:-$BIND_HOST}" \
  -e WRIGHT_ALLOWED_ORIGINS="$ALLOWED_ORIGINS" \
  -e WRIGHT_API_TOKEN="$TOKEN" \
  -e LLM_API_URL="${LLM_API_URL:-}" \
  -e LLM_API_KEY="${LLM_API_KEY:-}" \
  -e LLM_API_MODEL="${LLM_API_MODEL:-}" \
  -e WRIGHT_MCP_HERMES_CONFIG=/opt/wright/mcp/generated/hermes-mcp.generated.yaml \
  -e WRIGHT_MCP_STATUS=/opt/wright/mcp/generated/mcp-bundle-status.json \
  -v "${PREFIX}_data:/home/agent/.local/share/wright" \
  -v "${PREFIX}_workspaces:/home/agent/workspace" \
  -v "${PREFIX}_config:/home/agent/.config/wright" \
  -v "${PREFIX}_hermes:/home/agent/.hermes" \
  -v "${PREFIX}_logs:/var/log" \
  "$IMAGE"

echo "Started $IMAGE at http://${BIND_HOST}:${HOST_PORT}"
if [ -n "$PUBLIC_ORIGIN" ]; then
  echo "Remote browser origin allowed: $PUBLIC_ORIGIN"
fi
