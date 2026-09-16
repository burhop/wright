# Fixed CAD-to-CFD contract for prototype enclosure comparison

This is a supported solver/data contract, not customer geometry or a completed design.
Choose actual prototype geometry from the case brief and sourced primary references.

## Exact CAD contract required before preparation

The current draft's shell/fluid STEP/STL pair plus free-form lineage is insufficient.
The AgentCAD script must additionally export each **closed solid** fluid, shell/lid
and heat-source region as its own STEP, preserving units, source-load coordinates
and named roles. A disconnected lid can be a separate solid region. Every required
region must be actual CAD output, not a later surrogate fixture. Retain existing
STEP/STL deliverables and original four canonical task IDs.

One named material region may contain several closed solids, such as a base and
lid or a vented enclosure assembled from discrete printed panels. The compiler
accepts up to 64 solids per named region and 128 per variant, and records the
per-region counts when a bound is exceeded. OCC fragments created only by
intersections among solids with that same region name are grouped into one
physical material region. A fragment owned by two different region names
remains a hard failure because its material identity is ambiguous. Native gmsh
diagnostics and progress are written to files and stderr; MCP stdio stdout is
reserved for JSON-RPC frames.

CAD authoring must export mutually exclusive material volumes. Subtract
embedded insert and heat-source volumes from the shell before export, and
subtract all solid regions from the fluid region. Touching faces are expected;
coincident volume under different region names is not.

Each variant's JSON has only these supported fields:

```json
{
  "schema_version": 2,
  "units": "mm",
  "ambient_k": 298.15,
  "gravity_m_s2": [0, 0, -9.81],
  "mesh_size_mm": 2,
  "numerics": { "mode": "steady", "iterations": 300, "write_interval": 50 },
  "mesh_grading": {
    "far_size_mm": 10,
    "distance_min_mm": 2,
    "distance_max_mm": 25
  },
  "regions": [
    {
      "name": "air",
      "kind": "fluid",
      "step": "campaign/.../artifacts/air-a.step",
      "sha256": "actual-byte-sha256",
      "material": { "rho": 1.18, "cp": 1005, "kappa": 0.026 },
      "heat_w": 0
    },
    {
      "name": "shell",
      "kind": "solid",
      "step": "campaign/.../artifacts/shell-a.step",
      "sha256": "actual-byte-sha256",
      "material": { "rho": 1270, "cp": 1200, "kappa": 0.2 },
      "heat_w": 0
    },
    {
      "name": "board_source",
      "kind": "solid",
      "step": "campaign/.../artifacts/source-a.step",
      "sha256": "actual-byte-sha256",
      "material": { "rho": 2700, "cp": 900, "kappa": 120 },
      "heat_w": 6
    }
  ],
  "boundaries": [
    {
      "name": "inlet",
      "region": "air",
      "axis": 1,
      "coordinate_mm": 0,
      "tolerance_mm": 0.001,
      "role": "ambient"
    }
  ],
  "assumptions": [
    "Explicit material, domain, exterior thermal and numerical assumptions; convergence remains unvalidated"
  ]
}
```

An optional `evidence` object may carry bounded CAD inspection provenance for
the declared fluid STEP: `fluid_step_sha256`,
`fluid_domain_observed_bounds_mm`, `fan_inlet_face`, and `outlet_face`. Each
face record contains only its inspection method, matching count, selected face
index, six observed bounds and area in square millimetres. This metadata is
validated as closed descriptive lineage and is never used as a selector,
material value, dictionary, source or executable input; unknown evidence keys
remain invalid.

This example demonstrates the schema, not approved material or geometry choices.
Real values must come from each accepted design basis. Plane selectors must match
actual exterior CAD faces unambiguously; missing or overlapping matches fail.
Supported roles are `ambient`, `inlet`, `outlet` and `fan`; all omitted exterior
faces are walls. Version 2 prescribes ambient temperature at openings only on
incoming/reverse flow, using native `inletOutlet`; uncoupled walls remain prescribed
ambient and this limitation must be disclosed. To resolve shell-to-exterior
air transfer instead, the CAD air region must include the explicit external domain
and its named ambient boundary faces. Do not silently equate an interior-only
domain with resolved exterior convection. The current solver is laminar ideal-gas
air with fixed viscosity 1.85e-5 Pa s, conduction in solids and no radiation model.

Version 2 selects the installed OpenFOAM10 `chtMultiRegionFoam` steady mode:
every region uses `steadyState`, with one outer SIMPLE correction and iteration
step 1. Its solution controls follow the installed OpenFOAM steady buoyant-room
pattern: PCG/DIC for `p_rgh`, field relaxation 0.7 for `p_rgh`, equation
relaxation 0.2 for `U`, and 0.1 for fluid enthalpy and solid energy. The stated
iteration budget must be divisible by the write interval so
the final fields are written. Iteration numbers are not physical seconds. A
300-iteration profile is an explicit prototype comparison proposal to measure,
not a convergence claim. Preserve all customer loads, locations, materials and
geometry; disclose the numerical limits and keep content validation false.

Grading derives distance from the actual imported solid CAD surfaces. Near
those surfaces use `mesh_size_mm`; beyond `distance_max_mm` use `far_size_mm`,
interpolating from `distance_min_mm`. Geometry is not substituted or simplified.
Measure meshing, conversion, solve and export time before a full pilot; each
current canonical operation must fit its declared runtime budget.

Legacy version 1 retains its original uniform mesh and explicit `duration_s` /
`delta_t_s` transient behavior. Use it only for an explicitly justified transient
study. Do not add those fields to version 2 or silently shorten an accepted
transient to make it finish. A numerical-profile change requires a new documented
proposal, fresh source/contract hashes and the normal local test review.

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
