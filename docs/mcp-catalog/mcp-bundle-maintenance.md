# MCP Bundle Maintenance

The MCP Docker appliance is driven by `docker/mcp-bundle.yaml`. Update that
manifest first, then let validation, generated config, Docker smoke, and docs
follow from it.

## Bundle Rules

- Keep `applications` and `mcp_servers` separate.
- Pin Git sources to exact commits or immutable tags.
- Pin package sources to exact versions.
- Do not add OpenCAD or placeholder entries to the default image unless an
  installable source, license, and probe are reviewed.
- Do not use CAiD/OpenCASCADE as a BREP substitute. The BREP entry is the BREP
  application/tooling plus its BREP MCP server.
- Keep the standard non-MCP Docker appliance free of MCP host software.
- Keep third-party package fixes in Wright-owned launchers or wrappers when a
  runtime workaround is sufficient; do not rewrite installed package files just
  to make the appliance pass validation.
- Set `target_platform` and `catalog_policy` in every managed bundle.
- Give each `local_enabled` MCP server a `catalog_id` pointing at the canonical
  engineering catalog entry.
- Let `docker/mcp/verify-bundle.py` reject platform-incompatible bundle entries
  instead of relying on manual review alone.

## Current Default Set

Applications:

- `openscad`
- `freecad`
- `brep`
- `playwright`

MCP servers:

- `openscad-mcp`
- `freecad-mcp`
- `brep-mcp`
- `solid-edge-mcp`
- `playwright-mcp`

The default Linux bundle targets `linux-amd64`. The GB10 bundle targets
`gb10-linux-arm64`, and the Windows bundle targets `windows-amd64`. See
`docs/mcp-catalog/dynamic-engineering-catalog.md` for the catalog-backed
selection contract.

## BREP MCP

The Linux bundles install `brepjs-cad@0.103.0` from npm and launch its MCP
server through `/opt/wright/mcp/bin/brep-mcp-wrapped`. The wrapper corrects the
pinned package build's generated URL lookups so the MCP uses the real
`dist/cli/main.js` file when executing `run_program` or `export_part`.

Leave the package itself unmodified in the image. When a future pinned
`brepjs-cad` release no longer needs the wrapper, update the manifest launch
command, this note, and the live MCP validation evidence together.

## Playwright MCP

The Playwright application entry installs the standard Playwright Chromium
payload through `playwright_browsers`. The `playwright-mcp` server entry also
sets `playwright_mcp_browsers` to `chrome-for-testing` so the
`@playwright/mcp` package installs the exact browser revision expected by its
own pinned Playwright dependency. Keep both fields intentional when changing
Playwright or `@playwright/mcp` versions, then rerun the live gateway probe for
`playwright-mcp__browser_navigate`.

## License Profiles

Use `permissive` for MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, and ISC.

Use `gpl-2.0-runtime-redistribution` only for unmodified runtime components
where the manifest records source access, license text, no-warranty notice, and
modification status. OpenSCAD uses this profile.

Use `lgpl-runtime-redistribution` for unmodified LGPL runtime components with
the same evidence. FreeCAD uses this profile.

Use `internal-reviewed-source` for reviewed source-configured repositories such
as SolidEdgeMCP when repository-specific licensing or distribution approval is
not represented by a permissive/SPDX profile. The manifest must name how source
access is provided and the allowed redistribution scope.

## SolidEdgeMCP

Wright's repo treats SolidEdgeMCP as an independently versioned external server
configured through ordinary launch data. The MCP appliance mirrors that
contract:

```bash
WRIGHT_SOLIDEDGE_MCP_GIT_URL=https://github.com/burhop/SolidEdgeMCP.git
WRIGHT_SOLIDEDGE_MCP_GIT_REF=2aad5bd24df6ce1ac9578ad35c4da7ac241b5330
```

For private GitHub MCP sources, build with `GITHUB_TOKEN` in the host
environment or a valid `gh auth login`. The Docker helpers mount the token as a
BuildKit secret named `github_token`; never model private-source credentials as
bundle fields or Docker build args.

The generated launch environment uses:

```yaml
CADMCP_SOLID_EDGE_ALLOWED_ROOTS: "{workspace.path}"
```

Do not redistribute Solid Edge itself, vendor SDKs, license managers, or
desktop application assets in this Linux image.

The current bundle clones the pinned SolidEdgeMCP source into
`/opt/wright/mcp/src/SolidEdgeMCP` and installs a wrapper at
`/opt/wright/mcp/bin/solid-edge-mcp`. At commit
`2aad5bd24df6ce1ac9578ad35c4da7ac241b5330`, the server project is
`src/SolidEdgeMcpServer/SolidEdgeMcpServer.csproj` and targets
`net10.0-windows`, so it is not runnable in the Linux appliance. Keep the
wrapper/config entry so Wright can expose a clear platform limitation, and add
a Linux publish/install entry only after the upstream repo actually provides a
Linux-compatible MCP server target.

## Validation

Run:

```bash
uv run python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml
uv run python docker/mcp/verify-bundle.py docker/mcp-bundle.linux-arm64.yaml
uv run python docker/mcp/verify-bundle.py docker/mcp-bundle.windows-amd64.yaml
uv run python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check
uv run pytest packages/tool_registry/tests/test_catalog_resource.py packages/tool_registry/tests/test_catalog_platforms.py tests/docker/test_mcp_bundle.py
bash -n scripts/docker-mcp-smoke-test.sh
```

When host Docker and network credentials are available, run:

```bash
scripts/docker-mcp-smoke-test.sh
```

Record any skipped Docker or Playwright run with the exact local limitation.
