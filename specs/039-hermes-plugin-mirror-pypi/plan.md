# Implementation Plan: Hermes Plugin Mirror and PyPI Packages

**Branch**: `039-hermes-plugin-mirror-pypi` | **Date**: 2026-07-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/039-hermes-plugin-mirror-pypi/spec.md`

## Summary

Deliver Option A for Wright distribution: keep the main Wright monorepo as the source of truth, publish the plugin's shared Python dependencies as installable Python packages, and maintain a thin standalone Hermes plugin mirror whose repository root is directly installable and updateable by Hermes. The implementation adds release automation, mirror sync validation, PyPI/TestPyPI publication gates, and customer-facing mirror documentation so users can install, update, and remove Wright through the standard Hermes plugin lifecycle.

## Technical Context

**Language/Version**: Python 3.11+ package metadata and tests, Bash lifecycle scripts, GitHub Actions YAML, Markdown documentation

**Primary Dependencies**: Existing `hatchling` package builds, `uv` workspace management, `pypa/build` for distribution archives, `pypa/gh-action-pypi-publish` for Trusted Publishing, Hermes Agent 0.18, Docker-based Hermes lifecycle test image

**Storage**: Git repositories, release artifacts, Python package distribution archives, and generated provenance metadata only; no runtime database changes

**Testing**: `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, package build checks, clean-environment package install checks, and Docker-backed Hermes install/update/remove lifecycle tests

**Target Platform**: GitHub-hosted Linux CI for release automation; customer Hermes Agent 0.18+ environments on Windows, Linux, and macOS; Wright Docker lifecycle image for repeatable validation

**Project Type**: Monorepo release engineering plus standalone plugin mirror distribution

**Performance Goals**: A new tester can complete mirror install, update, and removal in under 10 minutes; package and mirror validation should run in CI without adding large toolchain downloads beyond the existing Wright image; mirror sync should complete in under 5 minutes for plugin-only content

**Constraints**: No changes to `NousResearch/hermes-agent`; mirror repository root must contain `plugin.yaml`; stable plugin releases must not depend on monorepo workspace paths; development Git dependencies must be pinned and documented; PyPI publishing must avoid long-lived API tokens; mirror must not include generated caches, personal paths, Docker appliance content, or unrelated monorepo files

**Scale/Scope**: One plugin mirror repository, two initial PyPI packages (`wright-core`, `wright-tool-registry`), stable and development release channels, and lifecycle validation for install, update, remove, and reinstall

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass. The monorepo remains source of truth; package metadata stays with `packages/core`, `packages/tool_registry`, and `hermes-plugin-wright`; sync/release scripts live under `scripts/` and workflows under `.github/workflows/`.
- **Offline-First Mandate**: Pass with distribution caveat. Initial install/update may require network access to GitHub and PyPI, but no core Wright runtime behavior gains a required cloud dependency after installation.
- **Agent Abstraction**: Pass. The plan does not hardcode any LLM or agent provider; it only changes plugin packaging and distribution.
- **Container Strategy**: Pass. Validation reuses the existing Wright/Hermes Docker image and does not add MCP-specific host software to make catalog checks pass.
- **Zero-Server Databases**: Pass. No new databases, background services, or persistent runtime stores are introduced.
- **Security & Identity**: Pass. PyPI publishing uses trusted publishing/OIDC rather than stored tokens; release checks must reject credentials, personal paths, and generated caches.
- **Engineering Tooling Protocol**: Pass. The tool registry package remains the owner of MCP catalog models and validation contracts; no GUI-only tool execution is introduced.
- **UI & Testing**: Pass. No UI changes are planned; test coverage focuses on package, release, and Hermes lifecycle behavior.
- **Observability & Tracing**: Pass. Runtime tracing is unchanged; release automation produces CI logs and provenance records for auditability.
- **Autonomous Agent Workflow Rules**: Pass. Work is isolated on `039-hermes-plugin-mirror-pypi`, and this plan stops before implementation tasks.

## Project Structure

### Documentation (this feature)

```text
specs/039-hermes-plugin-mirror-pypi/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── hermes-lifecycle-contract.md
│   ├── mirror-repository-contract.md
│   ├── python-package-contract.md
│   └── release-validation-contract.md
└── tasks.md              # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
.github/workflows/
├── python-quality.yml             # Existing quality gate, expanded for packaging checks
├── release.yml                    # Existing release workflow, kept for Docker/GitHub release
├── publish-python-packages.yml    # New package publish workflow for PyPI/TestPyPI
└── sync-hermes-plugin-mirror.yml  # New mirror sync and validation workflow

hermes-plugin-wright/
├── plugin.yaml
├── __init__.py
├── bridge.py
├── catalog.py
├── catalog.yaml
├── commands.py
├── pyproject.toml                 # Remove workspace-only dependency behavior for mirror builds
├── README.md                      # Mirror-ready install/update/remove and main repo links
├── schemas.py
├── tests/
└── verify_plugin.py

packages/
├── core/
│   ├── pyproject.toml             # PyPI metadata, project URLs, package data validation
│   └── src/core/
└── tool_registry/
    ├── pyproject.toml             # PyPI metadata and versioned dependency on wright-core
    └── src/tool_registry/

scripts/
├── build-python-distributions.sh          # New local build/check helper for release candidates
├── sync-hermes-plugin-mirror.sh           # New filtered export from plugin source to mirror root
├── validate-hermes-plugin-mirror.sh       # New mirror content/provenance/README validator
├── hermes-plugin-lifecycle-common.sh      # Update to support root mirror installs without subdir
├── test-hermes-plugin-install.sh
├── test-hermes-plugin-uninstall.sh
└── test-hermes-plugin-update.sh

docs/release/
└── hermes-plugin-mirror.md        # New maintainer release runbook
```

**Structure Decision**: Keep all development in the Wright monorepo and publish a filtered root-level mirror repository for Hermes users. The mirror contains only the plugin files, tests, metadata, README, license/provenance, and minimal release validation helpers needed for customer installation. Shared runtime code is distributed through versioned Python packages for stable releases and pinned Git dependencies for development testing only.

## Phase 0: Research Summary

Research resolved the open planning questions into five decisions:

1. Use a root-level standalone mirror repository for Hermes lifecycle compatibility.
2. Publish `wright-core` and `wright-tool-registry` before stable plugin releases.
3. Use PyPI/TestPyPI Trusted Publishing through GitHub Actions OIDC.
4. Generate the mirror from the monorepo with an allowlist and provenance record.
5. Validate the mirror as a customer would use it, including update behavior.

Details are captured in [research.md](research.md).

## Phase 1: Design Summary

Design artifacts created by this plan:

- [data-model.md](data-model.md): Mirror repository, package, release, channel, provenance, and validation entities.
- [contracts/mirror-repository-contract.md](contracts/mirror-repository-contract.md): Required and prohibited mirror repository content.
- [contracts/python-package-contract.md](contracts/python-package-contract.md): Package metadata, build, and publication contract.
- [contracts/hermes-lifecycle-contract.md](contracts/hermes-lifecycle-contract.md): Install/update/remove behavior expected by lifecycle tests.
- [contracts/release-validation-contract.md](contracts/release-validation-contract.md): Release gate inputs, checks, and outputs.
- [quickstart.md](quickstart.md): Maintainer validation path for package builds, mirror sync, and lifecycle tests.

## Post-Design Constitution Check

- **Modular Monorepo Boundaries**: Pass. Contracts keep `wright-core`, `wright-tool-registry`, and plugin mirror responsibilities separate.
- **Offline-First Mandate**: Pass. Network is limited to installation and release publication, not core post-install Wright operation.
- **Agent Abstraction**: Pass. No agent implementation changes.
- **Container Strategy**: Pass. Existing Docker validation remains the repeatable test surface.
- **Zero-Server Databases**: Pass. No storage service added.
- **Security & Identity**: Pass. Trusted Publishing, manual approval for PyPI release environment, provenance, and leak checks are required.
- **Engineering Tooling Protocol**: Pass. Tool registry ownership is preserved.
- **UI & Testing**: Pass. No UI scope.
- **Observability & Tracing**: Pass. CI logs and provenance cover release traceability.
- **Autonomous Agent Workflow Rules**: Pass. Planning artifacts only; implementation waits for task generation and approval.

## Complexity Tracking

No Constitution violations detected.
