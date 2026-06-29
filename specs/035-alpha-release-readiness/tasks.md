# Tasks: Alpha Release Readiness Slice

**Input**: `spec.md`, `plan.md`, prior release-readiness prompt, and
`specs/034-engineering-mcp-catalog/plan.md`

## Phase 1: Audit and Planning

- [X] T001 Create Spec Kit branch `035-alpha-release-readiness`.
- [X] T002 Read current engineering MCP catalog plan and clean-container MCP
  validation process.
- [X] T003 Produce durable release-readiness audit and phase plan in
  `docs/alpha-release-readiness.md`.

## Phase 2: Public Docs and Intake

- [X] T004 Update README with alpha status, bring-your-own-AI guidance, correct
  Docker quickstart, and selected-MCP-dependency language.
- [X] T005 Replace Docker quickstart with current compose paths, ports, LLM
  examples, persistence, LAN access, GPU caveats, and MCP validation boundary.
- [X] T006 Update environment variable documentation for LLM, Hermes, API, UI,
  and MCP settings.
- [X] T007 Update Docker Hub README and Dockerfile comments to match the
  gateway/appliance contract.
- [X] T008 Add public-alpha roadmap and needed MCP server backlog.
- [X] T009 Improve GitHub bug reporting template and allow blank alpha issues
  with contact links preserved.

## Phase 3: CI and Tests

- [X] T010 Add Vitest and production build steps to frontend CI.
- [X] T011 Fix Docker smoke supervisor process check from `hermes-webui` to
  `hermes-gateway`.
- [X] T012 Add release-readiness regression tests for README, Docker docs, issue
  templates, CI commands, and Docker gateway contract.
- [X] T013 Run targeted pytest release-readiness tests.
- [X] T014 Run frontend Vitest and production build.

## Phase 4: Continued Docs Release Gate

- [X] T015 Fix MkDocs strict-build warnings caused by source/spec links.
- [X] T016 Add PR-time strict MkDocs build gate in `.github/workflows/docs-deploy.yml`.
- [X] T017 Add public repository launch checklist to published docs nav.
- [X] T018 Add tests for docs build workflow and launch checklist coverage.

## Phase 5: Release Tag Policy

- [X] T019 Mark alpha, beta, and release-candidate tags as GitHub prereleases.
- [X] T020 Prevent prerelease tags from moving the Docker `latest` tag.
- [X] T021 Document prerelease and Docker `latest` policy in `docs/versioning.md`.
- [X] T022 Add tests for release workflow and versioning policy.

## Phase 6: Public Alpha Leak Gate

- [X] T023 Add repo-native public-alpha leak scan script.
- [X] T024 Add CI workflow for tracked-file leak scanning.
- [X] T025 Document local tracked and untracked leak-scan commands.
- [X] T026 Add tests for leak detection, placeholder allowlisting, and current tracked tree.

## Phase 7: Docker Smoke Contract

- [X] T027 Align local Docker smoke script with setup-pending LLM behavior.
- [X] T028 Add existing-image smoke mode for release candidate images.
- [X] T029 Update script documentation for current Docker smoke behavior.
- [X] T030 Add tests for Docker smoke script and CI process-name contract.

## Phase 8: GitHub Label Readiness

- [X] T031 Add `.github/labels.yml` with public-alpha triage labels.
- [X] T032 Ensure issue template labels exist in the manifest.
- [X] T033 Update public launch checklist to reference the label manifest.
- [X] T034 Add tests for required labels and template-label consistency.

## Phase 9: Docker Registry Publication Policy

- [X] T035 Add GHCR login and image tags to the release workflow.
- [X] T036 Preserve stable-only `latest` behavior across Docker Hub and GHCR.
- [X] T037 Document GHCR/Docker Hub image names and release prerequisites.
- [X] T038 Add tests for registry tags, permissions, and image-name docs.

## Phase 10: Optional Docker Hub Publishing

- [X] T039 Make Docker Hub login and description sync conditional on Docker Hub credentials.
- [X] T040 Generate Docker Hub image tags only when Docker Hub credentials are configured.
- [X] T041 Document GHCR as the default release registry path and Docker Hub as optional.
- [X] T042 Add tests for optional Docker Hub release behavior.

## Phase 11: Concrete Install Path Documentation

- [X] T043 Replace local quickstart with PC-local alpha setup that uses current
  `uv`, `uvicorn`, npm workspace, LLM, health-check, and verification commands.
- [X] T044 Add GB10/DGX workstation install path with host model-server,
  GPU-passthrough, architecture, and MCP validation boundaries.
- [X] T045 Add existing Hermes plugin install path with Hermes API server,
  plugin install, LLM status, and `/wright` command guidance.
- [X] T046 Publish install paths in MkDocs nav and overview.
- [X] T047 Add regression tests for getting-started install paths.
