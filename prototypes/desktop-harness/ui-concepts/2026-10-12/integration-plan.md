# Shared Wright UI in agent desktop hosts

12 October 2026 — implementation in progress under the submitted goal, following
the user's review of the three [UI concepts](README.md).

## Current tasks and evidence

| Task | Current state | Next boundary |
| --- | --- | --- |
| R0 bounded research | Complete; six source-backed comparisons, five findings, three experiments and an uncoached task script | Actual user walkthrough remains pending |
| Native read-only panel | Implemented; SDK/resource and browser protocol checks pass; named 0.2.0 update explicitly approved and installed | Native rendering user-confirmed in fresh chat; next confined editing spike. Build/theme/resize/lifecycle remain open |
| Shared presentation and canvas | Implemented; one neutral graph palette, scoped controls, distinct Wright-shell accent; URL mode is explicitly browser presentation with Wright document tabs | Native binding only after observed host capabilities |
| Native editor | Local 0.3.0 candidate; shared canvas/source/layout save and conflict checks pass in a simulated host against real isolated storage | Specific live update approval, then actual Windows edit/save/reopen walkthrough |
| Compact authoring | Toolbar Add step popover, contextual bottom/right inspector, existing focus control and saved preferences retained | Final browser checks pass; native editing prototype can now be prepared; live write-tool update requires its specific approval |
| Run + review | Actual installed tools completed one text-only run with this conversation supplying reasoning; saved result verified and reopened through served Workflows. Offline common-view/MCP transport and declared-input component checks pass | Native working-view registration/permission qualification and actual declared checkpoint/gateway journey remain open |
| Wright/Hermes shell | Same shared controls/canvas; its own single chat visible by default; explicit saved collapse preferences retained | Live Hermes acceptance not claimed from mock regressions |
| Original examples | Fresh isolated copies and byte hashes verified; both original starter sources display/reopen through Workflows; no engineering runs | Image/slicer/printer and numeric analysis provider gates remain unmet |
| Candidate qualification | Focused frontend/backend/pilot checks, build and browser Workflows evidence recorded | Native lifecycle, actual zoom, usability and full end-to-end remain open |

See [implementation-evidence.md](implementation-evidence.md) for exact boundaries,
versions, reproducible commands, failures, images and remaining gaps. The installed native panel is experimental and read-only. A native editor candidate is prepared locally, but actual native editing, tabs, file handlers and automatic chat wakeup are not claimed. Use the existing browser experience only
with an explicit browser label. Do not add its source/process transport or
remove duplicate outer chrome until the native surface is qualified.

## Outcome and scope

Create/open a Wright workspace from the desktop conversation or Workflows entry;
create, edit and save a workflow; run it with the bound harness supplying its
reasoning; inspect results and answer declared checkpoints in the same durable
run. The three concepts become views of one application: Conversation + canvas,
Focused authoring, and Run + review.

Keep one shared workflow editor and working-view implementation. Adapt buttons,
forms, menus, frames, navigation and document hosting to the surrounding host.
For the OpenAI desktop harness, use its chat and real panel/tab facilities where
qualified. Wright owns the outer shell when using Hermes, so its old navigation
and styling may be simplified; preserving its exact old appearance is not a
requirement. Preserve useful functions, saved data and run behavior.

Start with OpenAI desktop and Wright/Hermes. Claude Desktop and OpenClaw are future
integration targets, not implementations or capability claims in this milestone.
This is a prototype, not a release, universal plugin framework or redesign of
Wright's execution system.

**Canvas decision — user confirmed 12 October 2026:** adopt the concepts' neutral
canvas styling consistently across all hosts. Implement that treatment once in
the shared Wright canvas, preserving its editing behavior, typed ports,
connection semantics and status meanings. Light/dark variants may change
luminance while retaining that common visual language. Host-specific styling
remains in surrounding controls and frames, not separate canvas skins. The
generated images are visual/layout references; their example values and graph
semantics are not requirements. This decision approves the visual direction,
not a claim of implemented or validated UI.

## Minimal separation

| Responsibility | Shared or host-specific | Owner |
| --- | --- | --- |
| Nodes, ports, links, graph editing, source drafts, validation, Undo/Redo and accepted save | Shared | Existing Wright canvas/editor and command system |
| Workflow toolbar, inspectors, input/results controls and common working view | Shared components with scoped theme tokens and responsive layout | Wright UI and existing public UI kit |
| Outer navigation, conversation, document tabs, focus/close events and host style signals | Small presentation-host integration | OpenAI desktop or Wright's own shell; later other qualified hosts |
| Authenticated delivery of exact source/process operations | Existing services, with a narrow host transport where necessary | Wright source services/process client; MCP wrappers delegate to them |
| Model, memory, agent/session behavior and bounded reasoning handoff | Separate agent-platform integration | Existing Hermes/OpenAI adapters and frozen session/run binding |
| Execution, allowed actions, gateway, reviews, evidence and recovery | Shared, unchanged authority | Wright backend |

Selecting a theme, moving a tab or changing presentation mode never selects a
model or rebinds a session. Opening a Hermes-bound run in another presentation
does not redirect it to OpenAI. Unsupported continuation is explicit; inspection
of saved records should remain available where authorized.

Use one small presentation interface in `apps/web`, adjacent to the existing
host adapter. It describes observed theme/viewport, whether the host supplies
chat and document presentation, and the supported open/focus/close/layout hooks.
Reuse existing navigation targets and process-view locators. Add an operation
only when the first integration uses it. Return unsupported capabilities
explicitly; do not infer them from a product name, query string or visual theme.

Compose this with current transport and agent interfaces. The existing
`DesktopHostAdapter` means Wright's own desktop IPC bridge; it must not be
silently repurposed to mean the OpenAI desktop app. Avoid a broad adapter that
combines tabs, filesystem access, authentication, models and workflow execution.
No new database, package publication, dependency injection container, plugin
registry, dynamically loaded skins or per-host copies of the editor.

## Existing code to reuse and limited changes

| Current component/boundary | Proposed treatment |
| --- | --- |
| `WorkflowRecoveryConcept.tsx`, `ReactFlowRecoveryCanvas.tsx`, `command-system.ts` | Keep graph/model/commands; extract or relocate toolbar, palette and inspector composition only as needed |
| `workflow-recovery.css` | Separate canvas visual tokens from host control tokens; replace inappropriate viewport assumptions with actual panel-size layout |
| `WorkspacePanel.tsx`, `WorkspaceLayout.tsx`, `AppShell.tsx` | Compose shared content with either Wright shell or external-host frame; retire scattered `desktopConversation` layout checks as the new boundary takes over |
| `packages/ui_kit` | Reuse controls and semantics; add a small theme mapping for surrounding controls, retaining accessible behavior |
| `services/host-adapter` | Retain browser/native I/O; add a small adjacent presentation boundary rather than expanding privileged filesystem APIs into every host |
| `process-workspace-tabs.ts`, `process-navigation.ts`, existing viewer/surface stores | Keep exact document/process/run locators and navigation validation; change who renders/opens the outer document frame |
| `packages/process_client`, `services/process-client.ts`, source/workspace services | Keep validated requests, scope, immutable references and uncertainty handling; supply narrowly scoped transport operations where required |
| `ProcessWorkspaceTab`, `CommonProcessView`, `ProcessInterfaceView` | Reuse working interactions and saved-interface fallback; change frame/theme/navigation composition |
| `process-presentation-host.ts` | Reuse origin/source/nonce checks and lifecycle; resolve allowlisted theme values from the actual presentation container, not only global document styles |
| Prototype `mcp_bridge.py` | Add the minimum UI resource/render entry and typed service wrappers required by the slice; no generic HTTP proxy or second executor |
| Current desktop reasoning-status work | Preserve explicit pending/unavailable states; supply status by the bound reasoning integration, independently of theme or layout |

The existing surface system hosts MCP apps *inside Wright*. That is useful
experience and reusable lifecycle code, but it is not already an outbound
integration that hosts Wright inside another desktop. Likewise, a successful
MCP tool call is not proof of panel rendering, native tabs or model wakeup.

## Styling and layout rules

Maintain two scoped sets of values: host controls/frame values and Wright canvas
values. Host font, control spacing, neutral colors, corners and focus treatment
map into shared controls. Apply the approved neutral canvas treatment through
shared Wright-owned graph node/port/edge/status tokens across every host.
Avoid global host CSS resets affecting graph contents. Canvas-associated dialogs
and port/relationship legends use the corresponding Wright semantics.

OpenAI documents MCP Apps host CSS variables and theme-change notifications.
Prefer those observed values with Wright defaults for missing values. Keep
OpenAI-specific extension calls at the boundary; use standard MCP Apps behavior
where available. Start with the existing Wright kit and token mapping. Add an
OpenAI component dependency only if an actual control cannot reasonably fit the
host using existing primitives; do not create complete competing widget stacks.

For Hermes, Wright controls its shell, so adopt the same compact information
architecture with a Wright theme. Keep its conversation/session/model controls
in that shell. Claude/OpenClaw should later need a presentation binding and
theme mapping, plus separately qualified reasoning integration where needed.

| Concept | Arrangement |
| --- | --- |
| Conversation + canvas | Host chat beside workflow; Add step popover; Inputs/Results controls; closable bottom inspector; collapsed run details |
| Focused authoring | Host-supported expanded work view; same canvas; right inspector only when enough width remains; chat recovered through host controls |
| Run + review | Same run and process; job inputs, results, observed progress and exact pending interactions; direct route back to workflow/block/evidence |

Responsive placement follows the **available panel width and height**, not a
Codex/Hermes name. Use a few measured breakpoints, not a docking framework.
At narrow/short sizes use a temporary inspector sheet and overflow secondary
commands while keeping Save/conflict state, readiness, Run and required actions
reachable. Preserve keyboard access, focus return and readable zoom.

In externally hosted mode, omit Wright's duplicate activity rail, chat and outer
document tabs. Keep Workflows/Create/Open and workspace selection discoverable.
Move provider bindings/permissions to Workspace Tools and settings to a compact
workspace menu. Native file/Git facilities can replace duplicate navigation only
when they address the same resources; vault results still use Wright's viewers
and exact artifact references. A native file save must still pass canonical
source validation/CAS rather than overwrite accepted workflow state blindly.

## Delivery sequence

### R0. Research integration patterns and customer experience

Complete the bounded [research task](integration-experience-research.md) before
substantial UI implementation. Review six to eight relevant integrations,
separate documented features from evidence of customer value, and examine how
people begin, maintain context, inspect results, handle waits and return to work.
Use the findings to refine the approved layouts, not simply confirm them.

**Exit:** a short evidence-backed comparison, up to five actionable findings,
an updated Wright journey and at most three small experiments. Track ease,
confidence, pleasantness and task completion alongside technical correctness.
The native-panel qualification below can proceed alongside research. A later
small user walkthrough checks the implemented slice; unavailable customer
evidence stays explicitly unverified rather than becoming an indefinite blocker.

### 0. Prove the native host surface before committing to its layout

Use the existing approved prototype connection to prepare one read-only MCP App
panel showing a real Wright workspace and saved workflow summary. Record the
actual Windows app build and GB10 runtime separately. Qualify resource rendering,
remote-host asset delivery, resizing, theme changes and a scoped read. Exercise
the proposed `.wflow` handler/document entry and determine what real open, focus,
close, restoration and dirty-document handling the host exposes.

Separately test whether an explicit user action in the panel can continue the
same conversation using a supported bridge. The current progress notes report
manual chat continuation; do not describe automatic multi-step operation as
solved. A `ui/message` capability does not by itself prove background wakeup or
unattended execution. Any live plugin update needs the exact minimal package
change and rollback, within the existing approval scope or separately approved
if that scope expands. No unrelated host setting changes.

**Exit:** a native panel screenshot and a short observed capability table. A
browser URL in a host tab is labelled browser hosting, not native plugin UI. If
only one panel is supported, propose a visible document picker/back navigation
inside it; do not draw counterfeit host tabs. If native hosting is unavailable,
report the precise gap and continue shared/Wright-shell work independently.

### 1. Separate the shared work surface and theme boundary

Introduce the small presentation interface and scoped token mapping. Implement
the Wright-shell binding using existing tabs/navigation and the qualified MCP
host binding using only demonstrated capabilities. Inject the minimum scoped
source/process calls needed by the shared content; do not monkey-patch global
fetch for the new host or expose unrestricted backend access through the UI.
Apply the concepts' neutral canvas surfaces, restrained borders and selection
treatment once in the shared renderer's styling; retain functional geometry,
readable port distinctions and the existing editing command behavior.

**Exit:** the same saved workflow renders through both compositions with the
same approved neutral graph appearance and preserved behavior; host controls
differ; switching themes or views changes no workflow source, run or agent
routing. This is separation work,
not a wholesale extraction of the large editor into new packages.

### 2. Deliver the smallest useful native editing journey

Create/open a workspace from native chat or Workflows, create/open its workflow,
display the existing canvas in the real panel, edit one input or block, Save,
close and reopen the same accepted source/layout. Add the compact toolbar,
Add step popover and bottom inspector from Concept 1. Expose Source/Side by side,
instructions, Undo/Redo, checks and readiness without recreating document tabs.

**Exit:** one chat, one real hosted work surface, actual saved edits and restored
layout through the normal Workflows entry. Reject an invalid edit and a stale
save without losing the accepted source or editable draft. If native per-document
tabs were qualified, demonstrate them here; otherwise explicitly label the
single-panel fallback and keep native multi-tab completion open.

This is the first useful end-to-end UI milestone; it does not need every run
dashboard, another theme engine or a new generated interface.

### 3. Connect the Run + review experience

Reuse common working-view controls and the process client for readiness/start,
progress, saved results, declared input/review and cancellation. Run a fresh
small permitted digital workflow with real desktop-conversation reasoning, a
Wright gateway operation and a declared checkpoint. Use the exact same run when
returning from the canvas or another document.

Show queued reasoning, waiting for chat, declared human input, review, failure,
disconnection, cancellation and unknown outcomes as different states. If an
explicit Continue in chat action is qualified, use it; otherwise retain the
honest manual instruction. No alternate model worker or hidden Hermes fallback.

**Exit:** actual result/evidence navigation and same-run continuation after panel
close/reopen. Changing the UI or closing its tab neither cancels the run nor
resubmits an action. Saved compatible process interfaces can use the same theme
bridge; the common view remains available. UI-generation capabilities previously
gated by tool isolation remain gated; this layout does not grant them authority.

### 4. Add focused editing and refresh the Wright/Hermes shell

Finish Concept 2 using the same editor and contextual inspector. Simplify
Wright's own navigation, document chrome and controls around the shared layouts.
It need not copy Codex's two left lists or preserve the old Hermes shell. Keep
one useful navigation structure for Wright's standalone context and preserve
chat, sessions, workspace tools, settings, files and results.

**Exit:** the main authoring and working journeys function in both actual
environments, with unchanged saved workflows and platform-bound sessions.
Retain the earlier Codex-inside-Wright chat pilot functionality; a shell refresh
does not remove it. Remove obsolete layout branches only once replaced and
verified, without keeping two permanent implementations of the editor.

### 5. Qualify the prototype and record the next host extension points

Use the shared checks below and fresh isolated manufacturing-preparation and
Robot Tracking Diagnosis copies. Preserve their original requirements, images,
input files, tool bindings and required evidence. Retain their separate provider
readiness gates; a UI smoke workflow or illustrative plot is not a completed
engineering demonstration. No physical action or protected campaign resumption.

Document the small host interface with the two working implementations. List
Claude Desktop and OpenClaw as unqualified until their actual builds, plugin
surfaces and reasoning routes are investigated. Do not build speculative
adapters now. Keep unsupported platforms explicit and existing stub behavior.

**Exit:** reviewable local candidate, actual-host capability/version matrix,
repeatable walkthrough and remaining limitations. Repository gates apply at
their appropriate integration stage; no push/merge/release is authorized here.

## Checks that matter

| Area | Evidence required |
| --- | --- |
| Shared canvas | Approved neutral canvas styling remains consistent under both host themes; compare with concept references while preserving create/configure, typed connection success/rejection, edge identity, drag, pan/zoom, Source/Side by side, invalid draft containment, Undo/Redo, saved layout/reopen and CAS conflict |
| Host presentation | Native panel versus browser hosting recorded separately; actual tabs where available; correct document identity/focus/restore; unsaved work preserved even if close interception is absent; no extra chat/tab strip |
| Theme and accessibility | Light/dark changes, token scoping, readable graph/port/status contrast, keyboard actions, inspector focus return, actual 200% zoom, typical Windows desktop and narrow panel sizes |
| Usability and experience | First-use and return-use task completion, time to useful result, help requests, repeated context entry, comprehension of current state/next action, and reported ease/confidence/pleasantness; distinguish expert review from customer observation |
| State and authority | Wrong workspace/revision denied; host UI capabilities grant no process permissions; checkpoint response, engineering review and external-action approval remain distinct |
| Lifecycle | Panel close/reload, host/MCP disconnect, backend restart, stale responses, duplicate starts/responses and unknown effect reconcile with original durable identities; never automatically replay an uncertain action |
| Reasoning separation | Correct bound harness, no model/session change from UI/theme changes; frozen config verified on continuation; waiting-for-chat distinct from review; no false streaming or completion from missing observations |
| Regression | Existing Hermes behavior, preserved Codex chat pilot and OpenClaw stub/Pi unavailable behavior; saved working-interface compatibility and common-view fallback |
| Generality | Same mechanisms used by isolated manufacturing preparation and Robot Tracking Diagnosis; missing provider qualifications remain visible, not replaced by weaker examples |

Reuse existing editor acceptance/capture scripts, targeted frontend tests,
process-navigation/client tests and relevant backend regressions. Verify the
served Workflows entry, not only a component or alternate route. Add boundary
tests for new behavior; avoid duplicating every test per host or pixel-testing
every button. Report GB10 browser checks and actual Windows desktop acceptance
separately. Preserve failed evidence alongside repaired continuations.

## Practical boundaries and delivery management

The isolated feature worktree is `/tmp/wright-host-adaptive-ui-prototype` on
`codex/host-adaptive-ui-prototype`, based at `c0769319`. The original worktree and
its dirty reasoning-progress/private-LAN work were preserved. Exact inherited
bytes were frozen privately and committed only in this isolated worktree as
`2d1e6c02`; `baseline.json` records the provenance. Keep subsequent changes small
in `WorkflowRecoveryConcept`, `WorkflowRecoveryPage` and `WorkspacePanel` to
avoid parallel rewrites. Reuse their completed work; keep the independent MCP
catalog/testing workstream separate. Use small milestone commits in the
prototype feature workstream; do not reset shared files or treat installed
Wright as the source baseline.

UI preferences (theme, inspector placement, selected view) remain presentation
state. Source/layout persistence keeps its existing owners. Runs keep their
frozen platform/model/instruction/tool configuration. Pure styling changes do
not invalidate engineering outputs; accepted source/input changes still do.
Saved UI bundles retain compatibility versions and common-view fallback.

At milestones 0, 2, 3 and 4, capture an actual desktop screenshot or short
recording with clean data, an honest caption and the exact demonstrated scope.
Suggested sequence: first native Wright panel; chat plus saved canvas edit;
declared checkpoint continued in the same run; same canvas in OpenAI and Hermes
with different surrounding controls. Concept art remains in its labelled gallery.
Do not publish externally.

## Sources, assumptions and decisions

Inspected current code listed above, repository AGENTS guidance, workflow UI
integration handoff, recovered editor north star, process UI design and platform
vision/refactoring guidance. `reasoning-progress.md` reports fresh native-tool
and browser run evidence plus the manual-turn limitation; those observations
were read, not rerun during this planning turn. Historical `plan.md` contains
pre-installation statements superseded by the native-plugin evidence.

Official OpenAI docs checked 12 October 2026:

- [MCP App UI](https://developers.openai.com/plugins/build/chatgpt-ui): standard
  bridge, capability detection, optional host extensions and separate state owners.
- [Plugin extensions](https://developers.openai.com/plugins/build/extensions):
  conversation panels and file viewer/editor entrypoints.
- [UI changelog](https://developers.openai.com/plugins/changelog): standardized
  host style variables and theme-change notifications, documented 28 May 2026.
- [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines):
  native control styling, fonts and accessibility.
- [UI support distinction](https://developers.openai.com/plugins/deploy/troubleshooting):
  shared tool support does not by itself establish all ChatGPT UI behavior in
  every Codex build/conversation mode.

No claim is made about current Claude Desktop or OpenClaw panel/tab support.
Their capability research belongs to their future integration slice. No model,
authentication, host settings or live workflow was changed by this plan.

Decisions: OpenAI first, Wright/Hermes second; adopt the concepts' neutral canvas
styling once across all hosts; adapt surrounding controls through tokens; prefer native document hosting;
qualify same-conversation continuation separately; keep future hosts out of this
implementation until a real integration need establishes their requirements.
The canvas visual choice is resolved by the user's explicit reply. A missing
native host capability may later require a concrete choice between a disclosed
single-panel/browser fallback and waiting for upstream support.
