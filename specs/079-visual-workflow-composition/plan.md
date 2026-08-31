# Implementation Plan: Visual Workflow Composition Foundation

**Branch**: `codex/079-visual-workflow-composition` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

## Summary

Add a first-party, non-Rivet workflow composer beside the immutable EPP-F02 Process Definition view. An engineer can create the representative four-block product-definition draft, connect typed ports, declare a gate, feedback path, and intended artifacts, recover from invalid edits, save, close, reopen, and compare matching text and diagram identities. The backend owns a provisional versioned semantic contract, validation, canonical identity, and atomic persistence; the browser owns replaceable layout and interaction projections. No execution, MCP, LLM, benchmark, or release authority enters this slice.

## Technical Context

**Language/Version**: Python 3.11–3.14; TypeScript 6 / React 19

**Primary Dependencies**: Existing FastAPI, Pydantic, `jsonschema`, SQLite, React, React Router, Zod, Vitest, and Playwright; no new production dependency

**Storage**: One lazily created feature-owned SQLite sidecar in the Wright data root, containing immutable draft revisions; no change to the released definition or the main database migration ledger

**Testing**: pytest domain/repository/API/rollback tests; Vitest model/adapter/component tests; mocked Playwright; deployed Playwright walkthroughs; packaging and existing-journey non-interference; Windows writer plus exact-commit GB10 verifier

**Target Platform**: Native and Docker Wright on supported desktop browsers; Windows is authoritative for UI evidence and GB10 for isolated Linux verification

**Project Type**: Existing modular-monorepo FastAPI and React web application

**Performance Goals**: The bounded four-block draft validates and projects without perceptible interaction delay; automated functional waits remain under 5 seconds. Human acceptance is the spec's 10-minute journey, not an unproven large-canvas throughput claim.

**Constraints**: Offline; local-only; authenticated; additive; feature-flagged; strict bounded JSON; no Rivet, renderer lock-in, cloud, LLM, MCP, execution, benchmark, mutation of the released definition, or direct promotion to released status

**Scale/Scope**: One local editor, one draft at a time in the UI, four representative blocks, bounded generic concepts, three user stories, and no unlimited-scale claim

## Constitution Check

*GATE: Passed before research and rechecked after contracts.*

- FastAPI routes remain transport-only; validation and orchestration live outside API routes. **PASS**
- The composer is offline and uses local SQLite under the Wright-managed data root. **PASS**
- Existing engineer authentication/RBAC is reused; closed models, bounded payloads, compare-and-set revisions, and support-safe diagnostics fail closed. **PASS**
- UI follows tokens/primitives/components/patterns, uses stable `data-testid` values, and has component, mocked journey, and deployed-system coverage. **PASS**
- Structured tracing wraps draft reads/writes without logging draft content. **PASS**
- The released Process Definition reader, route, bytes, and packaged artifacts remain immutable and independently testable. **PASS**
- Planning is isolated from implementation. `DEC-P0-002` remains open; these provisional contracts do not close the permanent syntax/Apply decision. Human planning and implementation approvals are required before code. **PASS**
- The sidecar avoids a forward-only main-database migration that would make rollback to the prior binary fail. Removal leaves released-definition data untouched; the old binary ignores the sidecar. **PASS**
- Post-contract review found no constitutional exception. **PASS**

## Architecture and Boundaries

1. `WorkflowDraft` is the canonical semantic model. Phases, blocks, ports, connections, gates, feedback paths, and intended artifacts use globally unique stable IDs. Saved layout is a separate projection keyed by those IDs.
2. The authoring contract is provisional `1.0.0-draft.1`, strict, bounded, and distinct from the released EPP-F02 `process-definition` contract. It is not a permanent platform syntax and cannot be passed to any executor.
3. Pure backend validation returns stable diagnostic codes, affected identities, a safe explanation, and a bounded correction. Mutations operate on a working copy; an invalid operation never replaces the last valid persisted revision.
4. A feature-owned SQLite sidecar stores append-only canonical semantic and layout bytes plus digests. Save is an atomic compare-and-set against the current revision. Failed or interrupted writes preserve the prior revision.
5. FastAPI provides authenticated draft create/read/validate/save semantics with closed request/response models. Close is a browser working-session action and performs no server mutation. There is no release, apply, run, MCP, or LLM endpoint.
6. The React composer lives on a distinct feature-flagged route. A small renderer-neutral projection adapter feeds the first SVG/HTML canvas; text and properties are derived independently from the same canonical model and their identity sets are asserted equal.
7. The immutable `/process-definition` route and EPP-F02 API remain the compatibility baseline. Enabling, disabling, or removing the composer cannot change their bytes, identity, route, or behavior.
8. The frozen prototype is evidence only. Its phase lanes, compact block grammar, labeled feedback, inspector, and diagram/text parity inform fresh acceptance; execution, AI/MCP, run state, artifact rail, domain fixtures, and implementation are rejected.

## Product and Evidence Gates

- [north-star.md](north-star.md) freezes the reviewed visual direction; [prototype-parity.md](prototype-parity.md) records retain/revise/reject/defer decisions.
- Checkpoint C demonstrates a rendered four-block draft with text/diagram identity parity.
- Checkpoint D demonstrates edit, invalid connection, diagnostic, and recovery.
- Checkpoint E demonstrates atomic save, close, reopen, semantic equality, and preserved layout.
- Every second implementation increment refreshes the progress dashboard and produces a validated clickable walkthrough with raw and annotated screenshots and browser diagnostics.
- The current EPP-F02 deployed walkthrough remains a regression baseline, not authoring evidence.
- `PROD-01`, `PROD-02`, `PROD-08`, `PROD-10`, and `PROD-11` receive only incremental evidence. No gate, commercial-readiness, benchmark, or release claim changes in this slice.
- Benchmark qualification remains exactly `0/100`.

## Execution Resource Strategy

- Windows owns the write worktree, interactive UI loop, component tests, mocked and deployed Playwright, screenshots, narrow/zoom/accessibility checks, and final candidate assembly.
- GB10 receives only a committed exact candidate in an isolated worktree. It owns Linux backend/repository/API tests, frontend build/test, Docker build/smoke, schema/contract validation, and independent diff review.
- Hosts never share a writable worktree and never run the same expensive suite concurrently. Results identify exact commit and relevant image digest.
- Use focused tests first, then one consolidated Windows gate and one consolidated GB10 verification. Do not create standing agents for single checks.

## Project Structure

```text
specs/079-visual-workflow-composition/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── north-star.md
├── prototype-parity.md
├── quickstart.md
├── contracts/
│   ├── workflow-draft.schema.json
│   ├── draft-api.md
│   ├── renderer-adapter.md
│   └── representative-workflow.json
├── decisions/
│   └── 0001-provisional-draft-boundary.md
├── checklists/
└── tasks.md

packages/core/src/core/workflow_drafts.py
packages/data_vault/src/data_vault/workflow_draft_repository.py
apps/api/src/api/{schemas,routers}/workflow_drafts.py
apps/api/src/api/{composition.py,main.py}
apps/web/src/services/workflow-drafts.ts
apps/web/src/components/workflow-composer/
apps/web/src/components/pages/WorkflowComposerPage.tsx
apps/web/src/{App.tsx,components/layout/Sidebar.tsx}
tests/ui-integration/workflow-composer.spec.ts
tests/e2e/test_workflow_composer.py
```

**Structure Decision**: Reuse the existing monorepo boundaries while keeping the draft domain independent of legacy Rivet workflow packages and the immutable released-definition reader. `core` owns semantics, `data_vault` owns atomic persistence, API routes own transport only, and the browser owns projection/interaction.

## Delivery Sequence

1. Freeze the spec, north star, parity register, provisional decision, contracts, tasks, and analysis; obtain exact human planning and implementation approval.
2. Checkpoint C: implement pure draft model/validation, representative fixture, projection adapter, and read-only rendered composer shell.
3. Checkpoint D: implement bounded create/select/move/edit/connect/delete operations, diagnostics, and recovery.
4. Checkpoint E: implement sidecar persistence, API, save/close/reopen, revision conflict handling, and parity proof.
5. Add keyboard, narrow inspection, feature removal, EPP-F02 non-interference, accessibility, packaging, and dashboard/walkthrough evidence.
6. Freeze one exact Windows candidate, verify it independently on GB10, run independent reviews, follow the dev push runbook, push the feature branch, and prepare a PR. Do not merge or release.

## Complexity Tracking

No constitutional violation is accepted. The feature-owned sidecar is deliberate rollback isolation: adding a migration to the main ledger would make the pre-feature binary reject a newer schema, while browser-only storage would violate the local SQLite state rule and weaken API/system acceptance.
