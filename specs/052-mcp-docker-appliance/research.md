# Research: MCP Docker Appliance

## Decision 1: Separate Image Flavor

**Decision**: Build the MCP appliance as `docker/Dockerfile.mcp`, derived from the existing Wright image.

**Rationale**: Engineers get the same Wright access pattern while the standard image remains free of MCP host software.

## Decision 2: Manifest-Driven Bundle

**Decision**: Use `docker/mcp-bundle.yaml` as the source of truth, with separate `applications` and `mcp_servers`.

**Rationale**: Applications and MCP servers do not always map one-to-one. SolidEdgeMCP is a server without a redistributable Linux Solid Edge application. Playwright is both a browser automation runtime and an MCP server.

## Decision 3: Correct Initial Bundle

**Decision**: The initial Linux bundle installs OpenSCAD, FreeCAD, BREP CAD tooling, and Playwright locally. It configures OpenSCAD MCP, FreeCAD MCP, BREP MCP, and Playwright MCP as Linux-runnable local servers, while SolidEdgeMCP is represented as Windows-owned runtime metadata and a blocked Linux entry.

**Rationale**: This matches the corrected product scope. OpenCAD is skipped. BREP is not represented by CAiD/OpenCASCADE.

## Decision 4: Third-Party Compliance Profiles

**Decision**: Use reusable profiles for permissive licenses, GPL-2.0 unmodified runtime redistribution, LGPL unmodified runtime redistribution, and internal reviewed source.

**Rationale**: The bundle will grow. A general compliance gate is safer than one-off license exceptions and supports running redistributed third-party code without implying contribution or modification.

## Decision 5: OpenSCAD Source

**Decision**: Install OpenSCAD as the local application and use the pinned Quellant OpenSCAD MCP source.

**Rationale**: The repo already contains a validated OpenSCAD setup recipe. OpenSCAD's GPL runtime obligations are handled through generated license/source artifacts.

## Decision 6: FreeCAD Source

**Decision**: Install the FreeCAD 1.1.1 AppImage for Linux amd64 and the
official FreeCAD 1.1.1 Linux aarch64 AppImage for the Linux arm64 bundle. Both
platform bundles use the pinned `neka-nat/freecad-mcp` source from the
clean-container validation notes.

**Rationale**: The AppImage path passed real backend object-creation validation
in the repo's MCP catalog evidence and avoids package-version drift in the Linux
amd64 image. Live GB10 validation found Debian Trixie's arm64 FreeCAD package
segfaulting before startup, while FreeCAD publishes a platform-native aarch64
AppImage for 1.1.1. The arm64 bundle therefore uses the official aarch64
AppImage instead of distro packages or x86_64 application assets.

## Decision 7: BREP Source

**Decision**: Use the BREP CAD CLI/MCP shipped by `brepjs-cad`, pinned to the reviewed package version/source ref.

**Rationale**: This provides an installable BREP application/tooling and `brep-mcp` server without using CAiD/OpenCASCADE as a substitute. The Linux launch path uses a Wright-owned compatibility wrapper around the pinned package's MCP server so the package remains unmodified while the server resolves its file-backed CLI entry correctly inside Docker.

## Decision 8: SolidEdgeMCP Source

**Decision**: Publish SolidEdgeMCP in the Windows MCP runtime from `https://github.com/burhop/SolidEdgeMCP.git` at commit `2aad5bd24df6ce1ac9578ad35c4da7ac241b5330` by default, while allowing exact-ref overrides through `WRIGHT_SOLIDEDGE_MCP_GIT_URL` and `WRIGHT_SOLIDEDGE_MCP_GIT_REF`. Linux bundles keep a blocked SolidEdgeMCP metadata entry until the source has a Linux-runnable server target.

**Rationale**: Wright's existing docs/specs treat SolidEdgeMCP as an independently versioned external server with a generic workspace-binding contract, and the actual repository currently targets `net10.0-windows` for Solid Edge COM automation. A Linux appliance should not claim this server is installed or runnable until a Linux-compatible target exists.

## Decision 9: Playwright Source

**Decision**: Install Playwright and `@playwright/mcp` as pinned npm tools, install the standard Chromium browser assets for Playwright, and install the `chrome-for-testing` browser payload requested by the pinned Playwright MCP package.

**Rationale**: Engineers need an agent-accessible browser control path to drive Wright and browser-based CAD applications. The Playwright MCP package can depend on a different browser revision than the global Playwright package, so the bundle records the MCP browser channel separately.

## Decision 10: LLM Provider Setup And Seed Files

**Decision**: Start Wright/Hermes without a fake model endpoint when no LLM is
configured, and support a mounted `WRIGHT_LLM_CONFIG_FILE` provider seed for
Codex/OpenAI-compatible repeatable Docker tests. Codex reuse configures Hermes'
native `openai-codex` provider and imports a Hermes auth payload or token pair
into the Wright profile auth store.

**Rationale**: Hermes already owns Codex/OpenAI/Nous provider behavior. Wright
should wrap those provider choices instead of maintaining a competing credential
system. A seed file gives maintainers disposable test containers without
interactive model setup and avoids baking secrets into Docker images.

## Source Notes

- `docs/mcp-catalog/mcp-server-setup-recipes.md` records validated OpenSCAD and FreeCAD setup paths.
- `docs/integrations/solid-edge-creation.md` records the current generic SolidEdgeMCP workspace-binding contract.
- `specs/049-provider-neutral-mcp/research.md` records that SolidEdgeMCP is external and configured without Wright runtime provider branching.
- OpenSCAD uses the GPL-2.0 runtime redistribution profile.
- FreeCAD uses the LGPL runtime redistribution profile.
- BREP/Playwright MCP package sources are Apache-2.0 and use the permissive profile.
- Hermes 0.19.0 includes an `openai-codex` model provider backed by
  `https://chatgpt.com/backend-api/codex` and a Hermes-owned auth store.
