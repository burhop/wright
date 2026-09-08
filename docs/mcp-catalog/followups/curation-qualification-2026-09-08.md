# Core engineering MCP qualification backlog

Owner: Wright catalog maintainers. Next review: 8 October 2026.

The portfolio target is 10–20 dependable integrations for CAD, CAE, simulation,
and engineering data. A server counts only for the exact platform, distribution,
configuration, and workflow in its current qualification evidence. Similar
FreeCAD forks and capability aliases do not inflate the count.

## Qualified portfolio

| Integration | Proven workflow | Current boundary |
|---|---|---|
| OpenSCAD | 10 x 8 x 6 mm parametric model to STL; three direct sessions and both Wright gateway paths; independent dimensions and 480 mm3 volume | Clean Wright Intel Linux container, pinned source commit |
| BREP MCP | 40 x 20 x 10 mm exact BREP to STEP and STL; error and bounded-timeout checks; three direct sessions and both gateway paths | Clean Wright Intel Linux container, `brepjs-cad@0.103.0`, Wright compatibility launcher |
| FreeCAD MCP | FreeCAD `Part::Box` creation and STL export; three direct sessions and both gateway paths; independent dimensions and 480 mm3 volume | Clean Wright Intel Linux container, FreeCAD 1.1.1, server commit `63acb305...`, MCP SDK 1.28.1 |
| OASiS | scikit-fem unit-square Poisson solve; three direct sessions and both gateway paths; independent VTU mesh, boundary, field, and expected-range checks; controlled failure and process-tree timeout cleanup | Clean Wright Intel Linux container, Python 3.12.12, OASiS commit `7c184d5b...`, MCP SDK 1.28.1, scikit-fem 12.0.2 |
| ROSBag MCP | Known-message retrieval from a deterministic ROS 2 bag; three direct sessions and both gateway paths; independent SQLite schema, CDR payload, type, and timestamp checks | Clean Wright Intel Linux container, `rosbag-mcp==0.2.0`, Python 3.12.12, MCP SDK 1.28.1, exact data-stack pins; source link and broader tool surface unverified |
| Blender MCP | 10 x 8 x 6 mm polygonal mesh and STL export; three direct sessions and both gateway paths; independent geometry, topology, bounds, controlled-error, reconnect, and cleanup checks | Clean Wright Intel Linux container, source commit `5f8ddaf6...`, Blender 4.3.2, telemetry disabled, safe mode enabled; optional network services and native hosts unverified |
| Autodesk Product Help | Public Autodesk product discovery through direct MCP and Wright gateway | Read-only engineering reference data; no CAD authoring or repeat-use claim |

Repeat user adoption remains unknown for all seven. Repository stars, publisher
demos, historical tests, and catalog labels are discovery signals rather than
proof that Wright users rely on a server.

## Ordered qualification queue

Scores are relative planning judgments from 1 (weak) to 5 (strong). Confidence
uses Wright's historical backend evidence plus current source availability;
maintenance favors small, pinned, credential-free setups. The use column states
the evidence type instead of turning stars or downloads into an adoption claim.

| Order | Candidate | Lifecycle capability | Value | Distinct | Confidence | Maintain | Public/use evidence | Next qualification |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `solid-edge-mcp-burhop` | Native commercial parametric CAD | 5 | 5 | 3 | 2 | Maintained Wright-related implementation and prior native protocol pass; backend result-schema failure recorded | Use a disposable Windows/Solid Edge session; fix the nullable `activeDocument` contract; create/export a tiny part through both gateways; preserve user documents and process state |
| 2 | `caid-mcp` | Direct OpenCASCADE geometry and diagnostics | 4 | 3 | 3 | 3 | Prior Wright 72-test pass and box-volume task; primary URL later returned 404 | Resolve current primary repository identity before installation, then create/export a nontrivial solid and inspect topology through both gateways |
| 3 | `openfoam-mcp-webworn` | CFD setup, mesh checks, and pipe-flow analysis | 5 | 5 | 2 | 2 | Publisher reports 75% functionality and partial OpenFOAM 12 integration; no Wright backend pass | Pin build inputs; start with mesh/STL analysis, then a bounded laminar pipe case with analytical pressure-drop oracle; verify case artifacts and cancellation |
| 4 | `matlab-mcp-server` | Numerical analysis and engineering data | 5 | 5 | 3 | 2 | Official MathWorks implementation; Wright has no licensed-host qualification | Obtain a disposable licensed host; run a fixed matrix/numerical task and save MAT/CSV evidence through both gateways; test license/session loss |
| 5 | `simulink-agentic-toolkit` | System modeling and simulation | 5 | 5 | 2 | 2 | Community implementation; no current Wright real-model evidence | After MATLAB qualifies, build and simulate a minimal dynamic model; independently inspect model parameters and output time series |
| 6 | `autodesk-fusion-desktop-mcp` | Interactive mechanical CAD in Fusion | 5 | 4 | 2 | 2 | Official preview surface; requires a prepared desktop session | Use an isolated Fusion document/session; create and export a small part through Wright; verify document identity, units, revision, and cleanup |
| 7 | `autodesk-fusion-data-mcp` | Cloud design metadata and revisions | 4 | 5 | 2 | 2 | Official Autodesk service; OAuth/account evidence unavailable | Use a dedicated sandbox account; read a known design revision and preserve item/version identifiers through both gateways; test token expiry |
| 8 | `onshape-labs-featurescript-mcp` | Cloud parametric CAD and FeatureScript | 5 | 4 | 2 | 3 | Official Onshape Labs preview; no Wright OAuth-backed task | Use a dedicated document and least-privilege OAuth; make one reversible feature change, export, and verify document/microversion identifiers |
| 9 | `ansys-fluent-mcp` | Commercial CFD | 5 | 4 | 2 | 1 | Official PyFluent ecosystem, but Wright lacks a licensed Fluent host | Use a licensed disposable host; execute a canonical laminar case with analytical oracle, artifacts, timeout, and license-loss behavior |
| 10 | `kicad-mcp-lamaalrajih` or maintained replacement | Electronics CAD and DRC | 5 | 5 | 1 | 2 | Existing server initialized but 11 tool schemas incorrectly require client `ctx`; KiCad 9 unavailable in prior base | Recheck upstream fix and current KiCad 9 package; otherwise qualify a better maintained implementation with a tiny board, DRC, netlist, and BOM oracle |
| 11 | `rescale-mcp-hosted` | Remote HPC simulation orchestration | 4 | 4 | 2 | 2 | Publisher-hosted service; no Wright sandbox account or job evidence | Use a dedicated low-cost sandbox job; verify input hash, solver/version, job state, result checksum, cancellation, and credential revocation |

FreeCAD Robust and other FreeCAD variants are comparison or replacement
candidates. They should enter the portfolio only when they prove a materially
different dependable workflow or replace the current FreeCAD integration.

## Execution order and gates

Work one candidate at a time in a fresh standard Wright environment. Record the
exact repository commit or service/schema version, package constraints, host
version, image digest, prerequisite list, tool schema hash, task inputs, output
hashes, and cleanup result. A pass requires `initialize`, `tools/list`, a real
backend task, Wright `GatewayService`, the Hermes-facing `wrightgateway` MCP, an
independent numerical or artifact oracle, repeat execution, controlled failure,
and cancellation or a documented reason it does not apply.

The next credential-free Linux sequence is CAiD source resolution, then OpenFOAM.
For ROSBag, recover or replace the unavailable source repository, measure large-bag
performance, and qualify analysis/export separately. Solid Edge runs in parallel
order only when a clean Windows application session can be prepared without
touching user work. Licensed
MATLAB, Simulink, Ansys, Fusion, Onshape, and Rescale work waits for dedicated
hosts or accounts; lack of access remains a recorded blocker rather than a pass.

Do not begin portfolio process-chain qualification until at least ten distinct
integrations have current scoped evidence. At that point run three realistic
product-design chains: mechanical design to FEA and review artifact; system or
electronics design to simulation and test data; and field/test evidence back to
a controlled design revision. Verify identifiers, revisions, units, permissions,
artifact formats, provenance, error recovery, and cleanup at every handoff.

## Discovery and review

Run the bounded source and Registry intake weekly, but rank new leads only when
they add CAD, CAE, simulation, meshing, electronics, robotics/test data, PLM/PDM,
or engineering computation value. Confirm the primary publisher, implementation
identity, license, release or commit, install path, protocol, host prerequisites,
credentials, and security boundary before adding a qualification recipe. New
FreeCAD wrappers, generic project tools, and capability aliases remain outside
the portfolio count unless they add a distinct proven engineering workflow.
