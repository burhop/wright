# Contract: MCP Appliance Validation

Validation proves the image is runnable by engineers and that each bundled MCP/application path is honest.

## Required Phases

1. Build or select the MCP image.
2. Start it with fresh MCP-specific volumes and a fresh workspace.
3. Verify Wright API health.
4. Verify Hermes gateway health.
5. Load the MCP bundle status report.
6. Verify generated license/source-compliance artifacts.
7. Verify local application commands or wrappers exist.
8. Verify each generated MCP server appears in the Hermes profile.
9. Run Playwright UI prompts against the mapped Wright UI when a live container is available.
10. Collect logs/artifacts and stop the container.

## Per-Entry Expectations

OpenSCAD:

- `openscad` command is present.
- `openscad-mcp` is generated in Hermes config.
- GPL-2.0 runtime redistribution materials are present.

FreeCAD:

- FreeCAD provides `freecad` and `freecadcmd` wrappers through the amd64
  AppImage extraction path or the arm64 system package path.
- `freecad-mcp-wrapped` can start the FreeCAD backend under Xvfb.
- LGPL runtime redistribution materials are present.

BREP:

- `brep` CLI and `brep-mcp` are present.
- BREP validation prompt targets BREP tooling, not CAiD/OpenCASCADE.

SolidEdgeMCP:

- `solid-edge-mcp` wrapper is present.
- If internal Git source build args are supplied, the source is cloned at the exact ref and installed.
- Solid Edge desktop/vendor assets are not redistributed.

Playwright:

- `playwright` and `playwright-mcp` are present.
- Chromium browser assets are installed under the MCP image cache.

## Failure Reporting

Validation failures identify:

- service or component
- health phase or prompt phase
- expected status
- observed status
- relevant log/artifact path
- whether the failure blocks the image or indicates missing optional internal source build args
