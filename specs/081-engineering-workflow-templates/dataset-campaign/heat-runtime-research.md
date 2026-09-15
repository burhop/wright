# Heat-spreader selected runtime and execution preparation

Observed 2026-09-12. Setup and bounded real backend probes are complete. The
three first dataset attempts subsequently reached their project checks and
stopped before CAD/FE execution; see the campaign state for run counters.
Prerequisite probes and preparation do not count as complete workflows or
engineering correctness.

## Selected installation

Followed the clean-container process with original Wright Linux x64 image
`sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
Installed only selected OASiS prerequisites: git, isolated Python 3.12.12,
OASiS commit `7c184d5b7ca5cda6086f3912d1c7923c58307780`, MCP SDK 1.28.1,
scikit-fem 12.0.2 and their resolved dependencies. Wright's base image was
not changed. This preserves the existing catalog recipe's isolated backend.

The selected installed filesystem was retained in local derivative image
`wright:oasis-campaign-selected-20260912`, digest
`sha256:49ad6b866d93cf85fa4c82c175241be5e0e7c17239773c658e550b50e0580f8d`,
to add the explicitly authorized demo mount. Running container
`wright-oasis-campaign` has:

- `D:/repos/wright/.local-run/feature-081-live/oasis-workspace` → `/workspace`
- `C:/Users/markb/wright-feature-081/engineering-workflow-demos` → `/campaign-workspace`

The original qualification container is retained but stopped under
`wright-oasis-qualification-20260912`. The campaign container remains running.
No Docker socket, host application installation or credential directory is
mounted into the solver. Its Docker-exec stdio command clears `PYTHONPATH`
and sets `PYVISTA_OFF_SCREEN=true` before the pinned isolated launch.

Normal API registration created **OASiS campaign container**, server ID
`3253e0c4-2569-4585-b809-6fc2a6f16261`, with `default_enabled:false` and
explicit workspace-write/code-execution gates. Registration/install, demo
workspace tool toggle and activation all returned successful responses.
The demo tool API exposes 17 tools; `run_simulation` schema digest is
`a34df0e32e978905e88b5b378b665370d6f6ffac6755a8c09c39b88f060eef5c`.
The original public catalog row and qualifications were not modified. This
UUID names a selected local installation configuration, not another upstream
server project. Rediscover all schemas after any API restart before enrollment.

## Real numerical operation and evidence

`scripts/engineering/heat_conduction_skfem.py` assembles an actual 3D
tetrahedral P1 conduction matrix and solves sparse systems. The hot-face
Neumann load integrates to the supplied total watts; longitudinal faces are
insulated. Cases 01/02 use strong fixed cold-face temperature. Case 03 uses
Robin coefficient `1/(R_total * end_face_area)` with rail temperature in its
load vector. It never fills field arrays with the analytical formula.

Each candidate produces coarse and fine raw nodal VTU/CSV fields. The operation
computes heat removal from fixed-boundary reactions or integrated Robin flux,
then writes heat balance, original analytical/mesh comparisons and selection.
This remains the original workflow's work; it does not implement a separate
campaign correctness-scoring program. The exact linear end-loaded model is
representable by P1 fields, so near-zero mesh differences alone do not validate
the physical model.

When full workflows run, actual AgentCAD STEP files and reopened-kernel
measurements are required. The FE operation checks each measured STEP digest,
matches its measured box dimensions to the approved input and uses those
measured dimensions for the mesh. The source does not import arbitrary STEP
topology; this route is deliberately scoped to the specified unperforated
rectangular links. Geometry changes require an appropriate meshing operation.

The explicit live probe
`scripts/qualification/qualify-oasis-conduction.py --attempt attempt-004`
initialized MCP, listed 17 tools, ran actual fixed-temperature and Robin cases,
then repeated through native Wright `GatewayService`. It checked nonempty
same-run VTU/CSV/balance/mesh/decision files and recorded hashes. It did not
validate their numerical correctness or dispatch AgentCAD. Evidence is
[oasis-conduction.json](../../../docs/mcp-catalog/evidence/campaign-2026-09-12/oasis-conduction.json).
Raw logs, executed source and outputs remain in
`.local-run/feature-081-live/oasis-workspace/qualification/attempt-004/`.

`critic_approved` is false throughout these probes. OASiS explicitly labels
the returned outputs unverified; that label is preserved. No independent
critic or physics approval is invented. The remaining full public qualification
scope includes Hermes-facing gateway MCP proxy evidence and future physical
correctness criteria. Backend-touching execution readiness is established for
this scoped numerical operation, not for every advertised OASiS solver.

## Full workflow preparation and handoff

`scripts/prepare-heat-dataset-campaign.py` preserves all three original IDs:
`define_thermal_case`, `create_plate_geometry`, `solve_and_verify`. It inserts
exact local review, native-project context preflight, CAD source authoring and
numerical-call review. Seven compiled steps retain all customer CSVs/profile,
prompt/context and sketch, plus reviewable numerical source and exact solver
JSON. The call has no external device/supplier destination.

Three local drafts at `heat-campaign-drafts/<scenario>/attempt-001` compile with
10/10/11 staged files. They are prepared, unexecuted and unenrolled. No native
AgentCAD initialization was invoked by this subtask. Use a fresh API template
instance and attempt for actual demo execution:

```powershell
.venv/Scripts/python.exe scripts/prepare-heat-dataset-campaign.py `
  --oasis-server-id 3253e0c4-2569-4585-b809-6fc2a6f16261 `
  --workspace-root C:/Users/markb/wright-feature-081/engineering-workflow-demos `
  --container-workspace /campaign-workspace `
  --scenario heat-spreader-sizing-01 --attempt <fresh-attempt> `
  --instance-source <actual-api-created-source> --initialize-agentcad
```

The explicit initialization option only creates a fresh disposable AgentCAD
project and records native CLI results. Actual geometry remains a workflow
stage. Runtime `context` must succeed before generation. The campaign runner
owns dispatch and counters; fresh tool discovery is necessary after API tool
revisions. Neither qualification output
nor local prepared source should be substituted for actual API instance lineage.

## Problems encountered and resolutions

- Clean-image core is an editable pointer under `/workspace`; the isolated
  workspace mount hides it. Used native Wright's existing `StdioRunner` and
  `GatewayService` to exercise the clean selected solver through Docker stdio.
  This limitation is explicit; no complete in-container Hermes proxy pass is
  claimed and no host dependencies were added to the base image.
- First numerical solve generated fields but could not serialize a NumPy mesh
  count. Converted the actual count to Python `int` and reran in a new attempt.
- Second probe adapter assumed a Pydantic gateway response; real
  `GatewayToolResult` is adapted through its documented attributes. Fresh probe
  attempts 003 and 004 completed, retaining prior failures separately.
- First draft compilation rejected uppercase generated connection identifiers.
  Normalized those source keys; all three complete graphs now compile.
- All three actual `attempt-001` runs stopped in project preflight after treating
  downstream engineering deliverables as requirements of the empty-project
  check. The preparer now gives that stage explicit initialization-only success
  criteria, excludes the full customer-context input for that one stage, and
  retrieves actual AgentCAD quickstart/helpers for downstream source authoring.
  Empty model registries and absent future CAD/solver files are expected here.
- All three `attempt-002` cases use fresh normal template API instances, fresh
  native projects and newly enrolled source/input/tool digests. They retain all
  original semantic stages and the seven-stage complete graph. No enrolled
  `attempt-001` source was edited. The new local manifest is
  `.local-run/feature-081-live/campaign-execution/heat-attempt-002.json`.
  These retries have not been dispatched by the preparation task.
