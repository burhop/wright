# SteveCAD engineering demonstration delivery

Status: implementation in progress. Qualification is separate from engineering
compliance, process completion and human acceptance.

## User journey and ownership

Open each saved process from Wright's workspace Workflows control. Review its
inputs, original assumptions and selected capabilities; start the ready process;
inspect CAD and analysis outputs; respond to declared reviews on exact evidence.
The refined diagram/source editor remains available alongside the common working
view. No new UI or executor is introduced. The saved common view is the fallback;
closing/reopening reconciles with durable state and must not replay a tool call.

Wright owns accepted source, frozen instructions/configuration, run identity,
capability/schema bindings, gateway policy, exact file/result lineage, 082
validation, reviews and recovery. Independent SteveCAD owns CAD implementation
and OAuth; OASiS owns its execution environment; Casys owns its Gmsh/CalculiX
MCP; the selected KiCad provider owns KiCad implementation. Engineering model
inputs and standard solver decks remain reviewable workflow assets. Provider
protocol workarounds do not belong in Wright.

All three original assignments remain intact. Replacing providers creates a
visible proposed process revision; historical examples/evidence are not rewritten.
Credentials, protected campaign subjects, real review grants and GB10 work remain
separate. No physical action, production release or social publication is planned.

## Portfolio and evidence needed

| Job | Actual handoff and required outcome | Current state |
| --- | --- | --- |
| Equipment mount | SteveCAD baseline/revised editable L-brackets and STEP → independent mesh/structural tools → full stress/displacement/reaction fields, mass comparison and report. Preserve hole-bearing restraint, 100 N load patch, supplied material, ≥20% mass reduction, ≤120 MPa stress, ≤0.50 mm displacement and <5% mesh sensitivity. | Original requirements inspected; native Casys connection and coupon meshing passed. Bracket designs/analysis remain pending. |
| Heat-spreader selection | Two SteveCAD rectangular candidates and measured, digest-bound STEP → OASiS/scikit-fem coarse/fine fields → original full 082 checks and reviewed choice. Preserve 4 W, 25 °C cold face, insulated long faces, synthetic k=200, 45 °C limit, ≤2% analytical/refinement error and ≤1% imbalance. | Both exact CAD revisions/exported STEP exist. Saved native-003 run is waiting at its model-basis review. Numerical outputs remain pending. |
| PCB housing | Actual KiCad approved-connectivity schematic/board, component envelope and checks → SteveCAD housing → mounting, connector access and clearance evidence, editable sources and exports. | Original electrical/mechanical requirements inspected. Selected provider, actual board, electrical checks and housing remain pending. |

## Handoffs and invalidation

The heat preparer uses actual documented SteveCAD STEP transfers as explicit
preparation inputs. It never stores one-time tickets. The accepted process
re-reads editable source and generates pinned revisions, checks the recorded build
identities/current revision, consumes exact STEP bytes and measured dimensions,
and saves new fields in the run's own output directory. This does not claim
unattended transfer or arbitrary STEP-topology meshing. The independent validator
reopens the actual STEP and field files. Genuine model-basis and result reviews
remain human decisions; OASiS `critic_approved` stays false.

Changing source, STEP bytes, loads, dimensions, material, provider/schema or
requirements requires a new accepted binding/revision and new dependent
assessments. Supplied requirements cannot be relaxed to recover a failed tool.
Missing capabilities fail readiness or hold their affected stage. Preserve tool
errors separately from measured noncompliance and retain every run/revision.

## Bounded technical gaps

The pinned Casys 0.8.6 static generator selects complete surfaces inside boxes
and requests U/S, omitting RF. It cannot alone prove the reaction-force requirement.
The required top load patch must be a real selected surface; a whole-shelf load
is not an equivalent substitute. Inspect CAD partition capabilities before design.
Reference: [upstream provider](https://github.com/Casys-AI/mcp-calculix/tree/f92ac31e4a2a35f023522946b7aa81bac1ce4808).

An unchanged independent OASiS server with selected Gmsh/CalculiX prerequisites
has executed a standard one-element qualification deck requesting RF. Attempt 001
wrote native files outside its provider result location; the warning is retained.
Attempt 002 exports actual DAT rows to provider-supported VTU and passes automated
finite-output checks; the provider's independent critic remains pending and its
trustworthy-result flag remains false. This is native reaction-output readiness,
not a bracket analysis or full qualification. The selected Dockerfile changes no
Wright base image or vendor MCP protocol. Exact input/output image identities and
field digests are retained in the qualification evidence.

Earlier KiCad qualification identified a DRC stdout/protocol issue. Qualify an
existing independent check path before claiming electrical checks passed. Preserve
the original rules and exact revision across native sources and fabrication files.

## Delivery ledger

- [x] SteveCAD official connection/catalog and native gateway qualification.
- [x] New CAD coupon creation, inspection, STEP transfer and durable readback.
- [x] Scoped fresh neutral Linux read/inspection qualification; failures retained.
- [x] Original heat candidates created and exported with exact identities.
- [x] Saved thermal process and real waiting review through the normal runtime.
- [x] Served workspace navigation to the saved thermal process; no review submitted.
- [x] Independent structural provider native stdio discovery and actual mesh probe.
- [ ] Approve the exact thermal basis, compute fields, validate and review results.
- [ ] Qualify required structural outputs, design/analyse/refine the bracket.
- [ ] Qualify KiCad checks, create the actual board, design and verify the housing.
- [ ] Verify reusable processes and common views against exact completed runs.
- [ ] Create unpublished hero/detail visuals, captions, posts and storyboard from results.
- [ ] Final requirement-by-requirement completion audit and local commits.
