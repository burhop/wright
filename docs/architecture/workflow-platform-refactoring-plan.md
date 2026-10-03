# Workflow platform refactoring plan

**Date:** 30 September 2026.
**Prototype branch (historical):** `codex/prompt-to-3d-printed-part-demo`.
**Implementation branch:** `codex/083-process-working-interfaces`.
**Direction:** [Workflow platform vision](../design/workflow-platform-vision.md) and
[process UI design](../design/process-apps.md).
**Status:** Proposed staged implementation of the agreed user experience.
The shared interaction contract/client/kit and runtime migration are not complete.

## User outcome comes first

Users and AI can define a useful engineering process, then carry it out through
a common or tailored interface within Wright. Preserve complementary experiences:

- The existing flowchart, blocks, source, and inspectors for building and inspecting.
- A working interface for inputs, results, questions, decisions, and progress,
  hosted in a workspace tab and connected to the same accepted process and run.

The journey is create/open, choose a common or tailored view, review/save it,
run in the workspace, and inspect/refine when needed. A dashboard, comparison
table, interactive model, questionnaire, or guided sequence can be appropriate.
No single arrangement or manufacturing lifecycle is required.

The platform investment is the connection between a process and its interface:
an explicit interaction contract, shared components/style, a scoped client over
existing process services, and consistent workspace hosting. AI authors the
presentation using those foundations. Wright owns execution and durable state.

### Confirmed implementation choices

The user selected the complete experience, including AI-created reusable UIs and
proof on two different processes. Users request UI generation, preview, saving,
and updates through Wright. Start with the configured default LLM and prepared
Wright API/UI instructions, mapping a coding-agent role/profile into the existing
agent-adapter boundary. Model, role instructions, and platform remain replaceable;
future platform support is qualified separately.

Runs may be long running and unattended between declared interaction steps.
Resolve required user choices before starting, or explicitly identify configured
defaults, automatic upstream producers, and planned user-review/action steps.
At declared interaction steps persist waiting state and resume the same run.
Do not invent runtime questions or forms to repair predictable missing inputs.
Live prerequisite changes follow declared wait/recovery/failure policy.

The printing prototype is a reference and source of reusable work. Its integration
difficulties do not become the platform roadmap. Prefer existing MCP providers.
Creating a new Bambu MCP or maintaining Handy/firmware workarounds is outside
this plan. Provider-specific requirements and unsupported operations are disclosed.

## Deliverables and first implementation slice

1. A versioned process interaction contract describing available inputs, outputs,
   evidence, pending questions/decisions, observed state, and permitted actions.
2. A scoped process client, shared UI kit, and usable common working view, built
   on current services, design tokens, viewers, and workspace surface lifecycle.
3. An AI authoring reference and saved UI artifact/binding contract, allowing
   users to generate and update reusable tailored views through Wright, with
   compatibility checked as processes change and recorded agent/profile provenance.
4. Migration of the reference experience and proof with a substantially different
   existing engineering process using the same platform foundation.

The first implementation slice should let a user open an accepted process,
provide supported inputs, start or attach to a run, follow its actual state,
inspect a result, make an existing supported decision, navigate to its block or
evidence, close the view, and reopen the same run. Provide a common view first.

Map these operations to actual runtime support before freezing the feature plan.
Expose capability limits. Extend missing semantics only in an approved bounded
feature; do not create a second executor to make the UI appear complete.

## Architecture and existing ownership

| Foundation | Existing seam and intended use |
|---|---|
| Accepted definition and execution | `packages/workspace_service/src/workspace_service/workflow_source_execution.py` and `packages/workspace_service/src/workspace_service/workflow_mcp_execution.py`: retain canonical compilation, accepted revisions, artifact handoffs, run records, and gateway execution. |
| Results and evidence | `packages/workspace_service/src/workspace_service/workflow_results.py`: reuse `EngineeringResult`, representations, provenance, and `external_action_receipt`. |
| Checks and correction | `packages/core/src/core/process_validation.py` and `packages/workspace_service/src/workspace_service/process_validation/`: reuse exact subject/profile identity, findings, gates, bounded corrections, and report projections. |
| Capability operations | `packages/tool_registry/src/tool_registry/gateway_service.py` and existing onboarding: reuse discovery, installation, connection, workspace grants, schemas, audit, and lifecycle. |
| Workspace hosting | `packages/workspace_service/src/workspace_service/surfaces/` and `apps/web/src/components/surfaces/`: reuse tabs, managed applications, MCP App views, restoration, and scoped presentation. |
| Authoring and navigation | `apps/web/src/prototypes/workflow-recovery/` and `apps/web/src/components/chat/WorkspacePanel.tsx`: preserve the reviewed editor and workspace entry. |
| Client and style | `apps/web/src/services/workspace-service.ts`, `apps/web/src/tokens/design-tokens.css`, and `apps/web/src/styles/tokens.css`: reuse process calls and style primitives; review the public boundary needed by isolated process UIs. |

Pure shared contracts belong in `core`; persisted records in `data_vault`;
workspace use cases in `workspace_service`; MCP policy/lifecycle in
`tool_registry`; routes remain thin. UI components and the scoped browser client
compose those services rather than importing private backend implementation.

Existing hosting is a foundation, not a complete process-app contract. Packaged
MCP Apps have provider-scoped operations. Wright's current WebMCP SDK exposes
page-local tools to Wright; that direction alone does not allow the page to
drive a process. Design the bounded process host/client contract explicitly.
Do not widen a provider panel into arbitrary cross-server access.

## Contract decisions to close in the feature plan

- **Identity:** workspace, accepted process revision, UI source/binding version,
  run, and exact result/review subjects. Run inputs are distinct from definition edits.
- **Interactions:** input schemas/units, defaults, current availability, pending
  declared questions/decisions, results/evidence, and supported viewing options.
- **Readiness and autonomy:** required user choices resolved before execution;
  distinguish explicit defaults, upstream-produced data, and planned human
  interactions. Define durable pause/resume and permitted recovery without new
  ad hoc runtime questions. External freshness checks still apply.
- **Coding-agent role:** default-model inheritance, prepared versioned Wright
  API/UI instructions, permitted capability/workspace scope, adapter requirements,
  and generation provenance. Reuse existing configuration and agent services.
- **Actions:** currently permitted operation and subject, prerequisites, reason
  when unavailable, backend authority, and supported lifecycle. Submission,
  observed external execution, and completion remain distinct facts.
- **Dependencies:** option/input changes invalidate affected downstream work and
  reviews through runtime rules. Browser layout changes alone need not invalidate
  engineering outputs.
- **Presentation:** common fallback, shared components/theme, workspace tabs,
  deep links, accessibility, custom viewers, and the first packaging model.
  Isolated apps do not inherit parent CSS or private React components automatically.
- **Persistence and compatibility:** saved UI/binding manifest, kit/client/contract
  versions, compatible process changes, stale bindings, update path, and rollback.
  Do not regenerate the interface for every run.
- **Recovery:** close/reopen and reconnect reconcile with backend state. Closing a
  view is not cancelling a run. Unknown external outcomes do not trigger replay.
- **Engineering evidence:** use current validation and review contracts. Tool
  success and UI rendering cannot set a compliance verdict or remove a requirement.

These are bounded design subjects, not a requirement to build an all-purpose
screen language or support every graph shape in the initial slice.

## Staged work and acceptance

### M0: Direction, user journey, and baseline

- [x] D01 Record the agreed vision and process UI experience.
- [x] D02 Put stable guidance outside the managed Spec Kit section in
  `AGENTS.md`; align specification, planning, task, and PR templates.
- [x] D03 Record this roadmap with the shared platform foundation first and
  prototype migration inventory as supporting material.
- [ ] R01 Capture a reviewed snapshot of the existing prototype, uncommitted
  fixes, saved runs, artifact identities, and rollback basis with explicit paths.
  Preserve needed ignored evidence separately; exclude credentials.
- [ ] R02 Map the proposed first user journey to accepted definitions, run,
  event, review, result, validation, readiness, agent, and hosting contracts.
  State real gaps and capabilities before proposing extensions.

Exit: direction and current support are distinguishable. Documentation does not
prove runtime delivery, engineering correctness, or user acceptance.

### M1: Process interaction contract

Depends on M0 and review of the first feature's technical plan.

- [ ] R03 Define the minimal versioned interaction description using existing
  contract shapes: context, inputs, outputs/evidence, pending interactions,
  observations, declared interaction policy, readiness, and permitted actions
  with exact subjects and reasons.
- [ ] R04 Map those interactions to current services and accepted source semantics.
  Declare unsupported arrangements and any minimal approved schema extensions,
  including compatibility and migration. Define pre-run input readiness and
  durable declared pause/resume without creating a second executor.
- [ ] R05 Define scoped host/client operations and server enforcement. Keep the
  existing runner as the execution authority; preserve provider-panel grants.
- [ ] R06 Define UI artifact/binding compatibility, invalidation, restoration,
  common-view fallback, and rules for separating definition edits from run inputs.

Exit: a common view and a tailored view can consume the same process interactions.
No screen layout, mandatory stage order, or device protocol controls the contract.

### M2: Shared client, UI kit, and common working view

Depends on approved M1 contracts.

- [ ] R07 Implement the narrow process client over existing services, including
  following and reconciling durable run state, results, and current decisions.
- [ ] R08 Assemble shared inputs, result viewers, progress/findings, review/actions,
  and navigation using existing style tokens and useful components. Package the
  public pieces required by the chosen host; avoid copying private page code.
- [ ] R09 Integrate the common view into Wright workspace tabs. Preserve the editor,
  exact process/run context, deep links, and close/reopen behaviour.
- [ ] R10 Preserve evidence gates, actionable errors, missing-capability behaviour,
  currentness, option invalidation, and uncertain-action handling in the common view.
  Reject unresolved predictable input before a run; show planned human waiting,
  external waiting, and failure distinctly without inventing runtime questions.

Exit: users can complete the supported first journey without a custom app.
Reopening reconstructs presentation from backend state without resending work.

### M3: AI-authored, reusable tailored interfaces

Depends on M2 and the reviewed packaging model.

- [ ] R11 Implement UI generation, preview, saving, and updates through Wright's
  default coding-agent role over the existing agent boundary. Supply versioned
  API/kit instructions, documented client, examples, and a reference UI. Record
  resolved model/profile/prompt/adapter and artifact provenance. Design replaceable
  platform bindings without claiming unqualified future adapters.
- [ ] R12 Save a generated UI with its binding manifest and supported versions.
  Check bindings on process/capability changes; support focused updates and
  common-view fallback when incompatible.
- [ ] R13 Verify a tailored UI can present the same inputs, results, decisions,
  and permitted actions as the common view. Inspect actual layout, accessibility,
  failures, stale bindings, reload, navigation, and restored runs. Prove generation
  through Wright, upfront readiness, declared pause/resume, and uninterrupted
  unattended sections.

Exit: AI creates a reusable presentation from the shared foundation. The generated
code contains no graph executor, vendor protocol, or independent job-status truth.

### M4: Migrate and prove the general platform

Depends on M2; use M3 when proving AI-authored composition.

- [ ] R14 Inspect and select one substantially different existing engineering
  workflow and its useful tool chain. Reuse the existing examples and evidence;
  avoid inventing a new campaign or silently rewriting an assignment.
- [ ] R15 Qualify the existing providers needed by the chosen reference workflows
  through normal onboarding. Record actual schemas, operating requirements, and
  gaps. Provider-specific compatibility work does not block shared platform design.
- [ ] R16 Migrate the prompt-to-part reference using public capability bindings
  and the shared process UI foundation. Retire embedded vendor code after all
  live callers migrate; preserve saved-result access and historical evidence.
- [ ] R17 Use the same contract/client/kit to complete the supported journey for
  the different process, including an AI-authored view. Document its substantive
  engineering tools and handoffs, applicable checks, and actual limitations.
- [ ] R18 Compare the two experiences, remove discovered coupling in the owning
  layer, and record exactly which architecture and engineering claims are proved.

Exit: different process arrangements use one platform and consistent workspace
experience. Another printer alone does not prove generality.

## Verification and completion evidence

When implementation is separately authorised, verify the changed behaviours:

- Contract/currentness/recovery checks: revised inputs, stale outputs/reviews,
  missing required evidence, duplicate or uncertain actions, reconnects, resumed
  runs, incompatible UI bindings, and unsupported operations. Include predictable
  missing inputs rejected before execution, automatically produced intermediate
  data, declared human pauses, and unexpected AI clarification rejected/reported
  without presenting a new runtime question.
- Common and tailored UI use the same backend facts. Closing, reopening, and
  switching to the diagram retain exact context and do not launch duplicate work.
- Changed UI needs component, mocked journey, and served-workspace verification
  through the normal Workflow/Workflows entry. Preserve the existing editor
  acceptance harness and [integration guide](../contributing/workflow-ui-integration.md).
- Provider qualification follows [MCP validation](../mcp-catalog/mcp-server-testing-process.md).
  Protocol, engineering behaviour, browser experience, and physical actions have
  separate evidence; fixtures are labelled and support only their observed scope.
- Installed-package checks preserve native/Docker boundaries as applicable, public
  provider contracts, and freedom from private checkout/runtime dependencies.
- Preserve the 081 generation campaign, 082 validator evidence, and report contract.
  Use isolated demonstrations. Do not build the reporting UI assigned to another
  branch or rewrite the 30 examples as part of this architectural follow-on.

Record direction, planning, implementation, protocol qualification, engineering
evidence, browser verification, and user acceptance separately. Run push/merge/
release gates at their authorised transitions, not as a substitute for user evidence.

## Authority and next feature

The user approved the concept and requested these documentation and guidance
updates. This proposal does not start runtime implementation or an autonomous goal.

The concrete follow-on is
[Feature 083: Process working interfaces](../../specs/083-process-working-interfaces/plan.md),
with a [saved implementation goal](../../specs/083-process-working-interfaces/implementation-goal.md).
Its approved scope is the complete experience selected by the user: interaction/runtime
foundation, shared client/kit/common view, actual UI generation/preview/save/update
through Wright's coding role, and proof on two different existing engineering
processes. The shared foundation is an increment, not the final deliverable.
The user submitted that goal and approved local implementation and verification.
Local interaction/runtime, client/kit/common view, actual-model authoring and
saved reuse have evidence. Full engineering parity, active vendor-code retirement,
installed browser acceptance and the final completion audit remain pending. See
the [operator guide](../workflows/process-working-interfaces.md) and the feature's
[task record](../../specs/083-process-working-interfaces/tasks.md).

The managed context now points to approved Feature 083; preserve Feature 082's
historical approvals and validator contracts. This roadmap
does not create a new vendor project or authorise device/supplier actions or
external publication. The following inventory informs later migration work.

## Appendix: current prototype migration inventory

This inventory supports the general platform plan. It is not a vendor feature
backlog or evidence of completed migration. Inspect transitive callers before
removing or reusing code; preserve campaign sources and recorded digests.

| Current code | Observed responsibility | Target disposition |
|---|---|---|
| `packages/workspace_service/src/workspace_service/print_part_demo_printer.py` | Mixes package checks, dispatch receipts, Bambu tool aliases, AMS/state decoding, Studio binding restoration, and P1S camera protocol. | Reuse shared action/evidence behaviour in existing Wright seams. Replace vendor behaviour with qualified existing provider capabilities; remove the mixed module after caller migration. |
| `scripts/print_demo_p1s_mcp.py`, `scripts/print_demo_p1s_session.py`, `scripts/print_demo_p1s_transfer.py` | Vendor MCP tools, MQTT telemetry/replies, FTPS upload, slot mapping. | Retire repo-local adapters after binding existing MCP tools. Record unsupported operations for provider maintainers; do not create a new Wright-owned Bambu MCP. |
| `scripts/print_demo_studio.py`, `scripts/windows/inspect-bambu-studio.ps1`, `scripts/windows/studio-desktop.ps1` | Studio package conversion, desktop controls, OCR, worker monitoring. | Retain experimental evidence, then remove active vendor automation after migration. Cloud/Handy workarounds are outside Wright's product plan. |
| `scripts/configure_print_demo_studio.py`, `scripts/configure_print_demo_offline.py` | Registers repo-local vendor scripts, profiles, sources, and launch overrides. | Use existing providers' normal installation/configuration and Wright capability onboarding. Retain only neutral example configuration in Wright. |
| `scripts/engineering_dataset_slice.py`, `scripts/engineering_dataset_slice_mcp.py`, `scripts/engineering_jig_slice_mcp.py` | Bambu CLI, pinned profiles, P1S envelope, vendor slice metadata and support/toolpath extraction. | Replace operational vendor slicing with qualified existing capabilities. Preserve campaign copies/evidence; update active bindings deliberately with new provenance. Shared geometry algorithms may remain only after removing device assumptions. |
| `scripts/engineering_dataset_mesh_repair.py` and `scripts/engineering_dataset_mesh_repair_mcp.py` | Geometry operations plus scenario and fixed build-envelope constraints. | Separate generic geometry from configured scenario/machine requirements; keep vendor constraints external. Geometry changes need explicit workflow policy and evidence, not silent repairs. |
| `packages/workspace_service/src/workspace_service/print_part_demo.py` | Hard-coded example, server/tools, repo-root lookup, material defaults, and artifact conventions. | Retain the example as a saved workflow and binding data. Generalise only proven shared preparation mechanisms; remove production reliance on private demo naming or source-checkout paths. |
| `apps/api/src/api/main.py` | Restores one Studio binding after catalog reconciliation. | Remove vendor startup logic. Address configuration ownership in generic onboarding/reconciliation; metadata refresh must preserve authorised installed bindings. |
| `apps/api/src/api/routers/workspace.py` `/print-demo/*` handlers | Embedded preparation, package selection, vendor checks, submit/retry/cancel, and camera mediation. | Thin adapters to shared workflow/review/action services, or remove demo endpoints when the external panel uses normal gateway tools. Declare any temporary compatibility route and its removal milestone. |
| `apps/web/src/components/pages/PrintPartDemoPage.tsx` | Common previews and progress mixed with P1S/AMS controls, campaign paths, and package filenames. | Reuse format-based viewers and review components in the shared kit. Build a process UI using provider-backed options and Wright process services. Use provider panels where useful; bind artifacts by identity and role, not directory-name matching. |
| `apps/web/src/services/workspace-service.ts` and `apps/web/src/components/chat/WorkspacePanel.tsx` | Demo API types/calls and demo entry integration. | Keep the workspace/editor shell; migrate callers to reviewed shared contracts or the external surface. Preserve saved-result navigation. |
| Catalog entries, example bindings, campaign records, demo evidence | Names and qualifies specific providers; preserves observations. | Retain descriptive metadata and immutable history. Update active connection references without inheriting old physical qualification. |

The current prototype scripts import `printer_status_summary` from Wright's demo
service. This reverse coupling must disappear with their retirement. Copying
scripts into another repository is not the proposed solution; use existing MCPs.

### Entry-point migration checkpoint, 2 October 2026

The workflow workspace entry no longer imports the active `PrintPartDemoPage`.
New work uses the existing **Use saved process** common/tailored interface path.
Historical `printDemoRun` queries select a read-only `HistoricalResultView` over
the existing canonical run recorder, with exact source/run locator checks,
original result/error metadata, saved artifact navigation and no permitted
actions. Its native route is
`GET /api/workspace/process-interfaces/historical-results` with `session_id`,
`path` and `run_log_path`. It has no provider dependency or device monitoring.

This entry migration now has six passing served-workspace checks against an
isolated retained native engineering run: exact source selection, eleven saved
outputs, the original failure, editor return, history reopening and saved JSON
navigation. An explicit workflow URL takes precedence over restored active tabs;
other restored tabs cannot attach that workflow's history query. Both the initial
route failure and a subsequent test-selector failure remain in
`artifacts/process-interfaces/083/20261002-historical-result-navigation/`.
The original user workspace and installed distributions were not tested here.
The original prototype files and existing
mixed worktree changes are preserved. Demo endpoint implementations, vendor
startup restoration, client methods and repo-local automation remain retirement
debt; they are not removed or made independent by this checkpoint. T048/T049
remain incomplete until those active paths are retired and installed historical
navigation is verified.

### Operational caller retirement checkpoint, 2 October 2026

The source web client no longer exposes prototype preparation/status/dispatch/
retry/cancel methods or vendor status types. Its canonical image upload remains
as `uploadWorkflowImage`. The unused vendor page/style and three obsolete API
request models are removed. The Studio startup restoration hook is removed.
Eight operational API handlers are replaced by a hidden, inert HTTP 410
compatibility response directing users to the saved workflow/common working view.
The history adapter remains read-only and exact-source/run bound.

Original mixed/untracked prototype bytes are preserved in a private ignored
archive, with protected campaign/context checks retained. Fourteen API/history
checks and fourteen affected component tests pass; web TypeScript passes.
See [caller retirement evidence](../../specs/083-process-working-interfaces/evidence/prototype-caller-retirement.md).
Service modules, vendor scripts, transitive slicing bindings and fresh installed
history verification remain open T048/T049 work. Source retirement alone does
not establish their removal or the full migration.

### Device/Studio retirement checkpoint, 2 October 2026

Both prototype workspace-service modules and unused device/Studio setup,
transport and desktop automation scripts are removed after application caller
retirement. Their vendor-only test is retired with them; shared action/observation/
history authority is verified separately. Eighteen original files, including
mixed edits and untracked experiments, remain privately byte-preserved. No
configured provider or user run was mutated. The workspace owner no longer
imports or ships these two modules; aggregate/private/rebuilt-wheel checks pass.
Commands referring to removed scripts need qualified independent bindings;
their effects are not replayed or silently substituted.

This supersedes the historical inventory's two `print_part_demo` service rows
and device/Studio script rows. Dataset/jig slicing still has campaign/proof
dependencies. T048/T049 remain open for those dispositions, full replacement
proof and fresh installed history. See the [retirement evidence](../../specs/083-process-working-interfaces/evidence/prototype-caller-retirement.md).

Fresh installed native history now passes six read-only workspace/editor/file-tab
checks with the retired modules absent and eight inert compatibility replies.
Copied source/run/UI/continuation identities remain unchanged. The first launcher
and configuration failures are retained separately. Original user prototype
formats, transitive slicing and complete engineering replacement remain open;
T048/T049 are not complete. See [installed history evidence](../../specs/083-process-working-interfaces/evidence/installed-history-retirement.md).

### Original prototype compatibility checkpoint, 3 October 2026

The three actual original failed/completed pumpkin recorder formats are verified
through the shared historical adapter on an isolated current installed build.
Sixteen served workspace checks preserve exact results/errors, editor return,
read-only reopen and saved recorder/artifact tabs; eight retired URLs are inert.
Original and copied source/run/artifact/journal bytes and durable reviews remain
unchanged. Failed fixture/selector attempts are retained; source integrity was
not relaxed. See [original history compatibility](../../specs/083-process-working-interfaces/evidence/original-history-compatibility.md).
This qualifies those formats only. Active slicing wrappers and their transitive
campaign/probe bindings still require deliberate migration to existing independent
providers. T048/T049 remain open; historical campaign data and baseline bindings
remain immutable.

### Neutral example-helper extraction, 3 October 2026

The printing preparer's shared declaration/staging functions now live in
scripts/engineering_campaign_binding_helpers.py. Eleven other preparers and one
fixture load that file directly. Original function ASTs/preparation bodies and
campaign bindings remain unchanged; 74 focused/affected checks pass. The printed
preparer loads the exact file without an installed namespace assumption. Existing
AgentCAD guidance is metadata; no slicing/device implementation is relocated.
See [migration evidence](../../specs/083-process-working-interfaces/evidence/generality-and-migration.md#neutral-helper-extraction-before-slicer-retirement).

This removes transitive helper coupling before actual vendor slicing retirement.
The three slicing implementation rows, printed/drill-jig operation callers and
diagnostic remain debt. Original two-process digital UI/handoff/source-gate proof
now satisfies T045/T047; qualification, active retirement and final platform
acceptance retain their separate obligations.
