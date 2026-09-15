# Jig circular-edge extraction guidance

The read-only native diagnosis in
`.local-run/feature-081-live/campaign-execution/jig005-circle-center-diagnosis.json`
showed that the existing case01 attempt005 STEP contained the intended circular
hole geometry. Installed build123d 0.10.0 implements `Edge.center()` with
`position_at(0.5)` by default, yielding a point on the curve. Its `arc_center`
property returns the underlying circle center. The diagnostic preserved the
original STEP and its SHA-256; this is an API-use diagnosis, not full jig
engineering qualification.

The reusable jig preparer now supplies this narrowly scoped guidance in both
the source/DXF-authoring prompt and the independent inspection-authoring prompt:
filter `GeomType.CIRCLE`, use `edge.arc_center` and `edge.radius`, and apply the
original datum transform. Do not compensate by shifting supplied hole locations,
substituting bounding-box centers or loosening alignment tolerances. The
independent inspection still reopens the actual exported STEP and preserves all
keepout, stackup, clearance and failure reporting requirements.

All three fresh attempt006 instances were created through the normal template
API, prepared, mapped, saved and enrolled using current tool pins. The immutable
queue manifest is
`.local-run/feature-081-live/campaign-execution/jig-attempt-006.json`;
`jig-attempt-006-staging-verification.json` records each exact source/grant
identity. Each has eight stages, eight tool pins, ten verified inputs, complete
input-binding evidence, all three original stage IDs and both original edges.
Private AgentCAD project initialization completed with exit code zero. All seven
declared generated output files remain absent: no CAD generation or workflow
execution occurred during staging.

Twenty-three relevant preparer/input-binding tests passed and Ruff passed.
Attempt005's partial files and grants remain unchanged, as does active batch009.
This prompt correction requires no API or Hermes restart and grants no run-count
or output-correctness credit.
