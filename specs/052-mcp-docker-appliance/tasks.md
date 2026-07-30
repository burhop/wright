# Tasks: MCP Docker Appliance

## Phase 1: Bundle Contract And Validation

- [X] T001 Define manifest schema with separate `applications` and `mcp_servers`.
- [X] T002 Implement bundle validation for exact pins, permissive licenses, GPL runtime compliance, LGPL runtime compliance, and internal reviewed source.
- [X] T003 Add fixture coverage for permissive, GPL-compliant, GPL-missing, unpinned, and remote-only cases.
- [X] T004 Add generated Hermes config and compliance artifact generation.

## Phase 2: Correct Initial Bundle

- [X] T005 Remove OpenCAD from the default bundle.
- [X] T006 Remove CAiD/OpenCASCADE from the BREP path.
- [X] T007 Add OpenSCAD application plus OpenSCAD MCP.
- [X] T008 Add FreeCAD application plus FreeCAD MCP.
- [X] T009 Add BREP CAD tooling plus BREP MCP.
- [X] T010 Add SolidEdgeMCP as an internal configured source.
- [X] T011 Add Playwright plus Playwright MCP.

## Phase 3: Docker Appliance

- [X] T012 Add `docker/Dockerfile.mcp` derived from the standard Wright appliance.
- [X] T013 Add Node/npm runtime only to the MCP image flavor.
- [X] T014 Add manifest-driven installer for apt packages, AppImage assets, pinned Git sources, configured Git sources, Python tools, npm tools, Playwright browsers, and wrappers.
- [X] T015 Preserve standard entrypoint/supervisor behavior and idempotently merge generated MCP config.
- [X] T016 Add MCP-specific compose file and isolated volume names.

## Phase 4: Validation

- [X] T017 Update Docker MCP smoke script for OpenSCAD, FreeCAD, BREP, SolidEdgeMCP, and Playwright.
- [X] T018 Update Playwright UI integration prompt for the corrected bundle.
- [X] T019 Add probe definitions for the five MCP servers.
- [X] T020 Run focused manifest/config/unit validation.

## Phase 5: Documentation And Spec Kit Artifacts

- [X] T021 Update engineer quickstart.
- [X] T022 Update maintainer bundle documentation.
- [X] T023 Update spec, research, data model, contracts, quickstart, and checklist to the corrected scope.

## Phase 6: Managed Image Family

- [X] T024 Add `docker/image-family.yaml` with standard, Linux amd64 MCP, Linux arm64 MCP, and Windows amd64 MCP runtime profiles.
- [X] T025 Add Linux arm64 MCP bundle using arm64-compatible FreeCAD install metadata.
- [X] T026 Update base Dockerfile micromamba install for native linux/amd64 and linux/arm64 builds.
- [X] T027 Add Linux/Windows image-family build and run scripts with persistent volume mappings.
- [X] T028 Add Windows MCP runtime Dockerfile and bundle metadata for SolidEdgeMCP, BREP MCP, and Playwright MCP.
- [X] T029 Update engineer/maintainer docs for the four-image matrix and Windows host constraints.
- [X] T030 Add tests for image-family manifest, platform bundles, arm64 FreeCAD path, and Windows scaffolding.

## Validation Evidence

- [X] `python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml`
- [X] `python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check`
- [X] `bash -n scripts/docker-mcp-smoke-test.sh`
- [X] `bash -n docker/mcp/install-bundle.sh`
- [X] `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest tests/docker/test_mcp_bundle.py`

## Host-Limited Validation

- `WRIGHT_MCP_DOCKER_PLATFORM=linux/arm64 WRIGHT_MCP_DOCKER_IMAGE=wright:mcp-linux-arm64 WRIGHT_DOCKER_IMAGE=wright:standard-linux-arm64 WRIGHT_MCP_CONTAINER=wright-mcp-smoke-arm64 bash scripts/docker-mcp-smoke-test.sh` built the native arm64 standard image and reached MCP image installation. It installed the arm64 Debian FreeCAD/OpenSCAD package path, then stopped cloning private `https://github.com/burhop/SolidEdgeMCP.git` because this host's `gh` tokens are invalid and no `GITHUB_TOKEN` was exported. The Dockerfile and helper scripts now support a BuildKit `github_token` secret for private configured Git sources; rerun after `GITHUB_TOKEN` or `gh auth login` is repaired.
- `pwsh` is not installed on this Linux host, so the Windows PowerShell build/run scripts were covered by static tests but not executed locally.
