# Goal: improve Wright's engineering workflow experience

**Prepared:** 8 October 2026. **Priority revised:** 10 October 2026.
**Status at revision:** paused; local implementation remains authorized by the submitted saved goal.
**Implementation agent:** GPT-6.1 Sol, High reasoning.
**Repository:** `D:/repos/wright`.
**Basis:** [Mechanical engineering and product usability review](mechanical-engineering-product-review.md).

**User-agreed priority, 10 October:** improve Wright's ordinary user journeys and
shared capabilities first. Use a small set of existing engineering workflows to
expose and verify product defects. Complete necessary example refinements after
those journeys are dependable. The user subsequently deferred slide-deck work:
creating, revising, rendering or validating presentation PPTX/PDF files is outside
the current goal and is not a completion gate. Engineering drawings and verification
documents remain in scope. The work-order instructions in the prompt
below govern remaining work; completed evidence and unfinished deliverables remain
tracked. This revision does not itself resume the paused goal.

**User clarification, 8 October:** include Wright's existing swim-lane tools in
the engineering examples. Reuse and locate the reviewed implementation; show
responsibility and engineering handoffs on the same accepted process/run, and
include readable actual swim-lane captures in the demonstration and manual checks.
Do not replace the refined editor or build an independent executor for this view.

**Accepted scope clarification, 10 October:** the user selected a separate
130 mm shelf variant for the sheet-metal dock, retaining the 60 mm rear wall and
the other Option B requirements in
[the decision record](mechanical-engineering-decisions-059.md). Preserve the
original 75 mm design and run. Recheck current manufacturing limits before CAD;
this decision does not waive validation or authorize a supplier/physical action.
The pending dock choice referenced below is now resolved in favor of this new
variant; its implementation and deliverables remain required. The actual
swim-lane integration remains separately pending.

Select the implementation model before submitting. Saving this file does not
activate a goal. This saved goal has now been submitted. Its submission approves its bounded local work and
technical milestones; it grants no real engineering release or external action.
No token budget or arbitrary overnight deadline is specified.

## Delivery amendment — 10 October 2026
The user subsequently requested a good stopping point and authorized committing
current work, pushing the feature branch to GitHub, and completing the PR process
into `dev`. They also requested that the README and documentation match current
code, with fresh screenshots where helpful. This delivery amendment supersedes
older no-commit/push/merge statements for this development checkpoint. It does
not authorize `main` integration, a production release or engineering approvals.

Leave the latest 130 mm study at its declared intent-review checkpoint. Finish
and verify the bounded run-history navigation repair, update documentation, run
the required delivery gates and retain a clear list of unfinished work. Native
dock deliverables, its editor port-type finding, reviewed swim-lane integration
and final fresh engineering journeys remain unfinished. The full engineering
goal is not complete merely because this development checkpoint is delivered.
Codex-as-agent integration will be a separate project. PPT work remains deferred.

## Goal prompt

```text
/goal Improve Wright so engineers can author, carry out, inspect and reuse credible engineering processes. Address the product and engineering findings in specs/083-process-working-interfaces/mechanical-engineering-product-review.md: manufacturing-appropriate workflows, engineering validation and documents, an additional CAD system, and the remaining product usability work. Deliver implemented fixes, saved real workflows with inspectable outputs, repeatable evidence, and a concise user-testing handoff. Slide-deck production is deferred and excluded from this goal. Use GPT-6.1 Sol with High reasoning. Continue through the local implementation and verification milestones until the required work is done, I pause you, or configured resource limits stop the goal.

USER-AGREED WORK ORDER — 10 OCTOBER 2026

The primary objective is to improve Wright. Apply this priority to the remaining
M0-M5 work; their numbering is not an instruction to finish example preparation
before addressing a product defect. Preserve their engineering requirements,
authority boundaries and uncompleted deliverables.

1. Make ordinary user journeys dependable: enter a workspace; create a blank
   workflow; choose real workspace MCP capabilities; draw input/output connections;
   configure and save instructions; run; understand progress, waits and failures;
   open actual intermediate and final results; reopen and reuse the process.
   Start with the user's reported problems and reconcile their existing repair
   evidence. Verify through Wright's normal workspace controls.
2. Repair demonstrated shared gaps in explicit input/review steps, readiness,
   durable continuation and recovery, portable instructions/dependencies, result
   access, and common or Wright-generated working interfaces. Reuse the current
   owners and preserve the refined editor. Keep domain rules in versioned workflow
   assets/profiles and vendor behavior in independent providers.
3. Use a small set of existing, credible engineering workflows as acceptance
   cases for those changes. Reuse saved evidence when still applicable. Run fresh
   cases for a reproduced defect, an affected behavior, a missing acceptance case,
   or the final regression required below. Prove shared changes with a substantially
   different existing process. Do not expand the campaign or repeat successful
   native CAD/slicing runs merely to increase evidence counts.
4. Finish the necessary outstanding engineering example refinements after
   the relevant product journeys are dependable. Preserve the dock requirement
   conflict and actual swim-lane integration gap as explicit pending items. These
   example-specific dependencies do not delay independent Wright improvements,
   authorize changed engineering requirements, or count as completed work.

Do not create, revise, capture images for, render or validate presentation decks
under this goal. Preserve existing PPTX/PDF decks as historical artifacts. Their
improvement is deferred until separately requested and does not block completion.
Continue producing engineering drawings, verification documents and focused
screenshots needed to diagnose or verify Wright behavior.

On resumption, read the current execution ledger and remaining-work audit, then
maintain a compact, prioritized list of USER problems using the existing ledger.
For each item record the user task, observed failure/gap, existing shared owner,
smallest repair, and acceptance check. Distinguish Wright defects, provider limits
and example-definition conflicts. Select the next item by user impact and blocked
capability; do not follow the next numerical evidence entry automatically. Reconcile
any interrupted operation before retrying it, but do not let an evidence-only audit
displace a known product defect unless it is needed to establish correctness.

Report progress first as: what a Wright user can now accomplish; the problem fixed;
where the user can try it; and what remains unreliable or unavailable. Link concise
before/after evidence. Counts of runs, files and assertions are supporting evidence.
Keep engineering verification intact and retain the revised completion requirements
below. Record platform progress separately from example readiness and handoff
completion; do not claim the full goal complete while required work is outstanding.

AUTHORITY AND BOUNDARIES

I approve this implementation package, its routine technical planning refinements, local builds, targeted and regression testing, isolated digital runs, and installation/configuration of necessary free existing MCP providers in isolated environments. This submission approves the technical milestones; do not stop between them for routine lifecycle confirmation. It does not change Wright's configured user model globally. Use the available configured model paths, freeze and report actual routing, and identify missing capabilities honestly.

Preserve existing dirty work, source revisions, user workspaces, CAD documents and historical evidence. No reset, broad staging, destructive cleanup, commit, push, merge, release, public publication, supplier communication/upload/order, physical printing/machining, paid procurement, license acceptance or firmware/security workaround is authorized by this goal. Digital model/file generation and offline slicing are authorized. Use new isolated roots, workspaces and run subjects; do not resume or approve protected campaigns or earlier user runs. A failure of an independent provider is not permission to implement its vendor protocol inside Wright.

For new isolated digital test subjects only, I authorize predetermined synthetic input answers and synthetic review responses through the existing authorized test mechanism, explicitly attributed integration_test=true and tied to exact subjects. Show the real wait before answering. These responses cannot bypass mandatory failed checks, grant external-action authority, or count as human engineering/user acceptance. Keep a separate product-review example pending for my actual review. Old permissions to print in earlier conversations do not apply to this goal.

READ AND RECONCILE FIRST

Read AGENTS.md and relevant nested guidance, the constitution, docs/design/workflow-platform-vision.md, docs/design/process-apps.md, docs/architecture/workflow-platform-refactoring-plan.md, docs/architecture/workflow-instructions-and-interactions-plan.md, docs/design/engineering-demonstration-principles.md, docs/contributing/workflow-ui-integration.md and docs/mcp-catalog/mcp-server-testing-process.md. Apply V1-V7. Read Feature 083's plan, contracts, acceptance cases, instruction-portability completion/handoff/UI evidence/tasks/bug ledger and the relevant Feature 082 validation, rework and report-consumer contracts. Use the recorded product-review findings; consult historical demo screenshots only where needed to understand a specific product defect.

Record actual branch, dirty baseline, disk capacity, services, served build, authentication, configured models and workspace MCP bindings. Reconcile old pending notes with final evidence instead of restarting completed instruction-portability work. Create a new task/coverage/bug/progress ledger for this increment. Keep inherited implementation status separate from this goal's evidence and user acceptance. Preserve readable checkpoints across context compactions.

Wright remains a general engineering workflow platform. Start from the engineer's job, expected decisions and useful deliverable. The mechanical examples below are reference processes, not a mandatory lifecycle for every workflow. Reuse the accepted source runner, gateway, result/evidence model, Feature 082 validator, storage, workspace tabs, interaction contract, scoped client and shared UI kit. Generated interfaces contain no executor, independent status authority or vendor logic. Users request and refine them through Wright with the configured coding role. Instructions and engineering policy belong in versioned assets/settings or accepted workflow source, never executor literals.

M0 — ENGINEERING BRIEFS AND ACCEPTANCE BASIS

Before generating another model, write an engineering brief and verification plan for each selected example. Define purpose, intended use, material/process choice, critical interfaces, original constraints, loads/environment where applicable, datum/unit convention, deliverables, acceptance methods and remaining physical questions. Identify supplied facts, fictional dataset inputs, delegated assumptions and measurements separately. Retain all applicable original requirements; document the smallest changes to tool bindings and added deliverables in a new revision.

Use two existing assignments as the default primary demonstrations:

A. Sheet-metal barcode-reader wall dock: tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/. Read every applicable context, policy, stock-selection, CAD-choice and company-capability revision, plus its binding and Feature 082 checks. The process produces a fabricated sheet-metal review package. Keep native Solid Edge sheet metal, folded STEP and true developed DXF. Do not send this design to a polymer slicer. Preserve the dimensional basis, stock/bend-rule selection, mounting slots, cable notch, split front lip, reliefs and outstanding supplier issues. Supplement with a real dimensioned drawing and inspection plan. Retain the original quantity and local simulated supplier-preview scope; no real supplier effect. Keep manufacturing release held where required evidence or supplier confirmation is absent.

B. Additive focus-wheel replacement: tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/. Rebind a fresh copy to FreeCAD for native solid modeling; retain the original sketch, six scallops, 38 mm envelope, 18 mm overall height, D-shaft interpretation, clearances, blind socket, grip details, material/profile choices and restrictions. Preserve exact original context rather than relying on this abbreviated list. Produce native editable CAD, STEP, an inspection drawing/document, controlled mesh export, actual orientation/support assessment, and an actual offline sliced package through an existing independent provider. The PETG profile must not become PLA silently. Keep dimensional fit, torque/temperature behavior and physical printing explicitly unverified unless corresponding actual evidence exists. A provider producing a mesh or G-code alone does not establish these properties.

Inspect and reuse the existing 30 examples and useful validation profiles. Do not rewrite the campaign. Label the earlier sheet-metal-to-slicer sequence as a historical integration test in the new index, preserving the original run records. Do not invent a printed-mockup purpose retroactively. If an existing brief has a contradiction, preserve it and use its accepted resolution or report a precise blocker. Routine declared assumptions may be chosen and documented under the saved policy; do not impose a new blanket prohibition on AI design choices.

M1 — QUALIFY AN INDEPENDENT ADDITIONAL CAD SYSTEM

Use FreeCAD through the existing neka-nat/freecad-mcp provider as first choice. Start with docs/mcp-catalog/evidence/curation-2026-09-09/freecad-linux.json and the FreeCAD Core setup recipe. These establish historical box/STL/gateway scope only. Inspect the current catalog source, actual version, addon, tool schemas, launch settings and dependencies. Reconcile catalog aliases by source; packages/freecad_mcp is a different upstream and is not automatically the selected provider. Prefer the recorded qualified version unless required features justify an explicitly recorded upgrade.

Follow the clean Intel Linux Wright-container qualification process, installing host dependencies only for the selected provider. Also prove the actual user-facing host connection used by this goal. If Docker or a native host is unavailable, record the exact unverified platform scope and continue other work; do not mark that gate passed. Do not add CAD software or vendor SDKs to Wright's base image/runtime to satisfy qualification.

Qualify initialize/tools/list, actual backend call and gateway proxy, then native editable solid creation, save/reopen, parameter change, measurement, STEP and mesh export, actual screenshot and drawing export as needed by the jobs. Check file contents, units, topology and feature correspondence independently. Probe cold start, unavailable-addon diagnostics, restart and a second fresh run without duplicate effects or overwriting the first. Record host/version/tool/schema/configuration identities and setup/recovery recipes. Expose the real provider in the normal workspace tool picker and readiness views.

Current Solid Edge evidence says native Draft creation was unavailable. Qualify an existing independent drawing capability, preferably FreeCAD TechDraw reading the exact upstream STEP, for the sheet-metal drawing. Keep actual native flat-pattern generation with its owning sheet-metal CAD provider. Do not fabricate a dimensioned drawing by putting dimensions on an AI picture. Export paths and live CAD document identity must refer to the intended object, not whichever document happens to be active.

Use bounded retries for provider failures. Keep protocol/backend changes external. Select another existing provider only through an explicit recorded binding revision that preserves the required capability and engineering scope. Do not spend the whole goal rewriting a vendor integration, silently call a host tool outside the declared workflow to fake MCP success, or present mocked output as live CAD proof.

M2 — ENGINEERING VERIFICATION AND REVIEW DOCUMENTS

Reuse Feature 082's requirement baseline, validation profiles, measurements, exact output subjects, findings, bounded rework, currentness and review authority. Inventory what already exists before extending a contract. Reuse existing report exports and result readers; coordinate with the separate reporting work rather than creating a competing reporting application. Implement only demonstrated shared gaps. Domain-specific engineering rules belong in versioned profiles, source references and workflow assets.

Create a compact engineering package for each job: design basis, requirements-to-verification matrix, assumptions/decision log, design assessment, manufacturing assessment, drawing/inspection plan and exact revision manifest. Sections may share a document. A matrix row identifies requirement and source, expected value/unit/frame/tolerance, method and source of acceptance, exact artifact/feature, actual observation, uncertainty or limitation, status and required review. Freeze criteria before evaluating outputs. Use familiar engineering language in the default view and technical identities on demand.

Apply relevant documented practices. Research primary authoritative references and record edition, applicability and accessible source. ASME Y14.100 and Y14.5 are candidate drawing/dimensioning references; ISO/ASTM 52910 is general additive-design guidance; ASME V&V 10 is relevant if computational solid mechanics is actually used. Do not claim standards compliance from an abstract or checklist, invent clauses, or buy standards. Keep customer/company requirements, supplier design rules and general standards distinct. A reference family does not automatically become a new mandatory compliance requirement for the old fixture.

At meaningful handoffs check what the next engineer/tool relies on:
- Requirements to CAD: resolved dimensional basis, interfaces, material/process, delegated choices and intended verification method; preserve original requirements.
- CAD to downstream work: actual native/export identity, shape validity, units/frame, key features and dimensions, relevant mass/volume only when independently supported, and consistency between native/neutral/mesh forms. Tolerances for numerical conversion are distinct from manufacturing tolerances.
- Sheet metal: constant thickness, exact material/temper/stock evidence, bend radius and angle, development method/bend allowance, reliefs, hole/slot-to-bend distances, flange/tool access and sequence limits, genuine unfolded geometry, usable closed cut contours, bend information and correspondence to the folded model. Quantify unresolved development discrepancies and retain required holds.
- Additive: interface clearances, socket/bore feature measurements, mesh deviation from CAD, manifold topology, minimum walls, orientation, support contact/removal access, profile/material correspondence and actual toolpath/package contents. Treat anisotropy, creep and process variation explicitly. Do not infer printed strength or fit from bulk material properties or a successful slice.
- Drawing/package: sufficient views and sections, functional dimensions and tolerances, units, material/finish, part/revision identity, manufacturing notes, inspection characteristics and exact agreement with the assessed geometry. A correct title block alone is insufficient. Keep visualization renders separate from engineering definition.

Use analysis only where it answers the job's engineering question. When needed, retain loads, restraints, material source, idealizations, solver input/results, convergence/sensitivity and an appropriate independent calculation or comparison. Do not add FEA to inflate the workflow or use an idealized polymer model to certify a printed part. Where physical validation is absent, provide a practical test/inspection plan and label that scope unevaluated.

Demonstrate a genuine revision: a predeclared deliberate defect in a separate test copy must produce a specific finding and hold dependent work; correct it within the accepted bound, remeasure, regenerate affected outputs and revalidate. Keep all attempts. A changed geometry, material, profile or instruction revision invalidates dependent assessments/reviews. Cosmetic layout changes alone must not do so. Missing mandatory readers remain unavailable/held. No self-authored AI verdict, schema pass, hash, photograph or zero-check assessment can replace required measurement or human acceptance.

M3 — COMPLETE THE PRODUCT REVIEW PRIORITIES

Reproduce current behavior before fixing it. Implement the four recommendations on the existing “The next product review” slide through shared Wright mechanisms:

1. Final deliverable: prominent usable image/model/drawing or comparison; obvious Open and Download actions; useful intermediate evidence; exact result identity. Selecting the output from either flowchart or working view focuses its actual reader in a Wright tab. Pending, failed, missing and stale results are explained. No silent blank result or accidental rerun.
2. Status and questions: clear activity/progress, one understandable primary next action, planned input separated from review/approval, external wait, stale observation and failure. Put the pending question beside its relevant evidence, ahead of diagnostics. Provide field-level errors and visible same-run continuation. A disconnected UI reconciles without starting another job. Do not invent percentage completion when the backend cannot support it.
3. Cancellation: labels and enabled state agree with backend-permitted actions for the exact run/operation. Explain unsupported or already-finished states. Distinguish request sent from confirmed cancellation; no claim that a physical process stopped because an HTTP/MCP request ended.
4. Repeat use: friendly process/result names and a clear new-case action; preserve old results; allocate unique output locations through existing shared mechanisms. Address the previous one-shot CAD-folder limitation with provider-neutral, revision-safe artifact binding where feasible. No routine manual JSON/path editing, disabling safe mode or overwrite of earlier evidence. Reopen an existing run without executing it again.

Simplify user-facing “Representation,” implementation paths and noisy default labels where they obstruct the task, retaining details on demand. Make inputs, instructions, requirements, findings and transfer forms readable at realistic desktop sizes. Preserve the refined flowchart, typed port drawing, source/inspector editing, Undo/Redo and saved layout. Ordinary workspace entry, authentication, settings, real MCP choices and existing Git access must remain usable.

Locate and reuse the existing swim-lane tools in the engineering examples. Show
engineering, automated-tool, review and supplier-handoff responsibilities where
they apply, with real artifact/decision handoffs and links to the same exact
blocks/evidence. The external supplier lane is a local simulation/HOLD under this
goal, not an executed supplier effect. No mandatory lane layout applies to all
Wright processes. Verify this view through its actual supported workspace entry;
if its implementation is on another branch, record the ownership/integration gap
and preserve that work rather than inventing a lookalike and claiming reuse.

Verify the common view first. Create or refine at least one saved tailored engineering interface by requesting it THROUGH WRIGHT with the existing coding role, public kit and scoped client. Show exact requirements/findings/artifacts and permitted review actions without inventing decisions. Prove save, second-run reuse, update compatibility and common-view fallback. Do not substitute a hand-built standalone demo page or call a screenshot a generated interface.

M4 — SAVED WORKFLOWS, EXPLORATORY TESTING AND REGRESSION

Author/save/run through Wright's normal services; verify the actual served production build through the workspace Workflow/Workflows control. Include graphical authoring with real workspace MCP choices and drawn text/image/geometry/evidence connections. External scripts may drive and inspect Wright; they may not replace its runner or synthesize successful artifacts outside the declared process. Use actual engineering outputs between meaningful stages.

For each primary mechanical process, retain a baseline run and a meaningful changed-input/revision run under a declared test variation, preserving original baseline requirements. Verify preserved history, new measurements/results, updated dependencies, usable output readers and repeat-run isolation. Demonstrate a planned input and an engineering review as distinct waits. Use synthetic responses only within the isolated authority above. Leave actual engineering acceptance pending where appropriate.

Exercise the existing heat-spreader analysis or another substantially different existing non-manufacturing workflow against shared UI/validation changes. Retain its original numerical/engineering criteria. A small mass calculation may be a useful interaction regression; do not present it alone as the substantive engineering demonstration.

Cover targeted negatives: wrong units or feature dimension, manufacturing-method/material mismatch, stale drawing/output after geometry revision, missing measurement capability, unavailable provider, provider success with absent/invalid output, incomplete required input, invalid/duplicate/stale answer, uncertain cancellation, disconnect/reload and duplicate Start. Use clearly labelled fixtures where live failure injection would risk user work. Require visible specific diagnostics and inaccessible forbidden downstream actions. Do not weaken validators or narrow criteria after a failure merely to produce green tests.

Recheck saved instruction behavior across changed defaults, cloning, export/import to a separate workspace and durable continuation. Required source/reference/validation/UI dependencies travel with the process; credentials, prior answers, approvals, live runs and trusted UI builds do not. Preserve model/adapter provenance and actual request evidence. Shared scope/schema/validation enforcement remains backend-owned.

Add and run focused tests for reproduced defects and affected source/runtime/API/adapter/frontend contracts; run the relevant 082/083 regressions and package-boundary/resource checks. Use the playwright-ui-walkthrough skill for human-repeatable browser records and actual visual inspection. Passing recorder assertions alone is not a usability review. After the final implementation fix, perform two fresh different end-to-end exploratory journeys, including actual engineering outputs, without new critical/high-severity defects. Record defects, reproduction, cause, repair and original-reproduction retest. Keep software, live-provider, numerical, engineering, physical and human-acceptance claims separate.

M5 — CONCISE PRODUCT HANDOFF (SLIDE DECK DEFERRED)

Provide a short account of what users can now accomplish, the Wright problems
fixed, remaining limitations and a human test checklist. Link directly to the
actual workspace entry, saved workflows, exact results, engineering documents
and review states. Reuse existing evidence and include focused before/after
captures when they clarify a repaired behavior. Give the user an obvious answer
to “where is the image/model/drawing?” Handle authentication securely.

The existing swim-lane capability remains a product integration/example requirement
under M3, with its actual workspace entry and handoffs recorded. Its appearance
in a slide deck is deferred. No new PPTX, presentation PDF, deck-specific image
capture, slide rendering or presentation-polishing task is required or authorized
by this revised goal. Retain historical decks and their limitations unchanged.

COMPLETION AND PERSISTENCE

Keep a requirement/acceptance ledger that maps each milestone and user concern to actual evidence. Update agent guidance and relevant plans so future agents preserve manufacturing intent, substantive tool handoffs, applicable engineering documents, exact-output checks and readable user-facing evidence. Keep the platform general and preserve its external integration boundary. Do not rewrite historical completion records; append a clearly dated reassessment where claims need qualification.

Completion requires the shared usability fixes, the additional live CAD workflow, both mechanically coherent saved processes with their required digital outputs/checks, a substantially different regression journey, deliberate input/review and repeat/portability proofs, and the concise product handoff. Slide-deck work is deferred and excluded from completion. Expected test failures and intentionally pending real reviews are valid evidence; unresolved required digital capabilities are unfinished work, not a passing demonstration. No physical fabrication or human acceptance is required to complete this local goal, and neither may be claimed.

Proceed autonomously on routine design/implementation choices within the accepted briefs and saved assumption policy. Ask only when necessary for unavailable resources/credentials, real authority, or a consequential unresolved requirement that cannot be resolved from existing accepted context. Keep independent work moving when one provider is blocked. Bound retries, checkpoint failures and exact resume instructions, and follow goal lifecycle rules for pause, completion and external blockers. Do not run unrelated work or duplicate green tests merely to fill time.
```

## Submission shortcut

For the existing paused goal, resume it with:

```text
Resume the existing goal using the revised instructions in specs/083-process-working-interfaces/mechanical-engineering-usability-goal.md. Follow the 10 October user-agreed work order: Wright user journeys and shared fixes first, focused example-based verification next. Skip slide-deck work. Preserve existing work and evidence; reconcile the current ledger before choosing the next product problem.
```

The following submission is for starting a goal when no unfinished goal exists.
After selecting **GPT-6.1 Sol / High**, submit:

```text
/goal Execute D:/repos/wright/specs/083-process-working-interfaces/mechanical-engineering-usability-goal.md in full. I approve its local implementation, isolated testing, provider setup and explicitly attributed synthetic responses within the boundaries stated there.
```

If the slash-command UI fails, ask the agent to start the saved goal with the
same explicit approval. Current implementation and evidence are tracked in
[the execution ledger](mechanical-engineering-execution.md).
