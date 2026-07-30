# Wright MCP Appliance Addendum

This image is the MCP-enabled Wright Docker appliance flavor. It derives from
the standard Hermes + Wright appliance and preserves the same entrypoint,
supervisor, Wright API, Hermes gateway, and primary UI/API port behavior.

## MCP Bundle

The reviewed MCP bundle is stored at `/opt/wright/mcp/mcp-bundle.yaml`.
Generated runtime and compliance artifacts are under
`/opt/wright/mcp/generated/`.

Expected generated files:

- `/opt/wright/mcp/generated/hermes-mcp.generated.yaml`
- `/opt/wright/mcp/generated/mcp-bundle-status.json`
- `/opt/wright/mcp/generated/licenses/THIRD-PARTY-COMPLIANCE.json`
- `/opt/wright/mcp/generated/licenses/NO-WARRANTY-GPL-2.0.txt`
- `/opt/wright/mcp/generated/licenses/NO-WARRANTY-LGPL.txt`
- `/opt/wright/mcp/generated/licenses/source-offer.md`

## Persistence

Use MCP-specific volumes by default. Do not reuse the standard `wright_hermes`,
`wright_data`, `wright_config`, or `wright_workspaces` volumes unless you
intentionally want to share state between appliance flavors.

## Included Applications And MCPs

The local application bundle installs OpenSCAD, FreeCAD, BREP CAD tooling, and
Playwright. The local MCP bundle includes OpenSCAD MCP, FreeCAD MCP, BREP MCP,
SolidEdgeMCP, and Playwright MCP.

Solid Edge itself is not redistributed in this Linux image. SolidEdgeMCP source
is cloned from the pinned `burhop/SolidEdgeMCP` GitHub ref unless overridden by
`WRIGHT_SOLIDEDGE_MCP_GIT_URL` and `WRIGHT_SOLIDEDGE_MCP_GIT_REF`. The current
server project targets Windows/Solid Edge, so the Linux wrapper reports that
platform limitation while preserving the generic Wright
`CADMCP_SOLID_EDGE_ALLOWED_ROOTS={workspace.path}` contract.
