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
| AutoCAD MCP Pro | Headless mechanical DXF creation, save/reopen, exact entity inspection, and out-of-workspace rejection through direct sessions and both gateway paths | Clean Wright Intel Linux container, source commit `abc2a82e...`, 47-tool lean profile, ezdxf backend; live AutoCAD COM mode unverified |
| Rhino MCP | Millimetre solid Brep authoring, native 3DM save/reopen, and independent units, validity, topology, and bounds inspection through direct sessions and both gateway paths | Clean Wright Intel Linux container, source commit `3e10efb9...`, standalone rhino3dm mode; live Rhino/Grasshopper bridge and mesh/STL output unverified |
| KiCad MCP by blwfish | Footprint search, native PCB authoring/reopen, audit, and independently checked Gerber/drill archive through direct sessions and both gateway paths | Clean Wright Intel Linux container, release 0.13.0 commit `bcc6f11d...`, KiCad 9; DRC stdout defect and FreeRouter remain excluded |

Repeat user adoption remains unknown for all ten. Repository stars, publisher
demos, historical tests, and catalog labels are discovery signals rather than
proof that Wright users rely on a server.

## 11 September CAD-authoring comparison wave

This is the current credential-free Linux queue. It supersedes completed or
closed items in the 8 September ordering below. **Do not execute this wave until
the parallel UI and workflow cycle is complete.** Desk review and catalog
validation may continue while that hold is active.

AgentCAD goes first because it is packaged, credential-free, headless, and
documents creation, measurement, rendering, validation, version comparison, and
manufacturing exports in one surface. The next five are comparisons within the
same capability family. Test a later candidate only when AgentCAD evidence leaves
a meaningful gap or the candidate offers a materially different security,
artifact, or interaction model.

| Order | Candidate | Frozen intake reference | Distinct question | State |
|---:|---|---|---|---|
| 1 | `agentcad` | PyPI `agentcad[mcp]==0.6.0`; README blob `d251454e...` | Can one headless package create, render, measure, validate, compare, and export an exact solid safely through Wright? | Cataloged; planned; execution held |
| 2 | `build123d-mcp` (`D003`) | PyPI `0.3.84`; README blob `84f36178...` | Does its interactive construction and repair loop outperform the lead without weakening reproducibility or isolation? | Discovery record; compare after AgentCAD |
| 3 | CadQuery contrib MCP (`D002`) | Repository subdirectory `mcp-server`; README blob `9954de2a...` | Does the CadQuery-owned contribution provide a smaller, more maintainable render/inspect/export surface? | Discovery record; resolve commit before install |
| 4 | ShapeItUp (`D005`) | npm `@shapeitup/mcp-server@1.29.0`; README blob `1e1e4e28...` | Do its 25 headless TypeScript tools and verification loop add useful cross-runtime diversity? | Discovery record; compare if needed |
| 5 | vcad (`D006`) | npm `@vcad/mcp@0.10.0-main.87` observed 11 September | Does its bundled BRep WASM kernel reduce setup and improve reproducibility enough to justify a prerelease dependency? | Discovery record; compare if needed |
| 6 | Casys build123d MCP (`D004`) | JSR `@casys/mcp-build123d@0.6.3`; README blob `ac57e8ea...` | Do immutable MCP resources, exact mass properties, and MCP App output add a distinct artifact-provenance workflow? | Discovery record; resolve release digest before install |

For every row, capture the exact package archive or source commit and SHA-256,
the resolved dependency set, clean-container image digest, tool-schema hash, and
the common bracket input before execution. Stop after source or package review if
the license, immutable install path, workspace boundary, or arbitrary-code
containment is unclear. The detailed recipe is in
[`mcp-server-setup-recipes.md`](../mcp-server-setup-recipes.md#11-september-planned-cad-authoring-wave).

## 8 September ordered queue (historical)

Scores are relative planning judgments from 1 (weak) to 5 (strong). Confidence
uses Wright's historical backend evidence plus current source availability;
maintenance favors small, pinned, credential-free setups. The use column states
the evidence type instead of turning stars or downloads into an adoption claim.

| Order | Candidate | Lifecycle capability | Value | Distinct | Confidence | Maintain | Public/use evidence | Next qualification |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `solid-edge-mcp-burhop` | Native commercial parametric CAD | 5 | 5 | 3 | 2 | Maintained Wright-related implementation and prior native protocol pass; backend result-schema failure recorded | Use a disposable Windows/Solid Edge session; fix the nullable `activeDocument` contract; create/export a tiny part through both gateways; preserve user documents and process state |
| 2 | `openfoam-mcp-webworn` | CFD setup, mesh checks, and pipe-flow analysis | 5 | 5 | 2 | 2 | Publisher reports partial OpenFOAM 12 integration; no Wright backend pass | Pin build inputs; start with mesh/STL analysis, then a bounded laminar pipe case with an analytical pressure-drop oracle; verify case artifacts and cancellation |
| 3 | [`mcp-spice`](https://github.com/Casys-AI/mcp-spice) | Deterministic circuit simulation with ngspice | 5 | 5 | 2 | 3 | Active community source and a current tagged release; Wright has no protocol or solver evidence | Add a follow-up identity only after resolving license and package pins; simulate an RC transient and compare the time constant with an analytical oracle through both gateways |
| 4 | `matlab-mcp-server` | Numerical analysis and engineering data | 5 | 5 | 3 | 2 | Official MathWorks implementation; Wright has no licensed-host qualification | Obtain a disposable licensed host; run a fixed matrix/numerical task and save MAT/CSV evidence through both gateways; test license/session loss |
| 5 | `simulink-agentic-toolkit` | System modeling and simulation | 5 | 5 | 2 | 2 | Community implementation; no current Wright real-model evidence | After MATLAB qualifies, build and simulate a minimal dynamic model; independently inspect model parameters and output time series |
| 6 | `autodesk-fusion-desktop-mcp` | Interactive mechanical CAD in Fusion | 5 | 4 | 2 | 2 | Official preview surface; requires a prepared desktop session | Use an isolated Fusion document/session; create and export a small part through Wright; verify document identity, units, revision, and cleanup |
| 7 | `autodesk-fusion-data-mcp` | Cloud design metadata and revisions | 4 | 5 | 2 | 2 | Official Autodesk service; OAuth/account evidence unavailable | Use a dedicated sandbox account; read a known design revision and preserve item/version identifiers through both gateways; test token expiry |
| 8 | `onshape-labs-featurescript-mcp` | Cloud parametric CAD and FeatureScript | 5 | 4 | 2 | 3 | Official Onshape Labs preview; no Wright OAuth-backed task | Use a dedicated document and least-privilege OAuth; make one reversible feature change, export, and verify document/microversion identifiers |
| 9 | `ansys-fluent-mcp` | Commercial CFD | 5 | 4 | 2 | 1 | Official PyFluent ecosystem, but Wright lacks a licensed Fluent host | Use a licensed disposable host; execute a canonical laminar case with analytical oracle, artifacts, timeout, and license-loss behavior |
| 10 | `rescale-mcp-hosted` | Remote HPC simulation orchestration | 4 | 4 | 2 | 2 | Publisher-hosted service; no Wright sandbox account or job evidence | Use a dedicated low-cost sandbox job; verify input hash, solver/version, job state, result checksum, cancellation, and credential revocation |

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

The next credential-free Linux sequence is the `mcp-spice` identity/package
review, followed by its RC transient qualification, then OpenFOAM. CAiD's prior
identity is retired because its source remains unavailable and its useful scope
is covered by qualified BREP and FreeCAD integrations. For ROSBag, recover or
replace the unavailable source repository, measure large-bag performance, and
qualify analysis/export separately. Recheck KiCad's DRC stdout defect without
expanding the current PCB scope. Solid Edge runs in parallel order only when a
clean Windows application session can be prepared without touching user work.
Licensed MATLAB, Simulink, Ansys, Fusion, Onshape, and Rescale work waits for
dedicated hosts or accounts; lack of access remains a recorded blocker rather
than a pass.

The ten-integration gate is satisfied. Three fixed product-design chains now pass
through one disposable Wright workspace: mechanical BREP to scikit-fem screening
FEA and AutoCAD review DXF; KiCad PCB/fabrication to BREP enclosure envelope,
thermal FEA, and a ROS 2 validation trace; and field-deflection ROS 2 evidence
back to preserved AutoCAD revisions A and B. The evidence records 30 successful
gateway calls, exact tool-schema/configuration hashes, seven accepted handoffs,
corrupt-manifest rejection, units, revisions, artifact hashes, numerical and
file-format oracles, permissions, and cleanup. See
`../evidence/curation-2026-09-08/process-chains-linux.json` and the rerun procedure
in `../curation-runbook.md`. These are deterministic engineering screening and
traceability scenarios; they do not establish physical product validation or
repeat user adoption.

## Discovery and review

Run the bounded source and Registry intake weekly, but rank new leads only when
they add CAD, CAE, simulation, meshing, electronics, robotics/test data, PLM/PDM,
or engineering computation value. Confirm the primary publisher, implementation
identity, license, release or commit, install path, protocol, host prerequisites,
credentials, and security boundary before adding a qualification recipe. New
FreeCAD wrappers, generic project tools, and capability aliases remain outside
the portfolio count unless they add a distinct proven engineering workflow.
