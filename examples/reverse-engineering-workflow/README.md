# Reverse engineering: reusable preparation and staged implementation

For the current delivery scope, reproducible tests, historical source hashes and
remaining limitations, read [delivery qualification](delivery-qualification.md).
The dated qualification notes below retain their original evidence scope.

Read the [implementation plan](../../docs/workflows/reverse-engineering-implementation-plan.md)
and [method guide](../../docs/workflows/reverse-engineering-methods.md).

The user clarified the intended experience: supply text, images or other data;
Wright first researches the subject and gathers what is needed to build CAD.
Wright owns organizing evidence and calculating the modeling basis, with concise
questions for essential unresolved gaps. The new [research-first bundle](research-first/README.md)
implements and qualifies the supplied-material and targeted-research paths using
the existing runtime. Its README explains the remaining optional-tool and document
reading gaps. The existing structured preparation form below
is a retained technical test fixture, not the intended user entry experience.

`preparation.workflow.wflow` uses the existing source runtime: a declared first
input followed by an Astra-authored evidence-gap/measurement-plan task. It contains
saved protocol/helper instructions plus a scoped preparation asset and typed
`require_specified` policy. It has no CAD, export or provider-tool step. Open/save it
through the normal Workflows entry; local compilation or API execution does not
claim a new browser walkthrough. The existing common view remains available.

The three full-process `instructions.json` assets, `capability-plan.json` and
`acceptance-cases.json` are future authoring resources. They are not a qualified
end-to-end reconstruction graph or installed tool names. `astra-plan-proposal.md`
is the original proposal, retained separately from actual execution evidence.
`preparation-proposal.json` preserves the refinement response; the executable
instruction contains its verbatim report-writing paragraphs, omitting the first
two source-construction paragraphs. `authoring-provenance.json` records the initial
model/SDK identities; separate refinement/run receipts remain in pilot evidence.

`projection-qualification-basis.json` is a synthetic numerical control basis. The
existing validator profile is materialized from it by
`../reverse-engineering-research/qualify_validation.py`. The Windows pilot's new
[image-coordinate validation](../../docs/workflows/image-coordinate-validation.md)
candidate binds pixel observations to an exact related raster. Fresh live controls
pass the original numerical basis and reject wrong frames, units and missing
images; earlier inconclusive assessments remain historical. The older helper
alone does not supply the new frame binding. No fixture threshold is a Roadster
or real-camera tolerance. The basis is not globally registered.

The reference index utility consumes the existing `data/image_manifest.json` and
`data/parts_references.json` package format, checks confined local bytes and retains
unreviewed component links. It does not inspect images or download media. Its
research index schema is distinct from the runtime's EngineeringResult contract;
future integration must bind exact files through existing result/provenance owners.
Private Roadster assets and local absolute paths are not included in this bundle.

Earlier preparation qualification used an isolated Astra/high SDK route. Runtime
configuration independently selects and freezes the route for each new run;
source prose and the current chat selection do not select it. Existing route
freezing and capture own that behavior. Missing mandatory capabilities hold dependent reconstruction.
Provider/internal helper coverage, native editable CAD qualification and exact
export/correction remain separate readiness obligations.

Local proof root: pilot `state/research/20261020-re-workflow-implementation/`.
The current `STATUS.md` identifies actual scope and blockers. No human acceptance,
production release, physical execution or Roadster reconstruction is recorded.

The optional [fixed-camera mesh/photo comparison](../reverse-engineering-research/fixed-camera-projection.md)
now has a reusable local measurement utility and bounded numerical/visibility
qualification. It projects an exact tessellation with a recorded camera, preserves
the original raster frame and reports depth as well as silhouette. It does not
calibrate photographs or establish reconstruction accuracy. Use it only where
observable features and camera evidence make comparison meaningful; retain exact
CAD/camera/image identities through the existing result and validation owners.

The optional [two-view correspondence audit](two-view-consistency/README.md)
checks inspected feature identities before reconstruction. It preserves exact
image frames, exposes weak fits with leave-one-out checks and keeps epipolar-line
and homography-transfer errors separate. Its source has numerical and retained
pocket-artifact controls; it does not establish metric calibration or accept CAD.

The optional [native CAD section diagnostic](native-sections/README.md) intersects
exact exported geometry with declared planes and saves native section edges plus
sampled comparison plots. It exposes profile waves and section discrepancies that
face validity or a plausible rendering can miss. It retains exact artifact,
plane and face-selection identities, with analytic controls and the existing
pocket-correction artifact as a different-workflow compatibility check. It does
not choose corrections, alter tolerances or grant engineering acceptance.

For a declared surface T-contact, `../reverse-engineering-research/contact_topology.py`
provides a bounded CAD-authoring helper. It retains every input face, verifies an
unchanged geometric surface set and returns one explicitly connected open shell.
The Roadster local control showed why a loose pair is insufficient: STEP discards
its isolated shared vertex. A four-face connected group retains it. This helper
does not close a body, choose panels, alter engineering tolerances or supply a
new executor. Native source/build/export identities and an independent STEP
round trip remain required; local evidence is not a hosted-model correction.
