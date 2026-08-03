# Tasks: Rivet Compatibility Spike

**Input**: Design documents from `specs/055-rivet-compatibility-spike/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Required. This spike must produce deterministic contract/fixture assertions, reproducibility evidence, offline request evidence, and a documented decision; it must not introduce production application tests or production code.

**Organization**: Tasks are grouped by user story so each decision outcome can be evaluated independently. Experimental assets are isolated under `integrations/rivet/spike/` and never change production ownership.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its stated prerequisites.
- **[Story]**: Maps the task to an independently verifiable user story.

## Phase 1: Setup and Evidence Controls

**Purpose**: Establish a controlled, ignored experimental workspace and normalized evidence format before acquiring any upstream source.

- [X] T001 Create the isolated spike directory, README, and no-production-use boundary in `integrations/rivet/spike/README.md`.
- [X] T002 Create ignored generated-work/cache/report patterns without hiding committed fixture metadata in `.gitignore`.
- [X] T003 [P] Create the structured evidence helpers in `integrations/rivet/spike/scripts/evidence.mjs` and the normalized probe envelope schema in `integrations/rivet/spike/baseline/evidence-envelope.schema.json`.
- [X] T004 [P] Create the synthetic fixture data and expected capability inventory in `integrations/rivet/spike/fixture/`.
- [X] T005 Create a contract test that rejects real credential, workspace, session, token, and production-package references in spike assets at `tests/contract/rivet_spike/test_spike_isolation.py`.
- [X] T006 Run the isolation test and verify the workspace remains free of production route/schema/package/UI changes; record the initial result in `specs/055-rivet-compatibility-spike/evidence/phase-setup.md`.

**Checkpoint**: The experiment has a controlled root, synthetic-only data, structured evidence, and a testable production-isolation boundary.

---

## Phase 2: Foundational Candidate Acquisition

**Purpose**: Establish immutable source/package/build identities and reusable acquisition/probe commands. This phase blocks every user story.

- [X] T007 Implement immutable upstream source/tag/package resolution and checksum capture in `integrations/rivet/spike/scripts/acquire-baseline.mjs`.
- [X] T008 Implement deterministic patch discovery/application verification in `integrations/rivet/spike/scripts/verify-patch.mjs` and `integrations/rivet/spike/baseline/patches/README.md`.
- [X] T009 [P] Implement direct/transitive package/license/integrity inventory generation in `integrations/rivet/spike/scripts/inventory-supply-chain.mjs`.
- [X] T010 [P] Create tests for source immutability, lockfile integrity, and patch clean-apply failure behavior in `integrations/rivet/spike/tests/baseline.test.mjs`.
- [X] T011 Create the baseline record template and primary/fallback selection criteria in `integrations/rivet/spike/baseline/baseline.json` and `integrations/rivet/spike/baseline/README.md`.
- [X] T012 Execute the acquisition/inventory scripts for the primary candidate and record source, package, lockfile, environment, and initial supply-chain results in `specs/055-rivet-compatibility-spike/evidence/baseline-acquisition.md`.

**Checkpoint**: One inspectable candidate baseline is acquired by immutable identity. A source/package/patch mismatch fails closed.

---

## Phase 3: User Story 1 - Decide Whether Rivet Can Be Safely Adopted (Priority: P1)

**Goal**: Produce repeatable build and decision evidence for one exact Rivet baseline, with a clear result if it fails.

**Independent Test**: Two clean acquisition/build runs yield matching recorded identities and output manifests, or the candidate is rejected with a reproducible failure.

- [X] T013 [P] [US1] Implement a clean editor/core/node build command and static asset manifest generator in `integrations/rivet/spike/scripts/build-baseline.mjs`.
- [ ] T014 [P] [US1] Implement a two-run checksum comparison assertion in `integrations/rivet/spike/tests/reproducibility.test.mjs`.
- [ ] T015 [US1] Execute two clean baseline builds, capture timing/size/checksums, and write redacted raw evidence references in `specs/055-rivet-compatibility-spike/evidence/reproducibility.md`.
- [ ] T016 [US1] Classify the baseline source, application, core, Node, executor, build, and platform prerequisites in `specs/055-rivet-compatibility-spike/evidence/compatibility-matrix.md`.
- [ ] T017 [US1] Add a failure-path regression test that proves an unpinned revision/range or mismatched artifact digest is rejected in `integrations/rivet/spike/tests/reproducibility.test.mjs`.

**Checkpoint**: The slice can truthfully select or reject a precise candidate; no floating dependency is accepted.

---

## Phase 4: User Story 2 - Prove the Required Host Boundaries (Priority: P1)

**Goal**: Determine the editor/provider and Node/bridge seams necessary to preserve workspace ownership and Wright governance.

**Independent Test**: A synthetic two-workspace fixture records all editor persistence/native assumptions and executes a Node graph with a mock host external call, cancellation attempt, and debugger attempt.

- [X] T018 [P] [US2] Implement static editor behavior tracing for IO, dataset, native API, browser persistence, Tauri, global-directory, plugin, and external-navigation assumptions in `integrations/rivet/spike/scripts/probe-editor.mjs`.
- [ ] T019 [P] [US2] Implement a dual-synthetic-workspace provider-injection probe and expected-isolation assertions in `integrations/rivet/spike/tests/provider-isolation.test.mjs`.
- [X] T020 [P] [US2] Implement the Node fixture graph, mock external-call bridge, lifecycle event recorder, and abort/cancel probe in `integrations/rivet/spike/fixture/runner-harness.mjs`.
- [X] T021 [P] [US2] Implement the generated remote-debugger endpoint and stale/cross-fixture connection probe in `integrations/rivet/spike/fixture/debugger-harness.mjs`.
- [ ] T022 [US2] Run editor and provider probes against the built baseline and classify every observed host/persistence behavior in `specs/055-rivet-compatibility-spike/evidence/editor-host-seams.md`.
- [ ] T023 [US2] Run the Node/external-call/cancel/debugger probes and record event, error, cancellation, and connection evidence in `specs/055-rivet-compatibility-spike/evidence/runner-bridge.md`.
- [ ] T024 [US2] Decide and document External Call versus a Wright-owned approved plugin, including prohibited direct-MCP/plugin behavior, in `specs/055-rivet-compatibility-spike/evidence/bridge-decision.md`.
- [ ] T025 [US2] Update `specs/055-rivet-compatibility-spike/evidence/compatibility-matrix.md` with required later-slice controls for persistence, runner, editor adapters, and governed nodes.

**Checkpoint**: The program has evidence for the workspace/provider, runner, bridge, and debugger boundaries, or it stops with a no-go finding.

---

## Phase 5: User Story 3 - Preserve Offline and Release Viability (Priority: P1)

**Goal**: Establish whether the candidate can be packaged without runtime code or asset downloads and whether its supply chain is acceptable.

**Independent Test**: The built fixture runs under recorded outbound-denial policy and a complete license/security/asset inventory identifies every shipped dependency.

- [X] T026 [P] [US3] Implement a deterministic outbound request recorder/deny policy for build and fixture runs in `integrations/rivet/spike/scripts/network-policy.mjs`.
- [ ] T027 [P] [US3] Implement asset-manifest, size, checksum, and unexpected-authority assertions in `integrations/rivet/spike/tests/offline-assets.test.mjs`.
- [ ] T028 [P] [US3] Implement supply-chain inventory validation for missing license/integrity/security disposition in `integrations/rivet/spike/tests/supply-chain.test.mjs`.
- [ ] T029 [US3] Execute the supported fixture path under the denial policy and record attempted authorities, outcomes, and remediation in `specs/055-rivet-compatibility-spike/evidence/offline-trial.md`.
- [ ] T030 [US3] Generate the direct/transitive license, integrity, vulnerability, size, platform-prerequisite, and ownership inventory in `specs/055-rivet-compatibility-spike/evidence/supply-chain.md`.
- [ ] T031 [US3] Update the matrix with browser/Hermes/native/Docker/offline dispositions and explicitly mark unverified contexts in `specs/055-rivet-compatibility-spike/evidence/compatibility-matrix.md`.

**Checkpoint**: Offline/package feasibility is evidence-backed; any mandatory download or unresolved supply-chain issue blocks selection.

---

## Phase 6: User Story 4 - Hand Off a Safe Contract to Later Slices (Priority: P2)

**Goal**: Make the spike’s result reusable without promoting experimental code or ambiguity.

**Independent Test**: A maintainer can locate the pin, patch status, capabilities, limitations, evidence commands, and next-slice controls within ten minutes.

- [ ] T032 [P] [US4] Create the requirement-to-evidence traceability matrix in `specs/055-rivet-compatibility-spike/evidence/traceability.md`.
- [ ] T033 [P] [US4] Create the risk register and upgrade/fork/update policy in `specs/055-rivet-compatibility-spike/evidence/risk-register.md`.
- [ ] T034 [US4] Write the versioned go/conditional-go/no-go decision using the contract in `specs/055-rivet-compatibility-spike/evidence/go-no-go.md`.
- [ ] T035 [US4] Add the cleanup command and prove it removes only controlled generated spike material in `integrations/rivet/spike/scripts/clean-spike.mjs` and `specs/055-rivet-compatibility-spike/evidence/cleanup.md`.
- [ ] T036 [US4] Run the ten-minute handoff walkthrough and record the result in `specs/055-rivet-compatibility-spike/evidence/handoff.md`.

**Checkpoint**: Later slices have a bounded, evidence-backed baseline or an explicit stop condition; no experiment silently becomes production dependency.

---

## Phase 7: Polish, Gate, and Slice Completion

**Purpose**: Verify the entire spike, preserve branch isolation, and prepare its local integration evidence.

- [X] T037 Run all Node fixture tests and the Python spike-isolation contract test; record commands/results in `specs/055-rivet-compatibility-spike/evidence/test-results.md`.
- [ ] T038 Run the full quickstart sequence from a clean generated-work directory and update `specs/055-rivet-compatibility-spike/evidence/test-results.md`.
- [ ] T039 Reconcile every FR-001 through FR-014 and SC-001 through SC-007 with final evidence in `specs/055-rivet-compatibility-spike/evidence/traceability.md`.
- [ ] T040 Verify no production code/package/schema/UI/Docker change exists and update `specs/055-rivet-compatibility-spike/evidence/isolation-audit.md`.
- [ ] T041 Mark completed tasks, commit the approved spike branch intentionally, and prepare the local merge evidence in `specs/055-rivet-compatibility-spike/evidence/merge-readiness.md`.

## Dependencies & Execution Order

- Phase 1 precedes all other work.
- Phase 2 is foundational and blocks all user stories.
- US1 establishes the selected/rejected immutable baseline.
- US2 and US3 may proceed in parallel only after the buildable candidate from US1 is available; both feed US4.
- US4 produces the only allowed handoff to later program slices.
- Phase 7 requires every selected story and decision result.

## Parallel Opportunities

- T003 and T004 can proceed after T001.
- T009 and T010 can proceed after T007/T008 inputs exist.
- T013/T014, T018/T019/T020/T021, and T026/T027/T028 operate on different files after their prerequisites.
- T032 and T033 can begin once evidence identifiers stabilize.

## Implementation Strategy

1. Establish evidence hygiene and test the no-production boundary.
2. Acquire one immutable baseline, then prove/reject repeatable build identity.
3. Probe workspace-safe editor and runner/bridge seams with synthetic data only.
4. Prove/reject offline and supply-chain viability.
5. Publish the decision and handoff; if mandatory evidence fails, stop the wider program and amend the umbrella plan rather than working around the boundary.
