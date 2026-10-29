# Wright engineering journeys inside the OpenAI desktop harness

**Recorded:** 28 October 2026. **Status:** implementation goal submitted on 28 October.
Local implementation, isolated digital qualification, focused commits, repository
gates, feature push and draft PR are authorized. A locally qualified update to only
the named desktop prototype is authorized. Merge, release, physical operations,
protected campaigns and independent Windows-pilot changes are excluded. Personal
consent and engineering reviews remain user actions. No product acceptance is claimed.

**Next-session entry point:** read this document and the
[checkpoint](https://github.com/burhop/wright/blob/codex/desktop-usability-journeys/prototypes/desktop-harness/evidence/checkpoint-20261028/README.md).
Preserve the implementation, failures, screenshots and engineering evidence from
the first attempt. Start the next goal from the reviewed journeys below.

## Outcome and scope

An engineer working in the OpenAI desktop harness can configure engineering tools,
create a workspace, describe a job, create and edit its workflow, run it, inspect
each step and its outputs, revise the process or inputs, run it again, and obtain
clear usable results. The user calls this host “Codex”; this means the desktop
harness and its conversation, not an independent Codex CLI worker or Codex Cloud.

This work concerns the **Codex experience**, including the purpose, placement,
wording and behavior of individual controls. Preserve Wright's shared editor,
viewers, backend, saved workflows and durable runs. Hermes provides an experience
to learn from and a regression target; it does not need a parallel redesign here.
Keep future hosts possible through the existing small presentation boundary.

The [platform vision](workflow-platform-vision.md), [process UI design](process-apps.md),
[refactoring plan](../architecture/workflow-platform-refactoring-plan.md),
[instruction plan](../architecture/workflow-instructions-and-interactions-plan.md)
and [editor integration guidance](../contributing/workflow-ui-integration.md)
remain authoritative. Apply V1–V7. The handle is a reference job, not a mandatory
lifecycle for PCB, CFD, research or other workflows.

## User decisions captured in this discussion

- Wright setup manages independently provided MCP tools, including adding,
  connecting, changing, updating and removing them.
- A workspace holds workflows, reference images/documents and engineering outputs.
  By default, include the MCPs already loaded into Wright in its tool selection.
  Their actual readiness and existing authority still apply; selection does not
  grant additional tool permissions or authorize a physical operation.
- A workflow is a reusable program. A run is one recorded execution of a specific
  workflow revision with specific inputs. Editing the process and changing run
  inputs are distinct operations; both must be understandable.
- Users must be able to rerun the whole process. Preserve prior runs and their
  results; affected old checks and approvals cannot authorize changed work.
- Users need clear inputs, easy inspection of every step's work and outputs, and
  useful final results. Raw JSON, UUIDs and protocol language belong in details.
- Use the host's conversation and native document tabs where qualified. Keep
  Wright's common canvas appearance across hosts; adapt surrounding controls.
- Reuse compatible viewers, including external open-source viewers where needed.
  Do not build a new CAD-viewer suite under this UI work.

## Lessons from the first attempt

| Observed mistake | Rule for the next attempt | How to detect recurrence |
|---|---|---|
| Inspection/recovery of a retained block stood in for creating a new design | Define each journey's starting knowledge, inputs and outcome | A new-design story must not demand an existing CAD document |
| Functional controls accumulated without a coherent route | Every visible control must serve an identified task in the current state | Explain its purpose, next state and return path in the screen specification |
| Huge lists, repeated descriptions and technical identifiers dominated | Use concise names, contextual detail and purposeful lists/viewers | Review populated and empty screens at actual panel widths |
| Workspace selection, files, settings and workflow work competed on one screen | Separate choosing a workspace from working inside it | The tester can state their workspace and next action without coaching |
| Switching between panel and chat was implicit | Specify both entry routes and every chat/panel handoff | The tester knows where to enter a request and what it applies to |
| Selected controls looked disabled; Run and results obscured execution | Distinct selected/disabled styling and action-specific labels | Tester can identify the active view, start action and blocking reason |
| Opening a file lost context or placed the preview offscreen | Make the viewer visible and return to the same step/run | Open output, inspect producer, return, and verify identity and viewport |
| Generic JSON was treated as the engineering result | Present appropriate engineering summaries, plots, models and units | Tester can explain the outcome and limitations without reading raw JSON |
| Missing run context looked like missing outputs or a source mismatch | Distinguish draft, saved definition and selected historical run | Correct results on matching source; real source mismatch still detected |
| Unrestricted browser tests missed host image/download restrictions | Exercise actual SDK delivery and restrictive fixtures, then actual host | Keep simulated-host and Windows observations separate |
| Installed candidate and mounted old panels were confused | Record the served resource/build and actual mounted observation | An old panel cannot qualify a new build; avoid repeated identical tabs |
| Guided button-click tests passed while the experience remained confusing | Include task-only usability checks with no navigation hints | Record wrong turns, assistance and unclear outcomes, not just test counts |
| Repeated investigations, micro-installs and plan files obscured progress | One current plan, one backlog and a coherent candidate per reviewed slice | Link every change to a story, evidence and the exact candidate |

## Story map: engineering work first

All stories need a normal route, relevant failure/empty/waiting states, clear
outcome and a next action. Installation/connection, workspace access, execution
readiness, engineering review and physical-action authorization remain distinct.

| ID | User story | Observable acceptance |
|---|---|---|
| C01 | Set up and maintain my engineering tools | Find/add a tool, connect it, see current status, update/reconnect/replace/remove with affected-workflow impact visible. No silent substitution or surprise permission grant. |
| C02 | Create or reopen the workspace for my job | A simple chooser/name entry, or a chat request, leads to the same workspace. Loaded tools are selected by default; exceptions are clear. Files and tool selection are accessible without cluttering the task. |
| C03 | Turn my intent and references into an editable workflow | Chat request plus attached inputs produces understandable steps and dependencies. AI can propose documented assumptions and a declared review. No new-design request requires an already-created output. |
| C04 | Run the prepared workflow and respond when needed | Explicit start, specific readiness problems, visible progress and planned review/input points. Bounded correction and failure are understandable. Closing a view never starts, cancels or retries work. |
| C05 | Understand what any step did | Select a block/result to see its actual inputs, engineering tool, relevant instructions, outputs and findings for the selected run; open a suitable viewer and return to that run. |
| C06 | Change the requirements or process and run it again | Edit inputs or workflow, see revision/impact, start a new full run, retain the old run, repeat affected checks/reviews, and distinguish or compare the results. |
| C07 | Obtain usable results | Engineering previews, dimensions, plots/checks and limitations are easy to find. Files open visibly and downloads report an observable outcome. Technical records remain inspectable. |
| C08 | Return after closing, interruption or failure | Reopen the same workspace/workflow/run, see actual state and available recovery. Resume a waiting run and start a new run are distinct; uncertain effects are never replayed automatically. |

Use the existing export/import mechanism as an additional C03/C06 case: portable
workflow instructions/dependencies survive; credentials, live runs and approval
authority do not transfer. Do not expand the first slice into a new sharing system.

## Primary walkthrough: replacement handle with strength analysis

Starting point: Wright has selected CAD, FEA and printing MCP tools. The engineer
has reference images and a rough goal, not a finished CAD document or complete
specification. The request is: “Create a 3D printed replacement handle from these
images. Analyze its strength so I can assess whether it will withstand use.”

1. Create/select the workspace through a simple UI or an explicit chat request.
   Both routes establish visible destination context. Default its tool selection
   as agreed; make unavailable tools actionable rather than silently ready.
2. Attach images and enter the goal in the existing Codex conversation. A UI-first
   route explicitly directs the next interaction; it must not require guessing
   that conversation is elsewhere or introduce a second Wright chat box.
3. AI proposes an editable workflow whose inputs include the request and images.
   Its specification step identifies dimensions, mounting/hole sizes, loads,
   material and acceptance criteria, distinguishing supplied facts from proposed
   assumptions. Images alone do not establish scale or strength.
4. A declared user review presents the design document and assumptions. Approval
   applies to that revision. Corrections return to the relevant inputs/specification
   and present the revised document for review.
5. The CAD step consumes the approved specification and produces actual model and
   exchange files through the configured provider. The CAD document is an output.
6. Verification consumes both the exact CAD output and the approved specification.
   Findings feed a bounded correction back to CAD, followed by verification again.
7. FEA consumes the verified model and relevant requirements. Failed criteria feed
   engineering findings back to CAD, then verification and FEA repeat. Exhausted
   correction or an unsatisfied requirement visibly blocks progress with a reason.
8. Passing design/analysis permits the declared support-generation and slicing
   work. The user sees model, orientation/support consequences and prepared files.
9. A declared user-acceptance step presents the exact proposed print job before
   any physical action. A UI test never authorizes printing.
10. Change a supplied requirement or the process, save the appropriate revision,
    and run the whole workflow again. Preserve the first run and show which design,
    checks and results belong to each. Changed subjects require new applicable reviews.

This is the intended journey, **not a claim that the current desktop runtime
supports every required loop, review, provider or analysis**. Audit those mappings
before implementation. Existing unsupported conditional-path findings must not
be “fixed” by removing the required verification, review or correction step.
Preserve original accepted example requirements; select a suitable existing handle
example and explicitly record any proposed extension rather than rewriting it.

Inspection of an existing model is a separate journey: that user supplies the
existing document, and the process reads it without recreating the design. Keep
our retained block run as regression evidence for that case.

## Make every screen and control reviewable

Before implementing a screen, record: user goal; starting data/state; active
workspace/workflow/run; visible content; primary action; secondary actions;
where typing happens; successful next state; failure response; and return path.
For each control specify label, reason for appearing, enabled/selected state,
effect and feedback. Remove or relocate a control that cannot be justified by
the current task. Show engineering-tool contributions without protocol jargon.

Use actual Codex panel dimensions and the confirmed native tab behavior. Account
for the host's existing navigation and chat. Avoid redundant global navigation
inside every document. Exact labels and layout remain design-review decisions;
do not assume another top-level tab strip, mandatory wizard or fixed dashboard.

Include empty/populated workspace, workflow draft/saved, missing input/tool,
running, waiting for review, correction, blocked, completed, changed/stale,
historical-run inspection and reconnection states. Keep a usable common view;
custom process UI generation remains separately capability-gated.

## Bounded delivery sequence

1. **Inventory and design:** reconcile these stories with existing shared owners,
   observed Codex capabilities and current gaps. Maintain a single story/status
   table. Mark implemented, locally verified, host-observed and user-accepted
   separately. A missing backend capability gets its own scoped task.
2. **Review the interaction:** produce a short written first-run and changed-run
   walkthrough plus a rough clickable prototype at real panel sizes. Review the
   screens and controls against the stories before polished visuals or UI rewrites.
3. **Implement one coherent journey:** reuse existing canvas, source/draft/Undo/Redo,
   client/kit, file viewers, gateway, validator, recorder and storage. Preserve
   authoring capabilities and exact evidence. Start with full reruns; selective
   recomputation/caching is a separate later feature, not a prerequisite.
4. **Qualify the experience:** test the normal workspace entry, end-to-end task,
   correction and rerun; then a different existing nonmanufacturing workflow.
   Use Robot Tracking Diagnosis for applicable shared regression, not as proof
   of the handle's FEA or of a multi-tool manufacturing demonstration.
5. **Install and observe one candidate:** after local qualification, update only
   the authorized named prototype. Verify the resource actually shown. Check
   Windows panel, file delivery and return behavior directly before claiming
   acceptance. Apply the repository gates before integration; release is separate.

The next implementation goal must state its chosen slice and actual capability
gaps. Do not promise the complete handle chain if those gaps are unresolved.

## Testing and effort controls

- Give usability testers an engineering task and starting assets, without a
  list of button locations. Record what they tried, wrong turns, assistance,
  confusing wording and whether they could explain the result.
- Automate exact identities, invalidation, state, visibility/focus, native
  protocol and regression checks. “Control exists” is not a complete assertion.
- Use labeled fixtures for cheap UI state coverage and bounded real-tool checks
  for actual handoffs. Never label a mocked FEA response as engineering proof.
- Separate browser simulation, actual desktop observation, engineering verification
  and human acceptance. A helper on GB10 does not thereby see Windows pixels.
- Reuse user screenshots and the existing report/observation path. Requests to
  the user should be brief, one screen/task at a time. Do not repeatedly request
  new chats, sign-in, screenshots or a long acceptance checklist without a concrete
  need. Telemetry complements screenshots; it does not replace visual assessment.
- Batch related corrections and install one reviewed candidate. Explain old-panel
  versus new-build behavior. Do not treat a successful install as a rendered UI.
- Run affected tests once per change and required gates at the delivery boundary.
  Preserve failures, fix their causes and rerun affected checks; do not lower
  contracts to obtain passes. Do not repeatedly rerun engineering jobs to test layout.
- Time-box research to one specific capability question with a recorded answer or
  limitation. Avoid new executors, general authentication/test frameworks, custom
  viewer suites, generic UI schemas or separate per-host copies of Wright.
- Each implementation task names its story, expected visible improvement and
  acceptance evidence. New ideas go into the backlog until the selected journey works.

## Next review decisions

Review the first-run and changed-run storyboard, including how a workflow opens,
how chat knows its target and how results/step inspection return to the same run.
Choose the first implementation slice from the capability inventory. Decide how
much result comparison is necessary initially. Tool defaults are already decided;
do not ask the user to repeat that decision. No new goal prompt is submitted by
this plan; the user intends to request it after the preservation checkpoint.


## Current implementation ledger — 28 October 2026

This section is the current backlog and evidence index; earlier sequence and
lessons remain the design basis. Dedicated branch: `codex/desktop-engineering-experience`.
Baseline `1838f1b4174b5ea74524fb03901b3a6c40ab0ff2` includes fetched dev
`1514ea25a63e8e330f86dcac3ccf05f73bc0403b` (zero dev-only commits).
The original preservation checkout and independent Feature 084 checkout remain untouched.
The first-contact delivery brief is absent from this baseline; its current copy in
the independent main checkout was consulted read-only for context, not imported.

| Story | Existing owners to reuse | Concrete next work / qualification | Current evidence boundary |
|---|---|---|---|
| C01 tools | NativeConnections; existing gateway onboarding and controls | Separate installed selection, sign-in, validation and readiness; qualify default selection without authority grants | Fresh workspace catalog inspected: SteveCAD validation recorded but disabled in that workspace; required FEA/slicer not ready. Candidate defaults do not grant authority |
| C02 workspace | NativeHomePanel; workspace create/settings/files tools | Separate chooser from workspace contents; short naming form; explicit chat destination | Compiled chooser/return passed; real sandbox browser found silent native form submission. Corrected explicit actions pass workspace click/workflow Enter and visible saved-editor recovery; no installed update |
| C03 authoring | NativeNewWorkflow; shared recovery editor/source commands; instruction resolver | Explicit request/images handoff; retain shared editor and portable source; map existing handle example before extending it | Versioned chat handoff and exact workspace transport pass; actual complete handle authorship remains pending |
| C04 execution | workflow_source_execution; workflow_design_check; human-input/review owners | Verify required review and correction path support before enabling execution | Independent bounded producer/check pairs and opt-in verified segments are implemented and synthetically tested; actual retained-CAD meshing and synthetic structural-field checks passed through an isolated MCP/gateway route; real handle strength/slicing and human reviews remain unqualified |
| C05 step inspection | NativeWorkflowPanel; selected run context; shared process client/results | Visible exact-run inputs, work and outputs; return retains selected run | Actual retained-run API/storage with simulated host passes exact step/result navigation; engineering chain remains separate |
| C06 rerun | accepted source revisions; durable run/config/evidence owners | New full run; old results remain; repeat checks/reviews for changed subjects | New full-run preparation is visible; durable synthetic changed-input rerun requires a new review and preserves prior files |
| C07 results | shared CommonProcessView/UI kit; native previews/download adapter | Engineering summary before raw records; finish carried-forward download proof; actual host observation | Installed 0.33 image previously observed; corrected download not host-qualified |
| C08 return/recovery | native navigation; durable interaction/continuation owners | Same workspace/workflow/run restored without effect replay; clear missing versus mismatched context | Study only; actual chat-switch restoration remains unverified |

**Known execution boundary:** `workflow_design_check.validate_rework` supports
independent bounded correction pairs and explicitly opted-in verified segments;
unsafe crossing/replay of human answers or external actions remains rejected. `workflow_source_execution` recognizes typed design-check
pass/revise paths and unconditional order dependencies, not arbitrary conditional
connections. Existing Engineer review compilation is implemented. None of these
static findings establishes a qualified CAD → verification → FEA correction loop.
Do not remove required reviews or verification to bypass these checks.

### Early interaction study

Artifact: `prototypes/desktop-harness/engineering-experience/storyboard.html`.
This dependency-free, non-executing study labels all engineering state as simulated.
It uses an outline instead of replacing the shared canvas, and has no backend calls,
file writes, consent, engineering review or print action.

First run: name workspace → enter job/images in the existing Codex conversation
(explicit destination) → inspect proposed workflow → prepare run → review proposed
specification → inspect resulting work. The simulation skips actual review and
engineering computation using an explicitly labeled preview action.

Changed run: inspect old results → change requirements → save a new revision →
prepare a complete new run → repeat review → inspect new results or reopen the old run.
This is not selective recomputation or approval reuse.

| Screen | Task / primary action | Typing and feedback | Return / secondary controls |
|---|---|---|---|
| Chooser | Create or reopen a job workspace | Name field; required-name feedback | Engineering tools |
| Workspace | Find work or create workflow | File names; current workspace heading | Workspaces; tools |
| Request handoff | Describe job in Codex conversation | Existing chat, with named destination; sample response explicitly simulated | Workspace |
| Workflow | Inspect steps; prepare a new run | Revision shown; real editor retained for production | Edit requirements; previous runs; workspace |
| Prepare | Understand inputs and readiness before start | Missing readiness visible; study can only simulate | Workflow |
| Review | Assess specification and assumptions | Missing measurements/load explicitly unresolved | Change requirements; simulated later-results preview grants no approval |
| Results | Understand outputs and inspect producer | Run/revision and outstanding print review visible | Step view; change requirements; previous runs |
| Step | Understand inputs, tool work and outputs | Same-run identity; technical evidence collapsed | Exact run results |
| Change | Save revised requirements for a new full run | Required change field; new-review consequence visible | Workflow |
| History | Open earlier results | Run and revision in each row | Workflow |

Controls in the study are real navigation buttons, primary actions have stronger
contrast, return controls name their destination, and details disclose technical
records. No disabled-looking selected navigation or generic “Run and results”
control is used. Workflow-title editing and real image attachment stay with the
existing editor/chat; the study does not claim to implement them.

One independent reviewer is testing task-based navigation without click coaching.
Private local review evidence: `.local-run/experience-review/`. This is simulated
browser observation, not Windows acceptance. Record findings here before expanding
implementation. Actual provider qualification and required repository gates remain pending.


### First local increment and reviewer findings

The independent study review found three navigation/context defects: the changed
requirement disappeared, design review omitted run/revision, and a pre-run draft
disappeared from workspace navigation. All three were fixed and rechecked in the
study. Original findings remain in
`prototypes/desktop-harness/engineering-experience/evidence/early-review.md`.
The study does not test actual document approval, attachments, files or execution.
Two nonsecret study screenshots are retained beside that report; they are not
Windows screenshots or engineering results.

Production source changes so far: native file-mode Home separates chooser from
workspace contents and preserves context on Return; Connections initially shows
added tools, keeps unrelated catalog entries behind Browse, and moves advanced
setup/search out of the default view. Saved/current readiness distinctions remain.
The new-workflow form explicitly identifies the current workspace and the existing
Codex conversation as the place to describe the job and attach references; manual
blank-workflow authoring remains available. No second chat or executor is added.

Focused local checks: 64 tests passed across Home, Connections and existing
download paths; TypeScript and changed-file lint passed before the final small
wording/layout refinement, whose Connections tests also pass. The compiled native
resource was exercised with the existing SDK handshake, controlled fixture data
and a restricted iframe: chooser/return, visible file, default added-only list,
expired validation warning, catalog access, 480px fit all passed. Evidence in
`.local-run/experience-review/compiled-home-recheck/`; an earlier fixture encoding
failure is retained in `compiled-home/failure.json`. Rebuild/recheck the final
combined increment before committing. No installed update or Windows acceptance.

Read-only live connection audit: the desktop connection responds, but reports no
attested model/app version or native-tool ceiling. Its isolated workspace has
SteveCAD enabled, with a recorded protocol check at 2026-10-28 13:30 UTC; host
compatibility is still uncertain. No separate FEA or slicing provider is enabled
there. This is catalog/membership evidence, not fresh engineering readiness.

Existing reference: `tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md`.
Preserve its 96 mm mounting spacing, geometry/clearance, PETG/P1S/process settings,
orientation comparison and digital-only boundary. Its 40 N opening load is design
intent and explicitly carries no strength claim. The requested FEA is an extension
to a fresh accepted process, requiring explicit material, load/support and acceptance
basis at the declared specification review; never retroactively certify the original.

Next bounded work: qualify the final compiled workspace/tools increment; finish
the carried-forward host-download delivery proof; implement the scoped chat-to-
workflow handoff and run/result/revision experience using current owners. Audit
required corrections against single-safe-producer rework constraints before any
backend extension. Provider availability blocks real handoff qualification, not
offline UI and contract work. Full repository gates and draft PR remain pending.


Final checks for the first local increment: **250/250 desktop-panel tests**
(27 files), TypeScript, changed-file ESLint and the standalone resource build pass.
The final compiled fixture journey passes, including 480px layout and the visible
expired-validation warning. Public, nonsecret evidence is in
`prototypes/desktop-harness/engineering-experience/evidence/qualification.json`,
with workspace/tools screenshots. The runner beside `storyboard.html` accepts a
fresh output directory and exercises the built bundle; it uses no live tools.

The preserved **uninstalled 0.34** download package now passes its exact package
command, resource digest, app-only file handlers and retained-run/output identity
checks against the existing isolated backend. This closes its previous protocol
qualification gap, not Windows download acceptance or qualification of the newly
compiled UI. Fresh receipt is under `.local-run/experience-review/prior-download-protocol/`.
All nine protected workflow/run/output/backend-metadata hashes remain unchanged.
The installed named prototype is still 0.33; no plugin update, workflow run or
service restart occurred. The next candidate must combine the reviewed changes
and requalify its own exact resource before installation.


### Second local increment: return from results previews

The shared common view now names the return destination (Back to results or
Back to inputs), cancels a pending preview read, and restores focus and viewport
to its originating control. If a refreshed output removed that control, it returns
to the corresponding current section. Execution and durable identities are unchanged.

65/65 common-view/native-process tests, TypeScript and changed-file ESLint pass.
The newly compiled resource passed a read-only browser journey against the retained
run on the actual isolated API/storage, including the original file control entering
the viewport after return. All nine protected hashes remain unchanged.
See `prototypes/desktop-harness/engineering-experience/evidence/results-return.json`.
This uses a simulated host; Windows download, chat restoration and this build's
Windows rendering remain unverified. Browser harness selectors were updated, but
the full Home/usability/integration suites have not yet been rerun.

The first attempt correctly rejected a stale resource pin. A private isolated copy
of client metadata pins the new resource for qualification; installed configuration
and the frozen backend remain unchanged. No workflow ran.

Capability audit additions: desktop workspace creation currently selects only
Wright workspace status; default selection of loaded engineering tools is a gap.
The separate local_reviews-only flag is false, but code inspection confirms
workspace_mcp_tasks permits exact local reviews; end-to-end review qualification
remains pending. Existing rework
validation admits one safe producer revision path, not the whole CAD/FEA cycle.
Resolve these through existing owners and qualification; do not bypass their guards.


### Chat handoff and workspace defaults increment

User confirmed the workspace-first direction: choose/name the workspace, see its
files, then an explicit handoff to Codex chat to describe the job.

New workflow now offers Plan in Codex chat. It sends an explicit authoring-only
request and exact workspace/session context through the existing public host
message interface. The versioned instruction body is inspectable at
`apps/web/src/prototypes/desktop-panel/instructions/plan-workflow.v1.json`.
Missing host support and uncertain delivery are visible; neither retries nor
workflow execution occurs. Manual blank creation remains under a disclosure.

30 focused Home/new-workflow/transport tests passed; the final wording/disclosure
passed its 10 affected tests. The final compiled host fixture passes exact
message context, visible next action, tool navigation and 480px layout. Evidence:
`prototypes/desktop-harness/engineering-experience/evidence/chat-handoff.json`.
This proves delivery to a simulated host, not actual assistant authorship or Windows.

The backend increment snapshots the existing WorkspaceToolUseCases installed-tool
defaults for a new workspace. It creates no new credential, approval or server start.
Existing workspace selections remain untouched; new installations do not silently
expand the saved selection. 92 workspace/discovery and desktop-boundary tests pass outside the sandbox.
The sandbox attempt stalled in an async test; bounded diagnostics and the successful
host test log are retained under `.local-run/experience-review/`. Final TypeScript
and changed-file ESLint pass. No backend installed.


### Full rerun and review identity qualification

C06: Prepare new run was hidden inside collapsed completed-run details. It now
appears beside results, explains full rerun/history/review behavior, and never
starts work. The desktop host rereads accepted source before detaching the old
run. Changed/unavailable source keeps the prior run visible. Pending preparation
navigation is guarded against duplicate clicks; no approval or execution request
is issued by this control.

84 shared common-view/native-routing tests pass, including visible terminal-state
preparation and matching/changed/unavailable source. The actual durable owner suite
passes 26 tests, including a new full-rerun case: changed input creates a distinct
run and exact review subject, rejects the old subject, and preserves old run/file
bytes. Documents and decisions in this test are explicitly synthetic. This does not
establish engineering approval, CAD/FEA correction or Windows acceptance.

Independent reviewer rechecked the same workspace/chat fixture without coaching.
Current wording clarifies that workspace context was sent and editable steps are
the expected next output. The collapsed blank alternative fits at 480px. Remaining
minor backlog: distinguish Create blank workflow; clarify referencing an existing
workspace image versus attaching a new one; reduce the prominence of the host
restoration notice. No second independent reviewer or live actions were used.

Capability audit: the required FEA-to-CAD path is more than a second revision edge.
Current validation feedback requires the repair target to own every repairable
finding; current rework requires one immediately preceding safe producer. A
CAD → verification → FEA → CAD loop needs explicit upstream defect ownership and
revalidation of the affected segment, bounded attempts and preserved files. Do not
remove either guard or report independent single-producer tests as this chain.
Next: qualify the shared review/restart/rerun journey and map a narrowly typed
correction contract before extending execution. Robot Tracking Diagnosis and
full repository gates remain pending; no candidate installation or PR yet.

Exact combined-build browser receipt: `prototypes/desktop-harness/engineering-experience/evidence/rerun-qualification.json`; all nine protected hashes still match. Older receipts remain evidence for their own builds.

### Cumulative gate prerequisite — 28 October

The first full gate at `ccfd3514` stopped at OCI qualification because no
`WRIGHT_GATE_DOCKER_IMAGE` was supplied. Dependency audits and the initial
security/path/deadline contract checks passed; this is not a full-gate pass.
The failure receipt remains in
`test-results/docker-image-security/20261028T221549Z-9b0ebf16/public`, with
the full local log at `.local-run/experience-review/full-gate-ccfd3514.log`.

An isolated ARM64 candidate built successfully from a clean Git archive of that
exact commit, tagged `wright-desktop-experience:ccfd3514`, image ID
`sha256:8f31c532060ea8ca0a6993c29ff9aa1a545c80c1e2da1fd35ab9cbb47f16774f`. Build output is retained at
`.local-run/experience-review/image-build-ccfd3514.log`. No image publication,
installed-plugin update or live service change is part of this gate. Supply the
completed image to the existing scanner/gate; do not bypass its policy.

The full gate was relaunched with that exact image; its separate log is
`.local-run/experience-review/full-gate-ccfd3514-with-image.log`. It failed the current vulnerability policy; see the dated findings below.

### Fresh handle/Robot readiness and image findings

Fresh isolated original handle (Printed02) and Robot aisle-floor-seam scenario
copies preserve every input hash. Both templates remain declarative references:
the current executor rejects their unbound substantive tool steps. No workflow
ran, and no campaign state, credentials or approvals were copied. This is a
readiness finding, not shared execution qualification. See
`prototypes/desktop-harness/engineering-experience/evidence/handle-robot-readiness.json`.
The existing probe now accepts the original Printed02 scenario explicitly; its
default remains the original focus-wheel case. The initial sandbox attempt stalled
and was terminated by exact PID; its partial state was reconciled outside the
sandbox using the existing resume mechanism. Both logs remain local.

The exact candidate image scan failed on 28 October: libbrotli1
CVE-2026-111497, undici CVE-2026-109383/109869/87018, and msgpack
CVE-2026-114613 (two installed copies). Scanner-reported fixed versions are
libbrotli1 1.1.0-2+deb13u1, undici 6.29.1 and msgpack 1.2.3. The focused
Docker pins and dependency inventory were updated; all 16 smoke-contract tests
and changed Python lint pass. The original image and failed scan remain intact
at `test-results/docker-image-security/20261028T221957Z-2f3877ef/public`.
A rebuilt exact image and fresh scan remain required; no exception was added.

### Independent correction pairs (bounded shared prerequisite)

The existing compiler now accepts multiple independent safe producer/check pairs.
Every pair still has exactly one immediately preceding safe producer, exact
subject ownership and its own configured revision budget. No replay segment may
cross a check, human review or external-action step. The existing runner owns
revision counts, preserved attempts and downstream release; no executor or
configuration format was added.

48 design-check tests pass, including actual scheduler tests with synthetic CAD:
the first pair corrects once, the second corrects independently, earlier passing
work is not replayed, and exhaustion of the second pair holds the final stage.
A crossing path remains rejected. This does **not** yet implement FEA-to-CAD
upstream correction or qualify engineering tools. All 35 related source/validator
regressions pass. An initial test used the wrong dataclass field name;
its failed log is retained and the fixture was corrected to `output_path`.

The dependency-patched image built as
`sha256:7d548c311b2590aa6be6a8a096f612f54a8fbcf54a84b683f2f7631573ea870d`
at `ea516c95`. Its scan correctly rejected the concurrently changed source before
scanning. It is not qualified. Complete this code checkpoint, then build/scan
once against the stable source; avoid concurrent build-input edits during gates.

### Verified connected-file input identity

The stable `4ddbd581` candidate passed the current image policy and full reachable
Git-history leak scan. Its cumulative gate then stopped on Ruff formatting in
two test files; both are corrected. This was not a full-gate pass. The exact image
receipt is `test-results/docker-image-security/20261028T222614Z-153cfee9/public/scan.json`;
retain the full log `.local-run/experience-review/full-gate-4ddbd581.log`.

The runner now records hashes from its existing verified connected-file dependency
receipts on newly completed step records. The validation output owner carries
those hashes into the existing SubjectBinding.input_digests field. They establish
inputs Wright supplied at its observable boundary, not solver-internal consumption
or analysis correctness. No UI or prompt can grant new authority through them.

141 affected file/rework/validation/review/design-check tests pass. The new
assertions cover the corrected input rather than the failed prior attempt,
durable JSON round-trip/re-registration with unchanged identity, and legacy
records with no retroactively inferred linkage. Existing changed-file/review
checks remain intact. This prerequisite does not yet enable FEA-to-CAD replay.
Further contract notes are retained locally in
`.local-run/experience-review/upstream-correction-contract.md`; source changes
remain governed by the single C01–C08 plan.

### Exact-design analysis field reader

A new versioned `design-response` reader reuses the existing structural CSV
measurement functions and validation registry, keeping the old structural reader
identity and behavior unchanged. Its primary subject is the CAD file; its
explicit related roles supply an analysis field and a nonempty analysis basis.
Only a same-run, different-producer field with verified input digests matching
that exact design and every declared basis file can yield a measurement.
Units are explicit (MPa stress or mm displacement). Missing, stale, malformed
or nonfinite analysis blocks as an evidence problem, never a CAD repair.

This measures recorded fields and observed input linkage. It does not establish
solver correctness, mesh convergence, material suitability, approved loads or
physical safety; the accepted profile/process must retain those separate checks
and reviews. No workflow has been enabled to use this reader yet. The replay
segment extension and real CAD/FEA proof remain open.

15 structural-reader tests pass, including nine negative design-linkage controls.
The broader existing engineering-reader regression passed 112 tests; 34
external-artifact-dependent tests were skipped and are not claimed as qualified. No provider,
installed plugin or historical engineering file was changed.

### Explicit verified correction segments

Validator configuration now supports opt-in `rework_scope: verified_segment`
with explicit `repair_subjects`. Defaults retain adjacent-producer behavior.
Every repair subject must belong to the selected producer; the pinned profile
must assess only these subjects, with other bound inputs serving as supporting
evidence. The existing runtime still independently rejects feedback whose
actual finding owner differs from the correction target.

The replay interval admits only existing indexed create-new file tasks with
per-attempt output paths and read-only validators. Downstream tasks must consume
a verified connected output from the interval. Reviews, physical/external actions,
session edits, overwrites and unrelated work cannot enter replay. Combined
correction budgets permit at most three revisions of any repeated producer.
Existing scheduler invalidation, attempts, files and counters remain the owners.

122 affected compiler/validation/file tests passed before the new scheduler case;
the final file-owner suite passes 21 tests including that case. It proves a
synthetic design and its dependent analysis both repeat after a failed check,
receive distinct exact input hashes, and preserve all four attempt files. The
initial manually constructed test plan omitted its explicit reference edge;
that failed receipt remains local, and the corrected plan supplies the same
reference that normal compilation produces. This is not CAD/FEA accuracy or
full handle acceptance. Interrupted multi-step replay, profile negatives, exact
design-response integration and the full real-tool chain remain to qualify.

### Exact-design correction and saved-checkpoint proof

The real validation registry, exact-output repository, feedback owner and
canonical scheduler now have one combined synthetic chain test. The first
recorded stress field fails its pinned limit; feedback names the CAD producer,
CAD emits a new exact file, analysis consumes that new hash and the unchanged
basis, and the second assessment passes. Every prior attempt file is retained.
This uses synthetic STEP text/CSV fields; no engineering provider is involved.

A saved checkpoint after the corrected chain is serialized and resumed with
fresh service objects and the same run identity. No producer/analysis call is
replayed and attempt records remain equal. Tampering with a retained failed CAD
attempt rejects continuation without new calls. The checkpoint decision is
explicitly synthetic and creates no real approval. Four negative profile cases
reject missing/duplicate/unknown repair roles or assigning design checks to
supporting evidence. All six tests pass. This proves resumption **after** the
correction; mid-dispatch interruption and uncertain external outcomes remain
separate qualification obligations.

Evidence: `.local-run/experience-review/design-response-final.log` and
`packages/workspace_service/tests/test_workflow_design_response_rework.py`.
An earlier resume fixture omitted the exact prepared run ID and was correctly
rejected; its log is retained. Full real handle/CAD/FEA acceptance, Robot
execution regression, current cumulative gates and Windows acceptance stay open.

### Portable correction settings and editor compatibility

Saved ordinary and explicit grouped correction configurations now have a real
source → bundle → second workspace → reopened source → compiler regression.
Both preserve exact source, correction targets, profile pins and baseline; import
still reports that execution requires readiness and transfers no run authority.
The complete bundle suite passes 19 tests.

The editor audit found that its validator inspector rejected the new typed keys,
despite retaining them in source. It now recognizes them, preserves them through
diagram/source save/reopen, and explains that grouped correction is currently
configured in Source. The profile and correction-target selectors cannot silently
replace that configuration; the saved target remains visibly selected. Invalid
repair roles remain rejected. This is a deliberate authoring limitation, not a
claim that the graphical inspector can create a safe multi-step replay interval.
Backend readiness remains authoritative. Eleven affected editor tests pass.

Evidence: `.local-run/experience-review/portable-correction.log`,
`.local-run/experience-review/portable-correction-editor.log` and the bundle,
validation-settings and ValidatorBlockEditor tests. This change is local and has
not updated the installed plugin or established Windows acceptance.

### New-workflow handoff: engineering deliverables are part of authoring

The shared kit already recognizes exact validation records and opens the owning
service's readable assessment report. Arbitrary provider JSON has no equivalent
engineering meaning that the UI can safely infer. C03 must therefore declare
readable reports and linked engineering outputs, rather than expecting C07 to
invent dimensions, checks or strength claims from unknown data.

New desktop authoring handoffs use `plan-workflow.v2.json`; v1 remains preserved.
The versioned request covers requirements/reference inputs, documented assumptions,
declared reviews, actual tool capability checks, downstream revalidation, and an
engineer-readable report alongside exact supporting data and previews. It asks
for reusable saved workflow instructions and short, explicit chat/panel handoffs.
It grants no execution, review or physical-action authority. Existing accepted
workflow instructions and historical results are unchanged.

Three host-boundary tests pass, including exact v2 body/context delivery,
unsupported delivery and no automatic retry after uncertainty. This proves the
request sent, not that an LLM authored or executed the intended handle workflow.
That end-to-end proof remains required. Evidence:
`.local-run/experience-review/authoring-handoff-v2.log`.

### First concrete handle draft in the desktop workspace

The desktop connection was rechecked and a fresh workspace created through its
exposed tool. The actual catalog reports SteveCAD installed but not selected in
this workspace, with OASiS and the catalog slicer not installed. This is the old
installed backend; it does not prove the candidate's default-tool-selection fix.
No permissions or server lifecycle changed.

The saved handle draft now lives at
`prototypes/desktop-harness/engineering-experience/handle/` and in the fresh
desktop workspace. Its README and receipt distinguish saved source, open request,
missing image upload, unbound tools/profiles/correction edges and unverified
Windows rendering. Local and desktop source digests match; complete original
Printed02 prompt/context text is preserved. Current readiness correctly rejects
the unbound CAD step. This is a concrete authoring artifact for C03, not C04/C07
execution acceptance. No process has been started. The handle's original
no-strength-claim limits remain; the added FEA basis requires its declared review.

### Independent draft review and editor regression

Source storage alone did not establish editor compatibility: the compiled editor
rejected missing purpose fields, then duplicate global port identities. Both
failed observations remain preserved. The reviewed local draft supplies the
required fields and unique identities; its actual source now passes editor
parse/save/reopen while retaining all relationships, ports and configurations.
The original desktop revision 1 remains unchanged and its receipt is historical.
The reviewed draft also carries current reviewed requirements through CAD, checks
manufacturing changes against analysis, and puts a readable report before the
print-package review. No provider execution or engineering approval is claimed.

The full gate at 6dc8cd7a passed dependency/image/history security and Python
checks, then stopped on five frontend formatting failures. Those are corrected
locally; a complete current gate pass is still outstanding.

Independent compiled-editor recheck now displays the draft at 1100×900 and
480×900 and preserves exact source. This is simulated-host evidence. Remaining
findings are initial canvas ordering/crossing links, limited projected result
cards while tools remain unbound, and competing Run/Run readiness controls.
These remain open usability work, not acceptance. Fifteen affected frontend
tests and the full frontend formatting check pass.

### CAD-to-analysis prerequisite, 28 October

The selected OASiS/Gmsh environment now consumes an actual retained STEP through
official MCP and Wright GatewayService/StdioRunner in fresh restricted ARM64
containers. Both jobs yielded the same mesh; independent ASCII checks and exact
input/output hashes passed. See [evidence](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/cad-mesh-qualification/README.md).
The subsequent [structural-field qualification](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/cad-structural-qualification/README.md) consumed that exact mesh and passed force balance, support, energy, load-scaling and existing Wright-reader checks. This establishes numerical prerequisites only: no accepted handle strength model, human acceptance, live enrollment, handle execution or protected-run resumption. Next is the actual handle engineering basis and declared reviews, followed by manufacturing preparation through existing owners.

### First-run sandbox correction

Actual restrictive-iframe browser testing and the independent reviewer found workspace and blank-workflow creation silently blocked by native form submission. The native-only form wrapper now dispatches explicit validated click/Enter actions without expanding sandbox permissions. Existing single-flight and uncertain-outcome guards remain. [Evidence and reproducible check](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/sandbox-form-qualification.md). The broader suite exposed one outdated compact-JSON assertion, corrected to compare the actual data. The remaining reviewer navigation findings are now corrected locally: the handoff explains returning after chat confirms saving, distinguishes new chat attachments from named workspace-file inputs, and exposes Previous runs beside Connections without a hidden category. Actual compiled-source checks pass at 1100px and 480px, including viewport visibility and exact workspace handoff; 27 affected tests pass. [Evidence](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/workspace-chat-return.json) and [narrow-panel screenshot](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/workspace-chat-return-480.png). This does not prove the AI save round trip, installed delivery or Windows acceptance. The normal native builder produces the same SHA-256 as the tested compiled source: `32b8427efa6d486add8e569cef51633dc372c6d6f51a4de39e053e1b17b00307`.

The independent reviewer rechecked current screenshots/source and recorded browser evidence after the sandbox and navigation corrections: all four concrete findings are addressed locally, with no new material issue in the 480px handoff view. This was not a new Windows observation or the complete handle workflow. Reviewer report: `.local-run/experience-review/independent-current-journey-review.md`.

### Actual reference upload, 28 October

The compiled candidate UI uploaded the original handle concept and context into the existing fresh desktop workspace through the normal upload owner. Both saved messages were observed and exact stored bytes reconciled with the source dataset. The test harness had an envelope assertion error after the writes; failure evidence is retained and no upload was repeated. [Receipt and limits](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/handle-reference-upload/README.md). The draft still needs its placeholder path rebound through an accepted revision. This advances C03 input staging, not complete AI authorship, engineering execution or Windows acceptance.

### Actual handle source round trip

The compiled editor saved the reviewed draft and uploaded-image binding in the fresh workspace, preserving original revision 1. Revision 3 fixes the input setting and visibly shows 2/2 configured inputs after reload. Original requirements text is unchanged. [Receipt, screenshot and failed-attempt context](https://github.com/burhop/wright/blob/16e1eb5440a5b8ddb3535d237547180c80c341ea/prototypes/desktop-harness/engineering-experience/evidence/handle-source-roundtrip/README.md). This is actual source/storage and simulated-host UI evidence, not native Windows acceptance or a completed engineering run.

### Review binding qualification

The handle's seven-input `manual-review` draft is not yet a valid execution binding: that authoring template supports one connected document. The existing explicit `external-action-approval` declaration with `action_kind: local_review`, Wright's local review binding and `review_only` action supports multiple connected artifacts without external dispatch. Use that existing typed mechanism for the final package review when binding the draft; do not remove the required review subjects or generalize the compiler merely to accept this draft.

A new RFQ regression in `test_workflow_artifact_review.py::test_multi_document_local_review_seals_each_output_without_dispatch` exercises the existing source compiler, executor, file owner and durable recorder with a report plus supporting facts. It confirms an awaiting-review run, both exact file hashes in the subject/continuation, and only the two producer steps completed. Fixture generation is explicitly synthetic; this is not handle execution or a human review. The isolated sandbox run stalled and was interrupted; the host-side check passed in 0.17 seconds. Logs remain under `.local-run/experience-review/multi-document-review*.log`. No production runtime or approval contract changed.

### Final-review authoring boundary

The local handle draft now carries the existing seven-artifact local-review declaration. Applying it through the actual Source editor was rejected with `WFR-TEXT-STRUCTURE-UNSUPPORTED`; this is a concrete authoring gap, not a saved revision or successful engineering test. Accepted desktop revision 3 remains unchanged and the pending draft/failure screenshot are preserved. The first attempt could not connect inside the sandbox; the host-side attempt reached the editor and made no accepted-source save. Next: locate the supported structural authoring owner, or qualify a narrowly scoped edit without weakening review authority. Full gate session remains running (frontend suite after Python suites); no full-pass claim.

### Review edit and gate correction, 28 October

The missing task-type command is now implemented through the shared atomic editor batch. The actual handle source edit saves/reopens revision 4 with all seven review inputs. Twenty-eight focused tests and TypeScript pass, including Undo/Redo and unchanged connections. Evidence: `prototypes/desktop-harness/engineering-experience/evidence/handle-review-authoring/`. No backend approval enforcement changed, no run or approval occurred, and Windows remains unverified. Frozen candidate 0.35 still has its earlier resource; this new build has not been installed.

Full gate session 54055 terminated at strict documentation build after all Python suites and 2,127 frontend tests passed. Ten new evidence links escaped the docs root; these now use exact repository commit links. The exact strict docs command passes after correction. Live Playwright/later gates were not reached, and changed editor source requires affected qualification before a final full gate. Logs: `.local-run/experience-review/full-gate-9fca58d3.log` and `docs-gate-correction-uv.log`. No full-gate pass is claimed.

Independent review found no blocking correctness or authority issue in the task-type change. It noted that the reopened screenshot does not focus the final-package review and that structural tests do not prove runtime approval enforcement. Those limits remain explicit; the test title now describes preservation/revision history rather than claiming approval enforcement.

### Slicing capability decision and live-gate continuation

Editor/review correction and evidence are committed locally as `50bb2866`. The independent review found no blocking issue; 52 focused editor/instruction tests pass. The remaining live Playwright gate is running separately in an isolated temporary database on ports 18449/15449 (session 77642), without claiming the interrupted full gate passed.

Fresh actual connection inspection confirms SteveCAD installed/active but not enabled in the handle workspace; current model identity is still unreported. Provider configuration and exact task allowlists remain necessary before execution.

Bounded slicing research found a concrete ARM64 candidate: official OrcaSlicer v2.4.2 ARM64, compatible in principle with the already-pinned independent MCP's explicit `orca-slicer` discovery path. Official Bambu Studio Linux release assets were inspected at their ELF headers and are x86_64. The new provider usage guide records the exact Orca asset/hash and PETG profile requirements. Download verification is underway in isolated storage (session 34428); no slicer has executed and no printer was contacted. Next is a network-disabled selected-container protocol/native probe, explicit profile verification and actual artifact checks. Do not mark catalog or handle slicing qualified from release availability alone. This uses existing independent provider implementation, not a Wright-owned slicer or base-image addition.

### Offline preparation and browser-gate findings

The selected ARM64 slicer now initializes and produces an actual synthetic coupon package through Wright GatewayService/StdioRunner. Exact package settings and the existing passive nominal toolpath reader pass; the original embedded-PNG requirement fails. No printer access, handle execution or engineering acceptance occurred. Evidence: `prototypes/desktop-harness/engineering-experience/evidence/offline-slicer-qualification/`. Keep this prerequisite separate from C04/C07 completion.

The separate remaining live browser stage ended with 152 passed, 28 failed and 5 skipped. Nine failures used the former Start process label; the affected 15-test rerun passes with Start workflow. One accessibility check used former Fit workflow to view while the actual accessible button is Show all steps; its selector is corrected and both accessibility checks now pass, including the two-times page-scale and serious/critical axe assertions. Eighteen WebKit cases could not launch because this host lacks libgstcodecparsers-1.0.so.0. No gate was weakened and no complete gate pass is claimed. The scoped logs remain under `.local-run/experience-review/`.

### Native package preview and WebKit host recheck

A bounded actual virtual-display probe confirms the stable slicer still omits its package PNG. The official 2.5.0-alpha thumbnail fix was then qualified in a separate nonroot, network-disabled image with the unchanged independent MCP. The same synthetic coupon now passes actual package settings, existing passive nominal toolpaths and the original required PNG check. No requirement was relaxed and no image was fabricated. Keep the prerelease explicit; handle qualification and live provider enrollment remain outstanding. The evidence directory now includes separate alpha runtime/inspection receipts and its actual package preview.

The WebKit host dependency diagnosis was also rechecked using already-extracted private libraries and the original Playwright binary, without modifying host packages or shared browser cache. With libraries found, the browser aborts with SIGABRT before opening a page on this 64 KiB-page ARM64 host. This confirms an additional host-launch limitation, not a Wright assertion failure or proven kernel root cause. Logs: `.local-run/experience-review/webkit-host-probe/launch.log`. Do not count those 18 browser cases as passed or substitute Chromium for their coverage.

After the separate alpha qualification, all 21 existing manufacturing-package inspection regressions and the strict documentation build pass. The first docs attempt hit the sandbox cache boundary; the authorized host-side command passed. No new shared-runtime implementation, installed-plugin change, push or PR occurred in this increment.

### Candidate backend qualification: route ordering correction

The isolated 0.36 candidate built from `2d2e012a` produced verified wheel/sdist
artifacts and a compatible 61-package environment. Starting it on fresh storage
exposed a real installed-package defect: desktop GET routes returned the frontend
HTML fallback rather than JSON. FastAPI 0.162 retains included routers without a
route-level `path`; the prototype's path-based sorting missed those entries.
The correction moves the newly included desktop router entries before the existing
fallback, without inspecting private FastAPI wrappers or changing authentication.

The focused routing/bridge suite passes (32 tests), and the regression also passes
inside the exact candidate environment. Actual MCP Home, connection, all 59 tool
registrations and the exact native resource pass against the built wheel plus the
recorded preview-server correction. Existing API and frontend routes remain tested.
The initial sandbox TestClient attempt stalled and was interrupted; the bounded
host-side tests passed. Private reproduction, package identities and corrected
protocol evidence are under `.local-run/experience-review/candidate-036/`.
This is an intermediate qualification, not a coherent final installed build or
Windows visual acceptance. No credentials were copied, no workflows ran, and the
installed 0.33 plugin/backend030 and their state remain unchanged. A newly frozen
candidate must include the correction before deployment.

The corrected prototype is frozen at `0ecf3acc` and has now passed an actual
isolated workspace-create → handle-draft-save → disconnect → reconnect → exact
source-reopen check against the built runtime. The handle's source digest remains
`985013cf4b6b0818099008345915c00345b93084b560018016a5a83de8b34b52`;
its new disposable workspace has its own revision 1 and no engineering runs.
Compiled Home/editor rendering against that storage passes at 1100/480 px in a
simulated host, including exact Source/Diagram round trip. Evidence and inspected
screenshots: `prototypes/desktop-harness/engineering-experience/evidence/candidate-036-installed-runtime/`.
A narrow file-kind label wraps awkwardly; include it in the next coherent UI batch.
Actual Windows rendering/delivery and complete engineering execution remain open.
The owned fresh candidate is on loopback 18336; it has no copied accounts or tool
grants. Do not replace the installed plugin until tool setup and the complete
candidate's required local checks are qualified.

### Actual tool setup and loaded-tool membership correction

Both selected independent providers are now registered, protocol-validated and
enabled through the actual compiled Connections panel in the isolated 036 handle
workspace: OASiS (17 discovered tools) and the offline Orca/Bambu provider (11).
Their containers remain network-disabled and lack printer credentials; no
engineering tool was invoked. Exact validation receipts explicitly preserve
`invocation_approved: false`. SteveCAD personal sign-in remains outstanding;
availability was requested without generating an expiring code prematurely.

Creating a second workspace exposed a shared reporting bug: its loaded-tool
selection was correctly stored by name, but Connections hid that membership when
another workspace selected the same provider by ID. The read projection now unions
both supported identities with workspace deduplication; authority is unchanged.
Seven capability tests and eleven existing gateway tests pass, and a read-only
projection over actual candidate storage proves the correction. It is not yet in
the running candidate wheel. Reproduction, limitations and screenshots are saved
at `prototypes/desktop-harness/engineering-experience/evidence/candidate-036-provider-setup/`.
Do not repeat completed setup to repair a test assertion or conflate validation
with execution, engineering acceptance or native Windows rendering.
