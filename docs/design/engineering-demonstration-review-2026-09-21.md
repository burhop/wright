# Review of the 30 Wright engineering examples

Review date: 21 September 2026. Status: recommendations for agreement, not implementation approval.

## Recommendation

Keep the existing collection and its evidence. Do not rewrite all 30 examples.
There are **ten shared process families, with three scenarios each**. Addressing
a family-level gap can therefore improve three examples without replacing their
engineering assignments.

| Recommended treatment | Examples | Meaning |
| --- | ---: | --- |
| Keep the process | 12 | A substantive connected-tool foundation already exists. Improve its explanation and resolve execution/correctness issues separately. |
| Targeted improvement | 12 | The engineering job is useful, but the implemented chain is limited or a promised downstream capability is missing. Propose one specific improvement before changing anything. |
| Retain as a narrower example/test | 6 | Useful analysis or verification, but not a strong demonstration of Wright's extended multi-tool purpose today. Preserve it; do not automatically replace it. |

These are product-suitability judgments, **not acceptance of engineering results**.
“Keep” does not mean ready to demonstrate live. “Narrower” does not mean useless
to an engineer. None of these recommendations changes the campaign's 30 cases,
counters, requirements, historical results, or approval state.

The best starting sequence is a printed replacement part for a visible
design-to-production-preparation story, a bracket for a mechanical CAD-to-FEA
story, and then an enclosure for a richer CAD-to-thermal-analysis story.
Do not continue using Robot as the principal proof of Wright's product value.

## What was reviewed

This review applies the agreed
[engineering demonstration principles](engineering-demonstration-principles.md).
It examines the purpose, tools, meaningful handoffs, engineering outcome, and
smallest justified change for each case.

Evidence inspected: all 30 scenario manifests, prompts and context documents;
the ten reusable workflow templates; selected bindings and relevant campaign
preparation/engineering-operation code; retained run manifests for all 30 cases;
and selected native execution records and artifacts. This is a source-based
suitability review with retained-evidence spot checks, not a fresh execution,
an exhaustive artifact validation, or a UI acceptance test. Scenario links below
open the context; the prompt and manifest are in the same directory.

The report distinguishes the checked-in implementation from older template
aspirations and historical attempts. Current bindings can differ from the code
used to create retained artifacts. Proposed additional applications have **not**
been selected, tested, or shown to be available through an installed MCP server.

## Findings that matter across the collection

1. **Count engineering contributions, not servers or blocks.** The PCB chain
   actually connects KiCad and FreeRouting through one MCP server. Conversely,
   Robot uses multiple servers but concentrates on one motion-analysis activity.
2. **Substitutions sometimes remove the original demonstration's breadth.** The
   drill-jig implementation uses AgentCAD and a geometry-derived DXF writer, not
   an independently demonstrated AutoCAD drafting stage. The harness uses
   WireViz plus custom verification, rather than the originally contemplated
   harness application. Those substitutions must be visible in our description.
3. **Real engineering choices need room to happen.** Some bracket runs stop
   because every detail of the proposed lightweight geometry was not already
   specified. A design workflow should distinguish fixed customer requirements
   from choices the AI/tools may propose for engineering review. Otherwise the
   engineer must solve much of the design before using Wright. Changing those
   permission boundaries needs explicit agreement; it is not permission to
   override today's approved basis or invent tolerances silently.
4. **Preparation, prediction, and physical completion are different outcomes.**
   A sliced part has not been printed. Simulated supplier receipts are not a
   quote or supplier acceptance. CFD results are not a physical thermal test.
5. **Three variations are useful coverage, but are not three different tool
   chains.** Present ten recognizable process families with three use cases
   each, while preserving all 30 campaign cases.

## Assessment of all 30 scenarios

The chain codes refer to the evidence and implementation notes immediately below
the table. “Targeted” proposals are options for approval, not new requirements.

| Scenario and recognizable engineering job | Chain | Treatment | Main gap / smallest recommended adjustment |
| --- | --- | --- | --- |
| [printed-replacement-part-01: replace a broken telescope focus wheel](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/context.md) | P | Keep | Explain how the reference and shaft dimensions become the scalloped model and actual printer toolpaths. Show the socket fit dimensions; call the outcome print preparation, not a proven replacement. |
| [printed-replacement-part-02: replace a drawer handle with gloved-hand clearance](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md) | P | Keep | Make the mounting centres, finger clearance and requested orientation comparison visible beside the sliced geometry. Preserve the existing part and printing requirements. |
| [printed-replacement-part-03: recreate a removable synthesizer tilt foot](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/printed-replacement-part/03-synthesizer-tilt-foot/context.md) | P | Keep | Connect the sloped support, screw/pad interfaces and cable clearance to the model and slice. Explain handedness; do not silently mirror the part. |
| [lightweight-equipment-bracket-01: reduce camera-mount mass without excessive deflection](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/lightweight-equipment-bracket/01-conveyor-vision-mount/context.md) | B | Keep | CAD-to-FEA is the right foundation. Resolve the permitted pocket/blend design choices, then show the baseline/revision mass, deflection and stress trade-off. Do not add a drawing merely to increase the stage count. |
| [lightweight-equipment-bracket-02: lighten an instrument outrigger under an angled load](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/lightweight-equipment-bracket/02-pump-instrument-outrigger/context.md) | B | Keep | Clarify which rib/pocket geometry Wright may propose while preserving mounts, cable corridor and manufacturing limits. Compare both actual designs under the same load. |
| [lightweight-equipment-bracket-03: lighten a dock-sensor yoke under a cable-snag load case](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/lightweight-equipment-bracket/03-dock-sensor-yoke/context.md) | B | Keep | Preserve pivot and service clearances; show the mass-versus-stiffness assessment. Repair the recorded solver availability problem separately. Do not claim dynamic impact or fatigue qualification from a static calculation. |
| [raspberry-pi-enclosure-01: choose vents for a quiet desktop computer case](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure/01-riverstone-desktop-computer/context.md) | E | Keep | Show sourced board dimensions, two actual enclosure designs, matching thermal models and the choice between them. Explain what temperature is being compared and the analysis limitations. |
| [raspberry-pi-enclosure-02: cool a serviceable greenhouse gateway](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure/02-greenhouse-sensor-gateway/context.md) | E | Keep | Connect louvres/chimney alternatives to temperature and service access. Preserve the two heat sources and warmer environment. Do not suggest a weatherproof/IP qualification. |
| [raspberry-pi-enclosure-03: cool an edge-vision computer with a restricted fan path](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure/03-edge-vision-instrument/context.md) | E | Keep | Explain how the guide changes flow resistance and cooling while preserving rear access. Show the supplied fan-curve assumption and corresponding fields, not only a coloured image. |
| [sensor-interface-pcb-01: make a thermistor-interface board for a coffee roaster](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb/01-thermistor-interface/context.md) | C | Keep | Expose the real schematic → placement → routing → fabrication chain. Present outstanding rule-check warnings and native files alongside the fabrication package. |
| [sensor-interface-pcb-02: make a two-channel pressure-sensor filter board](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb/02-dual-pressure-filter/context.md) | C | Keep | Show that channel connectivity, fixed placement and test points survive routing and export. Keep the approved placement corrections rather than resetting the design. |
| [sensor-interface-pcb-03: make a fan-power/tachometer service board](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb/03-fan-tach-service-board/context.md) | C | Keep | Explain the distinction between fan-power paths and tachometer filtering; relate copper constraints and connector locations to the routed board. Do not describe it as a fan controller. |
| [heat-spreader-sizing-01: select a conduction strap for a silent sign controller](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/01-eink-sign-controller-strap/context.md) | H | Targeted | Genuine CAD/FE work, but CAD contributes only rectangular dimensions. Consider carrying the selected existing plate into a usable cutting/detail drawing through a real downstream tool. Keep the simple thermal assumptions explicit. |
| [heat-spreader-sizing-02: fit a camera-to-frame thermal link within a width limit](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/02-camera-cold-wall-link/context.md) | H | Targeted | Connect the temperature-versus-width decision to the selected part's manufacturing detail. Do not add holes, joints or arbitrary 3D physics to make the test look richer. |
| [heat-spreader-sizing-03: minimise a copper link while allowing for contact resistance](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/03-calibration-lamp-copper-link/context.md) | H | Targeted | Keep the real contact-resistance trade-off and carry the selected geometry into the same focused downstream handoff. Distinguish supplied interface resistance from a measured joint. |
| [parametric-drill-jig-01: locate repeatable insert holes in furniture rails](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/context.md) | J | Targeted | Strong job; current CAD plus generated hole-layout DXF lacks the advertised separate drafting capability. Feed the actual jig into a qualified drawing/production-preparation tool for a usable bushing and datum detail. |
| [parametric-drill-jig-02: drill a rectangular tube using a clamped saddle jig](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/02-extrusion-panel-mount-jig/context.md) | J | Targeted | Reuse the CAD and approved amendments. The downstream detail should explain seating, bushings, chuck/clamp access and the index tongue; it must not silently alter the workpiece or hole locations. |
| [parametric-drill-jig-03: drill a keyed six-hole pattern in a circular plate](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/03-indexable-circular-fixture-jig/context.md) | J | Targeted | Reuse the model and governed hole coordinates. Make key orientation, clamps and bushing installation usable in the downstream manufacturing/assembly detail. |
| [sensor-fan-harness-01: prepare wiring for an incubator fan and sensor](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-fan-harness/01-desktop-incubator/context.md) | W | Targeted | Preserve WireViz and the build package. Consider replacing the custom electrical-analysis stage with an existing electrical-network tool consuming the actual emitted wiring data. No new voltage or load requirements are needed. |
| [sensor-fan-harness-02: size long ventilation branches with simultaneous fan startup](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-fan-harness/02-growth-rack-long-run/context.md) | W | Targeted | Best harness candidate for a meaningful analysis handoff: shared trunk/startup loading should drive wire/connector decisions, then the build documents. Preserve the separate sensor return and physical branch-control constraints. |
| [sensor-fan-harness-03: document a serviceable two-zone sampler harness](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sensor-fan-harness/03-dual-zone-air-sampler/context.md) | W | Targeted | Carry the real netlist into the same proposed analysis stage and retain shielding, reserved pins and zone identity in the resulting package. Circuit analysis cannot prove physical mis-mating prevention. |
| [sheet-metal-supplier-handoff-01: prepare a bent wall dock for a barcode reader](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/context.md) | S | Targeted | Keep the useful sheet-metal job, but simulated supplier gates are not a second engineering application. Propose a genuine flat-pattern manufacturing/DFM consumer; resolve material and bend-access questions without calling a HOLD an approval. |
| [sheet-metal-supplier-handoff-02: prepare a four-bend cable trough](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/02-industrial-cable-trough/context.md) | S | Targeted | Repair native CAD execution separately. Carry the developed pattern and quantity into a real cutting/nesting or manufacturing-check stage, preserving interior service clearance and bend requirements. |
| [sheet-metal-supplier-handoff-03: prepare a fitted two-piece instrument chassis](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/03-precision-instrument-chassis/context.md) | S | Targeted | Preserve the approved tray/lid relationship and keepout clarification. Resolve forming/feature constraints, then demonstrate a real downstream consumer of both developed parts. A visual export is not a dimensioned manufacturing drawing. |
| [water-heater-sizing-01: select heater power for a single-cup brewer](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/water-heater-sizing/01-single-cup-countertop/context.md) | M | Narrower | Useful bounded Modelica sizing study, not yet an extended application chain. Retain it as a simulation example. Component selection or packaging would expand the assignment and needs a separate proposal. |
| [water-heater-sizing-02: budget heat-up power and energy for a mobile brewer](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/water-heater-sizing/02-mobile-field-brewer/context.md) | M | Narrower | Keep the inverter and energy constraints; make clear the battery estimate is accounting, not a separate battery simulation. Do not add a token second tool to relabel the same calculation. |
| [water-heater-sizing-03: choose batch-heater power robust to heat-loss uncertainty](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/water-heater-sizing/03-pilot-batch-dispensing/context.md) | M | Narrower | Preserve the candidate-power/loss matrix and worst-case choice as useful analysis coverage. A later component/thermal-packaging chain requires new agreed scope. |
| [robot-tracking-diagnosis-01: investigate tracking near a floor seam](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/context.md) | R | Narrower | Preserve the motion-analysis and review tests, including improved plots. Do not call it a complete corrective-design process or infer a proven mechanical cause. A richer robot job requires a separately agreed engineering question and tools. |
| [robot-tracking-diagnosis-02: compare tracking despite a separate camera clock](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/02-corner-time-alignment/context.md) | R | Narrower | Valuable clock/frame-alignment test. Preserve the specified transformation and timing correction; neither more reporting nor a new title creates a broader tool chain. |
| [robot-tracking-diagnosis-03: assess tracking with an external-pose dropout](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/03-figure-eight-occlusion/context.md) | R | Narrower | Valuable missing-data and evidence-limitation test. Retain the gap-handling rules and explicitly unobserved interval rather than manufacturing a diagnosis or synthetic proof of a fix. |

## Tool chains and supporting evidence

These sections name the implemented capabilities, including custom glue. They
describe configured paths, not a claim that every scenario has completed them.

### P — Printed replacement parts

Reference image and governed dimensions → Blender modelling → mesh repair and
orientation → Bambu Studio slicing → inspectable printer package → separately
authorised, simulated transfer. The repaired STL is the slicer's actual input.
The native modeller and slicer make distinct contributions toward producing a
replacement part; the custom repair wrapper does not need to count as another
engineering application.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/printed-replacement-part.json),
[preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-printed-dataset-campaign.py),
and retained native slice receipt (local retained evidence: `artifacts/engineering-workflow-datasets/output/printed-replacement-part-01/attempt-003/artifacts/slice-evidence.json`).
The receipt records Bambu Studio consuming the repaired mesh and producing a
nonempty package; it explicitly records no printer connection. Existing native
execution does not prove dimensional fit or print quality.

### B — Lightweight brackets

Mechanical basis → AgentCAD/build123d baseline and proposed revision → actual
STEP geometry and load/fixture definitions → CalculiX coarse/fine analyses →
measured mass, displacement, stress and reaction comparison. AgentCAD substitutes
for the originally named BREP provider. The field-export helper supplements the
native analysis evidence; it is not another independent design application.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/lightweight-equipment-bracket.json)
and [preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-bracket-dataset-campaign.py).
Both revisions are authored before comparison: do not advertise an autonomous
optimisation loop that has not been demonstrated. This is already a coherent
design-assessment chain; successful execution and engineering review remain
necessary. Proposed design latitude must be agreed before unblocking cases 01/02.

### E — Raspberry Pi enclosures

Manufacturer dimensions → AgentCAD/build123d enclosure alternatives and region
geometry → Gmsh mesh built from actual STEP regions → OpenFOAM thermal/flow
calculation → temperature/flow comparison supporting a vent or guide choice.
The fixed path exposes AgentCAD, reference-retrieval and CFD preparation tools,
and the foam-agent server. Do not describe this path using the older Blender
binding's story.

Evidence: [fixed binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/raspberry-pi-enclosure-fixed.json),
[visual preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-pi-visual-dataset-campaign.py),
[CAD-to-mesh operations](https://github.com/burhop/wright/blob/dev/scripts/pi_cfd_operations.py), and
retained preparation record (local retained evidence: `artifacts/engineering-workflow-datasets/output/raspberry-pi-enclosure-01/attempt-032/artifacts/cfd-preparation-a.json`).
This has a strong product-demonstration structure, but mesh/energy/convergence
and material assumptions still need their own current validation.

### C — Sensor-interface PCBs

Approved circuit → KiCad schematic/netlist and board placement → FreeRouting
copper routing → KiCad native checks → corresponding BOM, Gerber and drill
files. The blwfish KiCad MCP provider exposes the routing engine as well as
KiCad operations. Separate copying/evidence nodes preserve revisions but do not
add engineering capabilities.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/sensor-interface-pcb.json),
[preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-pcb-dataset-campaign.py),
retained routing summary (local retained evidence: `artifacts/engineering-workflow-datasets/output/sensor-interface-pcb-01/attempt-007/artifacts/routing-evidence.md`), and
[native run record](C:/Users/markb/wright-feature-081/engineering-workflow-demos/runs/campaign-sensor-interface-pcb-01-attempt-007/20260913T095221Z-7dc1de2083bb.json).
The recorded autoroute call used FreeRouting 2.2.4 and returned 27 tracks with
zero unconnected items. Its summary retained three DRC warnings. This is evidence
of a real routing handoff, not a claim of electrically validated hardware or
current-revision acceptance.

### H — Heat-spreader sizing

AgentCAD rectangular candidate plates → measured dimensions tied to actual STEP
files → OASiS exposing scikit-fem → coarse/fine temperature fields, heat balance
and minimum-size decision. This is a real finite-element calculation, not a
closed-form answer disguised as solver output. However, the FE mesh is built
from measured rectangular extents, not imported CAD surfaces; the permitted
physics is intentionally close to a simple conduction-bar model.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/heat-spreader-sizing.json),
[preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-heat-dataset-campaign.py), and
[solver operation](https://github.com/burhop/wright/blob/dev/scripts/engineering/heat_conduction_skfem.py).
The handoff exists, but its engineering breadth is modest. A selected-part
manufacturing detail is a possible focused extension, only if an actual
downstream application uses the selected geometry. Without that extension,
describe these honestly as introductory sizing examples rather than flagship
extended workflows. Do not add needless physics complexity.

### J — Drill jigs

Workpiece, hole table, bushings and keepouts → AgentCAD/build123d jig geometry →
STEP/STL and geometry-derived hole-layout DXF → independently executed geometric
checks. The actual binding explicitly substitutes AgentCAD and CAD-derived DXF
for the original BREP/AutoCAD combination. Extracting drawing geometry is useful,
but it does not demonstrate a separate established drafting application.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/parametric-drill-jig.json)
and [preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-drill-jig-dataset-campaign.py).
Smallest substantive proposal: preserve the designed jig and checks, then feed
the actual geometry to a qualified tool producing the manufacturing/assembly
detail an engineer needs. Do not represent the current hole-layout DXF as a full
toleranced drawing. New tolerances require engineering agreement.

### W — Sensor/fan harnesses

Component records and wiring schedule → WireViz 0.4.1/Graphviz harness package →
custom verification of the emitted netlist, ratings and voltage drop → pin
schedule, wire cut list, BOM and assembly information. This is useful work.
However, Graphviz is the rendering dependency, and the custom electrical check
does not establish another existing engineering analysis application.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/sensor-fan-harness.json),
[preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-harness-dataset-campaign.py), and
[native generation/custom verification operations](https://github.com/burhop/wright/blob/dev/scripts/harness_engineering_operations.py).
The proposed improvement is a qualified electrical-network analysis capability
consuming the actual generated connections, wire resistances and approved loads;
its result must affect wire/connector selection and the resulting assembly
package. Preserve the independent checks. If no useful integration is available,
retain the current harness job as a narrower example rather than padding it.

### S — Sheet-metal supplier handoff

Supplier capability research → manufacturing intent → Solid Edge native
sheet-metal model → measured checks and developed flat DXF → simulated supplier
preview/cart approvals and package handoff. Native folded-to-flat geometry is a
valuable engineering transformation, but the selected supplier leg is explicitly
simulated; file access and web retrieval do not substitute for a substantive
second engineering application.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/sheet-metal-supplier-handoff.json)
and [preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-sheet-metal-dataset-campaign.py).
A qualified cutting/nesting or manufacturing-check application consuming the
actual developed DXF would strengthen the existing job without ordering parts.
Choose the capability because it resolves the manufacturing need, not because
we need another logo. Do not promise supplier acceptance, a live quote, or a
native drafting capability that this binding does not expose.

### M — Water-heater sizing

Approved physical parameters → native Modelica candidate simulations and refined
selected simulations → CSV-based heat-up, energy and stability comparison →
heater-power recommendation. The selected tools expose the same bounded model
and its results. Export, numerical checks and report generation are important
supporting steps, but not an extended multi-application design process.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/water-heater-sizing.json)
and [native Modelica preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-modelica-dataset-campaign.py).
Retain all three as genuine engineering-analysis examples and solver tests.
Do not replace the native model with a custom calculation. A later component
selection/packaging process could reuse the study, but would change the current
assignment and needs its own approved brief.

### R — Robot tracking diagnosis

Supplied motion data → ROS 2 normalisation/bag inspection → supplied/custom
tracking analysis → plots and evidence-linked diagnosis. The bag server and
operation server provide real work, but largely within one analysis activity.
The three cases add seam-event, clock/frame and missing-data coverage, not three
extended corrective-design processes.

Evidence: [binding](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json)
and [preparer](https://github.com/burhop/wright/blob/dev/scripts/prepare-robot-dataset-campaign.py).
Preserve these tests and their improved review experience. Do not bolt CAD/FEA
onto the log analysis without a justified engineering question, necessary data
and a meaningful downstream decision.

## Execution evidence is a different assessment

The latest numbered retained run manifests, read for this review, report:

| Family | Latest local attempts, cases 01 / 02 / 03 | Recorded outcome |
| --- | --- | --- |
| Printed parts | 003 / 002 / 016 | Completed / completed / completed |
| Brackets | 006 / 005 / 012 | Failed / failed / failed |
| Enclosures | 032 / 031 / 046 | Completed / completed / completed |
| PCBs | 007 / 021 / 015 | Completed / completed / completed |
| Heat spreaders | 008 / 010 / 008 | Completed / completed / completed |
| Drill jigs | 012 / 012 / 011 | Completed / completed / completed |
| Harnesses | 003 / 003 / 003 | Completed / completed / completed |
| Sheet metal | 006 / 006 / 005 | Failed / failed / failed |
| Water heaters | 005 / 003 / 003 | Completed / completed / completed |
| Robot | 010 / 004 / 005 | Awaiting approval / completed / completed |

These are retained execution records, not present-day validation credit. Robot
01 also has an earlier completed attempt. No successful terminal record was found
for the bracket or sheet-metal families in the inspected local attempt folders.
The local status snapshot (local retained evidence: `artifacts/engineering-workflow-datasets/status.json`)
separately reports historical counters of 30 datasets, 30 run combinations,
24 with outputs and 0 valid-data credit; current-revision counters are 1 run,
0 with outputs and 0 valid-data credit. It would be wrong to turn the suitability
table into new campaign credit or to interpret a historical completed record as
current engineering acceptance.

Important recorded blockers:

- Bracket 01 (local retained evidence: `artifacts/engineering-workflow-datasets/output/lightweight-equipment-bracket-01/attempt-006/run.json`)
  and Bracket 02 (local retained evidence: `artifacts/engineering-workflow-datasets/output/lightweight-equipment-bracket-02/attempt-005/run.json`)
  stopped over unresolved revised-geometry definitions. This calls for a decision
  about permitted design choices, not a blanket rewrite or fabricated geometry.
- Bracket 03 (local retained evidence: `artifacts/engineering-workflow-datasets/output/lightweight-equipment-bracket-03/attempt-012/run.json`)
  reached the solver stage but recorded an unavailable child service. That is an
  execution blocker, not evidence that the engineering purpose is unsuitable.
- Sheet-metal 01 (local retained evidence: `artifacts/engineering-workflow-datasets/output/sheet-metal-supplier-handoff-01/attempt-006/run.json`)
  and Sheet-metal 03 (local retained evidence: `artifacts/engineering-workflow-datasets/output/sheet-metal-supplier-handoff-03/attempt-005/run.json`)
  stopped on mandatory manufacturing/forming evidence under their approved
  policy. Whether exploratory CAD may precede release qualification is a policy
  question for agreement; this review does not waive the gates.
- Sheet-metal 02 (local retained evidence: `artifacts/engineering-workflow-datasets/output/sheet-metal-supplier-handoff-02/attempt-006/run.json`)
  recorded a native Solid Edge flange-creation failure. Resolve the integration
  problem independently from any product-demonstration extension.

## Bounded next steps for approval

1. **Agree the classification, not a new campaign definition.** Keep all cases
   and their evidence. Treat the six narrower examples honestly in product
   presentations; do not delete them or change the 30-case denominator.
2. **Use Printed 01 as the first visual pilot.** Show the original image and
   dimensions, Blender model, actual slicer result and inspectable package.
   Revalidate the applicable current requirements before calling it ready.
   Simulated transfer stays clearly labelled.
3. **Use Bracket 01 as the mechanical design pilot.** Agree which geometric
   choices Wright may propose within the fixed requirements, obtain review of
   those choices, and complete the actual CAD-to-FEA comparison. Keep this
   separate from the quick printed-part pilot so unresolved geometry does not
   block all demonstration progress.
4. **Propose one targeted extension at a time.** Start with the drill-jig
   CAD-to-drawing handoff because it restores a capability the original story
   implied. Before implementation, name the existing application/MCP, prove it
   accepts the actual upstream geometry, identify the useful deliverable, and
   obtain agreement on any new engineering requirements. Repeat this process
   for harness, heat and sheet-metal only where the benefit justifies it.
5. **Give each family a short engineering introduction.** State the situation,
   job, named tools, what passes between them, expected outcome, limitations and
   where to inspect results. Use the existing input/output blocks. Keep software
   diagnostics available on demand without hiding the engineering applications.
6. **Resume execution only under the agreed existing campaign authority.** This
   report does not restart a goal or runner, approve Robot 010, or authorise a
   physical action, purchase or supplier upload. Product suitability and
   technical completion remain separate tracks.

The immediate decision requested is agreement on the pilot sequence and which
single targeted improvement to specify first—not permission to redesign all 30.
