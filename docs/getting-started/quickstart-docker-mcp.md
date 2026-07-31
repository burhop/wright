# Wright MCP Docker Quickstart

This image is the normal Wright Docker appliance with a reviewed engineering
MCP bundle installed. You still open Wright in a browser and use the same
API/token workflow as the standard container, but this flavor starts with CAD
and browser-control MCPs already configured.

Workspaces are created under `/home/agent/workspace`, which the Docker Compose
and helper-script paths mount as a persistent named volume.

For the full managed image matrix, including Linux arm64 and Windows-host
builds, see [Docker image family](docker-image-family.md).

## What This Image Includes

- OpenSCAD plus OpenSCAD MCP.
- FreeCAD plus FreeCAD MCP.
- BREP CAD tooling plus BREP MCP.
- SolidEdgeMCP metadata for the Windows MCP runtime. Solid Edge itself is not
  redistributed in this Linux image, and the current SolidEdgeMCP server target
  is Windows/Solid Edge only.
- Playwright plus Playwright MCP for driving Wright and browser-based CAD tools.

## Before You Start

Create `docker/.env` the same way you do for the standard appliance. At minimum
set a unique `WRIGHT_API_TOKEN`. The container can start without a language
model, but agent prompts need one of the provider setup paths below.

```bash
WRIGHT_API_TOKEN=change-this-long-random-token
```

For a normal OpenAI-compatible endpoint, keep using the existing environment
variables:

```bash
LLM_API_URL=https://your-provider.example/v1
LLM_API_KEY=your-key
LLM_API_MODEL=your-model
```

For repeated Docker tests, use a provider seed file instead. Copy
`docker/llm-seed.example.yaml` to a private location outside the repo, fill in
the provider values, then mount it read-only:

```bash
WRIGHT_LLM_CONFIG_FILE=/absolute/host/path/llm-seed.yaml \
./scripts/docker-mcp-run.sh linux-arm64
```

With compose:

```bash
WRIGHT_LLM_CONFIG_FILE=/absolute/host/path/llm-seed.yaml \
docker compose -f docker-compose.mcp.yml -f docker-compose.llm-seed.yml up -d --build
```

Codex/ChatGPT login reuse is supported through Hermes' `openai-codex` provider.
A seed file can point at a mounted Hermes auth payload:

```yaml
version: 1
provider: openai-codex
model: gpt-5.4-mini
auth_file: /run/secrets/wright/hermes-auth.json
```

Use a model that is supported by the Hermes `openai-codex` provider for
ChatGPT sign-in. For this appliance path, `gpt-5.4-mini` is the known working
low-cost default; placeholder names such as `codex-test-model` will authenticate
successfully but fail when chat starts.

When using `scripts/docker-mcp-run.sh`, mount that auth file by setting:

```bash
WRIGHT_LLM_CONFIG_FILE=/absolute/host/path/codex-seed.yaml \
WRIGHT_LLM_AUTH_FILE=/absolute/host/path/hermes-auth.json \
./scripts/docker-mcp-run.sh linux-arm64
```

The mounted auth file must contain Hermes `providers.openai-codex.tokens` with
both `access_token` and `refresh_token`, or a seed file can inline a `tokens`
mapping for disposable local testing. Do not commit seed or auth files.

For the Windows MCP runtime, SolidEdgeMCP source is fetched from GitHub by
default. To override the source or test a newer reviewed commit, set both
build-time variables:

```bash
export WRIGHT_SOLIDEDGE_MCP_GIT_URL=https://github.com/burhop/SolidEdgeMCP.git
export WRIGHT_SOLIDEDGE_MCP_GIT_REF=2aad5bd24df6ce1ac9578ad35c4da7ac241b5330
```

If that repository is private, export `GITHUB_TOKEN` with read access before
building, or sign in with `gh auth login`. The Docker helpers pass the token as
a BuildKit secret named `github_token`; do not put tokens in Docker build args.

The ref must be exact. Do not use `main`, `dev`, or another floating branch for
a distributed trial image.

At that ref, `src/SolidEdgeMcpServer/SolidEdgeMcpServer.csproj` targets
`net10.0-windows`. Linux bundles keep SolidEdgeMCP blocked instead of
installing a non-runnable local server.

## Run With Docker Compose

Build the standard image first, then the MCP flavor:

```bash
docker build -t wright:test -f docker/Dockerfile .
docker compose -f docker-compose.mcp.yml up -d --build
```

The current appliance target is `linux/amd64`, matching the standard release
constraint. On an ARM workstation with Docker emulation enabled, the compose
file uses `WRIGHT_MCP_DOCKER_PLATFORM=linux/amd64` by default.

## Open Wright

Open:

```text
http://127.0.0.1:8080
```

Use the same token you placed in `WRIGHT_API_TOKEN`.

If no model provider was configured before startup, open **Model Setup** in the
left navigation. Use **Start Login** for Codex/ChatGPT; Wright starts Hermes'
Codex device-code login, shows the OpenAI URL and code, then polls until the
Hermes profile is connected. Use **OpenAI-Compatible Endpoint** for OpenAI API,
OpenRouter, Groq, Ollama, LM Studio, or Docker Model Runner style `/v1`
servers.

## Remote Access

The compose file binds to localhost by default. For a trusted test machine on a
private engineering LAN, set the bind address and add the exact browser origin
engineers will use from their PCs:

```bash
WRIGHT_MCP_BIND=0.0.0.0 \
WRIGHT_ALLOWED_ORIGINS=http://<host-lan-ip>:8080,http://localhost:8080,http://127.0.0.1:8080 \
docker compose -f docker-compose.mcp.yml up -d --build
```

Use a strong token and do not expose this port to the public internet.

When using `scripts/docker-mcp-run.sh`, set `WRIGHT_MCP_PUBLIC_HOST` or
`WRIGHT_MCP_PUBLIC_ORIGIN` instead:

```bash
WRIGHT_MCP_BIND=0.0.0.0 \
WRIGHT_MCP_PUBLIC_HOST=<host-lan-ip> \
WRIGHT_API_TOKEN=change-this-long-random-token \
./scripts/docker-mcp-run.sh linux-arm64
```

## Included Tools

| Tool | Included App | MCP Server | Good First Prompt |
|---|---|---|---|
| OpenSCAD | OpenSCAD | `openscad-mcp` | Create a 10 mm cube and export STL. |
| FreeCAD | FreeCAD AppImage | `freecad-mcp` | Create a 10 mm by 8 mm by 6 mm box named `WrightBox`. |
| BREP | `brep` CLI from `brepjs-cad` | `brep-mcp` | Create and verify a 40 mm by 20 mm by 10 mm BREP box and export STEP. |
| Solid Edge | Windows host only | `solid-edge-mcp` in the Windows runtime | Create a 20 mm by 20 mm by 10 mm Solid Edge part under the workspace. |
| Playwright | Playwright Chromium | `playwright-mcp` | Open Wright and confirm the health page responds. |

The Linux images launch the pinned `brepjs-cad` MCP through
`/opt/wright/mcp/bin/brep-mcp-wrapped`. That wrapper leaves the installed
package files untouched and points the MCP server at the package's file-backed
CLI entry so `run_program` and `export_part` work reliably in Docker.

The image also installs the browser payload requested by the pinned
`@playwright/mcp` package. This is separate from the general Playwright
Chromium install because the MCP package may depend on a different browser
revision.

## Verification Prompts

Try these from a fresh workspace:

```text
Use OpenSCAD to create a 10 mm cube and save both the SCAD source and STL export.
```

```text
Use FreeCAD to create a document with a 10 mm by 8 mm by 6 mm box named WrightBox and report the volume.
```

```text
Use BREP MCP to create a 40 mm by 20 mm by 10 mm box, verify dimensions, and export STEP.
```

```text
Use Playwright MCP to open http://127.0.0.1:8080 and confirm Wright is reachable.
```

For Solid Edge, use the pinned source on a Windows host with Solid Edge
installed. The Linux image does not contain a Solid Edge license, vendor SDK,
desktop application, or runnable SolidEdgeMCP backend.

## Cleanup

```bash
docker compose -f docker-compose.mcp.yml down
docker volume rm wright_mcp_data wright_mcp_workspaces wright_mcp_config wright_mcp_hermes wright_mcp_logs
```

## Third-Party License

The image writes third-party evidence to:

```text
/opt/wright/mcp/generated/licenses/THIRD-PARTY-COMPLIANCE.json
```

GPL/LGPL runtime components are included unmodified with source-access and
no-warranty notices beside that file. Source-configured components such as
SolidEdgeMCP must keep their own approval and redistribution terms current in
the Windows bundle manifest before that image is shared.
