# Feature Specification: Engineering Workflow Templates

**Feature Branch**: `codex/081-engineering-workflow-templates`

**Created**: 2026-09-11

**Status**: Planning review

**Input**: Provide a dropdown of ten example engineering workspaces for demonstrations and social-media material. Establish the UI first, then make the 3D-printing, Raspberry Pi enclosure/CFD, and sheet-metal/SendCutSend examples work end to end. Choose seven further examples from credible engineering MCP capabilities. Preserve the existing workflow editor and previously agreed approval boundaries. These are engineering workflows, not usability studies.

## User Scenarios & Testing

**2026-09-12 campaign amendment:** Add three realistic human-submittable datasets
per existing template (thirty total), with user/company profiles, policies and
capabilities, prompts, documents/data and original images. Execute them as an
unattended integration campaign using explicit manual/test-auto approval modes
and labeled test destinations for external effects. Persist actual outputs and
the timestamped unique counts for datasets created, pairs run, and full processes
with expected files. Content-validity measurement is deferred and remains zero.
See [dataset-campaign/plan.md](dataset-campaign/plan.md). This file-presence cycle
does not satisfy or weaken the parent feature's engineering qualification.
For this campaign only, FR-011's simulation restriction permits explicitly
bound printer/supplier transport simulators within the full canonical graph.
This exception does not permit simulated CAD, mesh, slicing, solver, drawing
or report operations, and it does not satisfy FR-010/FR-021 qualification.
Existing execution safety and artifact integrity checks remain active while
new content-correctness measurement is deferred.

### User Story 1 - Start from a real engineering example (Priority: P1)

An engineer opens **Workflows** in an existing workspace, chooses **Start from template**, reviews ten engineering examples in a dropdown, and creates an editable copy of one example. Before creation, the engineer can see the problem being solved, supplied inputs, expected outputs, prerequisites, external effects, and current run-readiness status.

**Why this priority**: The template entry experience is the requested first milestone and must fit the reviewed workspace editor without replacing its authoring capabilities.

**Independent Test**: Enter a normal workspace through its Workflows control, inspect all ten entries, create each template under a new name, and verify that every copy opens on the established canvas with its source, inspector, editing, undo/redo, save, reopen, drag, connect, and artifact actions intact.

**Acceptance Scenarios**:

1. **Given** a writable workspace, **when** the engineer opens the template control, **then** exactly ten engineering examples appear with distinct purposes and truthful readiness information.
2. **Given** an existing workflow, **when** an engineer creates a template copy, **then** the new workflow receives its own identity and filename and neither overwrites nor mutates the existing workflow.
3. **Given** a template whose live tools are not configured or qualified, **when** the engineer reviews or opens it, **then** the workflow remains fully inspectable and editable while Run explains the missing prerequisites and cannot report simulated or fixture output as a live result.
4. **Given** the template menu, **when** the engineer dismisses it without creating, **then** no workflow, approval, run, or external action is created.

---

### User Story 2 - Run the three flagship workflows (Priority: P2)

An engineer can configure and run three complete examples: an image-to-3D-print workflow, a vented Raspberry Pi enclosure design and CFD comparison, and an image/text-to-sheet-metal supplier handoff. Each produces recognizable engineering artifacts, preserves lineage, checks the actual output, and pauses at the correct external-action gates.

**Why this priority**: These are the first working demonstrations requested after the UI is established.

**Independent Test**: Run each example in a clean supported environment with its declared input fixture and selected integrations. Independently inspect its intermediate and final artifacts, exercise a negative or correction path, and verify that no physical or commercial action occurs without a fresh decision bound to the exact action subject.

**Acceptance Scenarios**:

1. **Given** an original image and an explicit reference dimension, **when** the 3D-print workflow runs, **then** it retains the image, generated mesh, measured/repaired/oriented mesh, support configuration or supported toolpath representation, sliced package, settings, and independent checks before requesting authorization to transfer that exact package to the selected Bambu P1S.
2. **Given** a selected Raspberry Pi model and cooling requirements, **when** the enclosure workflow runs, **then** it retrieves manufacturer dimensions with source identity, creates a reviewable design document, generates and measures a CAD enclosure from that document, constructs the matching fluid domain, runs CFD, and reports convergence, mass balance, mesh sensitivity, and comparable vent results from solver fields.
3. **Given** image/text intent and approved manufacturing context, **when** the sheet-metal workflow runs, **then** it creates native sheet-metal CAD, performs evidence-backed design checks with at most two indexed corrective revisions, exports and independently verifies the exact native model, folded STEP, and developed DXF, and stops for human review before supplier submission or cart/quote handoff.
4. **Given** a changed input, workflow definition, binding, CAD model, mesh, slice, export, device, or supplier package, **when** a prior decision is evaluated, **then** that decision is stale and cannot authorize continuation.

---

### User Story 3 - Explore seven more engineering demonstrations (Priority: P3)

An engineer can start from seven further examples covering structural analysis, electronics, manufacturing aids, robotics data, thermal analysis, wiring harnesses, and system simulation. Every example states whether it is a reviewable template, needs setup, or is independently verified as runnable.

**Why this priority**: The complete set demonstrates Wright across multiple engineering disciplines without diluting the first three implementation milestones.

**Independent Test**: Instantiate all seven workflows and confirm their inputs, outputs, acceptance checks, prerequisite bindings, and negative controls. Promote an example to runnable only after its real tools and output assertions pass the documented qualification process.

**Acceptance Scenarios**:

1. **Given** the seven additional templates, **when** an engineer compares them, **then** each solves a concrete engineering problem and declares measurable checks on actual artifacts or numerical results.
2. **Given** a catalog-listed or newly discovered server, **when** its template is shown, **then** catalog presence, successful setup, protocol discovery, real backend execution, Wright execution, and independent result verification are presented as separate facts.
3. **Given** a deterministic fixture or mocked result, **when** it is used for UI demonstration, **then** it is visibly labeled and cannot promote a template to live or verified status.

---

### User Story 4 - Capture honest demonstration material (Priority: P4)

A demo operator can produce a repeatable capture package from a verified run: approved input attribution, key intermediate visuals, final engineering output, checks, run and artifact lineage, and a concise caption draft. Wright does not publish the material.

**Why this priority**: The examples should support social posts without turning polished imagery into unsupported engineering claims.

**Independent Test**: Generate a capture package from each verified flagship run and confirm that every included result resolves to the recorded run and artifact, while fixture, simulation, unqualified integration, and physical-action status remain visible.

**Acceptance Scenarios**:

1. **Given** a verified run, **when** the operator creates its capture package, **then** the package contains only selected redacted engineering evidence and records the exact source run and artifact digests.
2. **Given** a run containing secrets, private paths, personal information, device credentials, or unlicensed input media, **when** capture is attempted, **then** the package blocks or omits that content and explains the correction.
3. **Given** a capture package, **when** it is completed, **then** no social account, supplier, printer, or other external destination is contacted.

### Edge Cases

- A template version is removed or changed after the menu loads; creation fails cleanly or uses the exact reviewed version, never a mixed definition.
- Two sessions choose the same workflow filename; exclusive creation preserves the winner and asks the other session to choose a new name.
- A template source or layout is invalid, oversized, contains unsafe paths, or refers to missing blocks; it is rejected before workspace mutation.
- A configured tool disappears, changes schema, becomes unqualified, or returns success without the declared artifact; readiness or execution fails with an actionable explanation.
- A live run is interrupted, times out, or is cancelled after an external operation may have completed; the run records the uncertainty and never blindly retries the mutation.
- A source lookup returns conflicting dimensions or a non-manufacturer source; the design document records the conflict and requires resolution before CAD.
- A mesh or CAD result looks plausible but has the wrong scale, topology, boundaries, units, or identity; independent checks stop the workflow.
- A printer is offline or the selected device does not match the approved device; transfer remains unapproved and retry requires current device status.
- A supplier preview cannot prove uploaded-file association, bend recognition, material, quantity, or price; handoff readiness remains false.

## Requirements

### Functional Requirements

- **FR-001**: Wright MUST provide exactly ten built-in engineering workflow templates in the first release: 3D Printed Replacement Part, Vented Raspberry Pi Enclosure, Sheet-Metal Supplier Handoff, Lightweight Equipment Bracket, Sensor-Interface PCB, Parametric Drill Jig, Robot Tracking Diagnosis, Conduction Heat-Spreader Sizing, Sensor-and-Fan Wiring Harness, and Water-Heater Power Sizing.
- **FR-002**: The template entry MUST be part of the established workspace Workflows experience and MUST preserve the reviewed canvas, source, inspector, AI review, run overlay, direct manipulation, typed ports, file tabs, save/reopen, conflict handling, undo, and redo capabilities.
- **FR-003**: The selection surface MUST show title, discipline, purpose, expected visual result, provided inputs, user-supplied inputs, expected engineering outputs, tool/setup prerequisites, external effects, and one truthful readiness state before creation.
- **FR-004**: Instantiating a template MUST create a fresh, independently editable workflow identity, semantic definition, presentation state, and safe workspace filename without importing runs, approvals, credentials, or mutable external state.
- **FR-005**: Template preview and cancellation MUST be read-only. Creation MUST be explicit, exclusive, and atomic and MUST never overwrite another workflow.
- **FR-006**: Every template MUST remain inspectable and editable when its live integrations are unavailable. Execution MUST fail closed at the first unmet prerequisite and MUST explain the required setup or qualification.
- **FR-007**: Wright MUST distinguish template definition status, integration setup, real backend execution, Wright-path execution, engineering-result verification, physical completion, and user acceptance. A lower level MUST NOT imply a higher level.
- **FR-008**: Each live workflow step MUST bind to an exact server, tool, and input-schema version at run time; changes MUST invalidate readiness until reviewed.
- **FR-009**: Each claimed output MUST be a bounded workspace artifact or result with producer, definition revision, run, input, binding, media type, size, and digest lineage. Tool success without the declared output MUST fail.
- **FR-010**: Engineering acceptance MUST evaluate actual geometry, fields, files, or numerical results with independently computed or inspected assertions. Images and AI narratives alone MUST NOT establish engineering success.
- **FR-011**: Fixtures, mocks, theoretical correlations, and simulated outputs MAY support the UI milestone only when clearly labeled and isolated from live or verified evidence.
- **FR-012**: The 3D-printing template MUST preserve dimensional reference, source image, generated mesh, repair/orientation evidence, support configuration or support-bearing slice representation, slicing profiles, final print package, and checks for scale, manifold/toolpath validity, build-volume fit, and declared material/profile compatibility.
- **FR-013**: Printer transfer MUST require a fresh human authorization bound to the exact final package, printer identity, material and process profile. Authorization to transfer MUST NOT imply that the print physically succeeded; receipt and device status are separate evidence.
- **FR-014**: The Raspberry Pi template MUST require a selected board model, retrieve dimensions from a manufacturer-controlled source with date and document identity, and encode board envelope, mounting holes, connector/keepout geometry, thermal loads, vent assumptions, and operating conditions in a reviewable design document before CAD.
- **FR-015**: The Raspberry Pi CAD and CFD stages MUST verify design-document-to-CAD dimensions, CAD-to-fluid-domain identity, boundary names, mesh quality/sensitivity, solver convergence, mass balance, and results extracted from computed fields. The abandoned OpenFOAM integration that substituted different geometry MUST NOT be used.
- **FR-016**: The sheet-metal template MUST preserve the recovered sequence and policies: intent/context document; native CAD with exact installed material readback; independent measured design check; no more than two indexed corrective CAD revisions; native model, folded STEP and true developed DXF export; hash-bound DXF verification; supplier preview; and user-controlled cart/quote handoff.
- **FR-017**: Passing the sheet-metal design check is an automated engineering gate, not a human supplier approval. The supplier gate MUST verify exact uploaded-file association, units, scale, stock, thickness, quantity, services, bends, warnings, price, currency, delivery, shipping/tax availability, and timestamp before handoff can be ready.
- **FR-018**: Wright MUST NOT place an order, pay, use stored payment, accept production-releasing credit terms, contact supplier support, or record card data. The user performs final purchase outside workflow automation.
- **FR-019**: Human approval and continuation MUST be durable, resumable, and bound to the exact definition, input, artifact, binding, device/destination, and proposed external action. Any relevant change MUST invalidate the decision; retries MUST not replay completed mutations blindly.
- **FR-020**: The seven additional workflows MUST use the inputs, outputs, checks, qualification gaps, and implementation order defined in the workflow acceptance contract. Numerical values supplied there are example requirements, not pre-observed results.
- **FR-021**: A template MUST NOT be promoted to verified runnable until its selected integrations pass Wright's clean-environment qualification, real backend and gateway execution, artifact verification, negative/recovery case, and independent engineering assertions.
- **FR-022**: A verified run MAY create a local demonstration capture package containing selected visuals, a caption draft, input rights/attribution, verification status, and lineage. It MUST exclude secrets and private data and MUST NOT publish externally.
- **FR-023**: All user actions in the template UI and all approval/external-action controls MUST be keyboard accessible, visibly focused, and have stable test identifiers.
- **FR-024**: All template list, instantiate, readiness, run, artifact, approval, resume, and capture operations MUST enforce the existing workspace/session and role policies and generate traceable structured records.
- **FR-025**: The feature MUST work offline for template browsing, instantiation, editing, validation, saved fixtures, and previously cached references. Online/vendor operations MUST declare availability and fail gracefully without weakening evidence.
- **FR-026**: Existing user-authored workflows, legacy template formats, accepted definitions, layouts, run history, and data recovery behavior MUST remain readable and unchanged unless the user explicitly creates a new template copy.

### Key Entities

- **Engineering Workflow Template**: A versioned, immutable catalog item describing one engineering problem, editable starter definition, presentation, inputs, outputs, prerequisites, readiness, visual preview, acceptance checks, and provenance.
- **Template Instance**: A fresh workspace-owned workflow created from one exact template version, with independent identity, filename, revision, and layout.
- **Capability Requirement**: The exact operation and qualification evidence a workflow step needs, separate from local configuration and current availability.
- **Engineering Artifact**: A workspace-confined input or output with immutable lineage and verification state.
- **Approval Checkpoint**: A human decision about an exact action subject and its evidence, with explicit invalidation and continuation state.
- **External Action**: A proposed printer transfer, supplier upload/preview, or other non-local mutation whose request, outcome, ambiguity, and safe retry behavior are recorded.
- **Engineering Assertion**: A versioned check over actual artifacts or results, including method, tolerance, observed value, pass/fail state, and evidence.
- **Demonstration Capture Package**: A local, redacted set of selected visuals, caption material, attribution, status disclosures, and lineage from one verified run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: From a normal workspace, an engineer can inspect all ten templates and create a chosen editable copy in no more than 60 seconds and four deliberate actions, without losing any existing workflow.
- **SC-002**: All ten templates open successfully in the established graphical editor and survive edit, save, close, and reopen with identical accepted meaning and compatible layout.
- **SC-003**: Before any run, 100% of templates show accurate prerequisites, external effects, and readiness, with zero fixture-only or unqualified examples labeled as live verified workflows.
- **SC-004**: Each of the first three examples produces its declared real intermediate and final artifacts, passes independent positive checks, stops on at least one engineered negative case, and preserves complete lineage across correction and rerun.
- **SC-005**: In approval tests, 100% of relevant input, artifact, workflow, binding, device, destination, or action changes invalidate the prior decision, and zero denied, stale, or absent decisions trigger printer or supplier mutations.
- **SC-006**: The Raspberry Pi example reports results from a verified matching CFD domain with declared convergence, mass balance and mesh sensitivity; substituted geometry or theoretical-only results are rejected in every negative test.
- **SC-007**: The sheet-metal example cannot reach handoff-ready until its exact native CAD, STEP, DXF, design-check evidence, export verification, supplier selections, and quote association all pass; it places zero orders and records zero payment data.
- **SC-008**: Each additional example has one independently reviewable real artifact or result, one measurable engineering acceptance set, and one negative/recovery case before it is promoted to verified runnable.
- **SC-009**: A local capture package can be generated for each verified flagship run in under two minutes, and every included technical claim resolves to its run evidence while no external post is created.
- **SC-010**: Component, page-level browser, and system tests cover template states and the served workspace entry path; the final browser verification enters through Workflow/Workflows and preserves the reviewed authoring interactions.

## Assumptions

- “Example workspaces” means workspace-owned workflow copies created from packaged templates; the template does not clone or create a separate top-level Wright workspace.
- The first UI milestone includes all ten complete, reviewable workflow definitions and readiness disclosures. Only the first three must become live and independently verified before work begins on the remaining seven.
- Template inputs use distributable, attributable demo assets created for the feature or materials the project has explicit rights to use.
- The selected Raspberry Pi model is an explicit input; the initial distributable fixture targets Raspberry Pi 5 and pins the current official mechanical drawing used by the run.
- Support generation may be represented by slicer support configuration and support-bearing toolpaths rather than permanently modifying the source mesh, as long as the step and artifacts make this distinction visible.
- Vendor accounts, credentials, licensed hosts, printer access, supplier settings, and internet access are user-provided prerequisites and are never embedded in templates.
- Social publishing, supplier purchasing, payment, production release, and claims that a physical build succeeded are outside this feature.
- This feature validates real engineering work and functional UI behavior. It does not plan or claim a usability study, adoption study, or representative human-subject evaluation.
