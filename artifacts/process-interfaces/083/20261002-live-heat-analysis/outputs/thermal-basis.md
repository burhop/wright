# Thermal Case Basis and Mandatory Requirements

## Case basis

- Case: synthetic conduction-only sizing comparison for a silent e-ink sign-controller strap.
- Candidates:
  - `baseline_40`: 100 mm length, 40 mm width, 2 mm thickness.
  - `revision_60`: 100 mm length, 60 mm width, 2 mm thickness.
- Geometry: each candidate is an unperforated rectangular solid spanning X = 0–100 mm, Y = 0–W mm, and Z = 0–2 mm.
- Maximum permitted design-envelope width: 65 mm.
- Thermal conductivity: constant k = 200 W/(m·K).
- Comparative density: 2700 kg/m³, used only for comparative mass.
- Heat input: total 4 W, applied uniformly over the complete X = 100 mm end face.
- Cold boundary: complete X = 0 face fixed at 25 °C.
- Remaining boundaries: all four longitudinal faces perfectly insulated.
- Hot-end acceptance limit: at or below 45 °C, inclusive.
- Analytical baseline: steady one-dimensional bar conduction with thermal resistance L/(kWt) and temperature rise ΔT = QL/(kWt).
- Solver geometry, heat flux, and material quantities must be converted consistently to SI units.
- Comparison objective: select the narrowest declared candidate satisfying the inclusive 45 °C hot-end limit.

## Mandatory requirements

1. `HEAT01-GEOMETRY`: Retain each candidate as an unperforated 100 mm long, 2 mm thick rectangular plate with its declared 40 mm or 60 mm width. Both widths are within the 65 mm envelope.
2. `HEAT01-BOUNDARIES`: Fix the complete X = 0 face at 25 °C, apply a total of 4 W uniformly to the complete X = 100 mm face, and insulate all four longitudinal faces.
3. `HEAT01-MATERIAL`: Use constant thermal conductivity 200 W/(m·K). Use density 2700 kg/m³ only for comparative mass; do not present it as certified alloy data.
4. `HEAT01-FIELDS`: Retain actual coarse and refined numerical temperature fields for both width candidates. These fields must be distinct from the analytical calculation and from the supplied input diagram.
5. `HEAT01-ANALYTICAL`: For each candidate, the numerical hot-end temperature rise must agree within 2% of QL/(kWt), using that candidate’s declared dimensions and inputs.
6. `HEAT01-BALANCE`: For each refined candidate field, total heat removal must agree with the declared 4 W input within 1%.
7. `HEAT01-REFINEMENT`: For each candidate, the coarse-to-refined hot-end temperature-rise change must be no greater than 2%, and both mesh identities must be retained.
8. `HEAT01-OUTCOME-40`: The 40 mm candidate must exceed the inclusive 45 °C hot-end limit under the declared model.
9. `HEAT01-OUTCOME-60`: The 60 mm candidate must be at or below the inclusive 45 °C hot-end limit under the declared model.
10. `HEAT01-SELECTION`: The sizing decision must select `revision_60` as the narrowest declared candidate satisfying the inclusive 45 °C limit.
11. `HEAT01-DELIVERABLES`: Retain candidate STEP geometry, coarse and refined numerical fields, heat-balance data, mesh sizes and refinement evidence, and a machine-readable sizing decision with rationale.
12. `HEAT01-CLAIM-SCOPE`: Limit conclusions to the synthetic conduction-only model. Do not claim real-controller temperature, verified hardware performance, physical qualification, manufacture, or standards compliance.

## Model exclusions and claim limits

- No convection, radiation, screw holes, interface resistance, heat sink, local chip footprint, mounting holes, bending, or surface-finish requirement is included.
- The 4 W load and all case data are synthetic.
- The supplied concept image is an input-boundary schematic, not a computed temperature field or result contour.
- No material certification, purchasing conclusion, manufacturing action, device action, physical qualification, or critic review is asserted.
- Adding deferred features or thermal interfaces requires a new case.

## Numerical status

Numerical results have not yet been computed. The analytical-agreement, heat-balance, refinement, candidate-outcome, and selection statements above are mandatory acceptance requirements, not verified results.

## Assumptions

No assumptions beyond the supplied case basis are introduced.