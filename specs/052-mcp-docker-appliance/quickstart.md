# Quickstart: MCP Docker Appliance

## Build

```bash
docker build -t wright:test -f docker/Dockerfile .
docker build -t wright:mcp-test -f docker/Dockerfile.mcp --build-arg WRIGHT_BASE_IMAGE=wright:test .
```

To install the internal SolidEdgeMCP source during the build, pass:

```bash
--build-arg WRIGHT_SOLIDEDGE_MCP_GIT_URL=https://github.com/burhop/SolidEdgeMCP.git
--build-arg WRIGHT_SOLIDEDGE_MCP_GIT_REF=2aad5bd24df6ce1ac9578ad35c4da7ac241b5330
```

For private GitHub MCP repositories, export `GITHUB_TOKEN` with read access or
repair `gh auth login` before building. The helper scripts mount it as the
BuildKit `github_token` secret so credentials do not enter image layers.

The default build already uses those values. At that ref, SolidEdgeMCP targets
Windows/Solid Edge, so the Linux wrapper reports the platform limitation.

## Validate Generated Bundle

```bash
python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml
python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check
uv run pytest tests/docker/test_mcp_bundle.py
```

Expected manifest status:

- Applications accepted: `openscad`, `freecad`, `brep`, `playwright`
- MCP servers accepted: `openscad-mcp`, `freecad-mcp`, `brep-mcp`, `solid-edge-mcp`, `playwright-mcp`

## Run Smoke

```bash
scripts/docker-mcp-smoke-test.sh
```

The smoke test checks Wright health, Hermes gateway health, generated config,
generated compliance artifacts, and local binary/wrapper presence.
It builds and runs `linux/amd64` by default through
`WRIGHT_MCP_DOCKER_PLATFORM`.

## Run UI Workflow

```bash
WRIGHT_MCP_PLAYWRIGHT_BASE_URL=http://127.0.0.1:18080 \
  npx playwright test tests/ui-integration/mcp-appliance.spec.ts --reporter=list
```

The Playwright test opens Wright, creates/selects a fresh workspace, and submits
a prompt asking for health across OpenSCAD, FreeCAD, BREP, SolidEdgeMCP, and
Playwright.

## Engineer Docs

See `docs/getting-started/quickstart-docker-mcp.md`.

## Validation Evidence

- `python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml`: passed on 2026-07-30.
- `python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check`: passed on 2026-07-30.
- `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest tests/docker/test_mcp_bundle.py`: 17 passed on 2026-07-30.
