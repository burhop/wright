#!/usr/bin/env bash
set -euo pipefail

export MSYS_NO_PATHCONV=1

IMAGE_TAG="${WRIGHT_MCP_DOCKER_IMAGE:-wright:mcp-test}"
BASE_IMAGE_TAG="${WRIGHT_DOCKER_IMAGE:-wright:test}"
CONTAINER_NAME="${WRIGHT_MCP_CONTAINER:-wright-mcp-smoke-$$}"
HOST_PORT="${WRIGHT_MCP_HOST_PORT:-18080}"
SKIP_BUILD="${WRIGHT_MCP_SKIP_BUILD:-0}"
DOCKER_PLATFORM="${WRIGHT_MCP_DOCKER_PLATFORM:-linux/amd64}"
if [ -n "${WRIGHT_MCP_BUNDLE_FILE:-}" ]; then
  BUNDLE_FILE="$WRIGHT_MCP_BUNDLE_FILE"
elif [ "$DOCKER_PLATFORM" = "linux/arm64" ]; then
  BUNDLE_FILE="mcp-bundle.linux-arm64.yaml"
else
  BUNDLE_FILE="mcp-bundle.yaml"
fi
PYTHON_BIN="${PYTHON:-python3}"
DOCKER_SECRET_ARGS=()

configure_github_secret() {
  local token
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    DOCKER_SECRET_ARGS=(--secret id=github_token,env=GITHUB_TOKEN)
    return 0
  fi
  if command -v gh >/dev/null 2>&1; then
    if token="$(gh auth token 2>/dev/null)" && [ -n "$token" ]; then
      export GITHUB_TOKEN="$token"
      DOCKER_SECRET_ARGS=(--secret id=github_token,env=GITHUB_TOKEN)
    fi
  fi
}

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

show_container_diagnostics() {
  echo "Container status for ${CONTAINER_NAME}:" >&2
  docker ps -a --filter "name=^/${CONTAINER_NAME}$" >&2 || true
  echo "Container logs for ${CONTAINER_NAME}:" >&2
  docker logs "$CONTAINER_NAME" >&2 || true
  echo "Supervisor process status for ${CONTAINER_NAME}:" >&2
  docker exec "$CONTAINER_NAME" \
    supervisorctl -c /etc/supervisor/conf.d/wright.conf status >&2 || true
  echo "Wright API stderr for ${CONTAINER_NAME}:" >&2
  docker exec "$CONTAINER_NAME" \
    sh -c 'cat /var/log/supervisor/wright-api-stderr.log' >&2 || true
  echo "Wright API stdout for ${CONTAINER_NAME}:" >&2
  docker exec "$CONTAINER_NAME" \
    sh -c 'cat /var/log/supervisor/wright-api-stdout.log' >&2 || true
}

run_json() {
  "$PYTHON_BIN" - "$@"
}

if [ "$SKIP_BUILD" != "1" ]; then
  configure_github_secret
  docker build --platform "$DOCKER_PLATFORM" -t "$BASE_IMAGE_TAG" -f docker/Dockerfile .
  docker build \
    "${DOCKER_SECRET_ARGS[@]}" \
    --platform "$DOCKER_PLATFORM" \
    -t "$IMAGE_TAG" \
    -f docker/Dockerfile.mcp \
    --build-arg "WRIGHT_BASE_IMAGE=$BASE_IMAGE_TAG" \
    --build-arg "WRIGHT_MCP_BUNDLE_FILE=$BUNDLE_FILE" \
    --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=${WRIGHT_SOLIDEDGE_MCP_GIT_URL:-https://github.com/burhop/SolidEdgeMCP.git}" \
    --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=${WRIGHT_SOLIDEDGE_MCP_GIT_REF:-2aad5bd24df6ce1ac9578ad35c4da7ac241b5330}" \
    .
fi

docker run --rm --platform "$DOCKER_PLATFORM" --entrypoint /opt/hermes/.venv/bin/python "$IMAGE_TAG" \
  /opt/wright/mcp/verify-bundle.py /opt/wright/mcp/mcp-bundle.yaml >/tmp/wright-mcp-validation.json

docker run --rm --platform "$DOCKER_PLATFORM" --entrypoint test "$IMAGE_TAG" \
  -f /opt/wright/mcp/generated/hermes-mcp.generated.yaml
docker run --rm --platform "$DOCKER_PLATFORM" --entrypoint test "$IMAGE_TAG" \
  -f /opt/wright/mcp/generated/licenses/THIRD-PARTY-COMPLIANCE.json
docker run --rm --platform "$DOCKER_PLATFORM" --entrypoint test "$IMAGE_TAG" \
  -f /container-manifest.mcp.md

docker run --rm --platform "$DOCKER_PLATFORM" --entrypoint sh "$IMAGE_TAG" -c '
  command -v openscad >/dev/null &&
  test -x /opt/wright/mcp/bin/freecadcmd &&
  command -v brep >/dev/null &&
  brep --help >/dev/null &&
  command -v brep-mcp >/dev/null &&
  test -x /opt/wright/mcp/bin/brep-mcp-wrapped &&
  command -v playwright >/dev/null &&
  command -v playwright-mcp >/dev/null &&
  grep -R "@playwright/mcp/node_modules/playwright-core" /opt/wright/mcp/playwright-browsers/.links >/dev/null &&
  test -x /opt/wright/mcp/bin/freecad-mcp-wrapped
'

docker run --rm -i --platform "$DOCKER_PLATFORM" \
  --entrypoint /workspace/.venv/bin/python "$IMAGE_TAG" - <<'PY'
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    parameters = StdioServerParameters(
        command="/opt/wright/mcp/bin/brep-mcp-wrapped",
        args=[],
        env={**os.environ, "BREP_WORKSPACE": "/home/agent"},
        cwd="/home/agent",
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            tools = await client.list_tools()
    names = {tool.name for tool in tools.tools}
    if "run_program" not in names:
        raise SystemExit(f"BREP MCP did not publish run_program: {sorted(names)}")


asyncio.run(main())
PY

docker run -d \
  --platform "$DOCKER_PLATFORM" \
  --name "$CONTAINER_NAME" \
  -p "127.0.0.1:${HOST_PORT}:8000" \
  -e WRIGHT_API_TOKEN="${WRIGHT_API_TOKEN:-ci-mcp-smoke-token-000000000000000000000000}" \
  -e WRIGHT_WORKSPACES_DIR=/home/agent/workspace \
  -e WRIGHT_WORKSPACE_PATH=/home/agent/workspace \
  -e LLM_API_URL="${LLM_API_URL:-https://example.com/v1}" \
  -e LLM_API_KEY="${LLM_API_KEY:-not-needed}" \
  -e LLM_API_MODEL="${LLM_API_MODEL:-test-model}" \
  "$IMAGE_TAG" >/dev/null

for attempt in $(seq 1 30); do
  if docker exec "$CONTAINER_NAME" curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    break
  fi
  RUNNING_STATE=$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null || echo false)
  if [ "$RUNNING_STATE" != "true" ]; then
    show_container_diagnostics
    echo "Wright MCP container exited before API health became ready" >&2
    exit 1
  fi
  if [ "$attempt" = "30" ]; then
    show_container_diagnostics
    echo "Wright API health did not become ready" >&2
    exit 1
  fi
  sleep 2
done

for attempt in $(seq 1 30); do
  PROCESS_STATUS=$(docker exec "$CONTAINER_NAME" \
    supervisorctl -c /etc/supervisor/conf.d/wright.conf status 2>&1 || true)
  if echo "$PROCESS_STATUS" | grep -q "wright-api.*RUNNING" && \
     echo "$PROCESS_STATUS" | grep -q "hermes-gateway.*RUNNING"; then
    break
  fi
  if [ "$attempt" = "30" ]; then
    echo "$PROCESS_STATUS" >&2
    show_container_diagnostics
    echo "Required supervised services did not become ready" >&2
    exit 1
  fi
  sleep 2
done

STATUS_JSON=$(docker exec "$CONTAINER_NAME" cat /opt/wright/mcp/generated/mcp-bundle-status.json)
STATUS_JSON="$STATUS_JSON" run_json <<'PY'
import json
import os

payload = json.loads(os.environ["STATUS_JSON"])
apps = {entry["id"]: entry for entry in payload["applications"]}
servers = {entry["id"]: entry for entry in payload["mcp_servers"]}

for key in ("openscad", "freecad", "brep", "playwright"):
    actual = apps.get(key, {}).get("status")
    if actual != "accepted":
        raise SystemExit(f"{key} application status mismatch: {actual} != accepted")

expected_servers = {
    "openscad-mcp": "accepted",
    "freecad-mcp": "accepted",
    "brep-mcp": "accepted",
    "solid-edge-mcp": "blocked",
    "playwright-mcp": "accepted",
}

for key, expected in expected_servers.items():
    actual = servers.get(key, {}).get("status")
    if actual != expected:
        raise SystemExit(f"{key} MCP status mismatch: {actual} != {expected}")
PY

docker exec "$CONTAINER_NAME" test -f /home/agent/.config/wright/mcp-bundle-status.json
for server in openscad-mcp freecad-mcp brep-mcp playwright-mcp; do
  docker exec "$CONTAINER_NAME" grep -q "$server" /home/agent/.hermes/profiles/wright/config.yaml
done

echo "MCP Docker smoke passed for $IMAGE_TAG at http://127.0.0.1:${HOST_PORT}"
