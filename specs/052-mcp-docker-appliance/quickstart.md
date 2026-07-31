# Quickstart: MCP Docker Appliance

## Build

```bash
docker build -t wright:test -f docker/Dockerfile .
docker build -t wright:mcp-test -f docker/Dockerfile.mcp --build-arg WRIGHT_BASE_IMAGE=wright:test .
```

For the Windows MCP runtime, SolidEdgeMCP source is selected with:

```bash
--build-arg WRIGHT_SOLIDEDGE_MCP_GIT_URL=https://github.com/burhop/SolidEdgeMCP.git
--build-arg WRIGHT_SOLIDEDGE_MCP_GIT_REF=2aad5bd24df6ce1ac9578ad35c4da7ac241b5330
```

For private GitHub MCP repositories, export `GITHUB_TOKEN` with read access or
repair `gh auth login` before building. The helper scripts mount it as the
BuildKit `github_token` secret so credentials do not enter image layers.

The default Windows build already uses those values. At that ref,
SolidEdgeMCP targets Windows/Solid Edge, so Linux bundles keep the entry blocked
instead of installing a non-runnable server.

## Validate Generated Bundle

```bash
python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml
python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check
uv run pytest tests/docker/test_mcp_bundle.py
```

Expected manifest status:

- Applications accepted: `openscad`, `freecad`, `brep`, `playwright`
- MCP servers accepted: `openscad-mcp`, `freecad-mcp`, `brep-mcp`, `playwright-mcp`
- MCP servers blocked for Linux: `solid-edge-mcp`

## Run Smoke

```bash
scripts/docker-mcp-smoke-test.sh
```

The smoke test checks Wright health, Hermes gateway health, generated config,
generated compliance artifacts, and local binary/wrapper presence.
It builds and runs `linux/amd64` by default through
`WRIGHT_MCP_DOCKER_PLATFORM`.

## Seed A Model Provider

Fresh containers may start without an LLM. To reuse a provider across
throwaway containers, copy `docker/llm-seed.example.yaml` outside the repo,
fill it with private provider values, and mount it:

```bash
WRIGHT_API_TOKEN=change-this-long-random-token \
WRIGHT_LLM_CONFIG_FILE=/absolute/host/path/llm-seed.yaml \
./scripts/docker-mcp-run.sh linux-arm64
```

For Codex/ChatGPT login reuse, use `provider: openai-codex` and supply either
a mounted Hermes auth payload through `auth_file` or inline `tokens` in the
private seed file. Startup writes only the Hermes profile config/auth state and
the non-secret `/home/agent/.config/wright/llm-provider-status.json` summary.

## Run UI Workflow

```bash
WRIGHT_MCP_PLAYWRIGHT_BASE_URL=http://127.0.0.1:18080 \
  npx playwright test tests/ui-integration/mcp-appliance.spec.ts --reporter=list
```

The Playwright test opens Wright, creates/selects a fresh workspace, starts the
Linux-runnable MCPs, and submits a prompt asking for health across OpenSCAD,
FreeCAD, BREP, and Playwright. To test a Windows image with SolidEdgeMCP, set
`WRIGHT_MCP_PLAYWRIGHT_REQUIRED_SERVERS=openscad-mcp,freecad-mcp,brep-mcp,solid-edge-mcp,playwright-mcp`.

## Engineer Docs

See `docs/getting-started/quickstart-docker-mcp.md`.

## Validation Evidence

- `python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml`: passed on 2026-07-30.
- `python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check`: passed on 2026-07-30.
- `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest tests/docker/test_mcp_bundle.py`: 25 passed on 2026-07-30.
- `docker build --platform linux/arm64 -t wright:standard-linux-arm64 -f docker/Dockerfile .`: passed on 2026-07-30.
- `docker build --platform linux/arm64 -t wright:engineering-tools-linux-arm64-appimage-freecad-test -f docker/Dockerfile.mcp --build-arg WRIGHT_BASE_IMAGE=wright:standard-linux-arm64 --build-arg WRIGHT_MCP_BUNDLE_FILE=mcp-bundle.linux-arm64.yaml .`: passed on 2026-07-30.
- `WRIGHT_MCP_SKIP_BUILD=1 ... scripts/docker-mcp-smoke-test.sh`: passed on 2026-07-30 for `linux/arm64`.
- `PLAYWRIGHT_INCLUDE_LIVE=1 PLAYWRIGHT_BASE_URL=http://192.168.1.163:18181 ... npx playwright test tests/ui-integration/mcp-appliance.spec.ts --reporter=line`: 1 passed on 2026-07-30 against a clean `linux/arm64` container.
