# Wright Docker Image Family

Wright now manages four Docker image profiles:

| Image profile | Platform | Purpose |
|---|---:|---|
| `wright-standard` | `linux/amd64` | Existing Hermes + Wright appliance. |
| `wright-mcp-linux-amd64` | `linux/amd64` | Wright appliance plus Linux amd64 MCP bundle. |
| `wright-mcp-linux-arm64` | `linux/arm64` | Wright appliance plus GB10-class Linux arm64 MCP bundle. |
| `wright-mcp-windows-amd64` | `windows/amd64` | Windows MCP runtime for Windows-host MCPs such as SolidEdgeMCP. |

The source of truth is `docker/image-family.yaml`.

## Persisted Data

The standard and Linux MCP appliances persist:

- `/home/agent/.local/share/wright`
- `/home/agent/workspace`
- `/home/agent/.config/wright`
- `/home/agent/.hermes`
- `/var/log`

The Windows MCP runtime persists:

- `C:\wright\data`
- `C:\wright\workspace`
- `C:\wright\config`
- `C:\wright\hermes`
- `C:\wright\logs`

Use named Docker volumes for trials and bind mounts only when you explicitly
want the host filesystem layout to be visible.

## Build On GB10 Or Linux Arm64

```bash
./scripts/docker-image-family-build.sh linux-arm64
```

Run it:

```bash
export WRIGHT_API_TOKEN=change-this-long-random-token
export LLM_API_URL=https://your-provider.example/v1
export LLM_API_KEY=your-key
export LLM_API_MODEL=your-model
./scripts/docker-mcp-run.sh linux-arm64
```

Open `http://127.0.0.1:8080`.

For repeatable Codex/OpenAI-compatible testing, use a mounted provider seed
instead of re-entering model setup for every new container:

```bash
export WRIGHT_API_TOKEN=change-this-long-random-token
export WRIGHT_LLM_CONFIG_FILE=/absolute/host/path/llm-seed.yaml
./scripts/docker-mcp-run.sh linux-arm64
```

For Codex/ChatGPT login reuse, the seed selects `provider: openai-codex` and
either inlines a token pair or points at a mounted Hermes auth file through
`auth_file: /run/secrets/wright/hermes-auth.json`. With the run helper, set
`WRIGHT_LLM_AUTH_FILE=/absolute/host/path/hermes-auth.json` and it is mounted
at that container path.

## Build Linux Amd64

On a native amd64 host, or on an ARM host with amd64 emulation enabled:

```bash
./scripts/docker-image-family-build.sh linux-amd64
```

Run it:

```bash
export WRIGHT_API_TOKEN=change-this-long-random-token
./scripts/docker-mcp-run.sh linux-amd64
```

## Build On Windows 11

Use Docker Desktop Linux containers for the Linux images:

```powershell
pwsh -File scripts/docker-image-family-build.ps1 -Profile linux-amd64
pwsh -File scripts/docker-image-family-build.ps1 -Profile linux-arm64
```

Switch Docker Desktop to Windows containers before building the Windows image:

```powershell
pwsh -File scripts/docker-image-family-build.ps1 -Profile windows-amd64
pwsh -File scripts/docker-mcp-run-windows.ps1
```

The Windows build uses `WRIGHT_SOLIDEDGE_MCP_GIT_URL` and exact
`WRIGHT_SOLIDEDGE_MCP_GIT_REF` when set. For ordinary GitHub repos the helper
derives the archive URL; set `WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL` only when the
source is not a standard GitHub archive URL.

For private GitHub MCP sources, set `GITHUB_TOKEN` with read access or repair
`gh auth login` before building. Linux MCP builds mount it as a BuildKit secret
named `github_token`; do not pass credentials as build args.

Windows Docker images are normally based on Windows Server Core even when built
from a Windows 11 workstation. Solid Edge itself is not redistributed in the
image. The Windows MCP runtime publishes SolidEdgeMCP from the pinned GitHub
source, but live Solid Edge automation still requires a licensed Windows/Solid
Edge environment.

## Bundle Differences

- Linux amd64 uses the FreeCAD 1.1.1 x86_64 AppImage.
- Linux arm64 uses the official FreeCAD 1.1.1 Linux aarch64 AppImage.
- Windows amd64 includes Windows-oriented MCP runtime metadata for BREP,
  SolidEdgeMCP, and Playwright. OpenSCAD and FreeCAD are not included in the
  initial Windows runtime profile until their Windows install/probe path is
  validated.
