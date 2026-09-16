# Implementation Plan: Engineering Output Content Validation

**Branch**: `codex/082-output-content-validation` | **Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)
**Base**: fetched `origin/dev` at `86ee835974970cd05913b58e306e537f6dfaf181` (PR #129).
**Status**: implementation package prepared; G0 not ready; no validation implementation started.
**Input**: approved earlier 30-pack analysis and the request to prepare this work on a new branch.

## Summary

Build independent post-run validation using shared artifact readers, versioned requirements and profiles, immutable evidence, and generated traceability. Validate real retained output content across ten families; distinguish execution completion, content verification, design compliance and physical validation.

This feature adopts the earlier [detailed plan](../081-engineering-workflow-templates/content-validation/plan.md), [research](../081-engineering-workflow-templates/content-validation/research.md) and [30 acceptance seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md). They are already present in the merged base. This package supplies the separate feature selector, specification, executable task ordering and current handoff. Do not copy or fork the old normative details into a competing source.

**Precedence:** current user authority and constitution; this feature's explicit clarifications; adopted detailed design; historical campaign narratives. The old instructions to preserve the 081 selector and avoid branch creation described the September 13 planning session, not this newly authorized worktree. All technical G0, reader, outcome and evidence rules remain in force.

## Technical Context

**Language/Version**: Python >=3.11 per current metadata; verify supported release lanes at T002. Existing TypeScript/React UI only for evidence integration.
**Primary Dependencies**: existing core contracts, EngineeringAssertionRegistry, EngineeringArtifactNormalizerRegistry, data-vault state helpers, workspace/vault/run services, GatewayService lifecycle, structured logging and OpenTelemetry. Qualify optional CAD/field readers per capability; no new mandatory ALM service.
**Storage**: data-vault-owned additive SQLite WAL ledger at a separate validation root; artifacts remain in the file vault; bounded materialized summaries.
**Testing**: pytest contracts and negative controls, qualified native reader lanes, component tests, mocked Playwright journeys and served workspace E2E.
**Target Platform**: existing supported native and Docker paths; explicitly qualified hosts for native readers. No engineering-server-specific additions to the base image.
**Project Type**: existing modular monorepo service, thin CLI, additive workspace evidence view.
**Performance Goals**: profile/status/report operations never synchronously load solver fields into UI requests. Every reader has tested byte/entity, wall-time, memory and concurrency bounds recorded at T005/T072. Numeric values depend on the qualified reader and frozen formats, not an invented universal timeout.
**Constraints**: offline replay; original sources opened read-only; explicit source-root authority; no generation dispatch; no profile executable code; no arbitrary approval actor; no original artifact repair in place.
**Scale/Scope**: 30 profiles, ten families, all required variants and refinements; 74 implementation checkpoints.

## Constitution Check

Pre-design and post-contract review against v3.1.1: aligned by design. Implementation gates remain unexecuted.

| Principle | Design and verification |
|---|---|
| 1 Architecture/offline | Pure contracts in core; storage in data_vault; readers/evaluation in workspace_service; thin FastAPI routes. Offline test lane at T072. |
| 2 Distribution/runtime | Reuse shared native runtime and Docker; pin optional reader hosts and tool identities; no agent-manager hardcoding or special base-image additions. T002/T005/T072. |
| 3 Embedded data/vault | Separate SQLite WAL ledger and confined file artifacts. No server database; existing in-process semantic storage unchanged. T007/T071. |
| 4 Identity/security | Existing opaque local credential/session, origin and RBAC; explicit authorized source roots; authenticated subject-bound review. Existing unauthenticated review label is insufficient. T008/T010/T067/T070. |
| 5 Engineering tools | Code-driven reader operations; existing BaseTool contracts for any exposed engineering tool; sourced external information uses cached offline evidence. T008/T072. |
| 6 UI/testing | Existing tokens, primitives and test IDs; component/mocked/served-workspace checks preserving authoring. T066–T068. |
| 7 Tracing | Trace IDs and structured logging through readers, evaluator, DB, reports and review; local existing OpenTelemetry/Jaeger boundary. T007–T011/T073. |
| 8 Phases/branches/review | New feature worktree; this package ends at human review. Pasting the saved goal explicitly approves the package, but does not waive G0 or later constitution milestones. |
| Governance | No amendment; exact dev push/merge and production runbooks apply only when those actions are authorized. |

## Activation and source isolation

The [dated preliminary check](evidence/readiness-2026-09-16.json) reports 24 current completions and six missing cases. It is an early prerequisite failure, **not** a complete audit or a frozen cohort. T001 is still unchecked.

T001 must perform all six G0 conditions in the [adopted plan](../081-engineering-workflow-templates/content-validation/plan.md#g0-mandatory-start-gate): 30 canonical manifest IDs and retained inputs; selected current definition/binding full-run and step evidence; every required same-attempt nonempty artifact rehashed; stable outputs and reconciled native leases/unknown mutations; reconciled 30/30/30/0 generation conclusion; complete source/run/definition/binding/artifact/checkout identities. Content correctness is not part of G0.

Before the audit CLI exists, use bounded direct JSON/file inspection and read-only SQLite access through `connect_state_db(read_only=True, ensure_parent=False)` or equivalent snapshot-safe access. Do not run the current generation `status` CLI: it constructs Campaign and exports state. Do not copy an open SQLite main file while ignoring its WAL.

Current local inputs and campaign artifacts are in `D:/repos/wright`; this implementation worktree is `D:/repos/wright/.local-run/output-content-validation`. These are different source and code roots. Resolve the actual runtime/receipt/artifact roots from authorized configuration. Freeze a manifest of permitted read-only roots and exact content; source outputs are untracked and are not supplied by Git. Do not point a writable application data root at another task's database.

If G0 is not ready, write precise missing evidence and leave implementation deferred; no campaign recovery, repeated polling or partial activation. If it passes, freeze a cohort and continue T002. Later changed cases receive new subject identities; unaffected cases retain evidence.

## Architecture and changes from the earlier plan

The adopted pipeline remains:
requirements + frozen cohort → independent readers → measurements → assertions → immutable attempts/assessments → RTM and UI.

The review added these concrete implementation obligations:

1. Adapt legacy states explicitly. `workflow_engineering_assertions.evaluate_assertion` catches predicate exceptions as failure; the validation adapter must preserve framework error separately from measured design failure.
2. Existing artifact review reports `local_workspace_user_not_authenticated`. Reuse useful subject checks, but derive a permitted reviewer identity and type from the actual authority context. Never offer a caller-controlled “human” bypass.
3. Qualify circular geometry measurement against the [jig center guidance](../081-engineering-workflow-templates/dataset-campaign/jig-circle-center-guidance.md). A point on a circular edge is not its center; original datum and tolerances remain controlling.
4. Derive exact scenario IDs from all 30 `scenario.json` files; narrative `sheet-metal-part` aliases are not canonical IDs.
5. Keep latest authorized Modelica derivative/thermostat semantics, Pi image/manufacturer source evidence, and narrowly scoped sheet-metal amendments. Re-extract requirements at activation, including subsequent legitimate source changes.
6. All T016–T065 families have five explicit checkpoints: source/profile, reader/reference, assertions, qualified fixtures, retained evaluation. No family is done after only a profile or mock.

## Project Structure

### Documentation

`specs/082-output-content-validation/` contains spec.md, plan.md, research.md, data-model.md, contracts/validation-contract.md, acceptance-cases.md, quickstart.md, implementation-goal.md, tasks.md, progress.md, checklists/requirements.md and dated readiness evidence. The adopted 081 bundle remains the detailed design reference.

### Source ownership

| Location | Responsibility |
|---|---|
| `packages/core/src/core/engineering_output_validation.py` | Versioned pure schemas, statuses and result identity |
| `packages/data_vault/src/data_vault/engineering_validation_repository.py` | Migrations, ledger, immutable reviews and assessment sequence |
| `packages/workspace_service/src/workspace_service/engineering_output_validation/` | cohort audit, profiles, readers, evaluator, review service, reports/projection |
| `scripts/run_engineering_content_validation.py` | Thin CLI over services |
| `tests/datasets/engineering-workflow-validation/` | requirements, profiles, fixtures, catalog; outside generation inputs |
| `scripts/engineering-dataset-dashboard.html` | Separate validation projection |
| `apps/api/src/api/routers/workspace.py` | Thin existing-auth evidence transport only |
| `apps/web/src/prototypes/workflow-recovery/EngineeringValidationView.tsx` | New read-only evidence component integrated through existing run/history surfaces |
| `apps/web/src/services/workspace-service.ts` | Typed UI service calls |
| `tests/external/engineering_output_validation/` | Qualified native integrations |
| `tests/ui-integration/engineering-output-validation.spec.ts` | Mocked workspace journey |
| `tests/e2e/test_engineering_output_validation.py` | Real served-system evidence flow |
| `artifacts/engineering-workflow-validation/` | Generated validation.sqlite3, report and evidence root, unique to this worktree |

Other proposed filenames are spelled out in tasks.md. Resolve transport/schema ownership during T002 without moving business logic into routes. Shared geometry and field readers must be reused across families.

## Delivery and dependencies

| Stage | Tasks | Required exit evidence |
|---|---|---|
| Setup | T001–T002 | Full G0 pass; exact source/code/runtime roots and dependencies |
| Foundations | T003–T008 | 30 source inventories and frozen methods; schema, ledger and confined reader contracts |
| US1 / first useful slice | T009–T015 | Two independently measured, fixture-qualified retained pilots with traceability and replay |
| US2 / all families | T016–T065 | Ten A–E packages; no in-scope reader omitted; all 30 profiles evaluated |
| US3 / evidence UI | T066–T068 | Current/historical projection and served-workspace access preserving authoring |
| US4 / full corpus/review | T069–T070 | Frozen all-case report and authentic independent review |
| Cross-cutting closure | T071–T074 | Reliability/platform/security/gate evidence and final handoff |

US3 may begin after US1, using materialized records. US4 needs all family evaluations; final closure needs UI and review. Each family proceeds A→B→C→D→E, one case proved before siblings. Shared core/schema changes have one owner; concurrent readers need independent native leases. Parallel task markers describe potential work partitioning, not authority to spawn agents.

## Completion and review boundaries

Preserve all three completion definitions from the adopted plan:
- Framework complete: all in-scope readers, 30 profiles, qualified checks, ledger/report/UI implementation and required tests exist. Missing readers are unfinished work.
- Corpus evaluation complete: no missing mandatory measurement/review or infrastructure error for the frozen cohort; conclusive design failures are allowed.
- All designs compliant: every applicable mandatory design requirement passes. This is a separate outcome, never a forced target.

The saved goal approves this package only when the user submits it. At major lifecycle/milestone review gates, present concrete evidence and pause unless the user explicitly supplies broader authority. Report pending judgments precisely without inventing human acceptance. Do not start a persistent goal merely by saving the document.

## Complexity Tracking

No constitutional exception. Reuse existing assertion predicates and lifecycle boundaries while adding independent measurement and immutable evidence semantics. Avoid an additional executor, disconnected manually edited RTM, broad tool installation or duplicated family engines.
