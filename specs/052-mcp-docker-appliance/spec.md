# Feature Specification: MCP Docker Appliance

**Feature Branch**: `052-mcp-docker-appliance`

**Created**: 2026-07-30

**Status**: Implemented

**Input**: Create a Spec Kit-driven managed Docker image family: the existing Hermes + Wright appliance, a Linux amd64 MCP appliance, a Linux arm64 MCP appliance for GB10-class machines, and a Windows-host MCP runtime image. Preserve the current Docker access pattern, avoid corrupting local Wright/Hermes state, install curated license-compatible MCP/application bundles from pinned repositories or package registries, test through Docker and Playwright where the host platform supports it, and document it for engineers.

## User Scenarios & Testing

### User Story 1 - Run The MCP Appliance Like Wright (Priority: P1)

An engineer starts the MCP-enabled Docker appliance using the same basic workflow as the standard Wright appliance, opens Wright through the documented port, and gets a fresh workspace with bundled MCP servers configured.

**Independent Test**: Start the MCP image with distinct compose volumes, open the Wright UI through the mapped port, create/select a workspace, and verify the generated Hermes profile includes the MCP bundle while the standard appliance volumes remain untouched.

**Acceptance Scenarios**:

1. Given an engineer has the same environment file used for standard Wright Docker, when they run the MCP image, then Wright starts with the same UI/API access pattern.
2. Given existing standard Wright Docker volumes exist, when the MCP compose file is used, then the MCP appliance uses its own volumes by default.
3. Given remote test access is needed, when the engineer opts into LAN binding, then the UI is reachable through the documented host/port with token guidance.

### User Story 2 - Verify Bundled MCP Health And Application Backends (Priority: P2)

An engineer or CI operator runs validation that starts the MCP appliance, verifies Wright and Hermes health, checks each MCP, and proves local MCP/application pairs can perform representative work.

**Independent Test**: Run the MCP Docker smoke test against a fresh container and workspace.

**Acceptance Scenarios**:

1. OpenSCAD and `openscad-mcp` are installed and can produce a simple SCAD/STL artifact.
2. FreeCAD and `freecad-mcp` are installed and can create/read a simple Part box.
3. BREP CAD tooling and `brep-mcp` are installed and can verify/export a simple BREP geometry.
4. SolidEdgeMCP source is included from the pinned `burhop/SolidEdgeMCP` GitHub ref using Wright's generic workspace-binding contract; Solid Edge itself is not redistributed in the Linux image, and the current upstream server target is Windows/Solid Edge only.
5. Playwright and `playwright-mcp` are installed and can drive the Wright/browser workflow.

### User Story 3 - Maintain A Reviewable MCP Bundle (Priority: P3)

A maintainer changes included applications/MCP servers by editing `docker/mcp-bundle.yaml`, not by rewriting Dockerfile logic.

**Independent Test**: Modify fixture manifests, run the bundle validator/generator, and verify exact pins, license profiles, generated Hermes config, and compliance artifacts.

**Acceptance Scenarios**:

1. Permissive exact-pinned sources pass.
2. GPL-2.0 runtime components pass only with source-access, license, no-warranty, and unmodified-runtime evidence.
3. LGPL runtime components pass only with source-access, license, no-warranty, and unmodified-runtime evidence.
4. Source-configured entries such as SolidEdgeMCP pass only through an explicit internal-reviewed-source profile when their repository-specific terms are not represented by a permissive/SPDX profile.
5. Floating Git refs, unknown licenses, and unsupported obligations fail before image build.

### User Story 4 - Follow Engineer-Friendly Documentation (Priority: P4)

A mechanical/design engineer follows a short guide to run the image, open Wright, understand the included tools, verify a prompt, and clean up.

**Independent Test**: A new engineer can run the guide without reading Dockerfile internals.

### User Story 5 - Manage Platform-Specific Images (Priority: P2)

A maintainer can build and explain four managed image profiles: standard Wright,
Linux amd64 MCP, Linux arm64 MCP, and Windows amd64 MCP runtime.

**Independent Test**: Inspect `docker/image-family.yaml`, run bundle validation
for each platform bundle, and run the platform build script for the current
host or document the concrete host limitation.

**Acceptance Scenarios**:

1. The existing standard Wright image remains separately buildable.
2. The Linux amd64 MCP image uses the x86_64 FreeCAD AppImage bundle.
3. The Linux arm64 MCP image uses arm64-compatible install paths and does not
   attempt to run x86_64 AppImage assets.
4. The Windows image profile is buildable from a Windows 11 host in Windows
   container mode and persists its data/workspace/config/log directories.
5. The Windows image profile does not imply Solid Edge itself is redistributed.

## Requirements

- **FR-001**: Provide a separate MCP-enabled Docker image flavor derived from the existing Hermes + Wright appliance.
- **FR-002**: Preserve the standard appliance's primary Wright UI/API port behavior, environment-file workflow, entrypoint, supervisor model, and browser-based experience.
- **FR-003**: Keep MCP-specific host software out of the standard non-MCP Docker image.
- **FR-004**: Use separate default compose volume names for the MCP appliance.
- **FR-005**: Define the bundle in a reviewable manifest with separate `applications` and `mcp_servers` sections.
- **FR-006**: Reject unpinned Git sources, floating branches, unknown licenses, unclear metadata, and unsupported redistribution obligations.
- **FR-007**: Allow MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, and ISC by default.
- **FR-008**: Support reusable compliance profiles for GPL-2.0 runtime redistribution, LGPL runtime redistribution, and internal reviewed source.
- **FR-009**: Generate license, notice, no-warranty, source-access, and third-party compliance artifacts in the image.
- **FR-010**: Initially install these local applications: OpenSCAD, FreeCAD, BREP CAD tooling, and Playwright.
- **FR-011**: Initially configure these MCP servers: OpenSCAD MCP, FreeCAD MCP, BREP MCP, SolidEdgeMCP, and Playwright MCP.
- **FR-012**: Do not include OpenCAD in the initial bundle.
- **FR-013**: Do not use CAiD/OpenCASCADE as the BREP implementation.
- **FR-014**: Do not redistribute Solid Edge, vendor SDKs, license managers, or desktop application assets in the Linux image.
- **FR-015**: Clone SolidEdgeMCP source from the pinned default GitHub URL/ref, allow overrides through `WRIGHT_SOLIDEDGE_MCP_GIT_URL` and exact `WRIGHT_SOLIDEDGE_MCP_GIT_REF`, and report the current Windows/Solid Edge platform limitation from the Linux wrapper.
- **FR-016**: Generate Hermes MCP config from the manifest without overwriting unrelated user-owned profile settings.
- **FR-017**: Provide Docker smoke validation for Wright health, Hermes health, generated config, generated compliance files, local tool binaries/wrappers, and expected bundle statuses.
- **FR-018**: Provide Playwright UI coverage that can open Wright, create/select a workspace, and submit a prompt covering bundled MCP health.
- **FR-019**: Document run commands, ports, credentials, remote access, included tools, verification prompts, cleanup, and third-party license evidence for engineers.
- **FR-020**: Define a managed image-family manifest covering standard Wright, Linux amd64 MCP, Linux arm64 MCP, and Windows amd64 MCP runtime profiles.
- **FR-021**: Provide a Linux arm64 MCP bundle that avoids x86_64-only FreeCAD AppImage assets.
- **FR-022**: Provide host-specific build/run scripts for Linux/GB10 and Windows PCs.
- **FR-023**: Ensure every managed image profile has documented persistent data, workspace, config, Hermes/profile, and log paths.

## Key Entities

- **MCP Bundle Manifest**: Source-controlled manifest for applications, MCP servers, exact source pins, install data, launch config, probes, and compliance profiles.
- **Application Entry**: Installed local tool/runtime such as OpenSCAD, FreeCAD, BREP CAD tooling, or Playwright.
- **MCP Server Entry**: MCP launch/config record such as `openscad-mcp`, `freecad-mcp`, `brep-mcp`, `solid-edge-mcp`, or `playwright-mcp`.
- **Third-Party Compliance Profile**: Reusable policy record for permissive, GPL runtime, LGPL runtime, or internal reviewed source obligations.
- **MCP Appliance Image**: Docker artifact derived from the standard appliance with the reviewed bundle installed.
- **Managed Image Profile**: Platform-specific image record with Dockerfile, platform, bundle, image tag, and persisted paths.
- **Validation Workspace**: Fresh workspace used by Docker and Playwright validation.

## Success Criteria

- **SC-001**: A new engineer can start the MCP appliance and open Wright from the documented URL in 15 minutes or less after Docker and credentials are available.
- **SC-002**: The default manifest validates with four accepted local applications and five accepted MCP servers.
- **SC-003**: 100% of bundled sources included in the image have exact pins or an explicit internal-source configuration gate.
- **SC-004**: Generated third-party compliance artifacts include GPL/LGPL runtime source-access and no-warranty evidence.
- **SC-005**: The documented compose path leaves standard Wright appliance volumes unchanged.
- **SC-006**: Playwright can submit a bundle-health prompt through the Wright UI against a running MCP appliance.
- **SC-007**: The image-family manifest lists exactly four managed image profiles with persisted paths.
- **SC-008**: The Linux arm64 bundle validates independently and contains no x86_64-only FreeCAD AppImage install path.

## Assumptions

- The standard Wright Docker appliance remains the baseline for ports, entrypoint behavior, supervisor services, and environment-file usage.
- Build-time installation is preferred so engineers do not need first-run dependency downloads.
- SolidEdgeMCP source is configured at image build time from a pinned GitHub ref; at the current ref the server targets Windows/Solid Edge and is not runnable inside the Linux appliance.
- Windows Docker builds require a Windows host with Docker Desktop switched to Windows container mode; Linux image builds require Linux container mode or compatible emulation.
- Remote/LAN access is opt-in for trusted engineering test networks only.
