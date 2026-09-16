# Implementation Plan: Engineering Workflow Templates

**Branch**: `codex/081-engineering-workflow-templates` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/081-engineering-workflow-templates/spec.md`

**September 14 efficiency review (proposed next cycle):** See
[the measured review and execution recommendation](dataset-campaign/efficiency-review-2026-09-14.md).
It records 20 historical output completions, 19 current-revision completions,
140 accepted attempts, missing usage telemetry and shared runtime/storage
priorities. This review does not start another campaign or activate deferred
content validation. The real user's TEMP/TMP and inspected running processes
were subsequently verified on D:\TEMP. The user then resolved the immediate
disk shortage (approximately 9.95 GiB free on C:); retain storage preflight and
prioritize shared protocol, context and contract reliability fixes next.

**2026-09-12 testing amendment:** The user requested thirty human input datasets,
unattended integration-test execution, manual/test-auto approval modes, output
folders and a persistent four-series dashboard. Follow
[dataset-campaign/plan.md](dataset-campaign/plan.md) and its tasks/goal for this
cycle. The explicit unattended instruction supersedes routine milestone pauses
for the bounded local campaign. File-presence testing is separate from this
parent plan's later engineering-correctness and live-device qualification gates.

**Approved focused recovery amendment (September 12, recorded September 13 UTC):**
The user approved the results review and added native application shutdown
management. Follow [dataset-campaign/focused-recovery.md](dataset-campaign/focused-recovery.md)
and its ownership/lifecycle contract: prove failed tool contracts locally, finish
one pilot per family before sibling expansion, preserve ready independent work,
and manage Solid Edge/Blender leases and cleanup. Campaign tasks DC012–DC025
implement this amendment using Sol. The 30/30/30/0 target and later public
engineering qualification remain separate. No constitution change is required.

**Recovery progress (September 13):** Raspberry Pi cases01 and02 now complete
their full AgentCAD-to-two-variant-OpenFOAM chains. Case01 attempt032 completed
all required stages and its independent audit rehashed 40/40 nonempty outputs;
case02 retains its 42/42 audit. The recovery dashboard is live at
`http://127.0.0.1:8771/?view=recovery` and reports `30 / 30 / 18 / 0`.
Content validation remains deferred. Native GUI workflows continue to require
exact owned-process cleanup at every terminal outcome. Printing attempt013
proved that model-authored source construction can cross the Blender stage, but
also showed that asking a second model turn to author routine mesh repair is
slow and brittle. The current recovery design therefore keeps image
interpretation and source geometry with the model, then uses a pinned,
same-attempt MCP operation for Blender cleanup, measurement, topology and build
volume checks, preview rendering and repaired-STL export before the existing
pinned Bambu slicer. The fixed repair contract has focused test and static-check
coverage. Disposable qualification-repair-004 passed against the retained real
attempt013 mesh: Blender reduced 754,726 source triangles to a closed,
outward-facing, single-component 53,092-triangle mesh, wrote hashed STL and PNG
outputs, then exited its owned process and deactivated both temporary MCP
servers. Fresh canonical printing attempt014 is enrolled with both exact server
IDs under the same terminal-cleanup harness. It produced a same-run source mesh
but Hermes returned the exact null-final-text transport fault after every normal
and tool-free retry, so no repair or slice ran and cleanup completed. Wright now
creates a minimal format-aware completion envelope from recorded successful
tool-call numbers only after all six exact-null decisions fail; 41 focused tests
pass. The API reloaded this source with model, dashboard and Hermes state
preserved. Fresh attempt015 then used nine source calls and reached a valid
26 x 38 x 17 mm intermediate with both through bores and counterbores, but an
earlier rebuild had replaced its exported file with an empty 84-byte STL and the
stage timed out before adding the pad recess and re-exporting. No repair or slice
ran; cleanup completed. Attempts014/015 exhaust this source-stage repair episode,
so printing is quarantined until a retained-source authoring probe demonstrates
a single-pass or otherwise bounded material fix.
Independent PCB recovery continued while printing is quarantined. Cases02/03
attempt008 ran serially against the revised 15-stage graph in the isolated,
no-network KiCad container; completed case01 remained untouched. The split
schematic stages cleared both earlier call-budget failures. PCB02 then stopped
before autorouting because native DRC proved its model-selected fixed J2/H4 and
J3/H2 positions had two courtyard overlaps that could not be repaired while all
four positions remained immutable. PCB03 completed symbol authoring, every net,
project setup, fixed placement and the remaining component placement, then hit
the 600-second finish-board limit after applying its design rules and immediately
before the final read-only checks. Neither case receives output credit. The next
material revision makes PCB02's fictional human input explicit about feasible
J2=(34,19.5) mm and J3=(34,10.5) mm geometric centers and separates remaining
placement from rule application and sealing, producing a 16-stage graph. A
second bounded disposable native probe moved those connectors and the two now
conflicting unconstrained test points in a retained-board copy; native DRC then
reported zero non-unconnected errors and zero courtyard overlaps. PCB03's
retained board also returned its exact persisted rules and all 19 footprints
through the proposed short seal-stage observations. Focused budget tests pass
3/3 and Ruff is clean. Attempt009 then ran cases02/03 serially on that qualified
16-stage graph. PCB02 stopped in schematic connection after a successful save,
an in-memory correction, and a replayed save triggered Wright's completed-
operation guard. The future connection task now gathers all inspection and
correction evidence before one final save; its focused tests pass 3/3.
PCB03 cleared every prior stage bottleneck, sealed the board, passed pre-route
DRC apart from expected unconnected items, and completed one FreeRouter run
with 70 tracks, four vias, and zero unconnected items. Final native DRC found
six copper-edge errors, so fabrication remained blocked. In two bounded
disposable proofs, moving J3 and J4 inward eliminated those six errors; moving
the newly conflicting TP3 in the second proof produced zero pre-route blocking
errors and zero final DRC errors. The fictional case03 input now records the
proved J3/J4 geometric centers and TP3 center for a future fresh run. Both
attempt009 cases remain immutable and receive no output credit. The dashboard
therefore remains `30 / 30 / 18 / 0`, with content validation disabled.
PCB03attempt010 is staged alone from the qualified input and current source,
mounted into the same exact no-network KiCad image, and passed live preflight
1/1. Two old Pi CAD qualification directories were copied from C: to the
repository artifact store with 394 relative paths, byte sizes and SHA-256 hashes
verified before deleting the source copies. That restored the original 512 MiB
run guard. Attempt010 then hit the measured `TASK_TIMEOUT` in “Place remaining
footprints” after successfully placing through C2; the compiler’s 600-second
task cap is retained. The repair is a 17-stage graph that splits remaining R/C
placement from test/miscellaneous placement, with focused budget tests passing
3/3 and Ruff clean. A fresh attempt011 batch was staged and preflighted 2/2;
the no-network KiCad runtime was extended to 56 mounts at the exact pinned image
and reactivated after a wrapper assertion was repaired. PCB02 attempt011 then
reached the native pending-approval build boundary but was correctly blocked:
the extracted board had five nets and merged every required `GND` member into
`5V` (for example J2.3 and C3.2), so no placement or routing credit was issued.
The attempt011 runner stopped PCB03 before dispatch on the 512 MiB guard. The
next PCB02 repair must prove the ordering/representation of the `5V` and `GND`
connections in a fresh disposable source/build probe before another full run;
the PCB03 split-stage run remains eligible after headroom is restored. Three
bounded archives moved completed run logs to D: only after per-file size and
SHA-256 verification; no active container or current rollback archive was
deleted. The dashboard remains live at `30 / 30 / 18 / 0`, with content
validation disabled.

## Summary

**Deferred content-validation phase (2026-09-13 UTC):** The user requested a
saved implementation plan for a future agent, likely Sol, after all 30 current
process flows produce their required data. See [content-validation/plan.md](content-validation/plan.md)
and its [future-agent handoff](content-validation/quickstart.md). Its G0 gate
requires current full-run receipts, actual artifact hashes and reconciled
lifecycle evidence for all 30 cases. Saving this plan does not start it or
change the active generation campaign's 30/30/30/0 target and authority.

Add **Start from template** to the established workspace Workflows surface and package ten real engineering starter definitions. Selecting one creates a fresh canonical `.workflow.wflow` instance with separate layout and immutable template provenance. The UI shows inputs, outputs, external effects, setup, qualification and current readiness without presenting fixtures or discovered MCP servers as live execution.

Deliver in three controlled milestones: (A) the complete ten-template selection/preview/instance UI while preserving all recovered authoring behavior; (B) generic artifact, engineering-assertion and durable approval/resume capabilities plus independently verified end-to-end execution for the three flagship 3D-printing, Raspberry Pi enclosure/CFD and sheet-metal workflows; (C) qualification and execution of the remaining seven workflows in evidence-led order. Each verified run can create a local, redacted capture package for social material; publication is out of scope.

## Technical Context

**Language/Version**: Python 3.11–3.14; TypeScript 6; React 19

**Primary Dependencies**: Existing FastAPI/Pydantic application boundary, SQLite/data-vault repositories, workspace service, canonical `.wflow` parser/formatter/command system, React Flow adapter, GatewayService/MCP client, OpenTelemetry/structured logging, Vitest and Playwright. Selected external engineering hosts are installed and qualified per server; none is added to the Wright base image merely for a template.

**Storage**: Packaged immutable YAML/JSON catalog and canonical source/layout assets; existing workspace-confined workflow source/layout files and file vault; additive SQLite records for instance provenance, capability evidence references, approval checkpoints, continuations and external-action state; immutable run/artifact records; local capture-package manifests/assets.

**Testing**: Existing Python unit/contract/e2e suites, TypeScript component tests, mocked page-level Playwright, real served-workspace walkthrough, clean-container MCP qualification, selected-host integration tests, independent geometry/file/numerical assertions, cancellation/restart/stale-approval/ambiguous-outcome tests.

**Target Platform**: Wright native and Docker distributions on supported desktop hosts; browser workspace UI. External integrations retain their actual platform/license/device requirements. Initial real UI integration verification uses the existing Windows workspace harness; catalog and offline instance behavior remain cross-platform.

**Project Type**: Existing modular monorepo local web application with Python domain/application/storage layers and React frontend.

**Performance Goals**: Open the locally packaged ten-item menu within 500 ms after activation; preview selection within 100 ms; create/open a valid instance within 2 seconds under normal local storage; keep established canvas interactions responsive; show run/checkpoint progress within one second of persisted change. External engineering operations use explicit operation-specific timeouts and do not block the API event loop.

**Constraints**: Offline template browsing/creation/editing; exactly ten initial entries; workspace ownership and path confinement; maximum existing canonical source/layout limits; no template-ID runtime dispatch; no second semantic authoring model; no hidden credentials; no false live/verified status; no arbitrary retries of mutations; no printer/vendor/social action without exact authority; no ordering/payment/production release/posting; no usability study in this feature.

**Scale/Scope**: Ten versioned templates and previews; ten fresh-instance paths; three flagship live chains; seven follow-on chains; three initial external-action kinds; one approval/continuation model; one local social capture format. Normal editor acceptance remains at 25 steps or fewer per example.

## Constitution Check

*GATE: Passed before research and re-checked after Phase 1 contracts.*

- **Modular monorepo / thin API routes — PASS**: Template values and validation belong in `core`; persistence in `data_vault`; instance/readiness/approval/resume/capture use cases in `workspace_service`; API routes validate/map transport only. External hosts remain behind GatewayService/tool contracts.
- **Offline-first — PASS**: Catalog, previews, distributable inputs, instantiation, editing, validation, fixture playback, cached references and capture operate locally. Online/vendor steps declare availability, use cached retrieval where appropriate and fail closed.
- **Distribution / native isolation — PASS by design**: The shared Wright runtime and UI own templates and orchestration. Agent-manager adapters remain thin. MCP-specific CAD/CAE/slicer/vendor hosts, SDKs, license managers and printer drivers are selected prerequisites rather than base-image additions. Native and Docker acceptance will be included in later tasks.
- **Embedded state / file vault — PASS**: SQLite WAL and the workspace file vault retain all state/artifacts. No external database is introduced. LanceDB is not required for the bounded template catalog; any future semantic lookup remains in-process.
- **Security / identity / RBAC — PASS**: Existing opaque credential/session and role policy remain unchanged. Template preview is read-only; create/run/approve/resume/capture enforce workspace/session authorization. Credentials are configuration references, never template/source/artifact content. Current terminal review's unauthenticated attribution is insufficient for the new external-action checkpoint and must be corrected through existing identity context.
- **Engineering tooling protocol — PASS**: Generic versioned operation contracts remain CLI/headless accessible. External retrieval adapters use online/cache/offline behavior. No execution requires an agent to manipulate a GUI; browser automation is a selected MCP/tool operation with explicit scope, not an unrecorded manual agent dependency.
- **UI atomic design / three-tier tests — PASS**: New controls use existing tokens/primitives/patterns and stable test IDs. Component states, mocked workspace journey and real FastAPI/browser journey are all planned. The served build must be entered via workspace Workflow/Workflows; a component test or detached route cannot close Milestone A.
- **Observability / glass-box verification — PASS**: List/instantiate/readiness/run/approval/resume/external action/assertion/capture operations create structured traces and pass trace IDs to tools and data operations. UI exposes prompts, constraints, operation bindings/scripts where applicable, checks and artifact lineage.
- **Phase isolation / branch discipline / manual gate — PASS**: Work is on `codex/081-engineering-workflow-templates`. This plan stops for human review before `/speckit-tasks` or implementation. Future major milestones remain reviewable separately. No direct `main` work is planned.
- **Governance — PASS**: No constitution amendment is needed. Push/merge/release work, if later authorized, follows repository runbooks and exact gate scripts.

Post-design re-check: [template-api.md](contracts/template-api.md) preserves workspace authority and atomic create; [approval-resume.md](contracts/approval-resume.md) fails closed, binds decisions to exact evidence and prevents blind mutation replay; [workflow-acceptance.md](contracts/workflow-acceptance.md) requires actual-output checks and clean qualification. No gate failure or exception remains.

## Architecture and Design

### 1. Canonical template catalog

Add a Wright-owned engineering-template package separate from `workflow_catalog`, whose current contents are provider-neutral Rivet projects. Load and validate a bounded manifest plus exact `.wflow`, layout, preview and distributable-input resources at service startup. Validation checks template ID/version, exact ten-entry ordering, source/layout digests, canonical parse/format, fresh-ID replacement, input rights, safe paths, operation declarations and acceptance-profile existence.

Runtime compiles the instantiated canonical definition into generic operations. Template ID exists only in provenance, UI metadata and evidence grouping; it never selects execution code.

### 2. Template UI and instantiation

Extend the current New/Open dialog pattern in `WorkflowRecoveryPage` and the reviewed editor header with **Start from template**. Use an accessible ten-option select/listbox with adjacent detail panel rather than crowding the canvas with cards. The detail panel shows purpose, discipline, preview, input/output chips, external-effect warnings and a readiness facts list. A safe editable filename and explicit Create action complete atomic instantiation.

The API uses a new canonical-source namespace defined in `template-api.md` so legacy `/workflow-templates` Rivet behavior remains compatible. Workspace service replaces semantic IDs, validates the source, performs exclusive create, persists separate layout/provenance and opens the normal editor. Existing authoring commands and source/CAS remain unchanged.

### 3. Readiness and qualification

Build readiness from immutable catalog requirements plus named evidence, current configuration and read-only availability. Do not write qualification state from a normal demo run. A separate qualification workflow follows the MCP testing process and publishes exact subject/evidence records. The UI can truthfully show a complete reference template even when no live backend is ready.

### 4. Generic workflow/runtime extensions

Map every template block/port to the canonical language and existing execution compiler before adding types. Extend generic results for mesh, slicer package, solver case/fields, fabrication bundle, printer/vendor receipts and capture assets. Extend versioned assertion operations for geometry/units/topology, artifact identity, field-derived metrics, convergence/mass/heat balance, mesh/timestep sensitivity and comparison.

Add durable `awaiting_approval` continuations and the approval/external-action repositories from `approval-resume.md`. Reuse artifact snapshots, stale-digest checks, CAD result identity, design-check/rework and DXF verification. Remove the current compile-time restriction only after the resumable invariant is implemented and tested; do not weaken terminal review behavior for existing workflows.

### 5. Flagship pipelines

**Sheet metal first internally**: It has the richest recovered evidence and exercises generic design-check, bounded rework, CAD/export identity, DXF verification and supplier approval/resume. Port the recovered definition into a distributable canonical template, keep prior artifacts as research evidence rather than current passing evidence, qualify the current selected Solid Edge/browser path, refresh supplier requirements and prove the no-order boundary.

**3D printing second internally**: Qualify the smallest complete path for source image/scale → generated mesh → measured repair/orientation → support/slice representation → package verification → approved P1S transfer → receipt/status. Prefer existing qualified Blender scope where it fits; select and record any additional generator/slicer/device adapter through catalog qualification. Use a disposable non-hazardous fixture and dry transfer simulator until the exact physical printer action receives user authorization; simulator evidence remains labeled.

**Pi enclosure/CFD third internally**: Pin Raspberry Pi 5 manufacturer evidence, produce and approve the design document, qualify AgentCAD D001 or an equivalent contract-compatible CAD adapter, then qualify Foam-Agent D040 or an equivalent real solver integration. Verify document-to-CAD, CAD-to-fluid-domain, boundary/mesh identity and field-derived results. Include deliberately substituted geometry as a blocking negative control.

This internal order reduces platform risk without changing their equal user-facing flagship status.

### 6. Remaining seven and social capture

Implement in the contract order: drill jig, heat spreader, bracket, PCB, robot diagnosis, harness, water-heater sizing. For each, freeze distributable inputs, qualify the narrow tool chain, implement independent assertions and one negative/recovery case, record exact evidence, then promote only that subject.

Capture packages are generated from immutable verified run/artifact records. Rendering/caption generation is local and bounded. A redaction/rights pass blocks credentials, private absolute paths, personal data and unlicensed source assets. There is no publisher connector.

## Project Structure

### Documentation (this feature)

```text
specs/081-engineering-workflow-templates/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── implementation-goal.md
├── checklists/requirements.md
└── contracts/
    ├── template-api.md
    ├── approval-resume.md
    └── workflow-acceptance.md
```

### Expected source changes

```text
packages/core/src/core/
└── engineering_workflow_templates.py

packages/data_vault/src/data_vault/
├── workflow_template_repository.py
├── workflow_continuation_repository.py
└── workflow_external_action_repository.py

packages/workspace_service/src/workspace_service/
├── engineering_workflow_templates/
│   ├── catalog.yaml
│   ├── templates/*.workflow.wflow
│   ├── layouts/*.json
│   ├── inputs/**
│   └── previews/*
├── engineering_workflow_template_service.py
├── workflow_source_execution.py
├── workflow_artifact_review.py
├── workflow_engineering_assertions.py
├── workflow_external_actions.py
└── workflow_demo_capture.py

apps/api/src/api/
├── schemas/workspace.py
└── routers/workspace.py

apps/web/src/
├── components/pages/WorkflowRecoveryPage.tsx
├── prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx
├── prototypes/workflow-recovery/EngineeringTemplateDialog.tsx
├── prototypes/workflow-recovery/engineering-template-dialog.css
└── services/workspace-service.ts

tests/
├── ui-integration/engineering-workflow-templates.spec.ts
├── e2e/test_engineering_workflow_templates.py
└── external/engineering_workflow_templates/
```

**Structure Decision**: Keep semantic/catalog values in core/package resources, persistence in data-vault and orchestration in workspace-service. Integrate UI through existing feature-080 files only where necessary, with a new focused dialog component. Exact filenames may be refined by tasks after checking current ownership, but boundaries may not move into routes or renderer state.

## Delivery Sequence and Review Gates

1. **Planning review (current stop)**: Review the ten workflows, template UI contract, approval boundaries, MCP qualification truth model and scope. No implementation starts until explicit approval per constitution.
2. **Tasks and analysis**: Run `/speckit-tasks`, then `/speckit-analyze`; resolve all high/critical cross-artifact findings. Map every existing feature-080 authoring capability and current runtime block before editing.
3. **Milestone A — UI and ten templates**: Implement the catalog, ten valid definitions/previews, list/detail/instantiate API, dropdown/detail/create UI, fresh identity/layout/provenance and readiness display. Use labeled fixtures only. Run component and page tests, then verify the served build from a normal workspace Workflow/Workflows entry and repeat the author/save/reopen/drag/connect/source/undo/redo/conflict interactions. Prepare exact screenshots for product review.
4. **Milestone B0 — execution foundations**: Add generic result/assertion roles, identity-bound capability readiness, durable approval/continuation/external-action state, restart/cancel/reconcile logic and UI review/resume. Independently test stale subjects and unknown outcomes before connecting printer or supplier actions.
5. **Milestone B1–B3 — flagship workflows**: Implement and qualify sheet metal, 3D printing and Pi enclosure/CFD in the internal order above. Each slice requires actual artifacts, independent positive checks, one meaningful negative/recovery path, served UI run evidence and local capture package. Keep “working” false until the complete chain passes.
6. **Milestone C — seven additional workflows**: Qualify and promote one at a time in contract order. Do not block shipping the three verified flagships on unqualified follow-on templates; their reference/setup state remains truthful.
7. **Integration candidate**: Run applicable full suites, packaging/offline/native/Docker checks, security/dependency review and independent code/evidence review. Before any authorized push to a PR targeting `dev`, read `docs/contributing/dev-push-runbook.md` and run `scripts/check-dev-push.ps1`. Merge and release remain separately gated.

Major lifecycle milestones stop for human review. Physical printer transfer, supplier upload/handoff, paid or credentialed qualification, push, merge, release and publication each require their own applicable authorization; a plan approval alone does not perform them.

## Verification Strategy

- **Catalog/property tests**: exactly ten unique IDs; deterministic ordering; resource/digest/right records; every source parses/formats; no unsafe paths/secrets; fresh IDs; no run/approval import; idempotent atomic create and collision behavior.
- **Component tests**: closed/default, loading, error, reference/setup/ready/verified, keyboard traversal/focus return, preview rights/error, name validation, create pending/conflict/success, external-effect disclosure.
- **Page/UI integration**: workspace entry, ten entries, create/cancel, normal editor preservation, source/diagram correspondence, edit/save/reopen, drag/connect/mismatch, undo/redo, invalid-source containment and conflict handling.
- **System E2E**: real FastAPI and workspace session; list/detail/create/readiness; run/checkpoint/decision/resume; restart/cancel; artifact viewer; capture manifest; zero network for offline path.
- **Approval security**: mutate every subject component; actor/session/RBAC failures; races/idempotency; expiry; consumed decision; missing/changing artifacts; changed schemas; no dispatch on stale/denied; timeout-after-dispatch produces unknown and no automatic retry.
- **Engineering integrations**: pinned clean setup, direct/backend and Wright calls, exact artifacts, independent format/geometry/numerical oracle, negative input, cancellation and cleanup. The template contract supplies example-specific assertions.
- **Browser evidence**: actual served build, exact branch/commit/tree/frontend/API/workspace/flags, raw and annotated screenshots, trace and diagnostics. Product review and technical verification remain separate facts.

## Risks and Mitigations

- **Unqualified named tools**: AgentCAD, Foam-Agent, slicer/Bambu and several follow-on servers may fail qualification. Keep templates reviewable with exact blocking readiness; substitute only a contract-compatible qualified adapter and record the decision.
- **Physical/vendor side effects**: use simulator/read-only reconciliation until exact user authorization; bind approval to final bytes/settings/destination and consume once.
- **Plausible but wrong engineering output**: assert identity at every transform and compute checks from actual files/fields; retain negative substituted-geometry and missing-artifact cases.
- **Editor regression**: start from the feature-080 reviewed implementation and use its established workspace acceptance harness; do not replace the canvas or authoring source.
- **Template drift and marketing overclaim**: immutable versions and evidence-derived readiness/capture disclosures; never silently upgrade instances or publish from Wright.
- **Supplier requirement changes**: retrieve/cache dated primary sources at run time, surface conflicts, and require a new subject/decision rather than encoding stale values as universal rules.

## Complexity Tracking

No constitutional violation is accepted. The new catalog does not duplicate semantic authority: packaged template source is immutable seed material, and the fresh workspace canonical source becomes the sole editable authority. Durable approval/continuation storage is required to safely cross real external-action boundaries and replaces no existing run or artifact authority.

## September 14 PCB attempt011 diagnosis and next repair

The PCB02 attempt011 five-net result was reproduced in two disposable native
qualifications. Reordering the GND operations before 5V did not change the
result. A second qualification using neutral labels (`GROUND` and `VCC5`) also
merged the two rail groups, proving that the failure is geometric rather than a
KiCad power-name alias. The generated symbol layout placed C2 pin 2 and C4 pin
1 on the same x coordinate with their 2.54 mm label stubs touching; KiCad’s
authoritative XML exporter therefore treated the intended six-net design as one
power net. A direct-label probe that placed each label at its exact pin tip and
removed the stubs produced six native nets with the approved memberships.

The authoring prompt now requires planning the complete symbol grid before the
first mutation, leaving each 2.54 mm stub disjoint and separating adjacent
vertical passives laterally or beyond their combined stub reach. The normal
connect stage remains label-based, so a fresh attempt must regenerate symbols
from this revised prompt and then rerun the native netlist boundary. Probe
receipts are in `.local-run/feature-081-live/campaign-execution/`, including
the original order test, neutral-label test and direct-label XML qualification.
No campaign output credit was issued. The dashboard remains `30 / 30 / 18 / 0`;
content validation stays disabled.

## September 14 PCB attempt012 route result and repair qualification

PCB03 attempt012 reached the route-and-inspect boundary after the 17-stage
authoring graph completed. The model moved TP1 to (7.5,14) mm while resolving a
courtyard overlap, then ran the single permitted autoroute. Native DRC retained
one blocking `unconnected_items` error for the J2 GND pad; the run stopped with
no fabrication export and received no output credit. PCB02 was correctly held
before dispatch because the shared workspace had fallen below the 512 MiB free
disk guard.

Four bounded retained-board route probes then isolated the PCB03 repair. The
accepted qualification uses the existing J3/J4/TP3 geometry and moves only the
J2 footprint origin to (5.0,19.0) mm and TP1 footprint origin to (10.0,14.0)
mm. Its pre-route and final native DRC both have zero blocking errors, zero
unconnected items and zero copper-edge violations. The coordinates are now
recorded in the PCB03 input context; a fresh attempt013 must regenerate and run
the source with that contract. The attempt012 run and all probe receipts remain
immutable and uncredited. Dashboard remains `30 / 30 / 18 / 0`; content
validation stays disabled.

## September 14 PCB attempt013 placement retry result and guard

Attempt013 confirmed the PCB03 source repair through the native build boundary:
the regenerated schematic contained seven nets and the fixed geometry used J2
origin (5.0,19.0) mm and TP1 origin (10.0,14.0) mm. The run then stopped in
“Place remaining resistors and capacitors” with `WORKFLOW_NOT_READY` because
the model requested the completed `pcb` operation again after its final
`move_footprint` call. This is a model/task termination defect; no KiCad DRC or
routing failure occurred and no output credit was issued. PCB02 was held before
dispatch when the workspace fell below the 512 MiB guard.

Both bounded placement prompts now explicitly require an immediate final report
after the last successful mutation or audit and forbid any subsequent `pcb`,
`audit`, `suggest_placement`, `load`, or other tool call. Focused stage-budget
tests pass 3/3. Preserve attempt013 and stage a fresh attempt014 only after
archiving enough inactive evidence to restore the disk guard; dashboard remains
`30 / 30 / 18 / 0` and content validation stays disabled.

## September 14 PCB attempt014 terminal results and connect guard

Attempt014 split at two independent boundaries. PCB03 stopped in “Connect every
supplied schematic net” with `WORKFLOW_NOT_READY` because the model requested the
completed `schematic` operation again after its final save. PCB02 completed its
six-net source, all placement and sealing stages, and exactly one autoroute; its
final native DRC retained three `copper_edge_clearance` errors on ADC_B tracks
(0.6069 mm against the required 1.0000 mm) plus eight silkscreen warnings. No
fabrication export or output credit was issued for either case.

The connect-stage prompt now has the same immediate-terminal rule as placement:
after the single final schematic save and coverage report, no further tool call
is permitted. PCB02 requires a bounded retained-board geometry probe to move the
ADC_B route-sensitive placements inward before a fresh route. Dashboard remains
`30 / 30 / 18 / 0`; content validation stays disabled.

## September 14 PCB attempt015 launch and retained-board qualification

The retained PCB02 attempt014 unrouted source was copied into disposable
qualification subtrees and exercised through the real KiCad MCP, FreeRouter and
native DRC. Moving J1 to footprint origin `(4.5,18.81)` mm at 180°, C3 to
`(8.0,23.0)` mm at 90°, and C4 to `(12.0,23.0)` mm at 0° produced zero
unconnected nets and zero final DRC errors in the combined-placement proof;
the receipt is `pcb02-placement-qualification-003.json`. The source context and
board-build prompt now carry these qualified footprint origins and preserve the
connector-center distinction.

After two hash-verified inactive-evidence archives restored about 735 MiB of
free space, fresh PCB02/PCB03 attempt015 sources were staged and preflighted
(17 stages, 9 inputs, complete auto-approval grants, empty outputs). The pinned
KiCad runtime was replaced with the identity-verified 72-mount container. A
hidden serial runner is active under PID 37732, with durable state and logs at
`.local-run/feature-081-live/campaign-runner-state/pcb-attempt-015-live` and
`campaign-execution/pcb-attempt-015.*.log`; it dispatches PCB03 then PCB02 and
retains the 512 MiB guard. Dashboard is live at
`http://127.0.0.1:8771/?view=recovery`; at launch it remained `30 / 30 / 18 / 0`
and is checked after each terminal case.

## 2026-09-14 PCB attempt015 PCB03 completion and PCB02 handoff

PCB03 attempt015 completed all required workflow stages and produced the expected native KiCad package: schematic, project, PCB, BOM CSV, Gerber ZIP, ERC and DRC reports, evidence records and run metadata. Native ERC and DRC completed with zero errors (warnings are retained in the reports), and the output tree contains 203 nonempty files whose recorded export hashes were verified before the dashboard incremented `processes_with_outputs` from 18 to 19. The runner recorded a lifecycle snapshot mismatch after completion; the raw run, exported evidence and lifecycle records are preserved for diagnosis and no content-validity credit was assigned.

The same hidden serial runner immediately dispatched PCB02 attempt015. PCB02 is currently running under the 72-mount identity-verified KiCad runtime with the 512 MiB disk guard. Dashboard is live at `http://127.0.0.1:8771/?view=recovery` and currently reports `30 / 30 / 19 / 0`; content validation remains disabled. Persistent recovery state records the live dashboard metrics and PCB02 handoff.

## 2026-09-14 PCB02 attempt016 recovery dispatch

PCB02 attempt015 reached the native build approval boundary but retained two
courtyard collisions: H3-C2 and TP1-J3. A disposable KiCad qualification moved
only the unconstrained references and proved zero native audit errors at C2
footprint origin `(23.0,18.5)` mm and TP1 origin `(10.0,14.0)` mm. The PCB02
context, board-build prompt and passive-placement prompt now carry these exact
fixed origins.

The attempt016 staging script now strips preparation residue from the API
instance before rebinding inputs. This preserves the instance's canonical task
IDs and removes stale input-binding sections that otherwise produce duplicate
source declarations. The fresh case passed read-only preflight with 17 stages,
9 inputs, 14 granted tools and an empty output tree. The pinned KiCad runtime
was extended from 72 to 74 mounts without changing its image, network isolation
or 18 tool schema pins. Hidden worker PID 38860 is running PCB02 attempt016
under auto approval and the 512 MiB disk guard. Dashboard remains live at
`http://127.0.0.1:8771/?view=recovery` and is synchronized at `30 / 30 / 19 / 0`;
content validation remains disabled.

## 2026-09-14 PCB02 attempt016 C3 geometry stop and attempt017 recovery

Attempt016 completed authoring, connectivity and native project initialization, then stopped at the expected build approval boundary. The native build returned 14 components, 6 nets and 27 assigned pads, but reported C3 at origin `(8.0,23.0)` mm, rotation 90 degrees as off-board/overlapping. The run received no output credit and remains preserved as a terminal failure.

A disposable KiCad qualification copied the failed board and tested five C3 candidates. C3 origin `(8.0,23.0)` mm at rotation 0 degrees returned zero native audit errors and zero courtyard overlaps. The board-build prompt and PCB02 context now require that qualified rotation. Attempt017 passed fresh preflight with 17 stages, 9 inputs, 14 granted tools and an empty output tree. The pinned network-isolated KiCad runtime was extended to 76 mounts with unchanged image and tool pins; worker PID 10464 is running under auto approval. Dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and synchronized at `30 / 30 / 19 / 0`; content validation remains disabled.

## 2026-09-14 PCB02 attempt017 duplicate-operation stop and attempt018

Attempt017 passed the native placement audit with all 14 footprints clear and zero overlap or pad-clearance issues, but the model requested `pcb` again after the final silkscreen label mutation. The runtime rejected the completed operation and stopped the case without output credit. The source prompt now requires immediate termination after the final mounting-hole or silkscreen-label mutation, forbidding any later `pcb`, audit, load or inspection call.

Attempt018 passed fresh preflight with 17 stages, 9 inputs, 14 granted tools and an empty output tree. The pinned KiCad runtime was extended to 78 mounts with the same image, network isolation and 18 tool schema pins. Worker PID 4956 is running under auto approval. Dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and synchronized at `30 / 30 / 19 / 0`; content validation remains disabled.
