# SteveCAD heat-spreader comparison

This example preserves the existing e-ink conduction-strap assignment. It uses
two editable SteveCAD rectangular solids and OASiS/scikit-fem to compare widths
40 and 60 mm under the original 4 W conduction-only model. Requirements, synthetic
constants, numerical checks and full 082 validation remain unchanged.

Current execution is **waiting for its genuine model-basis review**, not completed.
Native source/run identities and exact export receipts are indexed under
`artifacts/stevecad-demonstrations/heat-spreader/attempt-001/`.

## Prepare and run

1. In Wright, connect the official SteveCAD remote MCP and a qualified existing
   OASiS server. Enable them in the intended disposable workspace. The OASiS
   provider must see that workspace at `/workspace`; export its fresh tool schemas.
2. Save `baseline_40.py` and `revision_60.py` as new SteveCAD part documents through
   its tools. Read before updating an existing document; never invent IDs/revisions.
3. Generate those exact revisions once. If the provider explicitly reports
   `still_working`, join the same revision until terminal. Inspect each actual model.
   Fetch each STEP with its documented one-time transfer; never save the ticket.
4. Retain credential-redacted receipts named `02-generate-baseline_40.json` and
   `02-generate-revision_60.json`, plus the actual `baseline_40.step` and
   `revision_60.step`, in a new CAD attempt directory. Each receipt must include
   the native `result.structuredContent.document/model` and an `export.sha256`
   computed from the exact downloaded file. These are explicit preparation inputs.
5. Run the declaration preparer with your real workspace, fresh tools and solver ID:

   ```powershell
   python examples/stevecad-demonstrations/heat-spreader/prepare.py `
     --workspace <absolute-workspace-path> --attempt <new-attempt-name> `
     --tools <fresh-workflow-tools.json> --cad <new-cad-attempt-directory> `
     --solver-server <selected-OASiS-server-id>
   ```

6. Accept the proposed source through Wright's normal workflow-source service,
   or open/save it through the workspace editor. Check readiness and start it
   through the common working view. The preparer does not execute or grant reviews.
7. Review the recorded original assumptions at the declared checkpoint. Approval
   continues the same durable run. After numerical fields and independent checks,
   review the exact result evidence. OASiS critic status is never fabricated.

Every run uses its own output directory. The process re-reads editable source,
generates the pinned revisions, verifies build identities, consumes exact STEP
hashes and dimensions, and retains coarse/fine CSV/VTU fields and correspondence.
The FE mesh is a dimensional rectangular idealization, not arbitrary STEP meshing.
The 082 gate independently reopens the STEP and numerical fields. Linear end
loading produces a linear field representable by P1 elements; mesh agreement
does not independently validate real device physics.

Changing CAD, inputs, provider or requirements requires a new accepted revision
and dependent validation. No manufacturing action, purchasing or release is made.
