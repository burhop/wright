# Wright in the OpenAI desktop harness: production integration plan

**Prepared:** 4 November 2026. **Status:** implementation goal submitted on 4 November 2026; M0–M4 and gated dev integration authorized. Production publication excluded.
**Source baseline inspected:** `origin/dev` at `4f370caa9743f869f769f8c8e2332b6b63be438b`.
**Planning branch:** `codex/codex-production-plan`.

This is the accepted next delivery contract. It retains the user decisions and
lessons in [the engineering-experience plan](codex-engineering-experience-plan.md),
whose dated implementation log remains historical evidence. The submitted implementation goal authorizes implementation and gated dev integration;
this document does not claim new qualification or authorize production publication.
The accompanying [tasks](codex-production-integration/tasks.md) and
[acceptance matrix](codex-production-integration/acceptance.md) are the bounded
working records. Adopt them in the next appropriate feature record if needed;
keep one authoritative checklist rather than duplicate backlogs.

Apply V1–V7 from the [platform vision](workflow-platform-vision.md), the existing
[refactoring ownership](../architecture/workflow-platform-refactoring-plan.md),
[instruction/interaction contracts](../architecture/workflow-instructions-and-interactions-plan.md),
[process UI design](process-apps.md), and [editor integration guidance](../contributing/workflow-ui-integration.md).
The [first-contact brief](first-contact-delivery-brief.md) informs onboarding;
the [engineering demonstration principles](engineering-demonstration-principles.md)
govern the reference proofs. This proposal does not replace those authorities.

## 1. Recommendation and definition of done

Turn the proven desktop prototype into a maintained, packaged integration over
Wright's existing services. Complete the engineering journey before expanding
features. Keep the shared canvas, editor, process client, UI kit, validators,
gateway and durable execution. Codex supplies the conversation and reasoning;
Wright supplies the accepted process and its execution authority.

The first supported customer topology should be **OpenAI desktop on Windows with
Wright running locally on Windows**. Continue development on GB10 and preserve
the working Windows-desktop/GB10 topology as a separately qualified deployment.
Neither setup may depend on a network share, an author's checkout, `/tmp`, SSH
callback forwarding, or a private prototype launcher. Linux x64/ARM64 and Docker
backend support have their own installation and integration evidence. A Linux
browser simulation is not Windows desktop acceptance.

There are three distinct delivery states:

1. **Maintained implementation:** packaged code, supported ownership boundaries,
   installation/migration, documentation, tests and observable diagnostics.
2. **Qualified desktop integration:** the advertised stories below work through
   the installed candidate in the actual target desktop, including file delivery
   and a changed-input rerun. Remaining exclusions are explicit.
3. **Published production release:** separately authorized release runbook,
   public artifacts, native lifecycle verification and release evidence complete.

Do not claim the integration complete merely because code was moved, CI passed,
or a PR merged. Retain the experimental label for capabilities without the
required evidence. A release with a stated limitation is a deliberate scope
decision; missing a mandatory story is not a passing result.

## 2. Baseline: reuse and outstanding work

| Subject | Evidence now | Consequence for this plan |
| --- | --- | --- |
| Live connection | This conversation's connection check returned `connected: true` on 4 November; model and app-build identities were unreported | Preserve the handoff; do not infer exact model/build or execution readiness from connection liveness |
| Installed desktop prototype | Available skill is 0.38.1; retained candidate receipt describes the isolated viewer-selection experiment | Reconcile actual launcher/backend/UI hashes before the next installation; merged `dev` is not the mounted build |
| Diagram/native tabs | User screenshots and confirmation establish inline diagrams and a native diagram after manual selection of Wright in Open | Automatic file-viewer selection remains unresolved; three-file experiment was prepared, not visually accepted |
| Workspace/editor/run/result mechanisms | Shared code and bounded test/engineering records exist; prior screenshots also establish confusing navigation and controls | Repair the end-to-end experience; preserve capabilities instead of replacing the editor |
| Images/downloads | User saw a retained image after correction; also reported Download doing nothing | Qualify exact image and download paths in the installed desktop; an acknowledgement is not delivery |
| Reference engineering chain | Printed02 has separate Hermes evidence; the desktop handle draft has useful bindings and partial proofs | Do not transfer Hermes acceptance or partial provider proof into a complete Codex handle claim |
| Packaging | `integrations/codex`, the native lifecycle and direct MCP bridge already exist | Integrate richer desktop behavior into these maintained boundaries; avoid a second installation/runtime system |
| Prototype composition | Rich UI backend/bridge live under `prototypes/desktop-harness`; the preview launcher changes composition and flags | Replace active prototype startup dependencies with normal packaged composition, retaining tests and historical evidence |

Primary retained evidence: the earlier plan, `prototypes/desktop-harness/engineering-experience/handle/README.md`,
Feature 083/084 completion records, and the private feature-worktree file
`.local-run/experience-review/pr174-ci/native-viewer-reproduction.md`.
Old dated summaries are not current capability guarantees. The baseline inventory
must reconcile each advertised operation with current source and exact evidence.

## 3. The experience to deliver

The user should always know **where the work lives, what happens next, and what
has actually been established**. Use one conversation and the host's document
surfaces. Keep workflow editing and carrying out the job complementary.

### First setup and workspace

An engineer opens Wright and sees a simple choice: open a workspace or create
one by name. Tool setup is a clear first-time action and remains accessible in
workspace settings. They can add a catalog tool or a custom MCP, connect it, and
see whether it is usable. Do not list the entire catalog as long status cards.
Show configured tools first; put discovery and technical details on demand.

Already loaded MCPs are selected by default for a new workspace, subject to
existing grants. Tool selection, authentication, permission and readiness remain
different facts. A compact tool status can say “Sign in needed” or “Check needed,”
with details explaining the cause. Updating, replacing or removing a connection
shows affected workflows and preserves historical bindings and evidence.

Chat can also start the same journey: “Create a workspace for a replacement
handle.” Both routes use the same workspace owner. A UI action such as **Describe
the job in chat** carries explicit workspace context; it never silently starts a
run. Do not add a second Wright chat box. Visible context and a successful handoff
must tell the user where to type and what their request will affect.

### From intent to editable process

The engineer supplies a goal, images and available measurements. AI proposes an
editable workflow, documents assumptions and declares review points. It does not
demand a pre-existing CAD document when the job is to create one. Intermediate
files belong to their declared producing steps.

The workspace is a useful file browser: readable names, type, folders/location
when needed, search, and restrained secondary actions. Preserve workflows,
reference content and outputs. Distinguish identical filenames by producing run
or folder; put internal run records under details, not in the default list.
Clicking a workflow opens its editor; other files open a compatible viewer.
Use existing qualified image, PDF, table and CAD viewers. Reuse compatible open
source components for missing formats after license/security and format checks;
do not write a new STEP/DXF/CAD viewing engine or silently convert an original.

### Run, review, understand, revise

The workflow document provides **Edit workflow**, **Run workflow**, and access to
previous runs. Run preparation shows required inputs and specific missing-tool
or unsupported-step issues. **Start workflow** is the explicit execution action.
Known prerequisites fail before start. A supported upstream producer satisfies a
future input dependency without requiring its output to exist yet.

The working view prioritizes progress, the next declared user action, results
and actionable failures. A review shows exactly what is being accepted. Each
step exposes inputs, instructions, tool contribution, outputs and findings.
Result → producing step → same result must preserve the selected run, source
revision and output identity. Distinguish missing run context from changed source.

Results lead with the engineering deliverable: model/image, measurements with
units, plots, findings and limitations. Raw JSON, hashes and protocol details are
available on demand. Generic summaries derive from declared representations and
assessments; do not add a block-specific JSON parser or invent a passing verdict.
Missing assessments say what has and has not been checked.

Changing inputs or the process creates a visible new execution subject. Offer a
full new run first; selective recomputation is not required for this delivery.
Keep the old run and results intact. Show affected checks/reviews as inapplicable
to the changed subject, and repeat required checks. Pure layout changes must not
invalidate engineering results. Resume a waiting run and start a new run are
different actions. Unknown external effects require reconciliation, never replay.

### Control-level rules

- A compact workspace identity and document title replace repeated global headers.
- Selected views have an explicit active indicator; disabled actions have a reason.
- One clear primary action per state. Advanced controls are reachable on demand.
- A viewer opens visibly, with a named return path that preserves context and scroll.
- Fit the canvas on first open and appropriate resize without resetting deliberate
  user pan/zoom; preserve keyboard and pointer editing, source and Undo/Redo.
- No silent clicks: show pending, success, rejection or an actionable error.
  Downloads say “requested” until actual delivery is observable.
- Test 480px, 800px and 1200px panel widths, light/dark themes and 200% zoom.
  Avoid nested scrolling where it obstructs the current task; do not hide controls.
- Task-only usability checks give an engineering objective, not button locations.
  Record wrong turns and assistance. Human satisfaction requires human feedback.

## 4. Production ownership and migration

| Existing code | Proposed disposition | Required proof |
| --- | --- | --- |
| `integrations/codex/`, `src/wright_engineering/manager_profiles.py`, `cli.py`, `runtime/`, `mcp_bridge.py` | Extend existing package/config/lifecycle ownership for the richer desktop profile. Distinguish general MCP tool access from workflow reasoning/UI capabilities | Clean installed launch and uninstall/update; no checkout dependency; no secrets in plugin manifests |
| `prototypes/desktop-harness/mcp_bridge.py`, `native_*_tools.py`, file contracts | Move maintained registration/transport into an explicit desktop module under the packaged integration. Reuse the direct transport where compatible; preserve typed app-only visibility and resource delivery | Normal MCP negotiation, tool/resource inventory, scope enforcement, errors and installed assets; no generic privileged proxy |
| `desktop_backend.py`, `preview_server.py` | Split thin API registration into `apps/api`; move reusable composition/use cases to existing `workspace_service` ownership. Use normal composition and native lifecycle. Leave test-only launch behavior in tests | No monkey-patched production startup, global profile switching or private enrollment grants; both ordinary and desktop entry paths work |
| `desktop_oauth.py`, credential/template helpers | Preserve presentation-only behavior over existing registry/OAuth/credential services; eliminate duplicate policy ownership | Device flow when provider supports it, supported alternative otherwise; private consent; no SSH or credential copying |
| `core/desktop_reasoning.py`, `agent_adapters/desktop_reasoning.py`, `data_vault/desktop_reasoning_repository.py` | Retain and harden the existing contracts, callback adapter and durable request store | Frozen configuration, request/response identity, cancellation, restart, stale response rejection and no uncertain replay |
| `workflow_source_execution`, `workflow_mcp_execution`, `workflow_reasoning_dispatch`, `process_interfaces`, validation and results | Retain canonical owners. Add only bounded missing behavior needed by accepted stories | Exact-output checks, reviews, recovery, instruction evidence and other platform regression |
| `apps/web/src/prototypes/desktop-panel/` | Promote maintained shell/transport components into the existing frontend structure. Reuse existing host/presentation adapters, process client and kit | Same compiled source tested and shipped; no per-host copies of the editor or working view |
| `apps/web/src/prototypes/workflow-recovery/`, `packages/process_client`, `packages/ui_kit` | Preserve the refined editor and common views. Change only necessary shared behavior. The directory name alone does not justify a mass move | Normal workspace entry, complete authoring regression, historical results, compatible saved UI fallback |
| Versioned skill/instructions, plugin manifests, hashed UI assets | Maintain in `integrations/codex` and normal packaged resources, pin matching versions/build identities | Reproducible build; installed source/backend/UI identities agree; packaged instructions remain inspectable |
| Diagnostic probes, fixtures, frozen candidates and screenshots | Keep useful tests in maintained test suites; retire obsolete active entrypoints only after caller replacement. Retain historical artifacts inactive | Caller/dependency audit, old result readability, migration receipt; no deletion of user evidence |

Exact new module filenames are routine implementation choices. This map is an
ownership constraint, not an instruction to build a new package/framework for
every row. Preserve public contracts or provide narrow, tested compatibility
adapters. Audit release packaging, tests and gates when moving files so coverage
does not disappear with the `prototypes` path.

Migration must be explicit: identify the old instance and state, copy nonsecret
test state for rehearsal, check schema/source/history compatibility, then offer
the user a scoped move or attachment to the maintained runtime. Preserve original
workspaces, drafts, runs, files and credentials in their existing owners. Never
silently point the prototype at the Windows pilot or switch an active run's route.
No broad database rewrite, credential export or deletion is part of cleanup.

## 5. Desktop decisions and bounded research

Official OpenAI documentation now describes file-viewer and conversation-panel
entrypoints. These support the proposed integration surfaces; they do not by
themselves establish which viewer this Windows host chooses for a file. Keep
native file tabs as the preferred route, and the same editor in a conversation
panel as the explicit fallback. Do not add a second tabbed application inside a
host tab. ([Extension reference](https://developers.openai.com/plugins/build/extensions))

Before changing registration, finish one controlled experiment: identical `.wflow`,
`.workflow.wflow` and `.txt` files, one registered handler, exact metadata/request,
host acknowledgement, handler invocation, mounted identity and actual Windows
observation. Compare supported extension variants only after checking the linked
protocol specification. Keep content-hashed UI URIs. Record remembered-choice
behavior on reopen if observable. Spend at most 60 minutes of active investigation;
missing desktop access produces an explicit pending row, not repeated new chats.

Display-mode metadata and requests concern presentation, not file dispatch.
Feature-detect the documented API, qualify beside-chat behavior, and never claim
fullscreen fixes default file selection. The current reference describes
`availableDisplayModes` and `requestDisplayMode`; use the API supported by the
pinned client/host rather than an assumed property from an old example.
([Plugin reference](https://developers.openai.com/plugins/reference))

Package one plugin with normal distribution metadata and a versioned skill,
using the existing runtime. Official packaging supports local and Git-backed
marketplace sources. Qualify the chosen distribution and update path; marketplace
registration is not proof a running chat loaded it.
([Packaging guidance](https://developers.openai.com/plugins/build/plugins))

Use the existing download implementation and diagnostics first. Bound one
investigation to the actual failed path: host capability, exact scoped bytes,
request result and local Windows file observation. An unsupported host gets a
clear supported alternative or a declared blocked capability, never a silent
no-op, arbitrary filesystem mapping or credentials in a URL.

## 6. Execution and host limitations

Codex's conversation is the requested LLM harness. Keep the separate embedded
Codex SDK chat experiment separate; it is not a replacement for this integration.
No silent Hermes/API/Cloud model fallback. Codex Cloud development tasks are also
outside this product route.

Freeze the observable desktop binding, runtime/client/UI contract versions,
accepted source, instructions, schemas, tool configuration and input identities.
Record requested model settings separately from confirmed/reported identity.
When the host does not disclose its model/build, record that fact; do not fabricate
a freeze guarantee. Requirements needing an attested model or enforced context
budget must fail readiness if this route cannot meet them. Continuation rejects
observable incompatible changes; hidden host changes remain an explicit limit.

The runtime submits bounded reasoning requests and accepts validated replies
through the existing handoff. Wright executes tool proposals through its gateway.
Helper, correction and recovery calls use the same frozen route and evidence
owners. Native Codex tools are outside Wright's control: do not claim global
confinement, and never use them to bypass Wright's action authority.

Qualify active-chat progression and what happens when chat closes, changes model,
disconnects or stops responding. Until supported wakeup/continuation is proved,
show “Waiting for Codex” and a deliberate continue action. Do not promise unattended
reasoning while the desktop is closed. Backend-only work may continue only under
its existing durable execution contract.

Generated process-UI authoring remains gated by its confinement requirement.
Use the common working view and already compatible saved interfaces. A later
qualified role must reuse the existing isolated builder, preview, saved revisions
and fallback; do not weaken zero-tools requirements or add a maintained Codex fork.
If this feature is required for the release claim, its unresolved gate blocks that
claim, not unrelated progress.

## 7. Delivery sequence

| Milestone | Result | Exit gate |
| --- | --- | --- |
| M0 — freeze the supported slice | Concise capability inventory, installed/source identities, screen/action map and blocker classification | Every mandatory story has an existing owner and a test; uncertainties have bounded decisions |
| M1 — installable vertical slice | Packaged plugin/runtime opens an existing workflow and result using the shared UI, without prototype startup | Clean install, actual resource loading, save/reopen and preserved historical evidence; host observations separately recorded |
| M2 — coherent workspace and authoring | Setup, workspace/chat context, files/viewers, create/edit/export/import and actionable readiness | Task-based first-user route and full editor regression on the served candidate |
| M3 — complete digital engineering journey | Handle workflow, reviews, bounded correction, results and full changed-input rerun; different-workflow regression | Actual tool/artifact chain, exact checks and preserved old run; no mocked engineering pass |
| M4 — production qualification | Restart/update/migration/security/platform checks, clean packaging, maintained tests and docs | Acceptance matrix complete for advertised scope; required repo gates and current-head CI pass |
| M5 — release | Authorized publication and verified installed public artifacts | Existing production release runbook complete; no unsupported production claim |

M1 is the smallest useful end-to-end migration milestone; M3 establishes the
intended engineering value. Reuse the Printed02 assignment and existing desktop
handle draft, reconciling their reviewed requirements. The intended extended
chain is specification/review → CAD → exact geometry validation/correction →
strength analysis/correction → manufacturing preparation → package review.
The 40 N design intent is not, alone, a qualified FEA acceptance basis. Record
material, loads, constraints, applicability and acceptance criteria explicitly;
do not invent user sign-off or quietly replace a solver with AI prose.

Use Robot Tracking Diagnosis as the substantially different shared-mechanism
regression, preserving its data/tolerances. It tests data/metrics/reporting and
interactions; it is not proof of FEA or a flagship multi-tool manufacturing demo.
Keep retained block inspection as a small navigation/history regression. Do not
recreate its design or turn historical failures into successes.

Before live engineering qualification, inspect provider guides/evidence and
bind the required existing MCPs. A missing provider, human review or engineering
basis blocks only dependent proof. Continue packaging, UI, negative controls and
other qualification. Conditional/rework semantics missing in the canonical runner
are scoped owner defects, not permission to flatten the workflow or execute it
in chat. Physical printing is excluded from this delivery's digital tests.

## 8. Efficiency, evidence and acceptance

Start with the existing tests and user screenshots. Add assertions on what the
user sees and understands: exact output availability, matching historical source,
visible preview, readable result, return destination and actionable disabled state.
Fixtures cover UI states cheaply; actual engineering runs prove tool handoffs.
Do not rerun CAD merely to inspect layout.

Use one task ledger and one current checkpoint. Each task records story, owner,
changed files, tested build, evidence, and next action. Cap each new capability
spike at 60 active minutes; after two failures with the same cause, diagnose once
and select the supported fallback or name the blocker. No new generic testing,
authentication, orchestration or UI-schema framework.

Batch coherent changes. Run affected checks during iteration, then the required
pre-push/full-merge gates at delivery boundaries. Collect all current-head CI
results before a consolidated correction. Follow the runbook's normal two-push
budget; scope/coverage exceptions must be exactly those it permits. No bypasses
or a new CI optimization project inside this goal. Report time spent in coding,
verification and waiting; do not promise an hour for gates known to take longer.

The evidence matrix distinguishes source implementation, automated tests,
installed-package checks, actual desktop observations, actual engineering evidence
and user acceptance. Use available authorized Windows tooling where accessible;
first prove it sees and interacts with the real app. GB10 agents or iframe telemetry
do not imply Windows access. If unavailable overnight, finish independent work
and leave one short native test per unresolved behavior. Keep visual observations
pending rather than repeatedly requesting screenshots or claiming success.

For sharing, retain a few sanitized screenshots or a short recording of working
milestones with build/context captions. Label actual desktop captures versus
simulation/concept images. Prepare draft captions only; external posting is a
separate authorization. Evidence must show the useful job, not just green tests.

## 9. Proposed authority for the subsequent overnight goal

These are recommended permissions to put in the next submitted goal, **not
permissions granted by this plan**:

| Proposed authorization | Boundary |
| --- | --- |
| Local implementation, isolated dependencies, tests and commits on a dedicated branch from current `dev` | Preserve all dirty work, separate pilot/Roadster branches and historical artifacts |
| Bounded digital provider tests in fresh test workspaces | Existing authorized accounts only; no purchases, changed terms, physical effects or protected campaigns; retain per-run limits and exact tool scope |
| Candidate-owned services and development installation | Only the named `wright-desktop-gb10-prototype` configuration/cache and uniquely identified candidate services/state; verify the concrete paths first, never stop unrelated processes |
| Gates, feature pushes and PR creation/update | Follow current repository gates, inspect every current-head CI result; no direct `dev` pushes |
| Merge into `dev` after all required gates/CI | Only if explicitly included in the submitted goal; completion of implementation does not authorize publication |
| Independent work while waiting | Personal login/consent and real engineering reviews remain user actions; blocked tasks stay pending while unrelated tasks advance |

Recommend keeping public release, `main` integration, production registry uploads,
Windows pilot configuration and desktop restart outside the overnight permission.
Development package publication also needs explicit authority and the existing
protected reviewer gate; local candidate testing does not require publishing.

No task should stop for routine implementation choices already within the goal.
The goal must be finite: complete the accepted checklist or reach a demonstrated
external blocker after independent work is exhausted. Never claim completion,
weaken a contract or loop on the same tests to keep a goal running.

## 10. Review decisions and next action

Recommended defaults for review:

1. Windows-local is the first customer topology; GB10 remains the development host
   and separately qualified remote backend.
2. Prefer native document viewers, with an explicitly labeled conversation-panel
   fallback if automatic file selection is host-controlled. Do not let that one
   preference stall all other stories.
3. Deliver the common working view first; confined generated UI and unattended
   closed-chat reasoning stay explicit qualification gates.
4. First overnight delivery targets M0–M2 plus all independent M3/M4 work possible.
   The complete engineering proof remains required, even if human review or a
   provider prevents finishing it overnight.
5. Authorize development integration in the next goal if desired; release follows
   later review and the production runbook.

After review, issue one goal referring to this packet and its exact authority.
At implementation start recheck `dev`, current plugin/host versions, provider
readiness and overlapping PRs. Do not restart the earlier prototype campaign or
repeat completed qualification without a changed subject or unresolved claim.
