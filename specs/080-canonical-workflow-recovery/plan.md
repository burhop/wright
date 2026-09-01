# Implementation Plan: Canonical Workflow Recovery

**Branch**: `codex/080-canonical-workflow-recovery` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/080-canonical-workflow-recovery/spec.md`

## Summary

Recover Wright around one versioned canonical workflow IR that is authoritative for diagram, text, forms, and reviewed AI proposals while keeping layout and immutable run records separate. Preserve the model/validation/revision/CAS/API/browser/renderer seams completed at Checkpoint D, freeze its current custom shell as technical evidence, and build a disposable but high-fidelity React Flow recovery concept over the existing renderer adapter. The slice includes measured JSON/YAML/DSL evidence, a tested parse/format/validate/apply/diff/project conformance kernel, a three-treatment block/port laboratory, a complete mechanical-engineering walkthrough, and revised dependency-ordered program artifacts. T051 is approved for exact subject `f9237763`; T052–T055 promote stable definition, layout, execution, reusable-component identity, collapsed-graph interaction, and bounded large-graph navigation. T057 now qualifies the canonical boundaries for exact RBAC scope, fail-closed secret handling, resource isolation, and offline restart. T056's real assistive-technology and moderated-engineer gates remain open. Dependency-ordered locally safe implementation may continue, while push, merge, publication, release, customer action, and material product-direction changes remain prohibited.

## Technical Context

**Language/Version**: Python 3.11–3.14 for evidence generation and retained domain foundations; TypeScript 6 and React 19 for the conformance slice and interactive concept

**Primary Dependencies**: Existing FastAPI, Pydantic 2, SQLite, PyYAML 6, React, Zod, Vitest, and Playwright; provisional `@xyflow/react` 12.11.3 only in the explicitly disposable recovery renderer

**Storage**: Preserve existing draft and legacy run storage. T052 adds independent stable definition storage, T053 adds independent stable layout storage, and T054 adds an independent normalized execution sidecar for canonical runs, immutable steps/activities/artifact lineage, reconnect, cancellation, cleanup, and exact historical recovery envelopes.

**Testing**: pytest for syntax evidence, retained Python invariants, canonical security/RBAC/resource boundaries, and zero-network restart; Vitest for conformance, commands, projection, renderer, and component behavior; Playwright for human-repeatable direct manipulation, text correspondence, AI review, run visualization, screenshots, trace, diagnostics, and automated accessibility

**Target Platform**: Wright web UI on Windows 11 for authoritative interaction evidence; current supported desktop browsers; optional GB10 Linux/aarch64 for bounded read-only and parallel verification

**Project Type**: Existing modular-monorepo local web application with Python domain/services and React frontend

**Performance Goals**: A valid graphical or text edit updates its paired projection within 1 second; invalid edits preserve the prior graph immediately; active run overlays update within 1 second; the final concept remains responsive for its 6-block acceptance workflow while retaining the frozen prototype's single non-qualifying 100-block observation only as provisional scale evidence

**Constraints**: Offline-first; one integration writer; no Rivet or orchestration resurrection; no renderer/source/run authority; no AI direct mutation/execution/approval; no benchmark qualification; locally safe post-approval work only; no push, merge, publication, release, customer action, destructive external change, or material product-direction change under the current authorization

**Scale/Scope**: One coherent mounting-bracket workflow with 6–8 visible blocks, typed ports, a gate/feedback path, exact binding disclosure, attached input, reviewed AI proposal, simulated immutable run, and recognizable output; three syntax treatments; three block/port treatments; one product-owner walkthrough

## Constitution Check

*GATE: Passed before research and rechecked after contracts.*

- **Modular monorepo and thin routes — PASS**: no new route business logic is required for the recovery concept; retained API/service boundaries remain unchanged. Any future persistence expansion belongs in core/data-vault/workspace-service before transport.
- **Offline-first — PASS**: fixtures, parsing, validation, graph editing, proposal review, and simulated run evidence operate locally without cloud or external MCP dependencies. T057 additionally hard-fails network resolution/connection while promoting and reopening stable definition, layout, run, step, activity, and artifact records.
- **Distribution and rollback — PASS**: no released artifact, installer, or main database version changes. The new definition sidecar is independent, its empty schema rolls back transactionally, populated history refuses destructive rollback, and exact promotion-source envelopes are retained for verified rollback.
- **Embedded state — PASS**: retained stores remain untouched. Stable definitions, layouts, and canonical execution records now have separate SQLite authorities. The recovery UI's simulated runner remains disposable presentation evidence and gains no external execution authority.
- **Security, RBAC, and authority — PASS**: no new external write or runtime authority. T057 proves exact workspace/session lookup, exact one-shot mutating capability grants, administrator-only attachment authority, fail-closed secret rejection before canonical hashing/immutable persistence, and bounded command/envelope resources. AI proposals cannot mutate, run, or approve. Artifact actions remain local concept fixtures and are labeled.
- **Engineering tooling protocol — PASS**: exact tool/MCP bindings are modeled and inspectable, but no GUI-only agent execution or tool invocation occurs.
- **UI atomic design — PASS**: the recovery stylesheet has zero raw color
  literals, 184 references to shared Wright tokens, and no malformed token
  expressions. One-off geometry dimensions are centralized as recovery tokens;
  canvas dimensions and responsive breakpoints remain documented structural
  exceptions. React Flow stays behind the existing adapter rather than becoming
  semantic authority.
- **Three-tier testing — PASS for this bounded concept**: four host-component
  tests cover default, loading, error, and invalid-source containment; three
  renderer-component tests cover default interaction, run overlays, and
  unknown-version rejection; the page-level mocked Playwright journey covers
  the complete product path. Retained backend contract tests remain available.
  T057 adds a local system E2E for stable definition/layout/run persistence and
  restart with network APIs hard-failed. A live production executor remains
  deferred because this slice commits no external execution authority.
- **Stable test identities — PASS**: every authored interactive concept control
  and every explicit renderer navigation control has a stable `data-testid`;
  the host-component regression enumerates rendered interactive elements and
  fails if an ID is missing.
- **Observability and transparency — PASS**: the walkthrough captures trace, console/page/network failures, raw/annotated screenshots, proposal assumptions/diff, run activity, artifact lineage, and known limitations.
- **Phase isolation and manual gate — PASS**: this plan is the recovery implementation authority supplied by the user. The exact `f9237763` subject passed the explicit product-review checkpoint; only dependency-ordered locally safe follow-on work is authorized.
- **Branch discipline — PASS**: all writes occur on `codex/080-canonical-workflow-recovery`, based exactly on frozen `b4a7e996`; no direct `dev` or `main` action is planned.
- **Post-design recheck — PASS**: the contracts keep semantic definition, layout, command candidates, proposals, and immutable run records separate; no constitutional exception is introduced.

## Evidence Baselines and Dispositions

1. **Checkpoint D foundation**: freeze `b4a7e996` (tree `accd9e1f...`) after T027. Its 11-step walkthrough/24 screenshots prove validated atomic draft edits, but not product usability. Preserve the captured-subject relation to `e0354dd7`, empty browser diagnostics, and retained API debug-table caveat.
2. **Frozen prototype direction**: inspect `e7bb75c1` (tree `88fe1511...`) only as evidence. Its React Flow bakeoff scored 91/100 and its visual work demonstrates ports, connections, palette, and overlays, but its renderer disabled dragging/connecting, the five-person study never ran, and its implementation is not merged or promoted.
3. **Production foundations retained**: canonical draft and separate digests; complete validation; immutable revisions and head CAS; service/API/browser closed decoding; renderer-neutral projection and intent seam; strict process-definition parser/canonical vectors.
4. **Current shell disposition**: retain backend/domain seams, revise the interaction/product grammar, and freeze custom SVG/HTML canvas polish. T028–T038 remain paused.
5. **Recovery code disposition**: ADR 0002 promotes only renderer-neutral definition, validation, atomic-command, semantic-diff, projection, migration, and storage concepts. React Flow, the DSL editor, simulated AI proposal, simulated run, and layout remain concept code.

## Architecture and Boundaries

```text
                         accepted base revision
                                  |
       +--------------------------+---------------------------+
       |                          |                           |
 graph/form gestures          parsed text               AI proposal
       |                          |                    (review only)
       +------------- canonical atomic commands --------------+
                                  |
                         validate complete candidate
                         /                         \
                   invalid                         valid
          retain last-valid definition       semantic diff/preview
                                                    |
                                           explicit accept only
                                                    |
                                      canonical workflow revision
                                      /                         \
                              layout document            immutable run record
                           (stable-ID keyed)       (revision, steps, artifacts)
                                      \                         /
                                       renderer-neutral projection
```

### Canonical definition

- `workflow-ir` vNext contains workflow/revision metadata, phases, blocks, typed ports, data/control/decision/feedback relationships, conditions, instructions, configuration, artifact contracts, exact bindings, deterministic/AI capability, and reusable components.
- Definition bytes and semantic digest exclude positions, viewport, selection, diagnostics, proposals, and run state.
- Stable semantic identities survive label, configuration, connection, and layout edits according to command semantics.

### Layout

- A separately versioned layout document is keyed by workflow identity, semantic revision compatibility, and stable block/component IDs.
- Position, size, collapsed state, group treatment, and viewport hints cannot alter the semantic digest.

### Commands and proposals

- Manual graph gestures, forms, parsed text changes, and AI suggestions normalize to one closed command set against `base_revision`.
- A complete candidate is validated before it can replace the accepted definition.
- AI adds assumptions, warnings, rationale, and provenance around the same commands; preview/reject are non-mutating and accept is explicit.

### Text

- Strict JSON remains the internal canonical interchange candidate.
- JSON, YAML, and a small workflow DSL are evaluated using identical fixtures and edits. The recovery concept may provisionally use the best-scoring form without closing the permanent syntax decision.
- Parsing returns either the complete IR plus source spans or structured diagnostics. Formatting is deterministic and its comment/formatting policy is explicit.

### Run records

- Run, step, activity, input, output, and produced-artifact records bind to an immutable workflow revision and never rewrite definition or layout.
- The recovery concept simulates these records to prove the product grammar; it does not claim executor integration.

### Renderer

- The existing `DraftCanvasAdapterProps` projection/intent seam is retained. An IR-to-draft projection adapter feeds a new React Flow renderer.
- React Flow owns viewport/gesture mechanics only. The host owns semantic IDs, commands, validation, selection, undo/redo, text correspondence, proposals, diagnostics, and run overlays.
- The recovery decision remains provisional until direct handles, drag/connect/disconnect, keyboard access, overlays, and large-graph behavior pass the recorded evidence.

## Project Structure

### Documentation (this feature)

```text
specs/080-canonical-workflow-recovery/
├── spec.md
├── plan.md
├── research.md
├── north-star.md
├── data-model.md
├── quickstart.md
├── capability-inventory.md
├── capability-source-map.csv
├── prototype-parity.md
├── tasks.md
├── checklists/
├── contracts/
│   ├── canonical-workflow-ir.schema.json
│   ├── workflow-command-batch.schema.json
│   ├── workflow-layout.schema.json
│   ├── workflow-run-record.schema.json
│   ├── command-protocol.md
│   ├── conformance-kernel.md
│   ├── renderer-adapter-vnext.md
│   └── run-records.md
├── decisions/
│   └── 0001-canonical-workflow-ir-vnext.md
├── fixtures/
│   ├── mounting-bracket.workflow.json
│   ├── mounting-bracket.workflow.yaml
│   └── mounting-bracket.workflow.wflow
└── evidence/
    ├── checkpoint-d-freeze.md
    ├── capability-coverage.md
    ├── independent-syntax-study.md
    ├── syntax-evaluation.md
    ├── block-port-lab.md
    ├── react-flow-recovery.md
    ├── prototype-side-by-side.md
    └── specification-analysis.md
```

### Source Code (repository root)

```text
packages/core/src/core/
├── workflow_drafts.py                    # retained production foundation
├── workflow_draft_validation.py          # retained production foundation
├── workflow_definitions.py               # stable v2 definition/kernel/projection and migration
├── workflow_layouts.py                   # stable v1 renderer-neutral layout and migration
└── canonical_workflow_runs.py            # stable run/step/activity/artifact contracts

packages/data_vault/src/data_vault/
├── workflow_draft_repository.py          # retained immutable revision/CAS foundation
├── workflow_definition_repository.py     # independent append-only stable-definition sidecar
├── workflow_layout_repository.py         # independent append-only layout/CAS/reopen sidecar
└── workflow_execution_repository.py      # independent lifecycle/lineage/reconnect sidecar

apps/web/src/components/workflow-composer/
├── renderer-types.ts                     # retained renderer seam
├── draft-projection.ts                   # retained projection seam
└── draft-intents.ts                      # retained atomic intent foundation

apps/web/src/prototypes/workflow-recovery/
├── model.ts / model.spec.ts               # ergonomic view plus adapter/replacement projection tests
├── canonical-wire.ts                     # exact snake_case vNext wire boundary
├── recovery-dsl.ts                       # disposable source-mapped Code projection
├── command-system.ts / command-system.spec.ts # shared atomic graph/form/text/AI commands
├── ReactFlowRecoveryCanvas.tsx / ReactFlowRecoveryCanvas.spec.tsx # disposable renderer and local state tests
├── WorkflowRecoveryConcept.tsx / WorkflowRecoveryConcept.spec.tsx # host authority, port lab, proposal/run and component-state tests
└── workflow-recovery.css

apps/web/src/components/pages/
└── WorkflowRecoveryPage.tsx

apps/web/src/config/
├── workflow-recovery.ts
└── workflow-recovery.spec.ts

apps/web/public/recovery-concept/
├── mounting-bracket.svg
├── mounting-bracket.step
└── manufacturability-report.html

scripts/recovery/
├── evaluate_workflow_syntaxes.py
├── workflow_conformance.py
└── audit_capability_coverage.py

tests/recovery/
└── test_workflow_conformance.py

tests/ui-integration/
└── workflow-recovery.spec.ts

artifacts/ui-walkthrough/workflow-recovery/<timestamp>/
```

**Structure Decision**: Keep the recovery interaction code in its explicitly named concept module. After approval, promote only its renderer-neutral semantic concepts into `core` and an independent `data_vault` sidecar under ADR 0002. Evidence generators live under `scripts/recovery`; product evidence and decisions live under spec 080; the walkthrough remains a timestamped immutable artifact.

## Delivery Sequence

1. Freeze Checkpoint D in Git and the program control plane; mark T028–T038 paused and feature 080 as the replacement recovery scope.
2. Build a source-complete capability inventory and machine-check every required identifier against its canonical capability row.
3. Freeze canonical IR vNext, layout, command/proposal, conformance, renderer, and immutable-run contracts in the ADR and design artifacts.
4. Generate identical JSON/YAML/DSL workflows, execute the same edit/error corpus, record measured and qualitative evidence, and select only a provisional concept syntax.
5. Implement and test the conformance kernel plus its required round-trip, containment, digest, revision, proposal, and run-separation invariants.
6. Build and compare three block/port treatments; select the treatment with distinct connection and artifact-inspection targets.
7. Build the full React Flow recovery concept over the existing adapter, including manual editing, attachments, Diagram/Code/Split, AI preview/accept/reject, run overlays, diagnosis/recovery, and output actions.
8. Run the complete Playwright walkthrough with raw/annotated screenshots, trace, diagnostics, and clickable report. Stop immediately on unresolved product ambiguity under the walkthrough rule.
9. Update dashboard and program/spec/roadmap/parity/tasks artifacts, run Spec Kit consistency analysis, bind the exact subject to product-owner direction approval, and continue only the authorized dependency-ordered locally safe work.

## Test and Evidence Gates

- **Conformance**: `parse(format(IR)) == IR`; text→IR→diagram and graph→IR→text→parse preserve semantics; invalid text/graph/AI never replaces last-valid state.
- **Identity**: diagnostics include stable codes/IDs/spans/explanation/correction; layout-only edits leave semantic digest unchanged; run updates leave definition bytes unchanged.
- **Commands**: manual and AI paths share a versioned base-revision envelope;
  stale and unsupported commands fail atomically; undo/redo restores through an
  isolated validated history command and returns exact semantic states.
- **Document versions**: the approved concept uses definition `2.0.0-recovery.1`
  and layout, command, and run `1.0.0-recovery.1`. The production boundary uses
  definition `2.0.0` and command `1.0.0`; recovery definition input enters only
  through the explicit digest-bound migration. Unknown inputs are preserved unchanged.
- **Component identity**: collapsed reusable components expose non-empty scoped
  internal semantic addresses that diagnostics and run lineage can retain.
- **Renderer**: visible left/right handles, drag, connect, disconnect, selection, separate artifact controls, non-color active overlays, and a keyboard path; the frozen prototype's single 100-node observation remains explicitly non-qualifying and production-scale evidence stays deferred.
- **Product journey**: one coherent no-code graphical path plus valid/invalid code edits, proposal review, needs-input recovery, and recognizable output.
- **Responsiveness**: local command application plus graph→text,
  text→graph, and run-overlay browser transitions each remain below the explicit
  one-second recovery bound.
- **Walkthrough**: progress/status/report remain current after every action; raw and annotated images are separate; browser diagnostics are captured; validator has zero missing evidence fields.
- **Program**: dashboard names the recovery goal as in progress while EPP-F02C remains proposed and unregistered, keeps the governed F02B ledger separate from a recovery task projection, orders checkpoint history newest-first, and leaves customer readiness incomplete.
- **Security/offline**: exact capability and workspace/session scopes fail closed; secret-shaped keys, bearer/assignment material, and credential-bearing URLs cannot enter canonical or immutable records; oversized batches/envelopes fail before write; definition/layout/run sidecars remain isolated and reopen with zero network calls.

## Resource Strategy

- Windows recovery worktree is the sole writer and owns UI, browser, screenshots, program artifacts, and commits.
- Read-only agents may audit independent requirement, architecture, dashboard, syntax, or test questions and return findings; they do not edit the integration tree.
- GB10 is optional for syntax/property/large-graph/parallel tests against a committed exact subject. Unavailability is recorded and never blocks local evidence.
- Focused tests run during exploration. Broader gates are limited to the selected recovery direction; dev-push/merge/release gates remain outside this approval slice.

## Complexity Tracking

No constitutional violation is accepted. Two deliberate concept-only additions are bounded:

| Addition | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Provisional React Flow dependency | Accepted bakeoff evidence is materially stronger than the current custom shell, and this slice must prove real direct manipulation/overlays through the renderer seam. | Further polishing the custom SVG/HTML canvas would harden the rejected product grammar and would not close the prototype's direct-manipulation evidence gap. |
| Purpose-built recovery DSL | A compact source-mapped text treatment is needed to demonstrate lossless bidirectional editing and compare it against JSON/YAML. | Making strict JSON or YAML permanent before the identical-task evidence would close DEC-P0-002 without the required proof. |
