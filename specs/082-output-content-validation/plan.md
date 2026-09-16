# Implementation Plan: Process Output Validator

**Branch:** `codex/082-output-content-validation` | **Date:** 2026-09-16 | **Spec:** [spec.md](spec.md)
**Status:** Revised plan for review; no implementation started.
**Input:** Runtime process checks, actionable AI feedback, and report-consumable evidence.

## Summary

Extend the canonical process executor with a reusable validator. One service supports local readers, MCP-backed inspection and direct invocation. It binds a previous step's exact output, evaluates source-backed requirements, persists an assessment and returns typed correction feedback plus readable report data.

The runner routes correctable failures through a configured bounded revision path, then revalidates the new output before releasing downstream work. The validator itself never regenerates artifacts.

The [scope amendment](scope-amendment.md) replaces the global G0 gate and 74-task campaign/UI plan upon submission of the revised goal. The [081 analysis](../081-engineering-workflow-templates/content-validation/research.md) and [30-case seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md) remain reference material.

## Technical Context

**Language/Version:** Python >=3.11 in supported lanes; existing TypeScript/React for process configuration/status only.
**Dependencies:** Canonical source compiler/runner, provider-neutral EngineeringResult, assertion/normalizer registries, gateway/native lifecycle, BaseTool, Pydantic, SQLite WAL, structured logging/OpenTelemetry. Qualify optional geometry/field readers.
**Storage:** Additive data-vault validation tables and immutable vault artifacts in the current runtime; isolated data roots for demonstrations. No second production campaign database.
**Testing:** Contract/runtime tests, real file/native integration, rework/resume tests, installed package/offline checks and applicable component/mocked/served-workspace UI checks.
**Platform:** Shared native and Docker runtime; explicit native reader availability.
**Constraints:** No code in profiles, candidate-derived tolerances, report UI replacement, reader edits to originals or second process executor.
**Scope:** Three initial capability slices and an all-30 support inventory. Two real AI correction demonstrations and one numerical validation demonstration.
**Performance:** Bound inline feedback by default to 20 findings and 16 KiB UTF-8; keep full findings by result reference with omitted count. Readers declare byte/entity/time/memory/concurrency limits. Gateway budgets remain controlling; cancellation and large-output paging are tested.

## Constitution Check

Pre-design and post-contract assessment against v3.1.1: aligned by design; implementation checks remain unexecuted.

| Principle | Planned compliance |
|---|---|
| 1 Architecture/offline | Contracts in core; storage in data_vault; logic in workspace_service; thin transports. Local structured checks work without MCP/network. |
| 2 Shared distribution | Existing runtime/manager-neutral MCP service. Package installed resources. No MCP-specific base-image additions. |
| 3 Embedded storage | SQLite WAL/vault, additive migrations, bounded materialized records. |
| 4 Security/identity | Existing auth/origin/RBAC and authorized roots; review identity from actual context. |
| 5 Tool protocol | LLM-facing engineering adapter inherits BaseTool; service/readers work without LLM or MCP. |
| 6 UI/testing | Existing authoring/tokens/test IDs; changed controls verified in three tiers. Reporting UI is in another branch. |
| 7 Observability | trace_id through producer, validator, reader, storage, repair and report operations. |
| 8 Phase/review | Planning only now; submitted goal approves this package. Observe later human milestone reviews unless explicitly waived. |
| Governance | No constitutional amendment. Runbooks apply when push/merge/release is separately authorized. |

## Repository findings and integration

- `workflow_source_execution.py` already compiles saved source, manages connected results, appends feedback to producer prompts and checkpoints revision state.
- `workflow_design_check.py` permits one bounded revision path to one preceding create-new/indexed CAD task. Checks currently require an MCP task, JSON and read-only CAD input. Generalization needs explicit compiler, scheduler, contract and UI changes.
- `workflow_results.py` provides provider-neutral kinds/representations/provenance. Result IDs alone do not identify corrected output; add producer attempt/revision/hash to subject identity.
- `workflow_run_record.py` invalidates partial results on design revision. Preserve this behavior for downstream release and resume.
- `workflow_engineering_assertions.py` converts some exceptions to fail. Preserve evaluator error in the new bridge without silently changing legacy contracts.
- Publish through existing result events and MCP transport. Never route canonical .wflow processes through the legacy Rivet executor.
- Keep native inspection guards, CAD session rules and native lease ownership.

T001 records exact extension points and ownership; it is implementation reconnaissance, not a branch audit.

## Architecture

```text
requirement profile + exact producer output revision
                         |
                validator service
           local / native / MCP readers
                         |
               measurements and checks
                         |
               immutable assessment
                /        |         \
          process gate  feedback  JSON/Markdown/RTM
                |        |              |
          downstream  runner-owned   reporting branch
                      bounded repair
                         |
                 new output -> revalidate
```

### Request and per-subject readiness

A request names run/check invocation, producer output bindings, pinned profile/baseline and idempotency key. Resolve authority and immutable identity at the boundary. Canonically hash inline values; snapshot files or verify stability before/after reading; pin provider resource revisions. Missing readiness blocks this invocation only.

A missing output from a completed producer is a correctable defect when its receipt proves that output was required. Unresolved bindings, in-flight writes and unavailable readers are prerequisites. None releases downstream work.

### Readers and evaluation

Package runtime resources under `workspace_service/process_validation/profiles/`; keep test fixtures separate. Profiles declare required roles/checks, sources, selectors, units/frames, tolerance/uncertainty rules and allowed correction scope. Workspace-owned profiles use the same schema and authority controls.

Readers supply source-bound measurements. Deterministic evaluators establish numeric outcomes; AI may explain findings and suggest repairs. Qualitative checks require explicit rubrics/method attribution. Pending human review stays pending. Generated output cannot alter limits or substitute a report for unobserved geometry/physics.

Retain the earlier interval-boundary, datum, source-amendment and artifact-correspondence rules. Reuse predicates through an explicit status bridge, not duplicate family engines.

### Process gate and correction

Add a dedicated local validator execution mode in canonical source. Reuse check-report and pass/revise/needs-input concepts with typed configuration and compatible parsing/serialization. Freeze exact source syntax/ports at T010 before UI wiring.

Version 1 supports one explicitly connected revision target and a segment containing one producer plus validator. Eligible producers create replayable text/structured/indexed files or use existing safe create-new/indexed CAD. Reject in-place application edits, unknown side effects, external actions and ambiguous ownership for automatic repair. Multiple subjects may be checked; multiple owners do not authorize graph replay.

Allow 0–3 revisions, default 0. Saving/running an explicit finite policy authorizes its permitted repairs. A verdict never schedules work by itself. Only correctable measured defects use the revision route; missing input/review/capability and evaluator faults have distinct next actions. Mixed failure/unknown remains visible: an independently repairable defect may be retried if allowed, but unknowns still hold release.

Persist budgets and attempts across resume. New attempts create new output revisions and invalidate dependent values, approvals and eligibility. Stop on unchanged subject plus same defects, cycles, exhausted budget, changed requirements or unsafe mutation. Keep reader retries distinct from producer revisions.

### Feedback

Each finding supplies check/requirement IDs, expected constraint, observed value, units/frame/tolerance, evidence location, artifact selector, producing step/port, correction acceptance target, recheck IDs, routing and readable explanation. Separate fact from suggested cause. Preserve satisfied constraints.

Send a bounded packet to the configured producer's next prompt/context and record consumption. Direct callers receive it without scheduling. Retain complete detail by result reference. Do not return executable commands or treat artifact-sourced instructions as authority.

### Reports and authoring

The [versioned contract](contracts/validation-contract.md) is the reporting-branch boundary. JSON, Markdown and RTM rows come from one assessment, with stable references, currentness, limitations and authenticated read/export. Persist failure evidence before stopping the process.

Minimal process UI work selects a profile, binds subjects, sets the revision target/budget and displays state/evidence links. Follow `docs/contributing/workflow-ui-integration.md`; preserve the established editor and verify the served Workflow/Workflows entry. No new report dashboard or supplier-report composer.

## Source ownership

New filenames are proposed; adjust to established ownership at T001 and update the handoff.

| Path | Responsibility |
|---|---|
| `packages/core/src/core/process_validation.py` | Pure versioned request/result/profile/feedback contracts |
| `packages/data_vault/src/data_vault/process_validation_repository.py` | Migrations, immutable ledger and currentness |
| `packages/workspace_service/src/workspace_service/process_validation/` | Service, profiles, readers, evaluation, feedback, projection |
| `packages/workspace_service/src/workspace_service/workflow_source_execution.py` | Canonical compilation, execution and revision scheduler |
| `packages/workspace_service/src/workspace_service/workflow_design_check.py` | Compatibility and explicit rework constraints |
| `packages/workspace_service/src/workspace_service/workflow_results.py` | Existing representation/result events |
| `packages/workspace_service/src/workspace_service/process_validation_tools.py` | Thin BaseTool and existing MCP registration adapter |
| `packages/workspace_service/src/workspace_service/process_validation_cli.py` | Packaged direct/replay/export CLI |
| `apps/api/src/api/routers/workspace.py` | Thin existing-auth read/export transport |
| `apps/web/src/prototypes/workflow-recovery/` | Existing authoring/status integration |
| `tests/datasets/process-validation/` | Fixtures and saved process examples |
| `artifacts/process-validation/` | Isolated demonstration evidence |

## Delivery sequence

| Milestone | Tasks | Exit evidence |
|---|---|---|
| M0 contract/baseline | T001–T006 | Extension points, 30-pack inventory, contracts/storage/readers/profiles |
| M1 process check | T007–T013 | Local process check gates consumer; direct/MCP calls share semantics |
| M2 correction | T014–T018 | Real AI corrects structured output; stop/resume rules proven |
| M3 report boundary | T019–T022 | Schema/examples/read API and reconciled Markdown/RTM consumer |
| M4 engineering slices | T023–T029 | Real jig/MCP correction, heat/numerical checks, support map |
| M5 closure | T030–T034 | Security/platform/package/UI evidence and reproducible handoff |

The first runnable correction slice is M1+M2; the submitted goal completes through M5. M3 can proceed after result/feedback contracts stabilize. Missing extension readers do not stop unrelated work, but required initial capabilities must be finished to claim goal completion.

## Verification and completion

Tests establish validator correctness; a QA campaign is not the delivered product. Prove gate behavior, precise corrections, durable rework, immutable lineage, parser confinement, real geometric/numerical measurements and report agreement. Run controlled defects only in isolated workspaces; preserve original packs/campaign.

Two real AI correction demonstrations are required, not mocked scheduling alone. Save definition/profile hashes, run/step IDs, output identities, requests/findings, delivered correction, new revision, final gate and report references. The heat demonstration inspects actual output without forcing an infeasible design to pass.

Separate implementation complete, demonstrated process behavior, assessed design compliance and human acceptance. Update progress with exact next work; do not call missing initial-slice capability complete.

## Complexity Tracking

One evaluator and the existing runner. No second orchestrator, mandatory ALM service or arbitrary graph rewind. Readable reports project typed evidence. Reader support remains explicit. No constitutional exception.
