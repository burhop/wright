# Quick Start: GB10 and DGX Workstations

Use this path for NVIDIA GB10, DGX Spark-style, DGX Station-style, or similar
local AI workstations where Wright runs beside a local model server and selected
engineering tools.

Wright is alpha software and bring-your-own-AI. The public-alpha appliance and
local checkout do not bundle model weights, an LLM runtime, hosted provider
credentials, CUDA variants, paid engineering software, or MCP-specific host
software. Treat the workstation as the place where you provide those pieces
explicitly.

## Recommended Topology

Run Wright as the control plane and run heavy AI or engineering backends beside
it:

| Component | Recommended location | Notes |
| --- | --- | --- |
| Wright API/UI/gateway | Docker appliance or local checkout | CPU is enough for the core app. |
| Local LLM server | Host OS or a dedicated model container | Expose an OpenAI-compatible `/v1` API. |
| Selected MCP host tools | Per selected MCP validation container or host install | Install only what that MCP needs. |
| Hermes Desktop/CLI | Host OS | Enable the Hermes API server when using the plugin. |

This keeps the Wright base image small and preserves the clean-container MCP
validation boundary.

## Docker Appliance Path

Start with the minimal appliance:

```bash
docker compose -f docker-compose.minimal.yml up -d --build
```

Open:

```text
http://localhost:8080
```

If your local model server runs on the workstation host, point Wright at the
host from inside Docker:

```env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_API_KEY=not-needed
LLM_API_MODEL=local-model-name
```

On Linux, add host gateway mapping in a local compose override when Docker does
not resolve `host.docker.internal` automatically:

```yaml
services:
  agent:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Then run:

```bash
docker compose -f docker-compose.minimal.yml -f docker-compose.workstation.yml up -d --build
```

## Local Checkout Path

For source iteration on the workstation, use the PC local setup:

```bash
uv sync --all-packages --all-groups
npm ci
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
npm run dev --workspace=apps/web -- --host 127.0.0.1
```

Set `LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL` to your workstation model
server or hosted provider.

## GPU Notes

The current release workflow smokes `linux/amd64`. `linux/arm64`, CUDA-enabled
Wright images, NVIDIA Container Toolkit assumptions, and `--gpus all` compose
profiles are alpha follow-up work until they are built and smoked in release CI.

If a selected MCP server or model container needs GPU passthrough, validate that
specific server with the NVIDIA Container Toolkit installed on the host and
record the exact driver, toolkit, image, command, and probe result in the MCP
setup recipe. The Wright control-plane container itself should not require GPU
access unless the selected workflow proves it.

## MCP Validation Boundary

Follow the clean-container process in
[MCP server testing process](../mcp-catalog/mcp-server-testing-process.md):

1. Start from a clean Wright container.
2. Install only the selected MCP package and its testable free/open host
   dependencies.
3. Do not add MCP-specific host software to the base Docker image just to make
   catalog validation pass.
4. Run `initialize`, `notifications/initialized`, `tools/list`, and one safe
   backend-touching probe before marking the MCP fully tested.
5. Record workstation-specific assumptions in
   `docs/mcp-catalog/mcp-server-setup-recipes.md`.

## Health Checks

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/agent/health
curl http://localhost:8080/api/inference/health
```

If the inference check is disconnected, verify that the workstation model server
is listening on the host and that the `LLM_API_URL` value is reachable from the
Wright runtime.

## Troubleshooting Sandboxing (Ubuntu 24.04+)

If you run sandboxed tool execution on Ubuntu 24.04+ (or newer Linux kernels that enforce AppArmor unprivileged user namespace restrictions) and encounter failures like:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

This occurs because AppArmor restricts unprivileged user namespace creation by default, blocking capabilities like `net_admin` and `setpcap` that Bubblewrap (`bwrap`) requires to configure sandbox loopback interfaces.

### Resolution (AppArmor Profile)

To allow Bubblewrap specifically to create unprivileged user namespaces without lowering the system-wide security posture:

1. Create a dedicated AppArmor profile file at `/etc/apparmor.d/bwrap-userns-restrict`:

   ```text
   abi <abi/4.0>,
   include <tunables/global>

   profile bwrap /usr/bin/bwrap flags=(unconfined) {
     userns,

     # Site-specific additions and overrides. See local/README for details.
     include if exists <local/bwrap>
   }
   ```

2. Parse and reload the profile:

   ```bash
   sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
   ```

3. Verify the fix:

   ```bash
   bwrap --unshare-net --dev-bind / / /usr/bin/true
   ```
   If successful, this command returns instantly with no output and exit code `0`.
