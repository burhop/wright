# One reusable prompt-to-reviewed-CAD process

User direction, 11 October 2026: establish one useful process with a simple
drilled block, then increase design complexity by changing its input prompt.
The earlier thermal, mount and PCB portfolio and its evidence are retained;
they are not the current delivery sequence.

## User journey

Open the saved process in Wright, enter the design prompt, run it, then inspect
the design specification, test plan, editable SteveCAD design, measured checks,
three realistic views and illustrated design review. The normal working view
and refined workflow editor refer to the same durable run.

The seven stages are:

1. **Design prompt** — the only design-specific input that changes between runs.
2. **Engineering design document** — dimensions, coordinate frame, features,
   materials/appearance, requirements with identifiers, and explicit assumptions.
3. **Test plan** — predeclared measurable checks, tolerances and required evidence.
4. **Create in SteveCAD** — an agent performs the necessary CAD calls within one
   engineering task, using the design document.
5. **Validate** — inspect the actual saved revision against the original test
   plan; retain measured failures and unverified requirements. Capture three
   actual CAD orientations and their revision identities.
6. **Three realistic renderings** — the native successor exports the inspected
   revision, transfers it privately, validates a STEP-derived mesh, and renders
   three corresponding CAD orientations. Compare each with its original capture.
   These are presentation images, not measurements.
7. **Design review document** — requirements/results table, actual CAD views,
   realistic images, links to the editable design, findings and limitations.

The original stage 6 used three image-edit tasks; retained examples showed
geometry changes in their outputs. The native successor replaces that stage
with explicit existing MCP/file tasks. Its sixteen execution tasks implement
the same seven logical stages. No additional executor or vendor protocol
implementation is introduced. Stage 6's full main-process handoff passed on the
block in v16; that generated review still failed its blue-gray appearance.
V18 corrected the palette but exposed an authoring scope conflict. V19 preserves
the original supplied prompt through planning/review and now completes the
original block assignment: `block-native-006`, 617.248 seconds, eight CAD-stage
checks and all ten final review requirements pass. Independent numeric,
file-handoff, six-image and browser checks agree. Same-source six-hole reuse also
completed in 542.533 seconds with the supplied final geometry verified. Its
original review retains an unrequested intermediate-stock-state check as
UNVERIFIED; the additive provenance audit documents the authoring issue. Bracket
and final assembly progression remain separate. Earlier failures remain.

## First prompt and progression

The first prompt specifies a 60 x 40 x 12 mm block, one solid, four diameter-6 mm
through holes parallel to Z at (10,10), (50,10), (10,30), (50,30), with the origin
at the lower-left bottom corner. CAD inspection tolerance is 0.01 mm. A neutral
matte gray appearance is a presentation choice, not a material qualification.

Increase complexity only after the first full process works: an L bracket;
a mating two-part joint assembly; then a small 3D-printable
industrial-style robot arm. Reuse the process and change its design input. Each
new prompt must make requirements testable and disclose capability gaps. Assembly
fit, motion and printability need corresponding evidence; appearance cannot
establish them. The first block is a deliberate process proof, not the flagship
multi-tool engineering demonstration.

Add actual CAD video capture toward the assembly stages: orbit, exploded view
and supported motion. Later prepare unpublished marketing assets from actual
results. The user supplied a planetary gear assembly image and a turbocharger-
style assembly image as complexity references. The supplied X video could not
be viewed: both web retrieval and an ordinary browser navigation failed.

## Ownership and current implementation boundary

Reuse accepted source, versioned workflow instructions, input snapshots, bounded
MCP agent tasks, native image tasks, gateway, file/results storage and common UI.
SteveCAD owns CAD geometry and inspection; AgentCAD exports the actual STEP as
a validated mesh, and Blender produces the native presentation images. The
configured model produces the specification, test plan and review, and invokes
the bound CAD tools. Validation must expose actual observations
and must never translate missing evidence into a pass or human acceptance.

Changing the prompt creates a fresh run and fresh outputs. Exact CAD revision,
test plan, images and review belong to that run. Changes invalidate dependent
results. Existing reviews on other processes confer no authority here.

The configured Wright image transport produced all three presentation images
in the first completed run. The shared handoff now saves selected MCP image
responses through the existing file/result owner, binds explicit output ports,
retains call provenance and rejects missing or ambiguous images. The model never
substitutes a claimed screenshot for returned bytes. The existing common working
view shows the durable run; no UI executor or vendor adapter was added.

Local regression proof includes the existing document-search MCP task with an
image output and 138 passing affected tests. A substantially different live
workflow proof remains required before treating this shared mechanism as ready
for broader platform integration. The independent providers remain external.

The initial milestone means the full first run is inspectable in Wright, followed by a
second run of the same saved source with a changed prompt. CAD and image outputs
must be real; dimensions must be verified numerically. The four-hole block run
`ba80cc2a76fa430eb3bc731b530c198c` completed all eight tasks in 438.74 seconds.
Its actual geometry, three captures, three renders and illustrated review are
retained in `artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-006/`.
The independent arithmetic/identity audit passed. The generated review retains
UNVERIFIED findings for presentation fidelity and a material-assignment check
introduced by the specification; completion is not blanket engineering approval.

The current v7 four-hole run `cd33cd5747b145f784a6007f6c244412` and six-hole run
`865735ee274c44e9be1540fd5caf2e75` completed the same accepted source, digest
`d4dfe869ecdc366b158a762da7904b96a8cdb91e5ab0d70ad7ac6acb7eb06a89`,
with different input snapshots. Independent geometry/identity audits passed.
The four-hole run took 511.93 seconds and the six-hole run 478.87 seconds.
Each has three actual captures, three renderings and its original illustrated
review. The reports retain provenance findings; the six-hole report also has a
desktop horizontal-overflow finding. These findings are preserved, not hidden.

The replacement goal extends beyond that initial milestone to the bracket,
joint assembly, printable robot-arm package and unpublished media. Track its
evidence in [the progression ledger](prompt-to-reviewed-cad-progress.md).
Read the [SteveCAD usage guide](../mcp-catalog/usage-guides/stevecad-mcp.md)
before further tool calls. Failed attempts remain retained. Source acceptance,
execution completion, geometric checks, presentation inspection and user
acceptance remain distinct.
