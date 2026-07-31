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

- [X] T017 Update Docker MCP smoke script for OpenSCAD, FreeCAD, BREP, Playwright, and blocked Linux SolidEdgeMCP metadata.
- [X] T018 Update Playwright UI integration prompt for the corrected Linux-runnable bundle.
- [X] T019 Add probe definitions/status metadata for the five MCP server entries.
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

## Phase 7: LLM First-Run And Seeded Provider Setup

- [X] T031 Add Spec Kit requirements for fresh-container LLM onboarding and reusable provider seed files.
- [X] T032 Add Hermes LLM seed helper for Codex/OpenAI-compatible config and auth seeding.
- [X] T033 Update Docker entrypoint and run helpers to avoid fake localhost LLM defaults and accept mounted seed files.
- [X] T034 Add setup API provider metadata/configuration endpoints and Codex login polling for browser-first setup.
- [X] T035 Add engineer docs and an example seed file for repeatable Codex/OpenAI-compatible Docker tests.
- [X] T036 Add focused tests for provider seed config, Codex auth seeding, and setup API behavior.
- [X] T037 Add Wright Model Setup UI for Codex login and OpenAI-compatible endpoint configuration.

## Phase 8: Engineering Tools Image Publication

- [X] T038 Rename public MCP image tags to engineering-tools tags across image-family metadata, compose defaults, build/run scripts, and engineer docs.
- [X] T039 Add GitHub Actions CD for Linux engineering-tools images on native amd64 and arm64 runners with GHCR and Docker Hub publication.
- [X] T040 Add static coverage for engineering-tools tag naming and Docker Hub publication workflow.

## Validation Evidence

- [X] `python docker/mcp/verify-bundle.py docker/mcp-bundle.yaml`
- [X] `python docker/mcp/generate-config.py docker/mcp-bundle.yaml --output-dir /tmp/wright-mcp-generated-check`
- [X] `bash -n scripts/docker-mcp-smoke-test.sh`
- [X] `bash -n docker/mcp/install-bundle.sh`
- [X] `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest tests/docker/test_mcp_bundle.py`
- [X] `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest packages/agent_adapters/tests/test_llm_seed.py apps/api/tests/test_setup_api.py tests/test_docker_smoke_contract.py`
- [X] `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest tests/test_getting_started_paths.py tests/test_readme_branding_and_docker_user_guide.py`
- [X] `python -m py_compile packages/agent_adapters/src/agent_adapters/llm_seed.py`
- [X] `bash -n scripts/docker-mcp-run.sh scripts/docker-smoke-test.sh docker/entrypoint.sh`
- [X] `npm test --workspace=apps/web -- ModelSetupPage.spec.tsx Sidebar.spec.tsx App.spec.tsx`
- [X] `npm run build --workspace=apps/web`
- [X] `UV_CACHE_DIR=/tmp/wright-uv-cache uv run pytest apps/api/tests/test_agent_stream_progress.py packages/workspace_service/tests/test_agent_sync.py tests/test_docker_smoke_contract.py tests/test_container_security_contract.py -q`
- [X] `PLAYWRIGHT_INCLUDE_LIVE=1 PLAYWRIGHT_BASE_URL=http://192.168.1.163:18182 WRIGHT_API_TOKEN=<test-token> npx playwright test tests/ui-integration/mcp-appliance.spec.ts --reporter=line`

## Host-Limited Validation

- Live ARM64 validation on GB10 showed Debian Trixie's `freecad` package segfaulting before startup and SolidEdgeMCP reporting the expected Windows/Solid Edge runtime boundary. The Linux ARM64 manifest now uses FreeCAD's official 1.1.1 Linux aarch64 AppImage and keeps SolidEdgeMCP blocked in Linux while the Windows runtime owns the runnable SolidEdgeMCP path.
- Live ARM64 Playwright validation passed against a fresh MCP appliance container after rebinding the supervised Hermes gateway through `supervisorctl` and aligning Wright workspaces with the mounted `/home/agent/workspace` volume.
- `pwsh` is not installed on this Linux host, so the Windows PowerShell build/run scripts were covered by static tests but not executed locally.
