# Implementation Plan: MCP Docker Appliance

**Branch**: `052-mcp-docker-appliance` | **Date**: 2026-07-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/052-mcp-docker-appliance/spec.md`

## Summary

Create an MCP-enabled Wright Docker appliance as a separate image flavor derived from the existing Hermes + Wright container. Preserve the standard appliance's UI/API access pattern, entrypoint, and supervisor contract while adding a manifest-driven MCP bundle, build-time source/license/compliance validation, generated runtime configuration, separate default MCP volumes, Docker smoke checks, Playwright prompt coverage, and engineer-facing quickstart documentation. The corrected initial bundle installs OpenSCAD, FreeCAD, BREP CAD tooling, and Playwright locally, and configures OpenSCAD MCP, FreeCAD MCP, BREP MCP, SolidEdgeMCP, and Playwright MCP. OpenCAD is skipped, and BREP is not represented by CAiD/OpenCASCADE.

## Technical Context

**Language/Version**: Python 3.13 runtime and scripts; Bash for Docker helper scripts; TypeScript 5 and React 19 for Playwright/UI test surfaces; YAML/JSON for bundle manifests and generated config

**Primary Dependencies**: Existing Dockerfile, `docker/entrypoint.sh`, `docker/supervisord.conf`, `docker-compose.minimal.yml`, `scripts/docker-smoke-test.sh`, `uv`, Hermes Agent 0.19.0, existing Wright FastAPI/frontend packages, Playwright, PyYAML/Pydantic-style validation through existing repo tooling where available, Docker CLI/Compose

**Storage**: Existing named Docker volumes for the standard appliance remain unchanged; MCP compose usage adds separate named volumes for Wright data, workspaces, config, Hermes profile, logs, and any generated MCP cache/license/source-compliance artifacts

**Testing**: Focused unit tests for bundle parsing/license/source pin/compliance checks/config generation; shell/static tests for Dockerfile and compose behavior; Docker MCP smoke/integration test; Playwright UI workflow against a running MCP appliance; existing `scripts/docker-smoke-test.sh`; `scripts/check-dev-merge.sh` before merge or documented host limitation

**Target Platform**: Linux Docker appliance, initially `linux/amd64` in parity with current image constraints; Solid Edge itself is not installed in Linux, while SolidEdgeMCP source is cloned from a pinned GitHub ref and its wrapper reports the current Windows/Solid Edge runtime limitation.

**Project Type**: Modular monorepo with Docker appliance, Python API/packages, TypeScript frontend, and documentation

**Performance Goals**: Build-time bundle validation completes before expensive image build steps when pins/licenses are invalid; MCP health checks use bounded per-server timeouts; Playwright smoke remains suitable for CI/operator use without long-running design tasks

**Constraints**: Preserve the non-MCP Docker appliance; do not add MCP-specific host software to the base non-MCP image; fail closed on unpinned sources, unknown licenses, unsupported obligations, or missing third-party compliance artifacts; allow GPL/LGPL runtime components only through reusable redistribution compliance profiles; avoid mutating local Wright/Hermes host setup; do not redistribute Solid Edge desktop/vendor assets in Linux images; remote/LAN binding is opt-in; no merge to `dev` or `main` during this feature

**Scale/Scope**: One MCP image flavor, one manifest schema, four local applications, five MCP servers, one engineer quickstart, one smoke/integration test path, and one Playwright prompt workflow

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- **Modular FastAPI boundaries**: Pass. Docker bundle generation and validation stay in scripts/config; API changes, if any, remain transport-thin and use existing MCP/gateway/tool-registry surfaces.
- **Offline-first**: Pass with explicit build/runtime separation. The built appliance should work without first-run MCP downloads; source retrieval occurs during image build or maintainer validation, not during ordinary engineer use.
- **Production distributions**: Pass. The MCP appliance is an additional image flavor and does not replace the mandatory standard Docker artifact.
- **Docker thick base**: Pass with a scoped exception model. MCP-specific host software is added only to the selected MCP image flavor, not the shared standard base or catalog validation base.
- **Native runtime isolation**: Pass. No local host Wright/Hermes state is modified; Solid Edge remains external and Windows-owned.
- **Agent abstraction**: Pass. Bundle entries generate ordinary MCP launch/config records rather than hardcoding product behavior into the API.
- **Embedded state and file vault**: Pass. Validation uses fresh workspaces and existing Docker volumes rather than new database servers.
- **Security and identity**: Pass. Existing token/env behavior remains; remote/LAN UI access is opt-in and documented with security requirements.
- **Engineering tooling protocol**: Pass. Tool validation is CLI/MCP-driven; Solid Edge GUI/vendor automation remains outside the Linux image.
- **Testing pyramid**: Pass. Unit/static checks precede Docker smoke and Playwright UI workflow.
- **Observability**: Pass. Health/prompt validation should report per-service/per-MCP status and preserve actionable failure evidence.
- **Phase and branch discipline**: Pass. Work is on `052-mcp-docker-appliance`; implementation stops until the operator approves.

## Project Structure

### Documentation (this feature)

```text
specs/052-mcp-docker-appliance/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- bundle-manifest-contract.md
|   |-- docker-runtime-contract.md
|   |-- validation-contract.md
|   `-- engineer-docs-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
docker/
|-- Dockerfile                         # existing standard appliance remains default
|-- Dockerfile.mcp                     # new MCP image flavor or thin target wrapper
|-- mcp-bundle.yaml                    # reviewed source of truth for included MCPs
|-- mcp-bundle.schema.json             # generated/maintained manifest schema
|-- mcp-compose.override.yml           # optional compose overlay with separate volumes
|-- container-manifest.mcp.md          # MCP-specific additive container context
`-- mcp/
    |-- install-bundle.sh              # build-time installer
    |-- verify-bundle.py               # pins, licenses, compliance, availability
    |-- generate-config.py             # runtime config and compliance artifacts
    `-- probes/                        # per-entry validation probe definitions

scripts/
|-- docker-mcp-smoke-test.sh           # starts fresh MCP appliance and validates health
`-- README.md                          # script documentation update

tests/
|-- docker/
|   `-- test_mcp_bundle.py             # manifest/license/config unit coverage
`-- ui-integration/
    `-- mcp-appliance.spec.ts          # Playwright prompt workflow

docs/
|-- getting-started/
|   `-- quickstart-docker-mcp.md       # engineer-facing usage guide
|-- mcp-catalog/
|   `-- mcp-bundle-maintenance.md      # maintainer-focused bundle update process
`-- user-guide/
    `-- docker.md                      # link/update existing Docker guide
```

**Structure Decision**: Keep the standard Docker appliance unchanged and add a separate MCP flavor around manifest generation, image build, smoke validation, and documentation. Tests live beside existing Docker/UI test conventions. Maintainer internals are documented separately from engineer quickstart usage.

## Implementation Sequence

1. Add manifest schema, fixtures, and failing tests for exact pins, license policy, GPL-2.0/LGPL runtime compliance, internal-source compliance, and generated config.
2. Add the MCP bundle manifest with OpenSCAD, FreeCAD, BREP, and Playwright applications plus OpenSCAD MCP, FreeCAD MCP, BREP MCP, SolidEdgeMCP, and Playwright MCP.
3. Implement bundle verification and config/license/source-compliance artifact generation.
4. Add the MCP Docker image flavor and compose overlay with separate default volumes while preserving the standard Dockerfile and compose behavior.
5. Extend entrypoint/startup idempotently so generated MCP config is materialized without overwriting user-owned profile settings outside the MCP appliance volume.
6. Add Docker MCP smoke validation with Wright/Hermes health, per-MCP health, and application-backed probes.
7. Add Playwright UI prompt workflow against a fresh workspace.
8. Add engineer quickstart and maintainer bundle documentation.
9. Run focused tests, Docker MCP smoke, Playwright workflow, standard Docker smoke, and merge gate or document concrete host limitation.

## Complexity Tracking

No constitution violation is required. The notable complexity is a general third-party compliance profile for redistributing unmodified runtime components such as GPL-2.0 OpenSCAD inside the image. This replaces one-off license exceptions with a fail-closed, reusable evidence gate.

## Constitution Check - Post-Design

All constitution gates remain passing. The design isolates the MCP appliance from the standard Docker artifact, keeps manager/product specifics in manifest data and validation probes, preserves Docker as a turnkey path, and stops implementation until human approval.
