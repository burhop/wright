# Research: MCP Docker Appliance

## Decision 1: Separate Image Flavor

**Decision**: Build the MCP appliance as `docker/Dockerfile.mcp`, derived from the existing Wright image.

**Rationale**: Engineers get the same Wright access pattern while the standard image remains free of MCP host software.

## Decision 2: Manifest-Driven Bundle

**Decision**: Use `docker/mcp-bundle.yaml` as the source of truth, with separate `applications` and `mcp_servers`.

**Rationale**: Applications and MCP servers do not always map one-to-one. SolidEdgeMCP is a server without a redistributable Linux Solid Edge application. Playwright is both a browser automation runtime and an MCP server.

## Decision 3: Correct Initial Bundle

**Decision**: The initial bundle installs OpenSCAD, FreeCAD, BREP CAD tooling, and Playwright locally. It configures OpenSCAD MCP, FreeCAD MCP, BREP MCP, SolidEdgeMCP, and Playwright MCP.

**Rationale**: This matches the corrected product scope. OpenCAD is skipped. BREP is not represented by CAiD/OpenCASCADE.

## Decision 4: Third-Party Compliance Profiles

**Decision**: Use reusable profiles for permissive licenses, GPL-2.0 unmodified runtime redistribution, LGPL unmodified runtime redistribution, and internal reviewed source.

**Rationale**: The bundle will grow. A general compliance gate is safer than one-off license exceptions and supports running redistributed third-party code without implying contribution or modification.

## Decision 5: OpenSCAD Source

**Decision**: Install OpenSCAD as the local application and use the pinned Quellant OpenSCAD MCP source.

**Rationale**: The repo already contains a validated OpenSCAD setup recipe. OpenSCAD's GPL runtime obligations are handled through generated license/source artifacts.

## Decision 6: FreeCAD Source

**Decision**: Install the FreeCAD 1.1.1 AppImage for Linux amd64 and use the
arm64 system FreeCAD package for the Linux arm64 bundle. Both platform bundles
use the pinned `neka-nat/freecad-mcp` source from the clean-container
validation notes.

**Rationale**: The AppImage path passed real backend object-creation validation
in the repo's MCP catalog evidence and avoids package-version drift in the Linux
amd64 image. That AppImage is x86_64-only, so the Linux arm64 image uses a
platform-native distro package path instead of trying to run x86_64 application
assets on GB10-class hosts.

## Decision 7: BREP Source

**Decision**: Use the BREP CAD CLI/MCP shipped by `brepjs-cad`, pinned to the reviewed package version/source ref.

**Rationale**: This provides an installable BREP application/tooling and `brep-mcp` server without using CAiD/OpenCASCADE as a substitute.

## Decision 8: SolidEdgeMCP Source

**Decision**: Clone SolidEdgeMCP from `https://github.com/burhop/SolidEdgeMCP.git` at commit `2aad5bd24df6ce1ac9578ad35c4da7ac241b5330` by default, while allowing exact-ref overrides through `WRIGHT_SOLIDEDGE_MCP_GIT_URL` and `WRIGHT_SOLIDEDGE_MCP_GIT_REF`.

**Rationale**: Wright's existing docs/specs treat SolidEdgeMCP as an independently versioned external server with a generic workspace-binding contract, and the actual repository currently targets `net10.0-windows` for Solid Edge COM automation. The Linux appliance can include the reviewed source and wrapper/config entry, but it must report the platform limitation rather than claiming a runnable Linux MCP.

## Decision 9: Playwright Source

**Decision**: Install Playwright and `@playwright/mcp` as pinned npm tools and install Chromium browser assets into the MCP image.

**Rationale**: Engineers need an agent-accessible browser control path to drive Wright and browser-based CAD applications.

## Source Notes

- `docs/mcp-catalog/mcp-server-setup-recipes.md` records validated OpenSCAD and FreeCAD setup paths.
- `docs/integrations/solid-edge-creation.md` records the current generic SolidEdgeMCP workspace-binding contract.
- `specs/049-provider-neutral-mcp/research.md` records that SolidEdgeMCP is external and configured without Wright runtime provider branching.
- OpenSCAD uses the GPL-2.0 runtime redistribution profile.
- FreeCAD uses the LGPL runtime redistribution profile.
- BREP/Playwright MCP package sources are Apache-2.0 and use the permissive profile.
