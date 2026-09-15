# Engineering Workflow Templates

Wright includes ten versioned engineering workflow templates in the workspace **Workflows** editor. Open the workflow file menu, choose **Start from template**, inspect readiness and expected outputs, enter a name, and choose **Create editable workflow**. Wright creates a new canonical `.workflow.wflow` file, layout, immutable template-origin record, and any distributable supplied fixture files inside the current workspace. Supplied files live under an instance-specific `inputs/` directory and their digests are recorded in the origin record. It does not overwrite an existing workflow or copy credentials, runs, or approvals.

The initial catalog contains:

1. 3D Printed Replacement Part
2. Vented Raspberry Pi Enclosure
3. Sheet-Metal Supplier Handoff
4. Lightweight Equipment Bracket
5. Sensor-Interface PCB
6. Parametric Drill Jig
7. Robot Tracking Diagnosis
8. Conduction Heat-Spreader Sizing
9. Sensor-and-Fan Wiring Harness
10. Water-Heater Power Sizing

Every entry is available offline for inspection, copying, editing, and validation. The picker shows one of four readiness states: **Reference workflow**, **Setup required**, **Ready to run**, or **Verified runnable**. Packaged definitions and successful UI tests establish definition validity only. They do not qualify a live MCP server, prove a backend engineering result, or show that a physical or commercial action occurred.

The first three templates carry the detailed engineering sequences requested for demonstration:

- The 3D printing workflow retains an attributed image and explicit scale, creates and repairs a mesh, checks dimensions and build volume, records supports and slice profiles, verifies the print package, and stops before transfer to the selected Bambu P1S.
- The Raspberry Pi workflow pins the selected board model and official manufacturer drawing, creates a reviewable design basis, measures AgentCAD output, requires CAD-to-fluid-domain identity, and checks CFD fields, convergence, mass balance, and mesh sensitivity.
- The sheet-metal workflow retains image and text intent, creates a design document and native Solid Edge sheet-metal model, allows at most two indexed corrections, independently checks the model and developed DXF, verifies the supplier preview, and hands control to the user without ordering or paying.

Printer transfer, supplier preview, and cart or quote handoff use durable approval checkpoints. A decision is bound to the exact definition, inputs, artifacts, tool binding, destination, settings, and proposed action. Changing any field makes the decision stale. Resume consumes the decision once and records `not_dispatched` before any adapter is allowed to act. A connection loss after the dispatch boundary must be recorded as `outcome_unknown` and reconciled; Wright does not retry it blindly.

The normal run drawer displays the complete approval subject and its digest. A run enters `awaiting_approval`, retains its already completed step and artifact evidence, and can issue one-shot adapter authority only after the exact subject is approved. At resume, the server re-reads the workflow and workspace files and recomputes their digests; the browser cannot assert that stale bytes are current. Repeating the same decision or resume request after a lost response is idempotent; a different request cannot reuse consumed authority.

The packaged SVG previews are distributable local assets and may be used in draft social material. A completed run with recorded engineering assertions, approved input rights, and unchanged persistent artifacts can create a local `.demo-capture.zip` from its run drawer. The archive contains a manifest, caption draft, selected artifacts, verification state, attribution, digests, and explicit no-publish/no-physical-completion disclosures. It rejects unverified, changed, sensitive, private-path, or unlicensed evidence. Current catalog entries honestly remain **Setup required** or **Reference workflow** until their named integrations pass the clean-container qualification process and a real Wright run passes the independent checks. Wright never publishes a post, submits a purchase, stores payment data, or claims physical completion from these templates.
