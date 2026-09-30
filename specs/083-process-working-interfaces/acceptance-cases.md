# Acceptance cases and evidence boundaries

**Read first:** [Engineering demonstration principles](../../docs/design/engineering-demonstration-principles.md).
These are selected existing assignments, not a new campaign or claims of qualification.
Fresh isolated roots: `.local-run/process-interfaces-083/`; retained evidence:
`artifacts/process-interfaces/083/<UTC-run-id>/`. Never write in campaign output roots.

## A — Printed replacement part: manufacturing preparation

Retain `printed-replacement-part` original inputs, dimension/feature/material/
process requirements, stages and pending reviews. Reference binding:
`tests/datasets/engineering-workflows/bindings/printed-replacement-part.json`.
Do not silently substitute the pumpkin or a canned cube for the assigned part.

| Stage | Tool contribution and actual handoff |
|---|---|
| Create mesh | Existing Blender MCP receives original image/prompt/dimensions; constructs and exports actual uniquely owned source STL |
| Repair/measure/orient | Existing independent geometry capability, initially Blender if qualified, consumes that STL, preserves source, checks topology/features/dimensions and records actual orientation consequences |
| Slice | Existing independent slicer MCP consumes selected geometry and approved configured profile, emitting actual nonempty sliced package/G-code |
| Inspect/check/review | Bounded generic geometry/package readers and 082 checks bind actual outputs/profile evidence; UI presents geometry, actual toolpaths/layers, material/profile, estimates where supplied, findings and final preparation review |

Candidate existing slicer: catalog ID `bambu-p1s-mcp-marctheshark3`; retained
upstream revision `7b50d0288fb7b91af8af422b96c4df4db0f1110c`. The existing catalog
has partial Windows offline-slice evidence, not fresh qualification. Read actual
current schema; provider configuration owns slicer/profile/runtime choices.
If user-visible alternatives require multiple preconfigured provider bindings,
expose those as configured capability options, not Wright vendor profile code.

No support-preview API is promised. Parse actual package/extrusion/layer data with
bounded format readers when supported; retain parser/dialect/method provenance.
Unsupported feature classification is unknown. A mesh silhouette or a rendered
STL is not a support/toolpath preview. Show only actual supported paths; use
download/inspection fallback for unrecognized formats. Validate exact package
correspondence before permitting its preparation review/action.

Required evidence: actual source/repaired/selected geometry references; dimensions/
features/topology and permitted repair/orientation evidence; actual external
slicer invocation/schema/profile/config identity; package/G-code hashes; bounded
toolpath representation and layer view; current 082 assessments; actual AI UI
authoring provenance; common/tailored view agreement; second-run UI reuse.

Physical printer status/material inventory/camera/dispatch are optional provider
capabilities, not prerequisites for this digital proof. Do not send a print or
start Studio/Handy automation as part of this goal.

## B — Heat-spreader sizing: design analysis and comparison

Retain `heat-spreader-sizing` original engineering assignment and frozen basis,
limits, candidate definitions and critic setting. Read:

- [Runtime research](../081-engineering-workflow-templates/dataset-campaign/heat-runtime-research.md).
- [Native result inspection](../081-engineering-workflow-templates/dataset-campaign/heat-native-result-inspection.md).
- [Protected attempt 902 review](../082-output-content-validation/heat01-attempt902-engineering-review.md).
- `tests/datasets/engineering-workflows/bindings/heat-spreader-sizing.json`.

| Stage | Tool contribution and actual handoff |
|---|---|
| Thermal basis | Original reviewed requirements or isolated test-basis source with all original limits; explicit unresolved review remains visible |
| CAD candidates | AgentCAD creates actual candidate STEP files, reopens/measures geometry and records exact correspondence |
| Numerical analysis | Existing OASiS/scikit-fem capability consumes measured dimensions linked to STEP digests and runs coarse/refined 3D conduction, retaining actual VTU/CSV fields |
| Independent verification/selection | Read actual field/balance/refinement/correspondence evidence; compare candidates and disclose failures, idealization and pending critic/review |

Retain analytical agreement ≤2%, coarse/refined hot-end temperature-rise change
≤2%, heat balance ≤1%, stated maximum temperature and exact candidate identity.
`critic_approved=false` absent independent critic evidence. Measured rectangular
dimensions inform solver meshing; this does not claim arbitrary STEP-topology
import or physical testing. UI should offer comparison/table/field views suited
to this analysis, without manufacturing/device controls as mandatory sections.

Required evidence: CAD exports/readback; solver input with exact CAD mapping;
actual coarse/fine fields and native summaries; independent checks and current
082 findings; tool contributions and candidate comparison; AI generation/update/
save/reuse through Wright; common/tailored parity and final analysis review.

## C — Runtime/UI negative and recovery cases

| Case | Required observation |
|---|---|
| Missing later user choice | No dispatch; reason links to exact binding |
| Upstream-produced intermediate | Start permitted when declared dependencies are valid |
| Declared input + review | Two real persisted barriers; same-run resume, schema/subject checks and one-shot consumption |
| Undeclared AI question | Diagnostic, no invented runtime form or engineering value |
| Duplicate/lost start/response/action | Recorded receipt/reconciliation; exactly one authorized dispatch |
| Browser disconnect/close/reopen | Backend run continues or durably waits; view attaches without replay |
| Service reopen during waiting | Same input/checkpoint/output identity; v2 history still readable |
| Unknown external outcome | Reconciliation required; no blind mutation replay |
| Unavailable option/evidence/operation | Required absence blocks; optional absence disclosed |
| Stale source/input/output/profile/decision | Affected action unavailable until fresh assessment/decision |
| UI incompatibility/update/rollback | Required stale bindings cannot mutate; common view works; revised saved UI retains provenance |
| Unavailable model/compiler | Generation unavailable; saved interface/common view still usable |
| Authoring scope escape/invalid app | Reject arbitrary files/imports/scripts/launch; isolated preview and enforced bridge |
| Wrong workspace/run/UI/presentation | Server denies; no credential leak or broader gateway authority |
| Explicit cancel | Request vs actual cancelled/unsupported/unknown shown correctly |

## D — Served user experience and distribution

Enter a normal workspace through Workflow/Workflows. Record checkout/branch/build,
frontend/API targets, workspace, flags and screenshots. Preserve existing canvas,
block inspector, Diagram/Source, drag/socket mismatch, pan/zoom, invalid drafts,
Undo/Redo, save/layout/reopen and conflicts. Working/preview tabs use the same host.
Verify realistic viewport/zoom, keyboard/accessibility/theme, image thumbnails,
progress/error/reconnect and exact block/result/assessment navigation.

For each UI, generate with the actual configured model through Wright, preview,
save, request one focused update, reopen saved built revision and reuse on another
run. Common and tailored views must reflect the same backend facts. A prewritten
reference app is useful for tests but does not prove AI generation.

Use installed wheel/native and clean Docker runtime checks for resources and
saved-app opening without repository imports, build or network package download.
Authoring build tools are a qualified local capability, not an implicit runtime
requirement. Follow normal MCP clean-container process and separately record host
provider proofs; host-only success is not clean-container qualification.

## Evidence and test authority

The future goal authorizes isolated nonphysical test enrollment only. A driver may
record explicitly labelled synthetic reviewer/input decisions in these private
proof runs to exercise continuation and reach later live engineering stages.
It must enroll exact source/subjects/destinations, keep real waiting transitions
observable, record `integration_test=true` and actor, and never mark them human
engineering acceptance. Real/un-enrolled user checkpoints still stop for the user.
Measured mandatory failures cannot be overridden by this test authority.

Do not resume, approve or rework campaign Heat902/Printed901/Water905 subjects.
Their checkpoints, counters and evidence remain untouched. Isolated test decisions
do not settle their pending engineering questions or grant physical authority.

Evidence index distinguishes: source inspection; fixture contract tests; live
model generation; served browser verification; live provider digital outputs;
engineering checked scope; test decisions; human acceptance; physical execution.
Required missing live proof leaves the feature incomplete, with unaffected work
and precise resource/authority request documented. Do not inflate qualification.
