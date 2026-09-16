# Remaining seven workflow families: real execution bindings

Read-only discovery and draft preparation, 2026-09-12. These findings establish
candidate implementation paths, not completed workflow runs. No shared CAD or
solver job, host change, account operation or hardware action was dispatched.

## Observed tools and readiness

The local workflow tool API currently returns AgentCAD (11 tools), Blender
(28), Foam-Agent (6), Solid Edge (55) and Wright workspace files (1). The
registry reports BREP, AutoCAD, OASiS, ROSBag and KiCad inactive/uninstalled.
Discovery entries D031 Splice, D034 Casys CalculiX and D035 Modelica are not
active server IDs. The unrelated `calculix-simulation` catalog entry is not
Casys CalculiX and must not be used as its identity. Native `kicad-cli`,
`FreeCADCmd`, `ccx`, `gmsh` and `omc` were not found on the inspected PATH;
this does not prove absence elsewhere on disk.

Blender's optional safe mode currently prevents several script/file/process
operations required by earlier drafts. Root is handling that prerequisite.
None of the proposed alternatives below bypasses that guard.

| Family and original stages | Exact tool route | Prerequisites and remaining execution work |
| --- | --- | --- |
| **Parametric drill jig:** `validate_inputs` → `generate_jig` → `check_alignment` | Available `wright-workspace-files/write_text_document`; `agentcad/context`, `docs`, `run`, `inspect`, `measure`, `export`. Real build123d modeling replaces unavailable BREP/AutoCAD; CAD-derived DXF remains required. | Native AgentCAD project initialization; actual source generation, kernel exports, geometric inspection and reviewed basis. Three seven-step drafts prepared. No Blender dependency. |
| **Heat spreader:** `define_thermal_case` → `create_plate_geometry` → `solve_and_verify` | Available AgentCAD for actual geometry; install selected OASiS and use its documented `run_simulation` with `solver=skfem` and a real numerical script. | OASiS is currently inactive. Author actual conduction FE model, boundary conditions, extracted temperature field, heat balance and mesh sequence. Do not populate field files from analytical answers. |
| **Lightweight bracket:** `define_load_case` → `create_bracket` → `solve_and_compare` | Available AgentCAD substitutes for BREP; selected Casys CalculiX `calculix_mesh_preflight`, `calculix_solve_static_recorded`, `calculix_run_get`. | Install exact released solver image and expose new server identity. Preserve loads, keepouts, material, baseline/revised mass and mesh comparisons. Resolve raw field artifact export before claiming original results contract complete. |
| **Sensor PCB:** `capture_electrical_basis` → `author_pcb` → `verify_and_export` | Selected blwfish KiCad tools `schematic`, `pcb`, `project`, `library`, `audit`, `drc`, `export`; live schema discovery must pin operation arguments. | Actual KiCad host and Python integration are absent from the live workspace. Generate native schematic/board then actual ERC/DRC, Gerbers and drill data. A generic CAD drawing is not an electrical-design substitute. |
| **Robot tracking:** `inspect_bag` → `align_and_measure` → `evidence_diagnosis` | Selected ROSBag `bag_info`, `get_message_at_time`; remaining topic/window extraction tools must be schema-discovered. Real `rosbags` writer prepares a ROS2 bag from supplied CSVs. | Install pinned clean selected host. Record CSV→bag conversion, coordinate and clock transforms, then inspect/read that actual bag. Compute metrics on actual extracted samples. Directly analyzing CSVs while skipping bag inspection changes the process. |
| **Sensor/fan harness:** `define_harness` → `generate_harness` → `verify_harness` | Selected Splice `search_connectors`, `search_wires`, `get_part`, `lookup_part`, `create_project`, `save_plan`, `validate_plan`, `generate_assembly`, `get_harness`. | No authenticated Splice installation is available. Need existing authorized beta account/API access, real component sourcing, disposable project, actual assembly/netlist and voltage-drop computations. A local WireViz route is a possible separately reviewed implementation, not currently bound or proven equivalent. |
| **Water heater:** `define_requirement` → `run_allowed_settings` → `verify_selection` | Selected Casys Modelica `modelica_kit_list`, `modelica_simulate`, `modelica_run_list`, `modelica_run_get`, approved `coffee-machine-v1` kit. | Install compatible Modelica HTTP server/OpenModelica runtime, discover kit constraints and retain actual samples for all allowed power/UA/timestep settings. The original `arbitrary_source:false` contract forbids substituting an unrestricted handwritten ODE. |

All server/tool spellings above are either the current local API names or
documented upstream candidates. Candidate schemas still require live discovery
and exact grant enrollment before execution. Available tools alone do not
establish a working operation. No qualification flag changes are implied.

## Prepared drill-jig family

The new `scripts/prepare-drill-jig-dataset-campaign.py` stages all original user
files, attaches the sketch, preserves the three original semantic task IDs,
and compiles seven steps: basis, exact local review, actual AgentCAD project
context, source authoring, original model generation, independent inspection
source authoring, and original alignment check. It binds only the real file
writer and AgentCAD. Source, STEP/STL, hole-layout DXF, CAD lineage and actual
dimension report must be produced during execution.

Scenario 01 is a two-hole furniture-rail plate with datum fences and two clamp
exclusions. Scenario 02 is a four-hole rectangular tube jig with a central
chip window and end clamps. Scenario 03 is a six-hole annular jig with a
specified existing notch, matching tab, center opening and outer clearance.
Supplied CSV coordinates control geometry; bushing tables are fictional
customer inputs, not claimed supplier specifications. No physical-fit or
manufacturing qualification follows from these integration runs.

Default preparation performs no AgentCAD invocation. The explicit
`--initialize-agentcad` option initializes only a new disposable project with
the pinned AgentCAD 0.6.0 native CLI, records its exact command and result,
and fails on preexisting project paths. This is an installation/project
prerequisite, not precomputed CAD. Runtime `context` must verify it before
`run` can generate geometry. Do not dispatch drafts that still report missing
initialization. Prefer a fresh API template instance supplied through
`--instance-source`; otherwise manifests explicitly mark that API instance
creation remains required.

Three current draft manifests are under
`.local-run/feature-081-live/jig-campaign-drafts/parametric-drill-jig-0{1,2,3}/attempt-002/`.
Each has seven compiled stages and ten staged files, `executed:false`.
`attempt-001` predates removal of the Blender initialization bridge and is
superseded; do not enroll it. No draft increments campaign execution/completion.

## Solver and application contract findings

### Heat spreader

The existing [OASiS setup recipe](../../../docs/mcp-catalog/mcp-server-setup-recipes.md)
pins upstream commit `7c184d5b7ca5cda6086f3912d1c7923c58307780`,
`mcp[cli]==1.28.1`, `scikit-fem==12.0.2`, Python 3.12 and an isolated
`python -m server` launch. Clear `PYTHONPATH` because upstream top-level module
names collide with Wright. Prior Linux qualification proves a narrow Poisson
VTU operation, not these heat-transfer studies; never reuse its result files.

The packs request end-cooled plates with different widths, conductivity,
thickness and applied heat. Scenario 03 additionally specifies **total cold
interface resistance 0.15 K/W**. A real FE implementation must include that
interface and correctly convert total resistance to a boundary coefficient
using the modeled contact area. Preserve original analytical baseline and
mesh-sensitivity stages alongside solved fields; they are process outputs,
not the deferred campaign correctness-validation program.

The available Foam-Agent `run` can execute an authored real OpenFOAM case
without a model API credential (see Pi research), but heat conduction solver
availability and boundary syntax still need inspection. That is a fallback
real solver route, not a currently prepared binding.

### CalculiX bracket

Casys' [current README](https://raw.githubusercontent.com/Casys-AI/mcp-calculix/main/README.md)
documents version 0.8.6, HTTP/stdio and a digest-pinned released image. Fetch
the [release identity](https://github.com/Casys-AI/mcp-calculix/releases/download/v0.8.6/release-identity.json)
before installation; mount only disposable input STEP and retained outputs.
The [analysis contracts](https://raw.githubusercontent.com/Casys-AI/mcp-calculix/main/docs/analysis-contracts.md)
describe single-volume STEP, bounding-box surface selection, recorded static
request IDs and input SHA-256. Confirm each supplied load fits supported
operations. Returned extrema alone do not satisfy required full fields;
retain real raw solver outputs through an explicit artifact route. The
coupled-thermal tool accepts prescribed temperatures, not heat-flux,
convection or contact physics, so it is not the heat-spreader substitute.

### KiCad, ROSBag and harness

The [blwfish KiCad README](https://raw.githubusercontent.com/blwfish/kicad-mcp/main/README.md)
describes domain tools and a KiCad-host Python dependency. Use actual
schematic connectivity and PCB design rules for the thermistor, dual sensor
and 24 V fan/tach scenarios, then collect native electrical-rule and
manufacturing outputs. Installation discovery is not a successful board run.

The local ROSBag setup recipe pins `rosbag-mcp==0.2.0`, `rosbags==0.11.5`,
`mcp==1.28.1` and numerical/plot packages. Existing Linux evidence covers
`bag_info` and one known-message extraction only. All three packs explicitly
provide bag conversion guidance; preserve floor-seam, camera-clock/transform
and figure-eight-dropout differences when generating their actual bags.
Some server failures return ordinary error content, requiring response checks
rather than only MCP `isError` handling.

The [Splice README](https://raw.githubusercontent.com/splice-cad/splice-cad-mcp/main/README.md)
requires beta account access and an API key; npm publication is pending in
the inspected source. Its default WebSocket port 9876 conflicts with the
local Blender bridge, so select another port if installed. Dataset connector
pin labels are requirements rather than selected manufacturer terminals.
Real harness work must source compatible housings, terminals, crimp tooling
and current ratings, then preserve independent returns/shared startup loads
and supplied wire-length/resistance assumptions. No credentials were read.

### Modelica heater

The [current Modelica README](https://raw.githubusercontent.com/Casys-AI/mcp-modelica/main/README.md)
describes version 0.2.0, stateless HTTP only and MCP protocol 2026-07-28;
former stdio setup is stale. Check Wright compatibility before installing.
Discover `coffee-machine-v1` and `heat-up-nominal` bounds; do not invent
overrides. Retained runs are capped at 20 and CSV artifacts at 5 MiB, so
collect each run before a larger power/UA/timestep study exhausts retention.
Preserve actual hashed CSV references and samples, not only success status.

The datasets vary water mass, vessel heat capacity, temperature/time goals,
allowed power, losses and interface assumptions. If the approved kit cannot
express a required parameter or expose timestep variants, record that exact
contract gap. A free-form model can be a proposed future change but cannot
be counted as this canonical approved-kit process.

## Execution order and counting

After the active printing/Pi/sheet-metal work, jig has the shortest independent
path because its actual geometry tools are already present. OASiS heat and
ROSBag next have reproducible local qualification recipes. Bracket needs
solver artifact-contract work; KiCad needs a full application; Modelica needs
kit/protocol confirmation; Splice needs service access or an explicitly
reviewed equivalent. These are readiness findings, not permission pauses.

Enroll immutable source/input/tool digests only after a fresh runtime tool
probe. Retain all reviews under scoped test auto approval. Completion remains
all original semantic stages finished plus all expected same-run files;
failures, successful preparation and partial graphs do not count. The fourth
dashboard line remains zero until output correctness validation is introduced.
