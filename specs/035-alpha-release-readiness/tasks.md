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
