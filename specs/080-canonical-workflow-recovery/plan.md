# Implementation Plan: Canonical Workflow Recovery

**Branch**: `codex/080-canonical-workflow-recovery` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/080-canonical-workflow-recovery/spec.md`

## Summary

Recover Wright around one versioned canonical workflow IR that is authoritative for diagram, engineer-facing source, forms, and reviewed AI proposals while keeping layout and immutable run records separate. Preserve the model/validation/revision/CAS/API/browser/renderer seams completed at Checkpoint D, freeze its custom shell as technical evidence, and finish a high-fidelity React Flow editor entered only from an active engineering workspace. Choosing **Workflows** is explicit workspace-scoped creation intent: Wright idempotently bootstraps one default visible `workflows/<safe-slug>.workflow.wflow` when absent and opens it immediately, while re-entry returns existing source unchanged. That file uses contextual engineering-script vocabulary; the host retains canonical IDs, revisions, digests, typed commands, atomic replace, conflict detection, tracing, and evidence as rigorous internal machinery. The nine-step acceptance workflow makes reference images, design intent as text/common document, and approved company context explicit before CAD and downstream tolerance work, omits low-value groups and search, fits a fixed-height desktop workbench, and treats the graph as a compact overview whose complete typed details remain available through focus, selection, disclosure, and the inspector. T051 records the requesting user's approval of the canvas-first direction; their subsequent hands-on corrections are the authority for T061–T080. The exact correction subject is commit `38b409bf149a1241cc87cdedd48f83fed16b5050`, tree `452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6`, with a validated 24/24 workspace walkthrough. T056's representative-participant and real assistive-technology gates and T058's independent-oracle qualification remain open. Push, merge, publication, release, customer action, and material product-direction changes remain prohibited.

## Technical Context

**Language/Version**: Python 3.11–3.14 for evidence generation and retained domain foundations; TypeScript 6 and React 19 for the conformance slice and interactive concept

**Primary Dependencies**: Existing FastAPI, Pydantic 2, SQLite, PyYAML 6, React, Zod, Vitest, and Playwright; provisional `@xyflow/react` 12.11.3 remains behind the renderer adapter

**Storage**: Preserve existing draft, stable definition/layout/execution sidecars, and legacy run storage. The workspace-scoped authoring correction adds exactly one visible UTF-8 `.workflow.wflow` file under the active workspace plus a hidden committed head and hash-chained revision journal. A plain read remains side-effect free. After a 404, the Workflows entry boundary calls exclusive create with the validated default. If another first entry wins, create fails without overwrite and one scoped refetch opens the winning existing document; any other unresolved failure stops with Retry. This composition is idempotent without weakening the storage create contract. The workspace service path-confines and size-bounds the file, holds an OS file lock across each local read/CAS/write transaction, and uses compare-and-set plus atomic replacement for later saves. It never creates a workspace, and merely opening an ordinary workspace never creates a workflow. Layout, proposal, run, and simulated artifact state remain outside that source file.

**Testing**: pytest for syntax evidence, retained Python invariants, canonical security/RBAC/resource boundaries, and zero-network restart; Vitest for conformance, commands, projection, renderer, and component behavior; Playwright for human-repeatable direct manipulation, text correspondence, AI review, run visualization, screenshots, trace, diagnostics, and automated accessibility

**Target Platform**: Wright web UI on Windows 11 for authoritative interaction evidence; current supported desktop browsers; optional GB10 Linux/aarch64 for bounded read-only and parallel verification

**Project Type**: Existing modular-monorepo local web application with Python domain/services and React frontend

**Performance Goals**: A valid graphical or source edit updates its paired projection within 1 second; a dragged block follows the pointer before mouse-up while semantic and layout identities remain unchanged until the atomic layout command is accepted; invalid edits preserve the prior graph immediately; active run overlays update within 1 second; the exact 1070×791 workbench has no document overflow; the nine-step workflow omits search and persistent edge/port metadata while a 26-step fixture proves bounded search behavior

**Constraints**: Offline-first; one integration writer; no Rivet or orchestration resurrection; no renderer/source/run authority; no AI direct mutation/execution/approval; no benchmark qualification; locally safe post-approval work only; local build/rehearsal is not production release authority; no push, merge, publication, release, customer action, destructive external change, or material product-direction change under the current authorization

**Benchmark preflight**: T058 may audit schemas, decisions, dependencies, and
the honest denominator, but cannot generate or count a case while the named
human oracle/holdout/population/license decisions and B01 dependencies remain
unresolved. The deterministic preflight therefore remains `BLOCKED` at `0/100`
with zero cases and zero state violations.

**Scale/Scope**: One real workspace, one workspace-scoped idempotently bootstrapped visible workflow source file, one coherent mounting-bracket workflow with nine visible steps, three explicit source inputs and provenance, one reviewed design specification, typed ports, a gate/feedback path, exact binding disclosure, contextual downstream additions, reviewed AI proposal, simulated immutable run, and recognizable output; three syntax treatments; three block/port treatments; one 26-step search threshold fixture; one requesting mechanical engineer's hands-on correction pass plus a still-open representative-participant protocol

## Constitution Check

*GATE: Passed before research and rechecked after contracts.*

- **Modular monorepo and thin routes — PASS**: workspace workflow-source semantics live in `workspace_service`; FastAPI validates typed requests and maps service errors without becoming the storage or canonical-semantic authority.
- **Offline-first — PASS**: fixtures, parsing, validation, graph editing, proposal review, and simulated run evidence operate locally without cloud or external MCP dependencies. T057 additionally hard-fails network resolution/connection while promoting and reopening stable definition, layout, run, step, activity, and artifact records.
- **Distribution and rollback — PASS for local T059**: exact wheel/sdist candidates clean-install, Windows native install/update/rollback/uninstall/reinstall/purge passes through Hermes 0.19.0, and the exact local Docker candidate passes the authoritative smoke. No tag, registry, public package, release, or main database mutation occurred; cross-platform/public gates remain T060.
- **Embedded state — PASS**: retained stores remain untouched. Stable definitions, layouts, and canonical execution records keep separate authorities. The engineer-owned source is a local workspace file with hidden host metadata; no server database or cloud dependency is added. The simulated runner remains presentation evidence and gains no external execution authority.
- **Security, RBAC, and authority — PASS**: no new external write or runtime authority. T057 proves exact workspace/session lookup, exact one-shot mutating capability grants, administrator-only attachment authority, fail-closed secret rejection before canonical hashing/immutable persistence, and bounded command/envelope resources. AI proposals cannot mutate, run, or approve. Artifact actions remain local concept fixtures and are labeled.
- **Engineering tooling protocol — PASS**: exact tool/MCP bindings are modeled and inspectable, but no GUI-only agent execution or tool invocation occurs.
- **UI atomic design — PASS**: the recovery stylesheet routes semantic color,
  contrast, focus, surface, and state styling through shared Wright tokens and
  contains no malformed token expressions. One-off geometry dimensions are centralized as recovery tokens;
  canvas dimensions and responsive breakpoints remain documented structural
  exceptions. React Flow stays behind the existing adapter rather than becoming
  semantic authority.
- **Three-tier testing — PASS for this bounded concept**: service/API tests cover path confinement, byte bounds, atomic compare-and-set writes, conflicts, side-effect-free reads, create-if-absent bootstrap, and existing-source preservation; component tests cover loading, automatic workspace-scoped bootstrap/open, saved/unsaved/save-failed/conflict states, source containment, renderer interaction, run overlays, and unknown versions; workspace-entered mocked Playwright journeys cover the complete product path.
  T057 adds a local system E2E for stable definition/layout/run persistence and
  restart with network APIs hard-failed. A live production executor remains
  deferred because this slice commits no external execution authority.
- **Stable test identities — PASS**: every authored interactive concept control
  and every explicit renderer navigation control has a stable `data-testid`;
  the host-component regression enumerates rendered interactive elements and
  fails if an ID is missing.
- **Observability and transparency — PASS**: the walkthrough captures trace, console/page/network failures, raw/annotated screenshots, proposal assumptions/diff, run activity, artifact lineage, and known limitations.
- **Phase isolation and manual gate — PASS**: this plan is the recovery implementation authority supplied by the user. The initial `f9237763` subject records approval of the canvas-first direction. The requesting mechanical engineer then directed workspace ownership, a compact single-page workbench, optional grouping/search, and a friendly but code-literate engineering source vocabulary while explicitly preserving strong internal software-development contracts. The exact `38b409bf` correction stays within that approved direction and passes a validated 24-step walkthrough, so the conditional T051 authorization is bound without claiming the reviewer executed it. One requesting engineer does not close T056's representative-participant or real screen-reader gates.
- **Branch discipline — PASS**: all writes occur on `codex/080-canonical-workflow-recovery`, based exactly on frozen `b4a7e996`; no direct `dev` or `main` action is planned.
- **Post-design recheck — PASS**: the contracts keep semantic definition, layout, command candidates, proposals, and immutable run records separate; no constitutional exception is introduced.

## Evidence Baselines and Dispositions

1. **Checkpoint D foundation**: freeze `b4a7e996` (tree `accd9e1f...`) after T027. Its 11-step walkthrough/24 screenshots prove validated atomic draft edits, but not product usability. Preserve the captured-subject relation to `e0354dd7`, empty browser diagnostics, and retained API debug-table caveat.
2. **Frozen prototype direction**: inspect `e7bb75c1` (tree `88fe1511...`) only as evidence. Its React Flow bakeoff scored 91/100 and its visual work demonstrates ports, connections, palette, and overlays, but its renderer disabled dragging/connecting, the five-person study never ran, and its implementation is not merged or promoted.
3. **Production foundations retained**: canonical draft and separate digests; complete validation; immutable revisions and head CAS; service/API/browser closed decoding; renderer-neutral projection and intent seam; strict process-definition parser/canonical vectors.
4. **Current shell disposition**: retain backend/domain seams, revise the interaction/product grammar, and freeze custom SVG/HTML canvas polish. T028–T038 remain paused.
5. **Recovery code disposition**: ADR 0002 promotes renderer-neutral definition, validation, atomic-command, semantic-diff, projection, migration, and storage concepts. React Flow, simulated AI proposal, simulated run, and static artifact actions remain bounded concept code; the workspace-source API is a narrow local persistence boundary and not a second semantic model.
6. **Mechanical-engineer correction**: preserve the seven-issue failed-first checkpoint; replace the fictional PDF brief with three provenance-labeled engineering sources feeding one reviewed design specification; make tolerance inspection downstream; project live drag before atomic release; remove decorative phase backdrops; clarify the minimap; keep internal IDs behind Technical details; remove the global Recovery entry; scope bootstrap/open/save to a real workspace; treat choosing Workflows as explicit intent to create one usable default if absent and open it immediately; preserve existing source on re-entry; use one visible workflow file; omit low-value search and grouping; fit the editor without document scroll; and use engineering-script vocabulary while retaining exact internal contracts. Commit `38b409bf` and continuation 14 are the fresh exact correction subject and passing evidence.

## Architecture and Boundaries

```text
              active workspace / one visible .workflow.wflow
                                  |
                        parse + lower + validate
                                  |
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

Host-only storage revision, digest, path confinement, lock, and atomic replace
wrap the visible source file. They are not fields in the engineer-authored source.
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

### Engineer-facing source and internal IR

- The visible `.workflow.wflow` file is a contextual engineering script with `workflow`, `input`, `task`, and optional `group` constructs. Labels describe prompts, files, design documents, engineering work, tools, and outputs rather than UI widgets or opaque storage types.
- Groups are optional organization, not mandatory phases or execution restrictions. The nine-step fixture has no author-authored group declaration.
- Authors never type definition/storage revisions, parents, semantic digests, canonical `block.*`/`port.*`/`artifact.*` identities, absolute paths, locks, or compare-and-set tokens. Technical details may reveal relevant non-secret values read-only.
- The parser resolves contextual names against the exact accepted base, lowers supported changes to the closed atomic command set, validates the complete canonical candidate, and returns stable source spans or structured diagnostics. Structural additions that cannot be resolved safely fail closed.
- Strict canonical JSON and the full internal IR projection remain developer/evidence interchange forms. They do not mirror the current UI vocabulary and are not a second visible workflow file.
- JSON, YAML, the full IR language, and the contextual authoring form retain identical semantic fixtures and edit evidence; the public source treatment is accepted for this slice without claiming that every future language feature is permanent.

### Workspace source storage

- The canonical editor is reachable only through a real active workspace and the explicit workspace-scoped **Workflows** action. Ordinary workspace entry retains the existing Rivet workflow surface while the canonical editor remains feature-gated; there is no global workflow creation/view destination.
- `GET` reads one exact safe workspace-relative `.workflow.wflow` path and returns 404 without creation. On that 404, Workflows entry calls exclusive `POST`: it atomically creates the default only if absent and fails without overwrite if the file now exists. One scoped `GET` then recovers a concurrent-create race; unresolved failure stops with Retry. `PUT` saves later changes against exact storage revision and digest. Concurrent first entry may create only one file; no bootstrap request may overwrite an existing source.
- The workspace service enforces safe slug/extension, path and symlink/reparse confinement, a 1 MiB UTF-8 ceiling, per-path in-process plus OS file locking across local API processes, a committed head and hash-chained hidden journal, and atomic visible-file replacement.
- A compare-and-set conflict returns the current stored identity while preserving both stored bytes and the engineer's local unsaved source. Layout, selection, proposals, runs, and simulated files never enter the source save.

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
├── recovery-dsl.ts                       # developer-facing full internal IR projection
├── recovery-authoring.ts                 # contextual engineer source parser/formatter/lowering
├── command-system.ts / command-system.spec.ts # shared atomic graph/form/text/AI commands
├── ReactFlowRecoveryCanvas.tsx / ReactFlowRecoveryCanvas.spec.tsx # disposable renderer and local state tests
├── WorkflowRecoveryConcept.tsx / WorkflowRecoveryConcept.spec.tsx # host authority, port lab, proposal/run and component-state tests
└── workflow-recovery.css

apps/web/src/components/pages/
└── WorkflowRecoveryPage.tsx               # workspace-owned load/ensure/open/save boundary

apps/web/src/services/
└── workspace-service.ts                   # typed workflow-source read/bootstrap/save client

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

packages/workspace_service/src/workspace_service/
└── workflow_sources.py                    # path-confined atomic workspace source store

packages/workspace_service/tests/
└── test_workflow_sources.py

apps/api/src/api/
├── routers/workspace.py                   # thin workflow-source endpoints
└── schemas/workspace.py                   # typed source requests/responses

apps/api/tests/
└── test_workflow_sources_api.py

tests/ui-integration/
└── workflow-recovery.spec.ts

artifacts/ui-walkthrough/workflow-recovery/<historical-timestamp>/
artifacts/ui-walkthrough/workflow-recovery-usability/<correction-timestamp>/
```

**Structure Decision**: Keep the recovery interaction code in its explicitly named concept module. After approval, promote only its renderer-neutral semantic concepts into `core` and an independent `data_vault` sidecar under ADR 0002. Evidence generators live under `scripts/recovery`; product evidence and decisions live under spec 080; the walkthrough remains a timestamped immutable artifact.

## Delivery Sequence

1. Freeze Checkpoint D in Git and the program control plane; mark T028–T038 paused and feature 080 as the replacement recovery scope.
2. Build a source-complete capability inventory and machine-check every required identifier against its canonical capability row.
3. Freeze canonical IR vNext, layout, command/proposal, conformance, renderer, and immutable-run contracts in the ADR and design artifacts.
4. Generate identical JSON/YAML/DSL workflows, execute the same edit/error corpus, record measured and qualitative evidence, and select only a provisional concept syntax.
5. Implement and test the conformance kernel plus its required round-trip, containment, digest, revision, proposal, and run-separation invariants.
6. Build and compare three block/port treatments; select the treatment with distinct connection and artifact-inspection targets.
7. Build the full React Flow concept over the existing adapter, including three explicit engineering source inputs, one reviewed design specification, contextual downstream editing, Diagram/Source/Side by side, AI preview/accept/reject, run overlays, diagnosis/recovery, and output actions.
8. Run the complete Playwright walkthrough with raw/annotated screenshots, trace, diagnostics, and clickable report. Stop immediately on unresolved product ambiguity under the walkthrough rule.
9. Update dashboard and program/spec/roadmap/parity/tasks artifacts, run Spec Kit consistency analysis, bind the exact subject to product-owner direction approval, and continue only the authorized dependency-ordered locally safe work.
10. Apply the requesting mechanical engineer's hands-on correction feedback, rerun focused and broad validation, capture a fresh exact-subject walkthrough, and refresh the approval/dashboard evidence while keeping T056 open.
11. Remove global recovery access, integrate the canonical editor into an active workspace without displacing ordinary Rivet workflows, persist one explicit engineer-facing source file through a typed atomic CAS service, prove conflict containment and fixed-height behavior, and repeat exact-subject evidence.

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
- **Renderer**: visible left/right handles, pointer-following drag before atomic release, connect, disconnect, selection, edge labels that do not obstruct blocks, a visible minimap frame, separate output controls, non-color active overlays, and a keyboard path; decorative phase backdrops are omitted while phase remains canonical metadata. The frozen prototype's single 100-node observation remains explicitly non-qualifying and production-scale evidence stays deferred.
- **Product journey**: enter **Workflows** from a real workspace; automatically create and immediately open one named default `.workflow.wflow` file if missing, or open the existing file unchanged on re-entry; show reference images, ordinary text/common-document design intent, and approved company context feeding one reviewed design specification; keep tolerance inspection downstream; demonstrate valid/invalid source edits, explicit save/reopen, idempotent re-entry, conflict containment, proposal review, needs-input recovery, and recognizable simulated output.
- **Responsiveness**: local command application plus graph→text,
  text→graph, and run-overlay browser transitions each remain below the explicit
  one-second recovery bound; exact 1070×791 evidence has no document scrolling,
  search is absent for the nine-step graph, and the 26-step fixture retains search.
- **Walkthrough**: progress/status/report remain current after every action; raw and annotated images are separate; browser diagnostics are captured; validator has zero missing evidence fields.
- **Program**: dashboard names the recovery goal as in progress while EPP-F02C remains proposed and unregistered, keeps the governed F02B ledger separate from a recovery task projection, orders checkpoint history newest-first, and leaves customer readiness incomplete.
- **Security/offline**: exact capability and workspace/session scopes fail closed; secret-shaped keys, bearer/assignment material, credential-bearing URLs, unsafe paths, symlink/reparse escapes, wrong extensions, oversized UTF-8 sources, and stale write bases fail before replacement; definition/source/layout/run authorities remain isolated and reopen with zero network calls.
- **Benchmark preflight**: schemas compile and denominator/case/decision/dependency drift fails closed. Current output is intentionally blocked at `0/100`; no self-authored oracle, visible fake holdout, or unapproved case can create qualification evidence.
- **Release-candidate hardening**: exact subject `fe6140d8` produces deterministic wheel/sdist hashes, a source-isolated Windows lifecycle pass, local OCI digest, full Docker smoke, and dry-run rehearsal with zero external mutations. Linux/macOS, scan/SBOM/provenance, public registries, digest promotion, docs, tag, and GitHub Release remain unrun T060 work.

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
| Contextual engineer-facing workflow source | A compact source-mapped engineering-script treatment is needed for lossless bidirectional editing without exposing host-managed metadata or coupling the language to current UI widgets. | Exposing strict JSON/YAML or the full internal IR would make engineers author revisions, hashes, and opaque identities; hiding all source would remove the requested code-literate workflow path. |
