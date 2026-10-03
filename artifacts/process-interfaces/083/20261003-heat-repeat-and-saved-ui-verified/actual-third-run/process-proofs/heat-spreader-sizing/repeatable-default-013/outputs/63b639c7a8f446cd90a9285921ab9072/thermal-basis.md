# Thermal Case Basis and Mandatory Requirements

## Case identity

- Scenario ID: `heat-spreader-sizing-01`
- Template ID: `heat-spreader-sizing`
- Title: Conduction strap for a silent e-ink sign controller
- Basis: Synthetic, idealized, steady conduction-only comparison.
- Candidates: `baseline_40` and `revision_60`.

## Exact model basis

| Parameter | `baseline_40` | `revision_60` |
|---|---:|---:|
| Length | 100 mm | 100 mm |
| Width | 40 mm | 60 mm |
| Thickness | 2 mm | 2 mm |
| Constant thermal conductivity | 200 W/(m·K) | 200 W/(m·K) |
| Comparative density | 2700 kg/m³ | 2700 kg/m³ |
| Total heat input | 4 W | 4 W |
| Fixed cold-face temperature | 25 °C | 25 °C |
| Inclusive hot-end limit | 45 °C | 45 °C |

Each candidate is an unperforated rectangular solid spanning X = 0–100 mm, Y = 0–W mm, and Z = 0–2 mm. Both widths are within the 65 mm design envelope.

## Boundary conditions

- Fix the complete X = 0 face at 25 °C.
- Apply a total of 4 W uniformly over the complete X = 100 mm face.
- Treat all four longitudinal faces as perfectly insulated.
- Convert geometry and heat-flux quantities consistently to SI units inside the solver.
- Do not include convection, radiation, screw holes, interface resistance, a heat sink, a local chip footprint, mounting holes, or thermal interfaces.

## Material and analytical basis

- Use constant thermal conductivity k = 200 W/(m·K).
- Use density 2700 kg/m³ only for comparative mass.
- Do not present the conductivity or density as certified alloy data.
- Use the steady one-dimensional bar baseline with thermal resistance L/(kWt).
- Compare each numerical hot-end temperature rise with QL/(kWt), using that candidate’s declared dimensions and inputs.
- An analytical calculation is not a numerical temperature field.

## Mandatory numerical requirements

- Retain actual coarse and refined numerical temperature fields for both candidates.
- Keep numerical fields distinct from both the analytical calculation and the supplied input diagram.
- Each numerical hot-end temperature rise must agree with QL/(kWt) within 2%.
- Each candidate’s coarse-to-refined hot-end temperature-rise change must be no more than 2%.
- Retain both coarse and refined mesh identities for each candidate.
- For each refined candidate field, total heat removal must agree with the declared 4 W input within 1%.

## Mandatory outcome requirements

These are required acceptance outcomes and are not reported here as computed results:

- `baseline_40` must exceed the inclusive 45 °C hot-end limit under the declared model.
- `revision_60` must be at or below the inclusive 45 °C hot-end limit under the declared model.
- The sizing decision must select `revision_60` as the narrowest declared candidate satisfying the inclusive 45 °C limit.

## Mandatory deliverables

The output set must retain:

- Candidate STEP geometry.
- Numerical temperature fields for both coarse and refined meshes.
- Heat-balance data.
- Mesh sizes, mesh identities, and refinement evidence.
- A machine-readable sizing decision with rationale.

## Claim scope

- Conclusions must remain limited to the synthetic conduction-only model.
- Do not claim real controller temperature, verified hardware performance, physical qualification, manufacture, material certification, or standards compliance.
- Do not reuse the supplied concept image or SVG as a computed temperature contour.
- Do not invent critic or reviewer findings.

## Current result status

Numerical results have not yet been computed. No numerical temperature, analytical-rise value, heat-balance result, refinement result, or physics-validation claim is recorded here.

## Assumptions

No assumptions beyond the supplied case basis and mandatory requirements are introduced.