# Fixed Pi reference and CAD-to-CFD operations

These operations remove the architectural need to send reference downloads,
filesystem staging or CFD preparation through Blender. They do not disable or
bypass Blender safe mode, communicate with its socket, or expose a replacement
unrestricted code executor. The reviewed binding is implemented in
`scripts/prepare-pi-fixed-dataset-campaign.py`; the earlier Blender-based preparer
remains historical. Three actual API-created Pi instances and native initialized
projects are staged and enrolled as attempt 002. Each persisted grant's eleven
tool identities match the fresh API discovery, including the verified selected
AgentCAD bootstrap authority. The manifest is
`.local-run/feature-081-live/campaign-execution/pi-fixed-attempt-002.json`;
pin verification is `pi-fixed-campaign/enrollment-pin-verification.json` under
the same local runtime root. No Pi campaign workflow was dispatched by this setup task.

## Implemented capabilities

`scripts/pi_reference_mcp.py` exposes a fixed retrieval tool,
`retrieve_pi_manufacturer_references(operation_source_document, output_directory)`.
It downloads three exact manufacturer URLs, validates every redirect origin,
extracts actual PDF pages with pypdf, and retains bytes, hashes and retrieval dates.
Its executing source must match a staged attempt input, and output is restricted
to that attempt's `artifacts/research`. It accepts no URL, shell or Python code.
Its second tool, `read_pi_reference_page`, returns one exact PDF page in slices
of at most 4,000 characters, with source URL, raw-PDF hash, page number and explicit
next offset. Full source pages remain on disk; retrieval returns a compact manifest.

The initial official documentation HTML endpoint returned HTTP 403. Published
manufacturer PDFs provide the required primary evidence without that endpoint:

- [Pi 5 board mechanical drawing](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)
- [Pi 5 product brief, DS-6](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008348-DS-6-raspberry-pi-5-product-brief.pdf)
- [Active Cooler mechanical drawing](https://pip-assets.raspberrypi.com/categories/993-raspberry-pi-active-cooler/documents/RP-008187-DS-1-raspberry-pi-active-cooler-mechanical-drawing.pdf)

The cooler reference is not a selection of that cooler for these studies and
does not replace the customer's fictional fan curve. Approximate/reference-only
dimensions and unresolved accessory/connector keepouts remain explicit.

`scripts/pi_cfd_operations.py` is a fixed declarative compiler. It imports actual
STEP solids through Gmsh/OCC, fragments interfaces into conformal topology,
rejects overlapping/ambiguous region identity, derives named exterior patches
from explicit CAD plane selectors, writes an actual tetrahedral mesh, then runs
`gmshToFoam`, `splitMeshRegions -cellZones -overwrite` and `checkMesh`. It writes
OpenFOAM10 conjugate heat-transfer dictionaries from bounded physical data.
No user-provided dictionary, source code, command or tutorial geometry is accepted.

`scripts/pi_cfd_mcp.py` exposes two source-bound tools:

1. `prepare_pi_cfd_comparison(operation_source_document, output_directory, contract_documents)`
   requires two actual same-run CAD contracts. It transfers exact STEP bytes to
   dedicated Foam scratch, meshes both alternatives, records hashes and writes a
   fixed parent `Allrun`. It does not perform the heat-transfer solves.
2. `collect_pi_cfd_comparison(operation_source_document, output_directory)`
   requires completed solver dispatch records, actual final fields, matching
   compiler/contract/geometry lineage and solver completion logs. It creates
   `cfd-comparison.json` and `cfd-fields.zip` from those computed files only.

The existing actual Foam-Agent **run** tool executes that Allrun between the two
fixed tools. The fixed solver path invokes `chtMultiRegionFoam`, `foamToVTK` and
PyVista extraction, retaining T/p/U/rho fields and actual boundary area, pressure
and integrated volume-flux observations. An unresolved dispatch is never replayed;
a completed matching result is reused without executing the solver. Explicit
`ERROR` signaling prevents upstream log scanning from hiding a failed child.

## Exact CAD contract required before preparation

The current draft's shell/fluid STEP/STL pair plus free-form lineage is insufficient.
The AgentCAD script must additionally export each **closed solid** fluid, shell/lid
and heat-source region as its own STEP, preserving units, source-load coordinates
and named roles. A disconnected lid can be a separate solid region. Every required
region must be actual CAD output, not a later surrogate fixture. Retain existing
STEP/STL deliverables and original four canonical task IDs.

Each variant's JSON has only these supported fields:

```json
{
  "schema_version": 1,
  "units": "mm",
  "ambient_k": 298.15,
  "gravity_m_s2": [0, 0, -9.81],
  "mesh_size_mm": 2,
  "duration_s": 1,
  "delta_t_s": 0.001,
  "regions": [
    {"name": "air", "kind": "fluid", "step": "campaign/.../artifacts/air-a.step", "sha256": "actual-byte-sha256", "material": {"rho": 1.18, "cp": 1005, "kappa": 0.026}, "heat_w": 0},
    {"name": "shell", "kind": "solid", "step": "campaign/.../artifacts/shell-a.step", "sha256": "actual-byte-sha256", "material": {"rho": 1270, "cp": 1200, "kappa": 0.2}, "heat_w": 0},
    {"name": "board_source", "kind": "solid", "step": "campaign/.../artifacts/source-a.step", "sha256": "actual-byte-sha256", "material": {"rho": 2700, "cp": 900, "kappa": 120}, "heat_w": 6}
  ],
  "boundaries": [
    {"name": "inlet", "region": "air", "axis": 1, "coordinate_mm": 0, "tolerance_mm": 0.001, "role": "ambient"}
  ],
  "assumptions": ["Explicit material, domain, exterior thermal and transient assumptions"]
}
```

The compiler also accepts an optional closed `evidence` object containing only
CAD inspection provenance (`fluid_step_sha256`, observed fluid bounds and the
bounded `fan_inlet_face`/`outlet_face` records). It is descriptive lineage only;
unknown evidence keys and all source or dictionary injection remain rejected.

This example demonstrates the schema, not approved material or geometry choices.
Real values must come from each accepted design basis. Plane selectors must match
actual exterior CAD faces unambiguously; missing or overlapping matches fail.
Supported roles are `ambient`, `inlet`, `outlet` and `fan`; all omitted exterior
faces are walls. Non-coupled exterior temperatures are prescribed ambient in this
compiler; the design basis must disclose that choice. To resolve shell-to-exterior
air transfer instead, the CAD air region must include the explicit external domain
and its named ambient boundary faces. Do not silently equate an interior-only
domain with resolved exterior convection. The current solver is laminar ideal-gas
air with fixed viscosity 1.85e-5 Pa s, conduction in solids and no radiation model.

For the fan case add `fan_curve` with `points` containing the exact uploaded
monotone [volume_flow_m3_s, pressure_pa] pairs and
`provenance: "synthetic_customer_curve"`; identify exactly one actual inlet fan
face. This represents a pressure boundary, not resolved fan blades or an internal
cyclic pressure-jump surface. Its location and omitted blade/duct physics must be
disclosed in the accepted design basis. No constant-velocity substitute is used.

## Native fan-pressure adapter

Installed OpenFOAM10 has native `fanPressure` and the templated `PrghPressure`
hydrostatic adapter, but does not register their combination. The fixed source
`scripts/pi_foam_boundary/wrightPrghFanPressure.C` registers that combination; it
does not implement a new fan equation. Native fanPressure uses actual patch volume
flux and the table; native PrghPressure applies the hydrostatic correction.
The compiler checks the built adapter source, copies the resulting library into
the case, and records source/library hashes. Only this fixed library is selected.

## Actual isolated evidence and deployment mapping

The independent selected container `wright-081-pi-fixed-qualification` uses the
existing Foam image at
`sha256:7a18a458e0d8e38e165b0126525b4fdf8337ff6a80f223b13ea9c47d0a1ac7cb`.
It mounts only its disposable qualification directory and read-only operation
sources. Added only `gmsh==4.15.1` and `pypdf==6.9.1` to its existing FoamAgent
Python environment. Built the fixed adapter with the installed OpenFOAM `wmake`.
No shared AgentCAD, Blender, Foam service, API process or base image changed.

`qualify-pi-cfd-prerequisite.py` creates independent actual OCC STEP air, shell and
heater solids. Probe 002 meshed all three regions, passed all three `checkMesh`
runs and produced actual transient fields: 1,784 air, 760 shell and 70 heater cells.
The separate fan prerequisite used the actual tabulated synthetic curve and
completed 100 time steps. These tiny models are explicitly prerequisite tests,
not any supplied Pi enclosure geometry and not campaign runs.

`qualify-pi-reference.py` reference 002 passed actual MCP initialize/list/call and
retrieved all three PDFs. `qualify-pi-comparison-mcp.py` exercises fixed preparation,
native Foam-Agent `run`, and fixed collection; its attempt evidence records the
actual result rather than assuming that an empty upstream error list proves fields.
All evidence is under `.local-run/feature-081-live/pi-fixed-qualification/`.
Twenty fast contract/replay/confinement/preparer tests passed. Canonical Pi completion,
full public catalog qualification, and engineering validation are not claimed.

The production selected companion `wright-081-pi-runtime` mounts the demo workspace at
`/demo`, existing dedicated Foam scratch at `/workspace`, and sources read-only
at `/operations`. Configure `WRIGHT_PI_CFD_WORKSPACE=/demo` and
`WRIGHT_PI_CFD_FOAM_ROOT=/workspace`. The existing Foam service already sees that
scratch as `/workspace`, so generated Allrun paths align. Build the fixed library
at `/workspace/pi-boundary-build/lib/libwrightPiFan.so` with its adjacent source.
The actual native Foam service needs only its existing Python/PyVista/OpenFOAM
environment to solve and extract; Gmsh belongs to the selected companion.

Normal API registration, install, demo-workspace enablement and activation completed
for reference server `4592ee69-a60c-4601-8674-8619083dc7ba` and compiler/collector
server `d044179a-bf3d-4086-b7c4-b00e8fd97f71`. Both are disabled by default for other
workspaces. The production Docker-exec stdio transports passed actual native
GatewayService discovery and calls; the existing Foam-Agent HTTP service performed
the two real prerequisite solves. Collection verified computed field hashes and
completed solver records. Evidence is
`.local-run/feature-081-live/pi-fixed-production-gateway.json`; the public scoped
summary is `docs/mcp-catalog/evidence/feature-081-pi-fixed-runtime.json`.
Tool observations ranged from about 1.2 KB to 5.6 KB. A separate completed-result
replay check made zero solver calls and preserved every recorded file timestamp.

Stage `pi_cfd_operations.py`, `pi_cfd_mcp.py`, and `wrightPrghFanPressure.C` as
explicit inputs. Stage `pi_reference_mcp.py` for reference retrieval. Pinned source
copies are provenance, not required newly generated engineering deliverables.
AgentCAD initialization can use the existing fixed native initialization
prerequisite pattern used by the jig/heat preparers; it does not need Blender.
The real AgentCAD run/exports and original sourced design review remain mandatory.

Native Foam-Agent defaults attempted OAuth-backed model initialization even for
its run-only server. Qualification supplies an explicitly unused model/embedding
configuration and placeholder key, plus `WM_PROJECT_DIR=/opt/openfoam10`; it sends
no model request and forwards no user credential. Its stdout diagnostic printing
pollutes stdio, so existing HTTP transport is preferable for runtime registration.

The prerequisite durations prove actual solver execution, not steady-state
convergence, target temperatures, mesh independence or physical accuracy. Actual
Pi run time/domain/material choices and convergence reporting remain engineering
design work. Every content-validity and canonical campaign counter stays unchanged
by these prerequisite probes.
