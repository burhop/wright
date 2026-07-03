# Implementation Plan: Community Release Readiness

**Branch**: `041-community-release-readiness` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/041-community-release-readiness/spec.md`

## Summary

Wright needs a public-release readiness pass that makes installation paths obvious for different user personas, improves discovery through public listings and launch materials, and documents funding routes for continued application work. The implementation will harden release documentation, package/container publishing guidance, install verification paths, public listing metadata, funding copy, and partner outreach materials while preserving Wright's local-first and public-alpha posture.

## Technical Context

**Language/Version**: Python 3.13 backend packages and package metadata; TypeScript 6.0 / React 19 frontend only if public surfaces need UI links; Markdown/YAML for release, docs, and workflow surfaces.

**Primary Dependencies**: Existing GitHub Actions workflows, PyPI Trusted Publishing workflow pattern, GHCR/Docker release workflow, Docker Compose appliance files, MkDocs documentation, README, FUNDING.yml, root `wright-engineering` package metadata, and public registry listing copy.

**Storage**: N/A for runtime state. This feature produces repository documentation, release metadata, workflow configuration, and public launch artifacts.

**Testing**: Documentation/link review, package metadata validation scripts, Docker release/smoke gates where applicable, markdown/docs build, existing release check scripts, and targeted workflow static review.

**Target Platform**: Public Wright repository, documentation site, PyPI/TestPyPI project pages for `wright-engineering`, GHCR/Docker Hub image pages for `burhop/wright`, Docker Desktop on Windows 11 using Linux containers, Linux workstations including Dell GB10-class systems, Hermes Desktop integration paths.

**Project Type**: Modular monorepo release-readiness and documentation feature spanning docs, GitHub workflows, Docker metadata, Python package metadata, and contributor-facing runbooks.

**Performance Goals**: New users should identify the correct install path in under three minutes; release artifacts should avoid requiring local image builds for standard install paths once public images are available.

**Constraints**: Preserve offline-first and bring-your-own-AI messaging; do not imply bundled LLMs, proprietary tool licenses, hosted services, or unvalidated platform support; keep MCP-specific host software out of the base image; use merge gate scripts before merging to `dev` or `main`.

**Scale/Scope**: Public alpha release readiness for at least eight user personas, one canonical appliance image family (`burhop/wright` and `ghcr.io/burhop/wright`), one alpha PyPI project (`wright-engineering`), one funding strategy, and one partner outreach packet.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass. Work is scoped to existing docs, workflow, Docker, package metadata, and release surfaces without moving package boundaries.
- **Offline-First Mandate**: Pass. Install and funding materials must preserve local-first/BYO-AI language and avoid cloud-only assumptions.
- **Container Strategy**: Pass with caveat. This feature documents and hardens the existing appliance strategy; any change to image contents must continue to avoid MCP-specific host software in the base image unless separately validated.
- **Agent Abstraction**: Pass. Hermes Desktop and Wright integration will be described without hardcoding Hermes into generic Wright install semantics beyond existing adapter/plugin surfaces.
- **Zero-Server Databases**: Pass. No new database services are introduced.
- **Security & Identity**: Pass. Public materials must point to security policy and avoid publishing secrets or private maintainer-only instructions.
- **Engineering Tooling Protocol**: Pass. MCP contributor guidance will point to the clean-container validation process.
- **UI & Testing**: Pass. UI changes are not required for MVP; if links are added to the app, existing frontend testing conventions apply.
- **Observability & Tracing**: Pass. No runtime observability behavior changes are required.
- **Branch Discipline and Manual Gating**: Pass. Work is on `041-community-release-readiness`; implementation edits should wait for human review of this plan/tasks.

## Project Structure

### Documentation (this feature)

```text
specs/041-community-release-readiness/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── public-release-artifacts.md
└── tasks.md
```

### Source Code (repository root)

```text
README.md                              # Primary public entry point
.github/FUNDING.yml                    # GitHub sponsor button metadata
.github/workflows/release.yml          # Container release publishing
.github/workflows/docker-build.yml     # Container build and smoke validation
.github/workflows/publish-python-packages.yml
pyproject.toml                         # Root `wright-engineering` alpha package
packages/*/pyproject.toml              # Component package metadata; PyPI publication deferred for alpha
hermes-plugin-wright/                  # Hermes plugin package and mirror guidance
docker/Dockerfile                      # Appliance image definition
docker/DOCKER_HUB_README.md            # Container registry listing copy
docker-compose.yml
docker-compose.minimal.yml
docs/getting-started/                  # Persona install guides
docs/release/                          # Release, package, and launch runbooks
docs/community/                        # Funding, visibility, and partner materials
scripts/                               # Existing release/check scripts
```

**Structure Decision**: Use the existing monorepo and documentation structure. The MVP should focus on public docs, release metadata, Docker Hub/GHCR image name updates, and a single `wright-engineering` PyPI helper package. Existing component package publication should be disabled or deferred for alpha rather than forced through colliding PyPI names.

## Setup Decisions Captured for Implementation

- **Public contact**: `wright@makerengineer.com`; inbound handling lives in the website/Resend setup, not this repository.
- **Docker Hub image**: `burhop/wright:<tag>`. Docker Hub repository and GitHub Actions secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured.
- **GHCR image**: `ghcr.io/burhop/wright:<tag>` for parity with Docker Hub and simpler public docs.
- **PyPI package**: `wright-engineering`. `wright` and `wright-core` are unavailable, and component package publishing is deferred for alpha.
- **Trusted Publishing**: PyPI and TestPyPI pending publishers are configured for `wright-engineering` using workflow `publish-python-packages.yml` and environments `pypi` and `testpypi`.
- **No release action in this feature branch**: implementation may update docs/workflows/package metadata, but actual Docker/PyPI publication waits for explicit maintainer release action.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design & Contracts

See [data-model.md](data-model.md), [contracts/public-release-artifacts.md](contracts/public-release-artifacts.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

- **Modular Monorepo Boundaries**: Pass. Release, docs, Docker, and package surfaces remain in their existing ownership areas.
- **Offline-First Mandate**: Pass. Design requires explicit local-first and BYO-AI disclaimers on public install/funding materials.
- **Container Strategy**: Pass. Public container work documents existing appliance boundaries and avoids adding MCP-specific host software.
- **Agent Abstraction**: Pass. Hermes Desktop is documented as an integration path rather than the generic Wright runtime.
- **Zero-Server Databases**: Pass. No new runtime storage or services.
- **Security & Identity**: Pass. Security links and secret-free publishing are part of public listing requirements.
- **Engineering Tooling Protocol**: Pass. MCP validation references the clean-container process.
- **UI & Testing**: Pass. Any UI changes are deferred unless tasks identify a necessary public link surface.
- **Observability & Tracing**: Pass. No runtime change.
- **Branch Discipline and Manual Gating**: Pass. Planning is complete on a feature branch; implementation awaits review.

## Complexity Tracking

No constitution violations identified.
