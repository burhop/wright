# Wright engineering demos inside the OpenAI desktop harness

Updated 14 October 2026. **The user submitted the linked implementation goal;
M0 is in progress. Capability completion still requires the stated evidence.** In this
plan, “Codex” means the user's OpenAI desktop application, with execution on GB10
and the desktop UI on Windows. This is an experimental prototype.

This is the current forward plan. It extends the approved
[shared UI design](ui-concepts/2026-10-12/integration-plan.md) and replaces the
old delivery sequence, not its design decisions or historical evidence. Keep
the separate Codex-inside-Wright chat pilot. It is not the execution mechanism
for these desktop demonstrations.

## Current continuation checkpoint — 14 October 2026

Continue in `/tmp/wright-desktop-engineering-execution`, branch
`codex/desktop-engineering-execution`. Baseline PR 153 is merged to dev at
`a61361384a3de15163fdb0a6b6a3da56ad92e673`; its post-merge CI is now successful, including Windows frontend/backend and
ARM64/x64 engineering-image smoke/publication jobs (baseline-postmerge-ci.json). Historical baseline tables below retain their dated
planning context and are not current installation status.

Named plugin 0.8.0 is installed and protocol-verified. Its frozen runtime checkout
is `/tmp/wright-desktop-ui-files-candidate`; do not edit runtime files there.
Home now includes workspace creation/selection, Workflows, Connections, Files
metadata search, bounded read-only UTF-8 text preview and Recent runs. Browser-host checks do not establish Windows
native acceptance. The short `desktop-08-walkthrough.md` covers that outstanding
user observation. Installed engineering execution/image input remain gated.

The separate execution checkout has an off-by-default exact-enrollment MCP-task
qualification profile. Its boundary and existing policy-owner suites pass 76
checks. A fresh actual MCP/HTTP/runtime/gateway run completed with a desktop-authored
inspection proposal and completion, one observed gateway dispatch, unchanged
input, and an explicit no-enrollment denial. This exercises the new profile with
its old confined-inspection flag disabled; it does not establish arbitrary
engineering providers or replace the required SteveCAD demonstrations.
See `workspace-home-progress.md` for exact receipts and remaining limits.

Existing SteveCAD account/terms setup is confirmed. The Windows-to-GB10 callback
route and interactive sign-in still need qualification. Required image perception,
CAD/direct-tool/export paths, genuine reviews and the multi-tool engineering
runs remain open. Keep independent implementation moving while waiting on login.

### Priorities that keep this practical

1. **Finish and expose the existing home slice.** Qualify workspace selection,
   workflow open, Back, draft protection and narrow-panel rendering. Do not
   rebuild these features because they are absent from the installed version.
2. **Connect a real engineering workspace.** Add Connections using existing
   catalog, custom-server, authentication, health and grant owners. Show a simple
   summary (Connected / Sign in / Setup needed / Unavailable), with technical
   details on demand. Provider installation and workflow permission are separate.
   Preserve the exact return destination through sign-in and setup.
3. **Finish one engineering journey.** Prioritize the reasoning/action and
   artifact paths required by the existing SteveCAD native workflow, then prove
   four-hole and six-hole runs. Do this before broad settings or Git parity.
4. **Make returning and reviewing effortless.** Add recent runs, files/results,
   declared reviews and explicit same-run continuation. Include required file
   inputs and result previews in the first slice when its workflow needs them;
   they must not wait for a later cosmetic management milestone.
5. **Demonstrate the connected engineering chain.** Complete the existing
   SteveCAD/OASiS comparison with exact handoffs and genuine decisions, then
   finish remaining routine management and the affected-platform regressions.

These priorities refine M0–M3 sequencing, not their engineering requirements or
completion criteria. A login or real review can pause its dependent path while
unrelated implementation continues. Do not turn an external wait into another
architecture project.

### Concrete host presentation decisions

- One desktop conversation supplies reasoning. Wright home contains Workflows,
  Connections, Files and Recent runs; workspace selection stays visible. Keep
  engineering names in the main view and identifiers in optional diagnostics.
- Use the same editor, neutral canvas and process/result components in each
  harness. Keep only theme, placement, navigation and host file/conversation
  hooks in the existing presentation adapter. Hermes may use a different shell;
  future harnesses do not need speculative implementations now.
- Prefer a documented conversation entry and supported file handler. Test a
  sidebar entry only to improve discoverability. Native document tabs require
  actual Windows proof; otherwise retain one panel with selection and Back.
- Panel actions have clear loading, success, waiting and failure states. Use one
  obvious next action, preserve unsaved edits, and return from Connections or an
  evidence viewer to the exact source/run. Opening a view never executes work.
- Model selection and general chat controls belong to the host. Wright settings
  cover its workspace, connections, process instructions and diagnostics. Do not
  offer controls that pretend to alter unobservable host settings.
- Use host-provided theme values and shared components first. Do not add another
  UI library or styling framework merely to imitate the host. Verify keyboard,
  focus, dark/light themes, resize and zoom in the actual desktop.

Official [extensions](https://developers.openai.com/plugins/build/extensions),
[UI guidance](https://developers.openai.com/plugins/concepts/ui-guidelines) and
[bridge reference](https://developers.openai.com/plugins/reference) were reopened
for this review. They document integration choices, not availability in this
particular Windows build. Optional file helpers require feature detection.
Computer use may assist testing if available; it is not a required engineering
execution path. Keep browser proof, native-host proof and user acceptance separate.

Use the short [continuation prompt](demo-readiness-next-goal.md) with the existing
[full execution scope](demo-readiness-goal.md). No new goal is necessary in the
current thread: its implementation goal is already active.

## Installed checkpoint — 15 October 2026

0.9.0 is installed and actual package/protocol checks pass. The separate local
review capability now works without enabling general MCP tasks. It still requires
exact authorized manual enrollment; it is not a general workflow-authority grant.
The private test used one actual desktop answer, rejected a stale subject,
reconnected and completed the same run after explicit Continue. See
[final candidate evidence](local-review-candidate-final-evidence.json),
[installation](installed-09-evidence.json) and [walkthrough](desktop-09-walkthrough.md).

Next actions, in order of useful available work:

1. Finish the live d070e351 repository gate, retain the actual WebKit host exception,
   run the required pre-push gate and prepare the first coherent integration PR.
   Attribute the separate 0.9 descendant checks explicitly; do not claim they
   were part of an earlier full gate.
2. Verify 0.9 in a fresh Windows desktop conversation. This existing conversation
   still reports an older binding. Keep native acceptance distinct from browser
   fixture and installed-command tests.
3. Complete the Windows-to-GB10 callback test using the discovered
   `promaxgb10-9666` alias, then the existing account's genuine SteveCAD sign-in.
   No account, callback or token substitution. The prepared Windows handoff stays
   actionable; this chat has no callable Windows shell or port-forward control.
4. Continue the original four-hole/six-hole SteveCAD and multi-tool demonstration
   requirements. Qualify the required engineering task/image profiles separately;
   local review support does not enable them.

The synthetic local-review proof does not satisfy the engineering demonstrations.
Remaining management gaps, real reviews, different-workflow regressions and
platform-specific acceptance retain their original scope below.

## Outcome and recommended approach

A user can stay in Codex to select or create a Wright workspace, connect its
engineering tools, create/open a workflow, supply inputs, run it, respond to
declared questions and reviews, and inspect actual engineering deliverables.
Returning later finds the same source, run, outputs and pending decisions.
The desktop conversation provides the LLM; Wright remains the process executor.

Extend the existing plugin, shared editor, process client and presentation
adapter. Add a compact Wright home and scoped management operations, then
qualify the missing engineering execution paths. Do not build a second desktop
shell, second chat, new workflow executor, or general host/plugin framework.
Do not require parity with every advanced Wright screen before the first useful
demo. Routine workspace, connection, workflow, run and file management are in
scope; genuinely unsupported functions stay visible and actionable.

## Baseline: implemented is different from demonstrated

| Boundary | Status checked for this planning update |
| --- | --- |
| Main GB10 checkout | `dev` at `c1a8d00942d8a80ca6229ebed23d7b8f4153a7d9`; existing untracked workflow copies and private state preserved |
| Integration candidate | `codex/stevecad-ui-rebase`, `7035cf029aa988f411c6ab4e39bcc93315a27e3d`; [PR 153](https://github.com/burhop/wright/pull/153) is open/draft, not merged |
| Installed plugin | Approved `wright-desktop-gb10-prototype` 0.4.0, using its retained isolated target; proposed 0.5.0 candidate is not installed |
| Native UI | User confirmed a Wright panel and completed the 0.4 walkthrough, reporting small bugs. This is not exhaustive Windows acceptance; detailed annotations remain needed |
| Run support | Text reasoning, declared inputs and an exactly enrolled read-only file inspection have bounded evidence. General CAD/application/MCP/image paths are explicitly gated |
| Recovery | Same-run observation, waits and some reconnect/cancel paths are checked. Automatic pending-task resurrection/background desktop wakeup is not qualified |
| SteveCAD | Examples are in `dev`; prior engineering evidence comes from other runs/hosts. GB10 credentials/provider readiness and new desktop-driven executions are not established |
| CI | Latest PR cycle is terminal: Windows backend passed; Windows frontend and aggregate CodeQL failed. Other reported required jobs passed, including hosted WebKit. Do not treat a draft/red PR as an integrated baseline |

Recheck these facts when implementation starts. The installed `wright` command,
CLI version, browser login, and Git branch name do not establish the loaded
desktop plugin, GUI build, backend source, model, or authenticated MCP account.

## User experience and current host capabilities

Use the existing desktop conversation and one Wright entry beside it. Start with
a conversation panel; qualify a persistent sidebar entry only if it materially
improves returning to work. Do not add another permanent left activity rail.

The panel opens a workspace picker and a short home view: **Workflows,
Connections, Files, Recent runs**. Workspace settings live in its compact menu.
An open workflow exposes **Edit / Run / Results** and contextual inspectors;
these are views of the same process, not separate applications. Keep the approved
neutral canvas across all hosts. Map host colors, spacing, focus, typography and
theme changes into Wright's surrounding controls.

Use actual host document tabs/file handlers when the installed app supports the
needed lifecycle. Otherwise use one panel with a document selector and Back;
do not imitate native tabs or add a competing outer tab strip. Browser-hosted
administration may be a temporary, clearly labeled fallback, but does not count
as a completed native management journey. No ordinary task should require a
user to copy run IDs, URLs, tokens, filesystem paths or terminal commands.

Show the current workspace and exact document/run context in readable form.
Changing workspace or model defaults must not redirect an open document, pending
operation or existing run. Preserve drafts, save conflicts and exact return
targets when opening Connections, answering a review, or inspecting evidence.
Errors offer a specific next action; unknown readiness is not an empty successful
list. “Continue in chat” is an explicit user action with acknowledgement, not a
claim that the desktop can wake or run unattended.

| Official capability | Consequence for Wright |
| --- | --- |
| [Conversation panels, sidebar/settings extensions, file handlers and deep links](https://developers.openai.com/plugins/build/extensions) are documented | Prefer supported host entry points; verify registration, remote asset access, tabs, file scope and restoration on this actual Windows build before depending on them |
| [MCP Apps UI](https://developers.openai.com/plugins/build/chatgpt-ui) documents resource-backed views, bridge operations and feature detection | Extend the existing resource/transport. Keep data mutations separate from opening/rendering so saving does not remount and lose drafts |
| [UI reference](https://developers.openai.com/plugins/reference) describes host navigation and UI state | Host state holds presentation intent only. Wright owns durable source/run state; a history API is not proof of native multi-tab support |
| [Desktop browser](https://learn.chatgpt.com/docs/browser) supports tabs and annotation | Use annotation to fix the reported UI bugs against the actual served build. Browser success does not establish native-panel success |
| [Computer Use](https://learn.chatgpt.com/docs/computer-use) is documented for Windows and macOS, subject to installation and permissions | Optional assistance for visual testing on Windows. It is not currently proven available to this chat and is not a required Wright executor or replacement for engineering MCPs |
| [MCP Events](https://developers.openai.com/plugins/build/mcp-events) documents a limited host/deployment scope | It does not establish wakeup support for this local GB10-backed conversation. Do not add cloud infrastructure or promise unattended execution to work around that gap |

These sources were checked on 14 October 2026. Documented extension support is
not proof of availability in every product build. Reuse the existing bounded
[integration research](ui-concepts/2026-10-12/research-findings.md); it suggests
design choices, not measured customer satisfaction. The next evidence should
come from an observed user journey, not another broad research project.

## Functionality to expose

“Partial” below refers to the desktop integration, not the maturity of Wright's
existing backend. Management operations reuse existing authorization and services.

| Wright functionality | Desktop now | Work in this goal |
| --- | --- | --- |
| Workspace create/open/select | Chat create and explicit reopen; no complete picker | List/create/select/reopen, current identity, normal settings and existing safe archive/delete behavior where supported; preserve other workspaces |
| MCP discovery and setup | Native management missing | Search existing catalog, inspect requirements, add catalog/custom existing server, use normal installation/OAuth/credential flows, test readiness, enable/grant per workspace |
| MCP lifecycle and permissions | Native management missing | Show scope, health, schemas and actionable failure; expose existing edit/update/disable/remove operations with their normal safeguards. Do not build new MCP providers or silently change live connections |
| Workflow library and authoring | Shared editor exists; discovery incomplete | Browse/create/templates/open/save/rename/delete using existing services; retain source, typed connections, instructions, layout, Undo/Redo and conflicts |
| Workflow bundles | Native import/export missing | Add existing portable bundle import/export and dependency diagnostics; never transfer credentials, live runs or approval authority |
| Inputs and readiness | Bounded text/checkpoint support | Bind actual workspace files, tools and models; diagnose all predictable prerequisites before starting; restore exact workflow after setup |
| Engineering execution | General MCP, CAD, application and image paths gated | Qualify required task types through existing dispatch and gateway; all LLM/helper calls use the bound desktop conversation, with no Hermes or headless-model fallback |
| Working views, questions and reviews | Common view/input slice partial; engineering reviews gated | Reuse common view and compatible saved UI where qualified; expose real input, review and permitted-action contracts separately, with exact evidence and subjects |
| Runs and recovery | Exact run view/cancel/reconcile partial | Recent/history list, explicit continuation, truthful terminal states, same-run reconnect/restart handling; uncertain effects require reconciliation, never automatic replay |
| Files and engineering results | Limited text results; native file management missing | Existing upload/download/browse, CAD/image/document/numerical viewers, exact artifact and producer links; safe download/details fallback for unsupported formats |
| Model, instructions, diagnostics | Desktop binding has limited provenance | Show actual readiness, saved instruction assets and frozen binding, existing Wright settings/diagnostics where relevant. Desktop owns its chat/model controls; unreported model revision/usage stays unreported |
| Git/project utilities | Not integrated as Wright functions | Reuse host facilities only where they address the same repository; otherwise offer existing scoped Wright status/history/diff. Git administration is not a demo prerequisite |
| AI-created working UI | Gated for this harness | Keep scoped/no-tools authoring gated until enforceable; shared common view must remain usable. Reusing an already compatible saved UI is a separate capability |
| Hermes, Claude Desktop, OpenClaw | Hermes has its own shell; future integrations unqualified | Regress shared Hermes functionality and preserve existing stubs/unavailable states. Implement no speculative Claude/OpenClaw adapters |

Installing a server in Codex does not enroll it in Wright or grant a workflow
permission to use it. Connection administration is an operator capability,
separate from the tools offered to a running workflow's reasoning task.

## Architecture and ownership

| Reuse | Limited extension |
| --- | --- |
| `process-presentation-host.ts`, desktop panel entries and existing navigation locators | Observed host capabilities, theme mapping, scoped home/navigation and qualified native document entry |
| Shared editor/command system, `packages/ui_kit`, process/common views and result viewers | Compact composition and missing management/results views; no second canvas or duplicate business logic |
| `packages/process_client`, native source/process transports, prototype MCP bridge | Explicit typed operation allowlist calling existing owners; no generic REST proxy, shell tool or unrestricted `invokeTool` |
| Existing workspace, MCP registry/onboarding/gateway, settings, bundle and artifact services | Expose authorized operator operations; keep secrets on the owning host and preserve current validation/grant enforcement |
| `desktop_reasoning.py`, existing dispatch factory and durable handoff receipts | Qualify response/action/helper/image paths and continuation without a second scheduler or independent job-status authority |
| Canonical source executor, validators, result recorder, reviews and recovery | Preserve bounded decisions, exact subjects, declared waits, currentness and permitted actions |

Freeze source, inputs, platform/connection, requested model, confirmed routing
where observable, runtime/client versions, instruction hashes, tool schemas,
grants and relevant settings before execution. Verify them on continuation.
Record requests/replies, helper calls, gateway dispatch and observed outputs at
their actual Wright boundaries. Do not claim the desktop's hidden prompts,
internal memory, model revision, costs or native-tool activity as observed facts.

The desktop retains its ordinary tools. Wright may enforce its own gateway,
state and acceptance boundaries; that does not make the desktop globally
tool-free. This goal proposes qualification of the separate desktop reasoning
bridge for bounded digital engineering. It does **not** waive a required
no-tools contract, enable the earlier embedded workflow adapter by exception,
or enable confined UI authoring. If a task requires confinement that cannot be
enforced, leave that capability blocked and report the precise dependency.

Backend identities remain authoritative: workspace + accepted source revision,
run + step + request/interaction, exact artifact bytes and review/action subject.
Changed required bindings invalidate continuation or saved-UI compatibility;
layout/theme changes do not grant authority or invalidate engineering evidence.
Closing/reopening a panel only reconciles observation. It does not start, approve,
cancel or repeat work. Model proposals cannot grant themselves tool permissions.

## Delivery and exit checks

### M0 — Clean baseline and resolve the risky dependencies first

Finish the existing PR's narrow Windows fixture and generated-bundle CodeQL
issues through repository gates, without weakening security checks. Prefer
merging that baseline before creating `codex/desktop-engineering-demos` from
fresh remote `dev`. If blocked externally, isolate follow-on work and document
its dependency; do not bury the new feature in unrelated fixes to PR 153.

Record installed plugin/backend/GUI identities and preserve all current worktrees,
state, evidence and services. Time-box the initial host tests to one concrete
experiment per uncertainty: native navigation/file lifecycle; user-triggered
return to the same chat; desktop-driven bounded action through Wright; binary
image/artifact handoff; headless SteveCAD authentication using its existing recipe.
Stop an unsuccessful experiment with an explicit capability result; continue
independent work. No new general framework, runtime fork or cloud service.

**Exit:** honest capability table, scoped connection plan and live positive and
negative controls for the first required engineering path. Readiness catches
unavailable paths; no general task gate is simply removed to obtain a pass.

### M1 — First useful end-to-end desktop slice

Implement the home/workspace picker, workflow library and the connection/file
operations needed for one existing engineering process. Extend the durable
desktop handoff and gateway only for the task types actually required.

Use a fresh isolated copy of
[`prompt-to-reviewed-cad`](../../examples/stevecad-demonstrations/prompt-to-reviewed-cad/README.md):
create/select workspace → connect required existing providers → open accepted
workflow → supply the clarified four-hole prompt → check readiness → execute
through the desktop conversation → inspect CAD, captures, documents and exact
checks → handle the genuine review state. Then supply the six-hole input to the
same accepted source and verify different measured outputs and separate run files.

The current native-render source includes a prospective camera correction; its
full new run is not already proven. Preserve original instructions, requirements
and validation. A revision needed for a genuine correction is visible, reviewed
and requalified; do not simplify the workflow to pass. Native rendering avoids
requiring an unchosen image-generation billing route, but still needs qualified
file/image transport and all original native-workflow task types.

**Exit:** a real engineering result from normal desktop controls and conversation,
not a text fixture or shell-driven demonstration. Capture the first useful
screenshot here. A required human decision may legitimately keep a run waiting;
do not label it completed until its accepted process actually finishes.

### M2 — Routine management, trustworthy runs and usable results

Complete the routine workspace/connection lifecycle, file input/results, bundle,
settings and run-history rows above. Prefer existing forms and owners. Finish
review/permission distinctions, same-run continuation, cancellation, conflict,
restart and uncertain-outcome handling before offering the corresponding controls.

Run a Windows annotation session against the actual installed panel and served
Workflows entry; convert observations into a short bug list and fix navigation,
focus, sizing, text, loading and error problems. Verify light/dark, narrow panels,
keyboard and zoom. Do not hide missing backend capabilities behind attractive UI.

**Exit:** returning to an existing workspace/run needs no copied identifiers;
connection fixes return to the original task; opening results does not execute;
ordinary authoring capabilities remain intact in both desktop and Wright shells.

### M3 — Complete multi-tool engineering demonstration and integration

Prefer a fresh copy of the existing
[`SteveCAD heat-spreader comparison`](../../examples/stevecad-demonstrations/heat-spreader/README.md)
as the flagship: editable CAD → exact STEP/dimensions → OASiS/scikit-fem coarse
and refined analysis → independent checks → comparison and genuine reviews.
Bring required preparation steps into the normal workspace journey using the
existing preparation owners. Do not silently prepopulate results off camera.

Keep the original 40/60 mm, 4 W assignment, limits, synthetic constants and full
082 validation. Clearly label dimensional idealization rather than arbitrary
STEP meshing or validated device physics. Original waiting reviews and evidence
are protected; use new source/run/output identities and real decisions for the
new demonstration. Never invent critic results or turn an integration-test
decision into engineering acceptance.

Also exercise fresh Robot Tracking Diagnosis copies to prove changed shared
mechanisms on a substantially different existing workflow. Retain the original
manufacturing-preparation regression obligation for affected paths, digital only.
Robot Tracking Diagnosis is a useful regression, not a substitute for the
multi-tool engineering demonstration. A blocked provider is reported honestly;
changing the chosen flagship requires a concrete alternative meeting the same
engineering criteria, not a generic file-processing demo.

**Exit:** repeatable real desktop walkthrough through the required engineering
stages and genuine decisions, exact artifact handoffs, affected platform gates,
evidence-backed limitations, reviewable commits/PR, and annotated screenshots.
Retain failed and waiting attempts honestly; engineering acceptance must never
be fabricated to complete the software goal. The goal is not complete merely
because code/tests pass while its required live journey remains blocked.
Record that state and the exact input needed.

## Validation and practical success measures

- Prove success plus missing credentials/tools/model/image support before start;
  denied permission, stale schema/grant, malformed proposals and cross-workspace
  requests must not execute. Administration is never a workflow self-grant.
- Test duplicate clicks, lost acknowledgements, chat/panel disconnect, restart at
  an input/review wait and during pending reasoning, cancellation and late replies.
  Unknown tool outcome must show reconciliation with no automatic repeat.
- Check source/input/instruction/model/runtime/tool drift on continuation. Keep
  old results and reviews tied to their exact bytes; save conflicts preserve drafts.
- Verify real CAD/image/file handoff, result currentness, review-to-evidence links,
  import/export exclusions and saved-UI compatibility/common-view fallback.
- Exercise the normal served Workflows control and the actual Windows native
  panel separately. Browser mocks and GB10 tests cannot establish Windows UI
  acceptance. Qualify Linux ARM64/x64, Windows and Docker at their real boundaries;
  preserve the documented GB10 WebKit startup limitation and hosted evidence.
- Regress Hermes, the preserved embedded chat pilot, OpenClaw stub/Pi unavailable
  behavior and changed common mechanisms. Run current dev push/merge gates; do
  not repeatedly rerun unchanged suites after passing without a reason.
- Observe time to first workflow/result, unassisted completion, manual ID/URL or
  terminal workarounds, recovery success, and a brief ease/confidence rating.
  Aim for zero identifier copying and hidden developer setup in the demonstrated
  journey; record actual observations rather than invent customer metrics.

## Decisions, limits and approval scope for the proposed goal

The recommended defaults need no new design questionnaire: one conversation,
compact contextual Wright UI, shared neutral canvas, existing services, ordinary
desktop reasoning, scoped digital effects, and a multi-tool engineering demo.
Native tabs and background wakeup remain capability tests, not promises.

Implementation will still need the user's account login/consent if no suitable
SteveCAD authorization exists, a billing choice before any new paid route, real
engineering decisions at declared reviews, and Windows observation if the host
cannot be controlled from GB10. Continue independent work while waiting.

The submitted goal grants **explicit ongoing authorization for updates only
to `wright-desktop-gb10-prototype`**, after candidate validation, exact change and
rollback preparation, using isolated demo state. This avoids asking for each
version again. It does not authorize other desktop settings, app upgrades or
restarts, unrelated connections, production data, or protected engineering runs.
The submitted goal also authorizes feature-branch PR integration to `dev`
through its gates; no release/main merge or physical effects. These permissions do not constitute qualification; each action must satisfy
the submitted goal and recorded candidate checks.

Keep generated UI authoring, guaranteed global native-tool confinement,
unattended desktop wakeup, unobserved cost/model attestations, new host adapters
and product-wide visual redesign out of the completion claim until separately
supported. No universal abstraction, new database, parallel scheduler, vendor
MCP implementation or speculative capability scaffolding is needed.

## Evidence and next-work index

- [M0 baseline correction](ui-concepts/2026-10-12/baseline-correction-20261014.md):
  current CI classification, scoped corrections and qualification status.

- [Ready-to-submit goal](demo-readiness-goal.md): execution scope and acceptance.
- [Current task record](tasks.md): next milestones and retained historical checks.
- [Approved shared UI plan](ui-concepts/2026-10-12/integration-plan.md),
  [research findings](ui-concepts/2026-10-12/research-findings.md), and
  [UI evidence](ui-concepts/2026-10-12/implementation-evidence.md).
- [Merge candidate](ui-concepts/2026-10-12/merge-candidate-20261013.md),
  [source rebase](ui-concepts/2026-10-12/source-rebase-20261013.md),
  [GB10 qualification](ui-concepts/2026-10-12/gb10-merge-qualification.md), and
  [uninstalled update proposal](ui-concepts/2026-10-12/native-merge-update.md).
- [Historical capability evidence](capabilities.md) is date-scoped; do not read
  its early uninstalled status as the current installation state.

During implementation, extend this index with exact source/package/host identities,
commands, pass/fail boundaries, artifact hashes and a short bug/status record.
Keep private credential material outside the repository. At M1, M2 and M3 save
real screenshots, short factual captions and a suggested 60–90 second demo
sequence. Clearly label concept images, test fixtures and waiting/unverified
engineering states. Prepare social content for review; do not publish it.
