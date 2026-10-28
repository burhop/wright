# Wright engineering journeys inside the OpenAI desktop harness

**Recorded:** 28 October 2026. **Status:** agreed direction and a proposed staged
design/implementation plan. The user authorized recording this plan and preserving
and pushing the existing work. This document does not start a new implementation
goal, authorize an engineering run, or establish product acceptance.

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
