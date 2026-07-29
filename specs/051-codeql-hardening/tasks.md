# Tasks: CodeQL Security Hardening

**Input**: Design documents from `/specs/051-codeql-hardening/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/security-boundary-contract.md, quickstart.md

**Tests**: Security regressions are mandatory and are written before each implementation task.

**Organization**: Tasks are grouped by independently testable user story and limited to the 14-alert baseline.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no dependency on an incomplete task
- **[Story]**: Maps the task to the corresponding specification user story

## Phase 1: Setup and Scope Guardrails

**Purpose**: Confirm the feature starts without hidden setup/configuration expansion.

- [X] T001 Verify existing ignore coverage and confirm no feature-specific dependency/configuration additions are required in `.gitignore`, `.dockerignore`, `apps/web/eslint.config.js`, and `.prettierignore`
- [X] T002 Confirm the 14-alert dev baseline and focused validation commands remain accurately recorded in `specs/051-codeql-hardening/research.md` and `specs/051-codeql-hardening/quickstart.md`

---

## Phase 2: Foundational Security Contracts

**Purpose**: Establish common limits and ownership before story implementation.

**CRITICAL**: User-story fixes must follow `specs/051-codeql-hardening/contracts/security-boundary-contract.md` and may not add scanner suppression or unrelated cleanup.

- [X] T003 Define shared probe bounds, configured-local-origin authority, address classes, sanitized result fields, and Host/SNI pinning compatibility assertions in `packages/agent_adapters/tests/test_health_probe_security.py`
- [X] T004 Define generated vault key and canonical containment behavior in `packages/data_vault/tests/test_file_vault.py`
- [X] T005 Define registered-existing versus generated-managed workspace authorization behavior in `packages/workspace_service/tests/test_workspace_service.py`

**Checkpoint**: Failing package-level contracts exist for the three authority-owning services.

---

## Phase 3: User Story 1 - Safely Check Local Services (Priority: P1) MVP

**Goal**: Preserve intentional local Hermes/local-LLM health checks while preventing unsafe URL, DNS, address, proxy, and redirect behavior.

**Independent Test**: The probe package and setup endpoint accept permitted loopback/configured local/global targets, connect only to validated pinned addresses, and reject every specified bypass without contacting a prohibited target.

### Tests for User Story 1

- [X] T006 [P] [US1] Add URL syntax, numeric-host, DNS class, mixed-answer, private-origin authorization, IP pinning, Host/SNI, proxy isolation, redirect, fallback, timeout, and sanitization regressions in `packages/agent_adapters/tests/test_health_probe_security.py`
- [X] T007 [P] [US1] Add authenticated setup endpoint contract tests for permitted local probes and generic blocked/network failures in `apps/api/tests/test_setup_api.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement provider-neutral URL parsing, configured-local-origin policy, DNS/address classification, numeric-IP pinning, manual redirects, structural fallback, bounds, and sanitized results in `packages/agent_adapters/src/agent_adapters/health_probe.py`
- [X] T009 [US1] Export only the required probe contract from `packages/agent_adapters/src/agent_adapters/__init__.py`
- [X] T010 [US1] Replace the arbitrary router fetch with thin probe delegation and generic response mapping in `apps/api/src/api/routers/setup.py`
- [X] T011 [US1] Run the US1 focused suite for `packages/agent_adapters/tests/test_health_probe_security.py` and `apps/api/tests/test_setup_api.py`

**Checkpoint**: User Story 1 passes independently with no external network access.

---

## Phase 4: User Story 2 - Keep Requests Inside Authorized Boundaries (Priority: P1)

**Goal**: Prevent path, parser, package, regex, and browser-origin input from escaping Wright's authorized boundaries.

**Independent Test**: Vault/workspace/title/package/glob/viewer focused suites accept current valid workflows and reject traversal, symlink, repeated input, metacharacter, malformed identity, and origin-manipulation cases.

### Tests for User Story 2

- [X] T012 [P] [US2] Complete traversal, Windows path, sibling-prefix, NUL, symlink, legacy confined read, and generated upload-key package tests in `packages/data_vault/tests/test_file_vault.py`
- [X] T013 [P] [US2] Add vault upload/download API regressions proving raw filenames never become storage paths in `apps/api/tests/test_vault_security.py`
- [X] T014 [P] [US2] Complete registered path, missing directory, symlink alias, unregistered path, and generated managed-root cases in `packages/workspace_service/tests/test_workspace_service.py`
- [X] T015 [P] [US2] Add session API filesystem-mutation and bounded `/title` parser regressions in `apps/api/tests/test_agent_security.py`
- [X] T016 [P] [US2] Add valid VCS/PyPI/scoped-npm and malicious substring, URL, traversal, leading-option, no-network, and no-subprocess regressions in `packages/tool_registry/tests/test_version_check.py`
- [X] T017 [P] [US2] Extend literal regex-metacharacter, backslash, wildcard, malformed-pattern, and priority tests in `apps/web/src/services/viewer-panel/__tests__/registry.test.ts`
- [X] T018 [P] [US2] Add root-relative source, query-encoding, sandbox, and normal HTML/PDF rendering tests in `apps/web/src/services/viewer-panel/__tests__/providers.test.ts`

### Implementation for User Story 2

- [X] T019 [US2] Implement generated vault storage keys and canonical confined file resolution in `packages/data_vault/src/data_vault/file_vault.py` and export the narrow API from `packages/data_vault/src/data_vault/__init__.py`
- [X] T020 [US2] Delegate upload/read behavior to the data-vault boundary in `apps/api/src/api/routers/vault.py`
- [X] T021 [US2] Implement registered-existing and UUID-generated managed session workspace authorization in `packages/workspace_service/src/workspace_service/service.py`
- [X] T022 [US2] Remove request-selected directory creation and replace title regex parsing with a linear 200-character bounded parser in `apps/api/src/api/routers/agent.py`
- [X] T023 [US2] Replace package/Git substring logic with structural VCS parsing, manager-specific package validation, and encoded registry paths in `packages/tool_registry/src/tool_registry/version_check.py`
- [X] T024 [US2] Implement one-pass complete regex escaping for supported glob tokens in `apps/web/src/services/viewer-panel/registry.ts`
- [X] T025 [US2] Build root-relative workspace content URLs and preserve HTML sandboxing in `apps/web/src/services/viewer-panel/providers/iframe-provider.ts` and `apps/web/src/services/viewer-panel/providers/pdf-provider.ts`
- [X] T026 [US2] Run the US2 focused Python and frontend suites listed in `specs/051-codeql-hardening/quickstart.md`

**Checkpoint**: User Story 2 passes independently and no caller-selected path is created.

---

## Phase 5: User Story 3 - Receive Safe, Traceable Failures (Priority: P2)

**Goal**: Keep full correlated diagnostics in protected logs while clients receive only generic traceable failures, and produce evidence-backed scanner dispositions.

**Independent Test**: Sentinel secrets/paths never appear in proxy or SSE output, SPA containment defeats traversal/sibling/symlink cases, and CodeQL dispositions match the contract.

### Tests for User Story 3

- [X] T027 [P] [US3] Add Onshape proxy exception-leak and SPA traversal, encoded traversal, absolute, sibling-prefix, and supported-host symlink regressions in `apps/api/tests/test_main_security.py`
- [X] T028 [P] [US3] Extend normal job and attach-path SSE failure tests to require generic trace-bearing errors without sentinel details in `apps/api/tests/test_agent_stream_progress.py`
- [X] T029 [P] [US3] Confirm the synthetic `http://llm.local` request is fully intercepted by `respx` and cannot reach the network in `packages/agent_adapters/tests/test_hermes_gateway_adapter.py`

### Implementation for User Story 3

- [X] T030 [US3] Replace raw Onshape proxy errors with generic trace-bearing responses and canonical `Path.relative_to` SPA asset containment in `apps/api/src/api/main.py`
- [X] T031 [US3] Log complete chat failures but emit generic trace-bearing events from both chat-job and attach failure paths in `apps/api/src/api/routers/agent.py`
- [X] T032 [US3] Run the US3 focused suites for `apps/api/tests/test_main_security.py`, `apps/api/tests/test_agent_stream_progress.py`, and `packages/agent_adapters/tests/test_hermes_gateway_adapter.py`

**Checkpoint**: All three user stories pass independently and together.

---

## Phase 6: Polish, Delivery, and Production Readiness

**Purpose**: Validate the complete scoped change, merge only to dev, and prove final-dev security/release readiness.

- [X] T033 Run focused Ruff/format, TypeScript, ESLint, and Prettier checks over all changed paths from `apps/api`, `apps/web`, `packages/agent_adapters`, `packages/data_vault`, `packages/workspace_service`, and `packages/tool_registry`
- [X] T034 Run every focused Python/frontend command in `specs/051-codeql-hardening/quickstart.md` and mark all completed task checkboxes in `specs/051-codeql-hardening/tasks.md`
- [X] T035 Run the complete `scripts/check-dev-merge.sh` gate and, only if CI later exposes a missing gate, update `scripts/check-dev-merge.sh` plus the corresponding contributor documentation in `docs/`
- [X] T036 Review `git diff dev...051-codeql-hardening` for unrelated changes, scanner suppression, dependency/workflow version changes, Hermes/MCP changes, and accidental `main` changes
- [X] T037 Execute the configured Spec Kit after-implementation commit for the completed files in `specs/051-codeql-hardening/`, `apps/`, and `packages/`
- [ ] T038 Push `051-codeql-hardening`, open a pull request targeting `dev`, and monitor/correct all workflows defined under `.github/workflows/` until every required check passes
- [ ] T039 Merge the green feature pull request only into `dev`, fast-forward local `dev` to `origin/dev`, and verify a clean synchronized worktree at `D:/repos/wright`
- [ ] T040 Monitor every workflow on the final dev commit and correct any failure through a narrowly scoped follow-up branch/PR before continuing
- [ ] T041 Verify dev has no production instances of alerts #3, #4, #5, #7, #8, #10, #12, #24, #25, #27, #28, and #29; dismiss #2 as `used in tests`; fix #13 or dismiss it as `false positive` only with evidence recorded in `specs/051-codeql-hardening/quickstart.md`
- [ ] T042 Run `scripts/check-prod-merge.sh` on final synchronized `dev` as a production-readiness check without merging or modifying `main`
- [ ] T043 Record the final dev commit, PR URL, focused/full tests, both gate results, final-dev CI, alert dispositions, main-versus-dev distinction, and any remaining production blocker in the goal completion report

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational contracts (Phase 2)**: Depends on setup and blocks story implementations.
- **US1 (Phase 3)**: Depends on T003 and may proceed while US2 test files are prepared.
- **US2 (Phase 4)**: Depends on T004-T005 and is otherwise independent of US1.
- **US3 (Phase 5)**: Error work can begin after foundational contracts; its `agent.py` implementation follows T022 to avoid same-file conflict.
- **Delivery (Phase 6)**: Depends on every story checkpoint.

### User Story Dependencies

- **US1**: No dependency on other stories.
- **US2**: No behavior dependency on US1.
- **US3**: No behavior dependency on US1/US2, but T031 follows T022 because both edit `agent.py`.

### Within Each User Story

- Tests must be added and observed failing before implementation.
- Owning package behavior precedes thin API routing.
- Focused story suites pass before the next story checkpoint.
- A task is marked `[X]` only after its behavior or verification actually completes.

### Parallel Opportunities

- T006 and T007 target different test layers.
- T012-T018 are independent test files.
- T027-T029 are independent test files.
- Python and frontend focused suites can run concurrently after implementation.
- GitHub workflow monitoring runs concurrently across all checks, but failures are corrected serially by root cause.

## Parallel Example: User Story 2

```text
Task T012: data-vault package traversal and symlink tests
Task T014: workspace-service registered/managed path tests
Task T016: tool-registry package/VCS validation tests
Task T017: viewer glob escaping tests
Task T018: viewer provider same-origin tests
```

## Implementation Strategy

### MVP First (US1)

1. Complete scope/setup and shared health-probe contracts.
2. Implement and independently verify the SSRF-safe probe.
3. Continue only after local Hermes and configured local-LLM cases still pass.

### Incremental Delivery

1. US1 closes the critical network boundary.
2. US2 closes filesystem/parser/package/browser boundaries.
3. US3 closes disclosure/static containment and establishes scanner evidence.
4. Phase 6 validates the combined production candidate and merges only to dev.

## Notes

- `[P]` tasks edit different files and can be prepared independently.
- Do not weaken CodeQL, add suppressions, or broaden the feature to nearby findings.
- Existing main instances may remain until a later separately authorized dev-to-main promotion.
- `scripts/check-dev-merge.sh` and `scripts/check-prod-merge.sh` are authoritative.
