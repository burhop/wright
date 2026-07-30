#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-linux-arm64}"
STANDARD_IMAGE="${WRIGHT_STANDARD_IMAGE:-wright:standard-${PROFILE}}"
MCP_IMAGE="${WRIGHT_MCP_IMAGE:-wright:mcp-${PROFILE}}"
DOCKER_SECRET_ARGS=()

configure_github_secret() {
  local token
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    DOCKER_SECRET_ARGS=(--secret id=github_token,env=GITHUB_TOKEN)
    return 0
  fi
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if token="$(gh auth token 2>/dev/null)" && [ -n "$token" ]; then
      export GITHUB_TOKEN="$token"
      DOCKER_SECRET_ARGS=(--secret id=github_token,env=GITHUB_TOKEN)
    fi
  fi
}

configure_github_secret

case "$PROFILE" in
  standard)
    PLATFORM="${WRIGHT_DOCKER_PLATFORM:-linux/amd64}"
    IMAGE="${WRIGHT_STANDARD_IMAGE:-wright:standard-linux-amd64}"
    docker build --platform "$PLATFORM" -t "$IMAGE" -f docker/Dockerfile .
    ;;
  linux-amd64)
    PLATFORM="${WRIGHT_MCP_DOCKER_PLATFORM:-linux/amd64}"
    BASE_IMAGE="${WRIGHT_BASE_IMAGE:-wright:standard-linux-amd64}"
    MCP_IMAGE="${WRIGHT_MCP_IMAGE:-wright:mcp-linux-amd64}"
    docker build --platform "$PLATFORM" -t "$BASE_IMAGE" -f docker/Dockerfile .
    docker build "${DOCKER_SECRET_ARGS[@]}" --platform "$PLATFORM" -t "$MCP_IMAGE" -f docker/Dockerfile.mcp \
      --build-arg "WRIGHT_BASE_IMAGE=$BASE_IMAGE" \
      --build-arg "WRIGHT_MCP_BUNDLE_FILE=mcp-bundle.yaml" \
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=${WRIGHT_SOLIDEDGE_MCP_GIT_URL:-https://github.com/burhop/SolidEdgeMCP.git}" \
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=${WRIGHT_SOLIDEDGE_MCP_GIT_REF:-2aad5bd24df6ce1ac9578ad35c4da7ac241b5330}" \
      .
    ;;
  linux-arm64)
    PLATFORM="${WRIGHT_MCP_DOCKER_PLATFORM:-linux/arm64}"
    BASE_IMAGE="${WRIGHT_BASE_IMAGE:-wright:standard-linux-arm64}"
    MCP_IMAGE="${WRIGHT_MCP_IMAGE:-wright:mcp-linux-arm64}"
    docker build --platform "$PLATFORM" -t "$BASE_IMAGE" -f docker/Dockerfile .
    docker build "${DOCKER_SECRET_ARGS[@]}" --platform "$PLATFORM" -t "$MCP_IMAGE" -f docker/Dockerfile.mcp \
      --build-arg "WRIGHT_BASE_IMAGE=$BASE_IMAGE" \
      --build-arg "WRIGHT_MCP_BUNDLE_FILE=mcp-bundle.linux-arm64.yaml" \
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_URL=${WRIGHT_SOLIDEDGE_MCP_GIT_URL:-https://github.com/burhop/SolidEdgeMCP.git}" \
      --build-arg "WRIGHT_SOLIDEDGE_MCP_GIT_REF=${WRIGHT_SOLIDEDGE_MCP_GIT_REF:-2aad5bd24df6ce1ac9578ad35c4da7ac241b5330}" \
      .
    ;;
  windows-amd64)
    echo "Build the Windows image from a Windows 11 host with Docker Desktop in Windows container mode:" >&2
    echo "  pwsh -File scripts/docker-image-family-build.ps1 -Profile windows-amd64" >&2
    exit 64
    ;;
  *)
    echo "Usage: $0 [standard|linux-amd64|linux-arm64|windows-amd64]" >&2
    exit 64
    ;;
esac
