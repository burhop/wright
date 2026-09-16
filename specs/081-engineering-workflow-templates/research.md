# Phase 0 Research: Engineering Workflow Templates

Research was completed on 2026-09-11 against the consolidated `dev` baseline, the recovered canonical workflow editor, the current Wright MCP catalog, the September 11 discovery sweep, the clean-container testing process, and the recovered sheet-metal evidence workspace. Upstream links establish documented capabilities only; they do not replace Wright qualification.

## Decision 1: Extend the reviewed canonical workspace editor

**Decision**: Add template selection and instances to the workspace-scoped `.workflow.wflow` experience recovered in feature 080. Preserve `WorkspacePanel`, `WorkflowRecoveryPage`, `WorkflowRecoveryConcept`, the React Flow canvas adapter, the command system, source/CAS behavior, and the existing run/artifact viewer. A template creates one fresh canonical definition plus separate layout and template-provenance metadata.

**Rationale**: `docs/contributing/workflow-ui-integration.md` identifies `codex/080-canonical-workflow-recovery` as the latest reviewed design and explicitly requires runtime work to preserve its authoring capabilities. The consolidated code already supports text, file, image, AI prompt, MCP task, direct MCP, CAD, design-check, and terminal review concepts. It also exposes a separate legacy Rivet template endpoint; that endpoint creates Rivet projects and cannot become the semantic authority for these native examples.

**Alternatives considered**:

- Extend the legacy Rivet template catalog: rejected because the current native language contract forbids new Rivet dependencies and the reviewed UI uses canonical workspace source.
- Add a detached examples route or separate editor: rejected because workspace entry and the existing graphical editor are explicit acceptance requirements.
- Dispatch runtime behavior by template ID: rejected because templates must remain ordinary editable workflows and runtime operations must be versioned and generic.

## Decision 2: Ten immutable definitions, fresh editable instances

**Decision**: Package exactly ten immutable catalog entries. The list/preview is read-only. Instantiate performs an exclusive workspace source create with a new workflow ID, fresh block IDs, independent layout, and a hidden provenance record containing template ID/version/digest. It imports no run history, approval, credential, or destination state.

**Rationale**: Fresh identities prevent collisions and cross-instance run/approval leakage. Version/digest provenance makes a social demo repeatable without freezing the engineer's copy after creation.

**Alternatives considered**:

- Open the packaged template directly: rejected because editing would mutate shared source or require a second authoring authority.
- Create a full top-level workspace per selection: rejected because the established product model owns workflows inside the active workspace.
- Silently upgrade instantiated templates: rejected because it would change accepted workflow meaning and stale evidence.

## Decision 3: Truthful readiness is a product concept

**Decision**: Track definition validity, prerequisite configuration, server qualification, current availability, real backend execution, Wright-path execution, engineering verification, external receipt, physical completion, and user acceptance separately. The template card derives a simple state (`reference`, `setup_required`, `ready`, `verified`) from these facts while exposing details. Fixture and simulated results never satisfy live states.

**Rationale**: The catalog's strongest warning is that protocol discovery and plausible output can still conceal the wrong geometry or a missing artifact. The abandoned `openfoam-mcp-webworn` integration claimed a pipe-flow result while meshing a rectangular block and returned a theoretical correlation rather than a value from solver fields. `freecad-mcp-sandraschi` is failed because reported success did not produce the required artifact.

**Alternatives considered**:

- One enabled/disabled flag: rejected because it collapses materially different evidence.
- Allow “demo success” to stand in for tool execution: rejected because the examples are intended to demonstrate real engineering work.

## Decision 4: Qualification follows the existing clean-container process

**Decision**: Each new or selected MCP adapter must follow `docs/mcp-catalog/mcp-server-testing-process.md`: pinned source and prerequisites; clean Intel Linux environment when supported; direct startup and discovery; smallest real backend operation; Wright gateway operation; artifact inspection; negative/recovery behavior; cleanup; and a reusable recipe. Licensed, credentialed, Windows-only, printer, or vendor boundaries receive equivalent disposable-host evidence and remain `setup_required` until available.

**Rationale**: This preserves the base image boundary and establishes actual outputs without adding every engineering host to Wright.

**Alternatives considered**:

- Install hosts into the base image: constitutionally prohibited.
- Treat upstream tests as Wright qualification: rejected because they do not prove Wright gateway, workspace, policy, or artifact behavior.

## Decision 5: Three flagship workflow integrations

### 5.1 3D Printed Replacement Part

Use an original image with an explicit reference dimension and engineering purpose. The preferred first generation host is cataloged `blender-mcp`, whose narrow box/STL path has qualification evidence; its credentialed image-to-3D integrations remain unqualified. Qualify a selected generator, mesh checker/repair path, slicer/support adapter, and Bambu P1S transfer adapter separately. Bambu Studio's documented CLI supports profiles, orientation, slicing, and 3MF export ([upstream CLI documentation](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage)); this does not establish printer submission. Bambu's current third-party authorization boundary informs the transfer gate ([integration policy](https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/)).

Supports may be slicer-generated toolpaths rather than a permanently combined mesh. Preserve the source mesh, repaired/oriented mesh, support parameters/preview, final package, profiles, independent scale/topology/build-volume checks, and receipt/status separately. No runtime catalog entry currently establishes Bambu, Meshy, Tripo, or a dedicated slicer adapter.

### 5.2 Vented Raspberry Pi Enclosure

Make board model explicit and initially use the official Raspberry Pi 5 mechanical drawing ([manufacturer PDF](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf)). Cache source identity and extracted dimensions; encode envelope, mounting holes, connector keepouts, thermal loads, vents, boundaries, and operating conditions in an engineer-reviewed design document.

AgentCAD is discovery candidate D001, absent from the runtime catalog and unqualified. Its upstream documents build123d CAD, STEP/mesh export, rendering, measurement, validation, and MCP launch ([AgentCAD](https://github.com/jdilla1277/agentcad)). Qualify it before live use and measure its CAD against the design document. Do not use abandoned `openfoam-mcp-webworn`. Qualify D040 Foam-Agent as the candidate CFD path; upstream documents plan, input writing, run, review/fix, visualization, external Gmsh meshes, and Foundation OpenFOAM v10 ([Foam-Agent](https://github.com/csml-rpi/Foam-Agent)). STEP-to-fluid-domain construction, named boundaries, vents/fan conditions, heat sources, convergence, mass balance, field extraction, and mesh sensitivity remain required integration work.

### 5.3 Sheet-Metal Supplier Handoff

Recover the actual chain from the evidence workspace referenced by `packages/workspace_service/tests/fixtures/run-progress-dispatch-20260908.json`, especially `design-to-sendcutsend.workflow.wflow`, `design-context/sendcutsend-sheet-metal.md`, `manufacturing/supplier-preview-package-004-v2.json`, and `manufacturing/flat-pattern.dxf.verification.json`.

Preserve: prompt/image/context to detailed design document; exact installed CAD material readback plus supplier alloy/temper; measured non-mutating design check; at most two indexed CAD revisions; native PSM, folded STEP, and genuine flat-pattern DXF; independent hash-bound DXF verification; actual supplier upload/configuration; validated quote association; and a user-controlled cart/quote handoff. A machine-evaluated design-check pass is not a human supplier decision. Current Wright code supports a bounded design-check/revision segment and terminal artifact review, but explicitly rejects human review followed by MCP/CAD continuation. Add durable digest-bound approval/resume before claiming the template works.

The supplier check must refresh current sources and resolve rather than average conflicting bend-radius guidance. Current SendCutSend references cover [quote/file troubleshooting](https://sendcutsend.com/faq/why-cant-i-get-a-quote/), [STEP bend configuration](https://sendcutsend.com/faq/how-to-configure-bends-for-my-step-file/), and [formal quotes](https://sendcutsend.com/faq/how-does-a-formal-quote-work/). No dedicated SendCutSend MCP is established; the recovered flow used Solid Edge plus a browser MCP. Order, payment, stored payment, supplier support contact, and production release stay outside scope.

## Decision 6: Seven additional engineering templates

The selected set favors distinct engineering disciplines, visual outputs, measurable actual-result checks, and a plausible Wright integration. Values below are template requirements, not observed outcomes.

1. **Parametric Drill Jig**: workpiece dimensions, hole-coordinate CSV, purchased bushing data, clamp keepouts, and clearances → qualified BREP primitives/export, drawing operations, then candidate D037 DFM checks. Outputs: STEP/STL, hole-location DXF, dimension report. Check all holes and keepouts against declared tolerances. Physical fit remains separate. Implement first of the seven.
2. **Conduction Heat-Spreader Sizing**: 100×40×2 mm plate, explicitly supplied 200 W/m·K conductivity, 4 W heat, 25°C cooled end, insulated remaining boundaries → BREP geometry and OASiS simulation. Compare 40 mm and 60 mm widths; analytical one-dimensional rises are 25 K and 16.67 K. Require result agreement within 2%, heat balance within 1%, mesh change below 2%, and revised maximum at or below 45°C. OASiS's qualified unit-square path does not yet prove this dimensional handoff. [OASiS](https://github.com/Hereon-InstituteMS/OASiS).
3. **Lightweight Equipment Bracket**: dimensioned sketch, 100 N load, explicit material properties/fixtures → BREP CAD/export and candidate D034 Casys CalculiX static analysis. Outputs: STEP, mesh/deck, displacement/stress fields, mass comparison. Require deflection ≤0.5 mm, evaluated stress ≤120 MPa with singularity treatment declared, mesh-refinement change <5%, and a lighter passing revision. [CalculiX MCP](https://github.com/Casys-AI/mcp-calculix).
4. **Sensor-Interface PCB**: approved schematic/netlist, datasheets, connector pinout, and 40×30 mm constraint → `kicad-mcp-blwfish` library, schematic/PCB, audit, independent ERC/DRC, fabrication export. Outputs: editable design, BOM, Gerbers, drill files. Require exact connectivity, dimensions, zero unreviewed errors, and reopened export equivalence. Current qualification covers library search, simple PCB create/reopen, audit, and export; the pinned DRC path currently corrupts MCP stdout and must be fixed/qualified. [KiCad MCP](https://github.com/blwfish/kicad-mcp).
5. **Robot Tracking Diagnosis**: redistributable ROS 2 bag with planned path, external pose/odometry, velocity commands, timestamps, and one annotated event → `rosbag-mcp-pypi` metadata/schema/range retrieval and independent analysis. Outputs: event timeline, trajectory overlay, tracking RMSE, evidence-linked diagnosis. Require metrics within 1% of an independent calculation and event time within one sample; disagreement alone does not prove wheel slip. Current qualification covers known-message retrieval only.
6. **Sensor-and-Fan Wiring Harness**: wiring schedule, connector datasheets/pins, branch lengths, currents, and wire/drop constraints → discovery D031 Splice CAD search, plan, validate, and assembly plus independent electrical checks. Outputs: plan, pin schedule, cut list/BOM, assembly document. Require exact netlist equivalence, no unexpected opens/shorts, sourced ratings, and ≤3% calculated drop. Structural plan validation is not electrical verification; beta access/API key require qualification. [Splice CAD MCP](https://github.com/splice-cad/splice-cad-mcp).
7. **Water-Heater Power Sizing**: approved CoffeeMachine kit, recorded water mass/losses, 20°C start, 90°C target, and heat-up limit → discovery D035 Casys Modelica approved-kit execution and parameter comparison. Outputs: temperature-time CSV, heat-up time, energy estimate, and setting decision. Require target time, model-consistent energy, and timestep stability. D035 is unqualified and accepts bounded approved kits rather than arbitrary source. [Modelica MCP](https://github.com/Casys-AI/mcp-modelica).

Recommended qualification order after the flagship workflows: drill jig, heat spreader, bracket, PCB, robot diagnosis, harness, water-heater sizing.

## Decision 7: Durable approvals and external effects

**Decision**: Introduce a generic approval checkpoint and continuation state in the canonical runtime. The subject digest includes definition, inputs, relevant artifacts, exact bindings/schemas, destination/device, requested action, and bounded settings. `approved` or `changes_requested` decisions are immutable. Changed subjects require a new checkpoint. Execution resumes from persisted completed steps; it never reruns a recorded successful mutation unless the operation is declared safely repeatable and current state is independently reconciled.

**Rationale**: Current `workflow_artifact_review.py` snapshots and rejects stale evidence but only supports terminal review, records local unauthenticated attribution, and cannot resume into CAD/MCP. Printer transfer and supplier upload need the same evidence integrity with stronger identity and resumability.

**Alternatives considered**:

- Put approval edges only in the canvas: rejected because UI state cannot authorize runtime actions.
- Treat a run-level approval as sufficient: rejected because destination, package, profile, quantity, or price may change.
- Restart the entire run after approval: rejected because it may repeat external mutations.

## Decision 8: Social output is a local evidence-derived package

**Decision**: Capture from a verified immutable run into a local manifest plus selected screenshots/previews and a caption draft. Record input rights/attribution and disclosure state. Scan for secrets, host paths, credentials, personal data, and unsupported claims. Do not integrate posting in this feature.

**Rationale**: Social material should be easy to create and honest. Keeping publication outside Wright avoids adding unrelated account authority and makes product claims reviewable.

## Sources in this repository

- Reviewed UI handoff: `docs/contributing/workflow-ui-integration.md`
- Canonical editor plan and north star: `specs/080-canonical-workflow-recovery/`
- Native language/runtime constraints: `specs/079-wright-native-authoring/`
- Current catalog: `packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`
- September 11 discovery: `docs/mcp-catalog/discovery/2026-09-11/` and `artifacts/mcp-discovery-2026-09-11/`
- Qualification process: `docs/mcp-catalog/mcp-server-testing-process.md`
- Critical CFD failure: `docs/mcp-catalog/evidence/curation-2026-09-10/openfoam-mcp-webworn-qualification.json`
- Existing narrow backend evidence: `docs/mcp-catalog/evidence/curation-2026-09-09/`
- Current workflow runtime: `packages/workspace_service/src/workspace_service/workflow_source_execution.py`, `workflow_cad.py`, `workflow_design_check.py`, `workflow_dxf_verification.py`, and `workflow_artifact_review.py`
