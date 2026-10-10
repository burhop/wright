# Mechanical engineering and product usability review

**Prepared:** 8 October 2026. **Status:** review and proposed follow-on work;
implementation has not started. The user's review of the engineering demo is
the authority for the priorities below. The executable proposal is
[mechanical-engineering-usability-goal.md](mechanical-engineering-usability-goal.md).

## What the results establish

The [demo deck](../../artifacts/demos/20261008-user-progress/output/wright-engineering-process-demo.pptx),
its [slide manifest](../../artifacts/demos/20261008-user-progress/build/manifest.json),
the [completion record](instruction-portability-completion.md), and the
[handoff](instruction-portability-handoff.md) establish useful local software
progress: inspectable saved instructions, deliberate input, durable continuation,
actual CAD/image handoffs, results that can be reopened, and portable reuse.
These mechanisms should be retained. Their test results do not establish that
the demonstrated engineering assignment or presentation is suitable for engineers.

The user's critique identifies a real planning and evaluation failure. The
sheet-metal CAD, mesh and slicing chain proves scoped file and tool interaction.
It does not establish a sensible manufacturing route for that sheet-metal design.
Slide 13 calls slicing an engineering manufacturing contribution without an
appropriate additive design brief. Describing its digital nature does not fix
that gap. Preserve its evidence as an integration regression; remove it from
future flagship engineering demonstrations.

A deliberately specified printed fit mockup of a metal design could have a
legitimate purpose, but that was not the accepted assignment. Do not retroactively
use this rationale to justify the example. A change of manufacturing route needs
an explicit purpose, revised design basis and appropriate verification.

## Findings and proposed corrections

| User finding | Evidence and diagnosis | Required follow-on result |
|---|---|---|
| Keep the next product review priorities | Slide 15 names final deliverable visibility, status/questions, cancellation and repeat use. These remain useful. | Preserve that slide's four recommendations and implement/test each through normal Wright workspace journeys. |
| Poor engineering process | Slide 13 joins native sheet metal to an offline polymer slice. Neither topology nor unit checks establish process suitability. | Separate sheet-metal fabrication and additive part design, using existing engineering briefs, meaningful tool contributions and actual downstream artifacts. |
| Unreadable screenshots | Slide 11 places an entire dense export/import form in about half a slide. Slides 7 and 9 likewise need more focused framing. Higher image resolution alone cannot fix small apparent text. | Improve the real UI, then record focused task views and readable slide close-ups. Preserve originals and show context; no reconstructed successful UI. |
| Weak interstage engineering validation | Geometry/file checks and software tests are useful but do not cover manufacturing intent, fit, drawing completeness or physical behavior. | Present requirements, design basis, engineering assessments, process checks and inspection plans as revision-linked deliverables. Apply appropriate checks at each meaningful handoff. |
| Add another CAD system | The catalog already records multiple FreeCAD providers, with different qualification outcomes. | Qualify an existing independent FreeCAD MCP for the selected solid-part job and ordinary workspace use. Keep its implementation external. |

## Recommended engineering demonstrations

### A. Sheet-metal fabrication package

Reuse the **barcode-reader wall dock** from
`tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/`.
Read the original brief, manufacturing policy, stock-selection decision, CAD
choices and company-capability revisions together. Preserve their authority,
dimensions, material-selection rules and unresolved supplier issues in a fresh
isolated copy. Historical campaign outputs and reviews stay untouched.

The useful job is a reviewable fabricated-part package: design intent and
requirements; native Solid Edge sheet metal; folded geometry and genuine flat
pattern; independently checked geometry and fabrication rules; dimensioned
drawing and inspection plan; local review package. A slicer contributes nothing
to this fabrication route.

Existing bindings explicitly report that the Solid Edge provider lacked native
Draft/dimensioned drawing creation. Qualify a current independent drawing
capability, potentially FreeCAD TechDraw consuming the actual folded STEP, before
promising a drawing. Native Solid Edge remains the owner of the true developed
flat pattern. A screenshot or projected outline cannot replace either deliverable.

The original brief includes a load assumption and unknown wall anchors. Preserve
those limits. Source suitable material and bend data. A documented K-factor
choice is a geometric development assumption until its manufacturing basis is
confirmed. Existing release holds and supplier uncertainty remain visible.

### B. Solid-part design for additive manufacture

Reuse the **observatory focus wheel** from
`tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/`.
Its original assignment already calls for a polymer replacement with a D-shaft
socket, specified clearance, grip features and an explicit PETG slicing profile.
Use a new FreeCAD-bound revision; preserve the requirements and identify changed
tool bindings. Do not replace the part with a box or reuse the sheet-metal part.

The job is editable native solid CAD, independent dimensional/feature checks,
controlled mesh export, orientation/support assessment and actual slicing by an
existing external provider, followed by a reviewable digital build package.
Include a dimensioned inspection document and a physical fit/test plan. The
dataset's 0.20 mm clearance is a prototype choice, not proof of achieved fit.
PETG process anisotropy and the intended torque/temperature assumptions need
explicit treatment; a bulk-material FEA plot would not prove printed strength.

These examples use different mechanical manufacturing routes. Reuse the existing
heat-spreader analysis as a further shared-platform regression so the UI does
not grow a mandatory manufacturing layout. Keep its idealized numerical scope.

## Additional CAD recommendation

**First choice: FreeCAD through `neka-nat/freecad-mcp`.** FreeCAD's
[PartDesign documentation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Workbench.md)
describes editable feature-based solid mechanical modeling; its
[TechDraw documentation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_Workbench.md)
provides a drawing capability to qualify. The independent
[MCP documentation](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md)
lists modeling, inspection, screenshots, code execution and a CalculiX analysis
tool. Availability in documentation is not Wright qualification.

Wright already has [clean-container evidence](../../docs/mcp-catalog/evidence/curation-2026-09-09/freecad-linux.json)
for this provider: a 10 x 8 x 6 mm box, STL export, measured 480 mm3 volume,
direct protocol and both gateway paths. The recorded upstream commit is
`63acb305573194a011641ab13ccfb391fe95769f`. This is a useful starting point,
not evidence for the proposed focus wheel, STEP, drawing or Windows journey.
The [setup recipes](../../docs/mcp-catalog/mcp-server-setup-recipes.md) record a
required MCP SDK pin and addon prerequisites. Reconcile the catalog names
`freecad-core-nekanat` and `freecad-mcp-nekanat` by source and actual registration.

Do not confuse this provider with the repository's existing
`packages/freecad_mcp` submodule, which points at a different upstream. Other
providers have retained false-success/export or platform-path failures. Qualify
the chosen revision and host directly, then through Wright. The provider's
[configuration guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md)
documents addon startup; use isolated settings and preserve the user's CAD work.

No installation or fresh provider execution was performed for this review.

## Engineering checks and documents

Feature 082 already owns requirements, measurement methods, tolerances,
assessments, revision checks, review authority and traceability export. See its
[validation contract](../082-output-content-validation/contracts/validation-contract.md)
and [report consumer contract](../082-output-content-validation/contracts/report-consumer.md).
Use these records to produce readable engineering documents; do not add a second
approval or validation engine. Broad reporting UI belongs to another branch;
this work uses existing readers/exports and bounded shared presentation improvements.

For each selected job, prepare a concise design basis, requirements/verification
matrix, assumption log, design assessment, manufacturing assessment, drawing,
inspection plan and revision manifest. These can be sections of a compact package.
Each matrix row needs its requirement/source, exact subject, units/frame,
acceptance criterion, evidence method, observed result, uncertainty/limitations,
status and any required human decision. A missing mandatory observation cannot
turn into a passing check through a written AI verdict.

Reference applicable standards with editions and scope. Public descriptions
support selecting these references, not claiming clause-by-clause conformity:

- [ASME Y14.100](https://www.asme.org/codes-standards/find-codes-standards/y14-100-engineering-drawing-practices)
  concerns preparation and revision of engineering drawings and associated lists.
- [ASME Y14.5](https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing)
  concerns dimensioning and tolerancing of product definitions. Apply functional
  dimensions, datums and tolerances where justified; symbols alone do not verify a design.
- [ISO/ASTM 52910](https://www.iso.org/standard/67289.html)
  provides general additive-design guidance. Its public abstract expressly does
  not supply process-specific or material-specific data; use the actual selected
  process/material sources for those values.
- [ASME verification and validation resources](https://www.asme.org/codes-standards/vvuq-standards)
  identify V&V 10 for computational solid mechanics. When analysis is justified,
  separately assess numerical verification, physical validation and uncertainty.

These are proposed reference families, not new customer compliance requirements.
Use accessible authorized sources, cite supplier rules separately from standards
and fictional company policy, and disclose unavailable clauses. Never invent
clause numbers, tolerances, material properties or physical tests.

## Remaining work and completion scope

The prior instruction-portability tasks are recorded complete locally. Its old
intermediate ledger entries are not automatically new open bugs. Start the next
goal by reconciling them against final evidence and the served build.

Remaining work is product usability, engineering demonstration quality, fuller
CAD/provider qualification, evidence presentation and user acceptance. Specific
carry-forwards are the four slide-15 priorities; friendly result/field names;
questions near relevant evidence; readable forms; safe repeated CAD runs without
manual path surgery; missing native-property capability; and untrusted slicer
estimates. Keep the exact instruction, typed policy, invalidation and portability
protections already delivered.

The next goal should produce actual saved processes and engineering artifacts,
focused regression/live-browser evidence, a revised readable PPTX/PDF and a
short product-manager handoff. It should preserve the original review slide,
add a separate progress assessment of its four recommendations, and retain all
original evidence. Manufacturing release, physical verification and user
acceptance remain distinct from completion of the local software work.
