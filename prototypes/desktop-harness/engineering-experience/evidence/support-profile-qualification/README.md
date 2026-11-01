# Support-enabled profile qualification — actual digital tool outputs

Preparing the handle inspection resources exposed a readiness defect: candidate
036 still selected the earlier coupon profile with `enable_support=0`. That
profile is preserved unchanged. A fresh copy changes only `enable_support` to `1`.
The candidate registration has **not** been switched to it and the handle remains
not ready. Freeze/select the new profile explicitly before executing that stage.

The same pinned independent provider and OrcaSlicer 2.5.0-alpha ARM64 container
sliced a closed synthetic 20 × 8 × 24 mm L-shaped overhang in two orientations.
Both calls went through actual GatewayService/StdioRunner with only
`slice_model_file` exposed. Container networking was disabled, the root was read
only, and no printer credentials or hardware tools were available. No previous
workflow was started or resumed; this is a provider prerequisite.

| Observed property | Upright | Side |
|---|---:|---:|
| Returned `ok`, exact source/output/plate | PASS | PASS |
| Actual package/native PNG | PASS | PASS |
| Layers | 120 | 40 |
| Nominal model segments | 3,438 | 1,247 |
| Nominal support segments | 14,042 | 0 |
| Unclassified nominal segments | 789 | 0 |

Both actual packages record PETG, P1S, 0.4 mm nozzle, 0.20 mm layers, five walls,
40% infill, Textured PEI Plate and support enabled. The preserved response also
records the actual CLI profile paths. Profile hashes and image/runtime identity
are in `identity.json` and `inspection-report.json`; exact profile bytes are
under `profiles/`.

The existing passive reader/inspector consumed the real package and response.
Selected call schema/arguments came from this probe's discovery and intent,
not a fabricated historical schema. This is a direct gateway probe, not canonical
workflow-task execution. Inspection is scoped to the declared nominal G-code
section; it is not machine simulation. Unclassified paths remain explicit.
Segment counts do not measure support contact area, print time or strength.

The native PNGs were visually inspected and show the two actual model
orientations. They **do not show generated supports**. The separate nominal-path
SVG comes from actual G-code with support paths colored orange; it shows one
layer, not all physical contact locations. No substitute native preview was made.

Limits: the actual handle, orientation-dependent strength, support removal and
physical fit remain unqualified. No engineering review, printer approval or
Windows acceptance is claimed. The alpha runtime remains experimental.

Private reproducible call records, geometry, packages and audit:
`.local-run/experience-review/support-profile-036/gateway-support-01/`.
Both bounded calls terminated; the owned provider was stopped normally.
The retained drivers refer to that qualification directory and reject existing
output directories. They are evidence, not campaign launchers. The initial
inspection driver name shadowed Python's `inspect` module and failed before
inspection; renaming it resolved the import. No slicing was repeated.
