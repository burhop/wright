# Engineering jobs illustrated by the 30 examples

These are the existing thirty examples, described in terms of the work an
engineer wants to accomplish. The scenarios, input data, calculations, models,
and requested deliverables are retained. The purpose is to make their value
clear, not to turn each example into a new project.

All examples use fictional briefs and synthetic data. They support design
studies, prototype preparation, or diagnosis, not automatic product release.
The benefits below describe Wright's intended contribution, not measured time
savings or a claim that a particular run has succeeded.

## Find an engineering job

| Job | Three existing examples |
| --- | --- |
| [Investigate robot motion](#robot-motion) | Aisle wandering; apparent turn lag; tracking with missing measurements |
| [Choose heater power](#heater-power) | Desk brewer; portable brewer; batch dispenser |
| [Size a passive thermal link](#thermal-links) | Sign controller; inspection camera; calibration lamp |
| [Reduce bracket mass](#lighter-brackets) | Camera arm; instrument outrigger; sensor yoke |
| [Develop sheet-metal parts](#sheet-metal) | Reader dock; cable trough; instrument chassis |
| [Design an electronics enclosure](#enclosures) | Desktop computer; greenhouse gateway; inspection computer |
| [Prepare a replacement part](#replacement-parts) | Focus wheel; drawer handle; instrument foot |
| [Create a drill jig](#drill-jigs) | Furniture rail; rectangular tube; circular fixture plate |
| [Turn a circuit into a PCB](#circuit-boards) | Temperature sensor; pressure sensors; fan-speed service board |
| [Document a serviceable wiring harness](#wiring-harnesses) | Benchtop chamber; growth rack; two-zone sampler |

<a id="robot-motion"></a>

## Investigate robot motion

Wright's contribution: bring the route, motion measurements, and operator notes
onto a common time and coordinate basis, then keep each conclusion linked to the
plots and measurements behind it. This helps an engineer decide what to measure
next instead of interpreting disconnected traces or guessing at a cause.

Wheel odometry means motion estimated from wheel rotation. An external tracker
provides a separate position measurement. Neither is automatically ground truth.
These examples analyze recorded data; they do not operate or tune a robot.

<a id="robot-tracking-diagnosis-01"></a>

### Investigate why a mobile cart wanders off its intended path

- **Purpose:** A commissioning engineer has noticed an unloaded cart wobbling in
  an aisle and conflicting motion measurements. Determine what the evidence
  supports before choosing the next experiment. Crossing a taped floor seam is
  an event to investigate, not an assumed cause or the whole purpose of the job.
- **Work:** Compare the intended route, wheel-based motion estimate, and external
  tracking measurements. Quantify path error and speed disagreement, and examine
  their timing relative to the seam crossing.
- **Useful result:** An annotated path plot, aligned timeline, error measurements,
  and a diagnosis separating observations from possible causes, with one
  inexpensive follow-up experiment. The brief supplies no allowable tracking
  error, so the result cannot establish acceptable aisle performance or readiness
  for service. Different speed traces alone do not establish wheel slip.

[Original request](scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/prompt.txt)
· [Engineering basis](scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/context.md)

<a id="robot-tracking-diagnosis-02"></a>

### Determine whether apparent cornering lag survives measurement alignment

- **Purpose:** A delivery cart appears late entering a turn. Check whether the
  apparent behavior remains after correcting the camera's different clock and
  position origin, before recommending any tuning.
- **Work:** Apply the supplied coordinate translation and time relationship once,
  compare the unaligned and aligned interpretations, and correlate the corner
  entry with the operator's observation.
- **Useful result:** Before-and-after path plots, tracking measurements, and an
  evidence-linked diagnosis of the remaining discrepancy. Identify uncertainty
  rather than equating a camera time offset with a controller fault.

[Original request](scenarios/robot-tracking-diagnosis/02-corner-time-alignment/prompt.txt)
· [Engineering basis](scenarios/robot-tracking-diagnosis/02-corner-time-alignment/context.md)

<a id="robot-tracking-diagnosis-03"></a>

### Assess path drift when the external tracker temporarily loses sight

- **Purpose:** An inventory cart's wheel-based path appears to diverge on a curved
  route, but a tote also blocks the external tracker. Determine which parts of
  the run support a diagnosis and which need another observation.
- **Work:** Compare the planned and measured paths over valid intervals, leave the
  occlusion visibly missing, and distinguish observed drift from missing evidence.
- **Useful result:** A path overlay, aligned data and tracking metrics that state
  which samples were used, plus a report identifying uncertainties and a useful
  additional observation. Filling the gap must not create fictitious measurements.

[Original request](scenarios/robot-tracking-diagnosis/03-figure-eight-occlusion/prompt.txt)
· [Engineering basis](scenarios/robot-tracking-diagnosis/03-figure-eight-occlusion/context.md)

<a id="heater-power"></a>

## Choose heater power

Wright's contribution: run comparable heating cases, retain the model settings,
and assemble the temperature, time, and energy evidence for a power-selection
decision. A model that cannot represent the supplied conditions must report that
limitation; substituting another calculation does not complete the requested study.

<a id="water-heater-sizing-01"></a>

### Choose heater power for a single-cup brewer

- **Purpose:** Choose the lowest offered power that heats the specified water
  fill to the target temperature within the customer's three-minute wait.
- **Work:** Compare the supplied power options in the approved heating model with
  the same water mass, vessel heat capacity, and heat-loss assumptions.
- **Useful result:** Temperature curves, heat-up times, energy comparisons, and a
  supported heater recommendation for the hardware team's next prototype. If no
  option meets the target, show that rather than changing the fill or power menu.

[Original request](scenarios/water-heater-sizing/01-single-cup-countertop/prompt.txt)
· [Engineering basis](scenarios/water-heater-sizing/01-single-cup-countertop/context.md)

<a id="water-heater-sizing-02"></a>

### Balance portable-brewer warm-up time against available power and energy

- **Purpose:** Find a heating option that serves a field crew within the specified
  wait while respecting the inverter limit and battery-energy planning budget.
- **Work:** Compare the three allowed heater powers, then account separately for
  the declared inverter losses when estimating battery-side energy per batch.
- **Useful result:** A power comparison showing both heat-up time and energy
  against their targets, with a recommendation or an explicit unmet requirement.
  Estimated battery consumption is not a measured runtime or battery qualification.

[Original request](scenarios/water-heater-sizing/02-mobile-field-brewer/prompt.txt)
· [Engineering basis](scenarios/water-heater-sizing/02-mobile-field-brewer/context.md)

<a id="water-heater-sizing-03"></a>

### Choose batch-dispenser power despite uncertain heat loss

- **Purpose:** Select a power level for the next bench prototype that meets the
  heat-up target throughout the customer's declared range of heat loss.
- **Work:** Compare the allowed powers at low, nominal, and high loss, where the
  approved model supports them, and check numerical sensitivity for the decision.
- **Useful result:** Temperature, time, and energy comparisons identifying the
  lowest candidate that meets every declared case, or explaining why none does.
  The loss range is a design assumption, not measured product behavior.

[Original request](scenarios/water-heater-sizing/03-pilot-batch-dispensing/prompt.txt)
· [Engineering basis](scenarios/water-heater-sizing/03-pilot-batch-dispensing/context.md)

<a id="thermal-links"></a>

## Size a passive thermal link

Wright's contribution: keep each candidate geometry connected to its numerical
temperature results, heat-balance checks, and sizing decision. These are early,
deliberately simplified link-sizing studies. They do not predict an entire
product's temperature or demonstrate hardware performance.

<a id="heat-spreader-sizing-01"></a>

### Choose a conduction-strap width for a silent sign controller

- **Purpose:** Explore a fan-free heat path to a cooled backing rail and choose
  the narrower offered strap that satisfies the specified hot-end temperature.
- **Work:** Compare the two aluminum-like plate widths under the same supplied
  heat load and cold-end temperature; check solved fields against the simple
  one-dimensional calculation and retain the heat balance.
- **Useful result:** Candidate models, temperature fields, and a justified width
  selection. Interfaces and mounting details remain outside this first study;
  the hot-end result must not be called the controller's actual temperature.

[Original request](scenarios/heat-spreader-sizing/01-eink-sign-controller-strap/prompt.txt)
· [Engineering basis](scenarios/heat-spreader-sizing/01-eink-sign-controller-strap/context.md)

<a id="heat-spreader-sizing-02"></a>

### Fit a camera thermal link into the available channel

- **Purpose:** Choose a compact heat-conduction link between an inspection camera
  mounting block and a cooled frame without exceeding the packaging envelope or
  the link's stated hot-end limit.
- **Work:** Compare the three widths with consistent material and boundary
  assumptions, numerical fields, heat balance, and mesh refinement.
- **Useful result:** A comparison identifying the narrowest passing candidate,
  with CAD and calculation evidence. Camera sensor temperature, contact losses,
  and frame-cooling performance are not established by this link-only model.

[Original request](scenarios/heat-spreader-sizing/02-camera-cold-wall-link/prompt.txt)
· [Engineering basis](scenarios/heat-spreader-sizing/02-camera-cold-wall-link/context.md)

<a id="heat-spreader-sizing-03"></a>

### Size a lamp heat link without overlooking its contact resistance

- **Purpose:** Choose the lowest-mass offered copper-like link that meets the
  fixture's hot-end temperature target, including the specified loss at its
  connection to the cooled rail.
- **Work:** Model each width and the declared total interface resistance, then
  compare numerical temperatures with the corresponding resistance calculation.
- **Useful result:** A mass-and-temperature decision supported by actual fields
  and heat balance. If the numerical tool cannot model the interface, state that
  limitation; an ideal-contact comparison is not the requested design result.

[Original request](scenarios/heat-spreader-sizing/03-calibration-lamp-copper-link/prompt.txt)
· [Engineering basis](scenarios/heat-spreader-sizing/03-calibration-lamp-copper-link/context.md)

<a id="lighter-brackets"></a>

## Reduce bracket mass without losing function

Wright's contribution: preserve mounting interfaces and manufacturing constraints
while comparing original and revised CAD, mass, stress, and displacement under
the same stated loading. The result supports a prototype design choice, not
fatigue qualification or production release.

<a id="lightweight-equipment-bracket-01"></a>

### Lighten a conveyor camera arm while preserving camera position

- **Purpose:** Remove unnecessary bracket mass while keeping camera movement
  within the optical team's displacement budget.
- **Work:** Model the original arm and a machinable lighter version, retain the
  mounting patterns, and compare their responses to the specified service load.
- **Useful result:** Original and revised models, mass comparison, stress and
  displacement results, and mesh checks showing whether the reduction target
  and stated response limits can be met together. Keep joint-model assumptions visible.

[Original request](scenarios/lightweight-equipment-bracket/01-conveyor-vision-mount/prompt.txt)
· [Engineering basis](scenarios/lightweight-equipment-bracket/01-conveyor-vision-mount/context.md)

<a id="lightweight-equipment-bracket-02"></a>

### Lighten an instrument outrigger without obstructing service access

- **Purpose:** Reduce a bulky pressure-instrument support while retaining its
  attachment points, access opening, and cable route beside a pump test station.
- **Work:** Compare the solid-rib original with a machinable revision under the
  supplied diagonal load, including the effect of its offset from the mounting.
- **Useful result:** A mass, stress, and displacement comparison with both CAD
  revisions and solver evidence, showing whether the requested reduction is
  worthwhile and feasible without sacrificing the stated clearances or limits.

[Original request](scenarios/lightweight-equipment-bracket/02-pump-instrument-outrigger/prompt.txt)
· [Engineering basis](scenarios/lightweight-equipment-bracket/02-pump-instrument-outrigger/context.md)

<a id="lightweight-equipment-bracket-03"></a>

### Reduce sensor-yoke mass while checking sideways bending and twist

- **Purpose:** Lighten a dock-position sensor support without losing its fixed
  mounting and pivot geometry or maintenance access.
- **Work:** Compare the solid and pocketed yokes under the declared sideways
  cable-snag load, including twist and the available machining access.
- **Useful result:** A traceable comparison of mass and structural response that
  supports a prototype choice or explains an unmet target. The static load study
  does not establish behavior during an actual impact or repeated snagging.

[Original request](scenarios/lightweight-equipment-bracket/03-dock-sensor-yoke/prompt.txt)
· [Engineering basis](scenarios/lightweight-equipment-bracket/03-dock-sensor-yoke/context.md)

<a id="sheet-metal"></a>

## Develop sheet-metal parts for a reviewed manufacturing handoff

Wright's contribution: connect design intent and sourced manufacturing
capabilities to the folded part, developed flat pattern, and review package.
The examples stop at a local, clearly simulated supplier preview; they do not
place orders or establish supplier acceptance.

<a id="sheet-metal-supplier-handoff-01"></a>

### Make a barcode-reader dock that keeps the packing bench clear

- **Purpose:** Give a handheld reader a convenient storage location without
  trapping its cable or occupying the labeling area.
- **Work:** Resolve the shelf, retaining lip, cable notch, and wall slots against
  the brief and researched sheet-stock and bending capabilities.
- **Useful result:** A reviewable design basis, editable sheet-metal part, folded
  model, true flat pattern, and four-part handoff preview. Wall anchors and load
  verification remain separate decisions, not assumptions hidden in the model.

[Original request](scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/prompt.txt)
· [Engineering basis](scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/context.md)

<a id="sheet-metal-supplier-handoff-02"></a>

### Route test-stand cables in a serviceable folded trough

- **Purpose:** Organize sensor and fan cables while preserving cable-loop space
  and maintenance access beneath the work surface.
- **Work:** Develop the four-bend open trough, check interior clearances and
  mounting slots, and compare the proposed stock, finish, and bend sequence with
  sourced manufacturing capability.
- **Useful result:** Native and exchange models, a developed flat pattern, and a
  six-part handoff preview showing resolved and unresolved choices. A drawn
  trough is not a verified machine guard or electrical enclosure.

[Original request](scenarios/sheet-metal-supplier-handoff/02-industrial-cable-trough/prompt.txt)
· [Engineering basis](scenarios/sheet-metal-supplier-handoff/02-industrial-cable-trough/context.md)

<a id="sheet-metal-supplier-handoff-03"></a>

### Develop a serviceable two-piece instrument chassis

- **Purpose:** Package a tabletop data-acquisition instrument with a removable
  lid, organized panel openings, and a consistent industrial appearance.
- **Work:** Resolve the supplied packaging conflict using the already authorized
  keepout decision, then develop the tray, lid, reliefs, interfaces, and bend
  sequence against sourced manufacturing capabilities.
- **Useful result:** A documented assembly design with native parts, folded models,
  and flat patterns for both components, plus an itemized two-chassis preview.
  Cooling, electronics, electromagnetic compatibility, and safety remain unqualified.

[Original request](scenarios/sheet-metal-supplier-handoff/03-precision-instrument-chassis/prompt.txt)
· [Engineering basis](scenarios/sheet-metal-supplier-handoff/03-precision-instrument-chassis/context.md)

<a id="enclosures"></a>

## Design electronics packaging and compare cooling alternatives

Wright's contribution: carry researched board dimensions and the design brief
through alternative enclosure models and comparable airflow/temperature studies.
The engineer can review appearance, access, and cooling together. Computed
temperatures apply to the declared simplified models, not qualified products.

<a id="raspberry-pi-enclosure-01"></a>

### Balance a quiet desktop-computer appearance with passive cooling

- **Purpose:** Develop a rounded, serviceable Raspberry Pi case for a creative
  studio and determine the cooling tradeoff of discreet versus visible vents.
- **Work:** Research the actual board and connectors, document the design basis,
  and model both vent alternatives with matching airflow domains and heat loads.
- **Useful result:** Enclosure models and computed temperature/airflow comparisons
  that support a vent choice within the styling and packaging brief. The input
  sketch is not a board drawing, and the simulated heat source is not a verified processor model.

[Original request](scenarios/raspberry-pi-enclosure/01-riverstone-desktop-computer/prompt.txt)
· [Engineering basis](scenarios/raspberry-pi-enclosure/01-riverstone-desktop-computer/context.md)

<a id="raspberry-pi-enclosure-02"></a>

### Compare serviceable cooling layouts for a sheltered greenhouse logger

- **Purpose:** House a data gateway where it can be serviced and cabled under a
  dry canopy, while addressing the declared heat load and installation envelope.
- **Work:** Verify board interfaces and compare downward-facing louvers with a
  raised chimney, preserving lid access, mounting clearance, and drip-loop space.
- **Useful result:** A sourced design basis, both case models, and a cooling
  comparison showing tradeoffs or unmet targets. Debris and screen-loss questions
  stay explicit; neither ventilated concept is presented as waterproof or IP rated.

[Original request](scenarios/raspberry-pi-enclosure/02-greenhouse-sensor-gateway/prompt.txt)
· [Engineering basis](scenarios/raspberry-pi-enclosure/02-greenhouse-sensor-gateway/context.md)

<a id="raspberry-pi-enclosure-03"></a>

### Decide whether an airflow guide improves a compact inspection computer

- **Purpose:** Cool an inspection-station computer inside a low-profile enclosure
  while retaining the rear cable-service space and intended instrument appearance.
- **Work:** Compare straight-through flow with a curved guide using the same
  supplied fan assumption, vent area, heat loads, and comparable numerical setup.
- **Useful result:** Both enclosure designs, matching airflow models, and computed
  temperatures and pressure losses to support a layout choice. The synthetic fan
  curve and unverified fits remain assumptions, not supplier or hardware evidence.

[Original request](scenarios/raspberry-pi-enclosure/03-edge-vision-instrument/prompt.txt)
· [Engineering basis](scenarios/raspberry-pi-enclosure/03-edge-vision-instrument/context.md)

<a id="replacement-parts"></a>

## Prepare replacement parts for a physical prototype

Wright's contribution: carry a dimensioned repair brief through geometry, mesh
repair, orientation/support review, and slicing, keeping fit-critical features
and material choices visible. These examples prepare local files and a simulated
transfer receipt; no physical printer is operated.

<a id="printed-replacement-part-01"></a>

### Replace a cracked telescope focus wheel with a glove-friendly grip

- **Purpose:** Restore a manually operated focus grip while improving its handling
  for the observatory's intended use.
- **Work:** Build the supplied scalloped shape around the specified D-shaped shaft
  socket, preserve the prototype clearances, and prepare the declared print setup.
- **Useful result:** Inspectable source and printable meshes, support/slicing
  preview, and a material-identified print package for fit review. Socket fit,
  torque capacity, and handling remain questions for a later physical prototype.

[Original request](scenarios/printed-replacement-part/01-observatory-focus-wheel/prompt.txt)
· [Engineering basis](scenarios/printed-replacement-part/01-observatory-focus-wheel/context.md)

<a id="printed-replacement-part-02"></a>

### Replace a drawer handle while preserving mounting and glove clearance

- **Purpose:** Restore a convenient drawer pull that fits the existing bolt
  spacing and provides room for a gloved hand.
- **Work:** Model the bowed grip, flat mounting pads, through-holes, and thumb
  recess; compare the requested printing orientations and support contact.
- **Useful result:** Reviewable geometry and a supported print package showing
  the intended mounting and finger clearances. The part is a drawer-opening
  prototype, not a tested lifting handle or a validated strength result.

[Original request](scenarios/printed-replacement-part/02-repair-cart-bow-handle/prompt.txt)
· [Engineering basis](scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md)

<a id="printed-replacement-part-03"></a>

### Recreate a missing synthesizer foot without obstructing its cable

- **Purpose:** Restore the intended desktop support geometry with a replacement
  rear-left foot that respects the supplied screw pattern and cable clearance.
- **Work:** Model the wedge, counterbores, pad recess, and cable notch from the
  prototype specification, then prepare a support-aware print package.
- **Useful result:** Inspectable and printable geometry with the declared material
  and orientation. Screw fit, stability, and creep require physical review; a
  replacement for the other side is not silently inferred or generated.

[Original request](scenarios/printed-replacement-part/03-synthesizer-tilt-foot/prompt.txt)
· [Engineering basis](scenarios/printed-replacement-part/03-synthesizer-tilt-foot/context.md)

<a id="drill-jigs"></a>

## Create repeatable drilling aids from workpiece datums

Wright's contribution: translate hole tables, locating surfaces, bushing sizes,
and clamp clearances into reviewable jig geometry and a dimension report. This
helps avoid repeated manual layout while making the intended location method
explicit. Digital geometry alone does not prove drilling accuracy or safe setup.

<a id="parametric-drill-jig-01"></a>

### Locate two pilot holes consistently across a batch of furniture rails

- **Purpose:** Prepare a reusable jig so the same hole pattern can be located
  from the rail's end and edge rather than marked out separately on every part.
- **Work:** Build the datum fences, guide-bushing seats, and orientation mark while
  retaining the supplied hole coordinates and clamp clearances.
- **Useful result:** A jig model, hole drawing, and dimension/clearance report for
  prototype review. Actual bushing fit and drilling accuracy need checking; the
  requested hole depth is an operator setting, not an automatically enforced stop.

[Original request](scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/prompt.txt)
· [Engineering basis](scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/context.md)

<a id="parametric-drill-jig-02"></a>

### Locate a top-wall hole pattern on rectangular tube without blocking clamps

- **Purpose:** Prepare a repeatable drilling saddle for display-frame tubes,
  retaining the existing end clamps and access for chip removal.
- **Work:** Use the specified datum and indexing arrangement, bridge the hole
  pairs, and check bushing seats, clamp exclusions, and tool-access geometry
  against the brief's already authorized prototype decisions.
- **Useful result:** A model, hole layout, and dimension report that show how the
  jig locates and clears the workholding. The guide does not set breakthrough
  allowance or authorize drilling the tube's opposite wall.

[Original request](scenarios/parametric-drill-jig/02-extrusion-panel-mount-jig/prompt.txt)
· [Engineering basis](scenarios/parametric-drill-jig/02-extrusion-panel-mount-jig/context.md)

<a id="parametric-drill-jig-03"></a>

### Locate a six-hole pattern using a fixture plate's existing datum notch

- **Purpose:** Repeat a circular fixture's bolt pattern with the correct angular
  orientation while leaving room for clamps and debris removal.
- **Work:** Build the keyed annular jig around the supplied Cartesian hole table,
  existing notch, guide-bushing geometry, and asymmetric clamp keepouts.
- **Useful result:** A jig model, hole drawing, and measurement report explaining
  the locating method and clearances. No new indexing hole is invented; actual
  bushing retention and attainable hole-position tolerance remain physical checks.

[Original request](scenarios/parametric-drill-jig/03-indexable-circular-fixture-jig/prompt.txt)
· [Engineering basis](scenarios/parametric-drill-jig/03-indexable-circular-fixture-jig/context.md)

<a id="circuit-boards"></a>

## Turn a defined instrument circuit into a prototype circuit board

Wright's contribution: carry approved electrical connections and mechanical
constraints into editable circuit-board files, then keep the parts list,
manufacturing exports, and electrical/layout rule reports consistent. These
are interdisciplinary instrument-packaging jobs; rule checks do not establish
electrical performance or authorize ordering boards.

<a id="sensor-interface-pcb-01"></a>

### Package a temperature-sensor interface for a roaster prototype

- **Purpose:** Replace the interface sketch with a compact board that connects
  the external thermistor to an existing controller using the supplied circuit.
- **Work:** Preserve divider/filter connectivity, mounting holes, connector
  assignments, and readable labels while laying out the specified board.
- **Useful result:** Editable schematic and board, parts list, fabrication files,
  and rule-check reports for review. Exact connector selection and controller
  compatibility remain explicit; temperature-conversion firmware is outside scope.

[Original request](scenarios/sensor-interface-pcb/01-thermistor-interface/prompt.txt)
· [Engineering basis](scenarios/sensor-interface-pcb/01-thermistor-interface/context.md)

<a id="sensor-interface-pcb-02"></a>

### Turn a two-pressure-sensor breadboard into a serviceable interface PCB

- **Purpose:** Package two independent sensor filters in the available mounting
  footprint without swapping channels or losing access for signal measurements.
- **Work:** Preserve exact pin assignments, separate signal paths, labeled
  channels, and accessible raw/filtered test points using the supplied placement basis.
- **Useful result:** A consistent schematic, board, parts list, fabrication package,
  and rule-check record for a prototype review. This board filters signals; it
  does not control the pump or establish a safety function.

[Original request](scenarios/sensor-interface-pcb/02-dual-pressure-filter/prompt.txt)
· [Engineering basis](scenarios/sensor-interface-pcb/02-dual-pressure-filter/context.md)

<a id="sensor-interface-pcb-03"></a>

### Make fan-speed signals accessible without mixing power and logic wiring

- **Purpose:** Give a technician a compact passive service interface for two
  fans, with clearly identified power connections and raw/filtered speed signals.
- **Work:** Route the specified power and signal circuits, preserve the required
  separation, and provide labeled connectors and probe-accessible test points.
- **Useful result:** Editable board and schematic, fabrication files, parts list,
  and rule reports with unresolved fan/connector compatibility identified. The
  assumed fan output must be checked against its datasheet; this is not a fan controller.

[Original request](scenarios/sensor-interface-pcb/03-fan-tach-service-board/prompt.txt)
· [Engineering basis](scenarios/sensor-interface-pcb/03-fan-tach-service-board/context.md)

<a id="wiring-harnesses"></a>

## Document wiring that can be assembled, checked, and serviced

Wright's contribution: keep the connection schedule, physical routing, wire
lengths, sourced parts, voltage-drop calculations, and assembly instructions in
agreement. This reduces repeated transcription work without replacing part-rating
checks, electrical review, or a physical continuity test.

<a id="sensor-fan-harness-01"></a>

### Make a clear, serviceable fan-and-temperature-sensor harness

- **Purpose:** Turn a benchtop chamber's wiring sketch into a package a technician
  can assemble while preserving the controller interfaces and separate sensor return.
- **Work:** Select documented wire and connector parts, account for installed
  routes and service loops, and check the loaded supply/return path during normal
  running and fan startup against the supplied voltage-drop budget.
- **Useful result:** Labeled drawing, pin schedule, cut list, parts list, assembly
  instructions, and voltage-drop results. Unknown contact resistance and interface
  compatibility remain stated assumptions until resolved; nothing is energized.

[Original request](scenarios/sensor-fan-harness/01-desktop-incubator/prompt.txt)
· [Engineering basis](scenarios/sensor-fan-harness/01-desktop-incubator/context.md)

<a id="sensor-fan-harness-02"></a>

### Size long fan-harness branches for simultaneous startup

- **Purpose:** Supply two remote growth-rack fans and a humidity transmitter
  without exceeding the permitted wiring voltage drop or complicating service.
- **Work:** Account for both fans' startup current in the shared trunk and return,
  compare permitted wire sizes, and retain the sensor's separate signal return.
- **Useful result:** A buildable wiring package with branch and shared-segment
  calculations, documented connector ratings, and independently removable fans.
  High-humidity installation does not by itself establish a connector's sealing rating.

[Original request](scenarios/sensor-fan-harness/02-growth-rack-long-run/prompt.txt)
· [Engineering basis](scenarios/sensor-fan-harness/02-growth-rack-long-run/context.md)

<a id="sensor-fan-harness-03"></a>

### Make two air-sampler zones independently serviceable

- **Purpose:** Let a technician disconnect either fan-and-sensor zone without
  confusing the zones or mixing sensor returns with fan-current returns.
- **Work:** Develop the removable connections, splice arrangement, labels, and
  shield treatment; calculate voltage drop through loaded shared segments and
  connectors during simultaneous startup.
- **Useful result:** An illustrated assembly package with exact pin and cut
  schedules, parts list, and electrical calculations, including how crossed
  connections are prevented. Continuity instructions are not evidence that a
  physical harness has already been tested.

[Original request](scenarios/sensor-fan-harness/03-dual-zone-air-sampler/prompt.txt)
· [Engineering basis](scenarios/sensor-fan-harness/03-dual-zone-air-sampler/context.md)

## What to ask when reviewing any example

The result should help with the decision described above, not merely contain
the expected files. A useful review answers:

1. What job is being done, and why does this result matter?
2. Which supplied requirements, data, and assumptions does it use?
3. What did the work actually produce, and where can I inspect it?
4. What conclusion is supported, and what remains uncertain or unmet?
5. What decision or next observation is needed from me?

When work pauses, explain its consequence and the next action: for example,
"The calculation tool cannot represent the specified contact resistance, so
the required link temperature is not available," or "The diagnosis is ready
for your review; inspect the path comparison and proposed next experiment."
These are wording examples, not live status reports. A request for review is
different from a failed calculation. Technical identifiers can remain available
for troubleshooting without becoming the explanation.

## Alignment scope and remaining questions

This guide is companion presentation content. It does not replace the original
requests, add acceptance criteria, change workflow definitions, or modify past
attempts. It is linked from the example collection's README; the application does
not yet load these descriptions into workflow titles or purpose fields. Applying
them there is a separate presentation integration, preserving authored workflows
and their history.

The focused review found the following issues to retain explicitly rather than
solve by inventing requirements:

- **Robot commissioning:** The first brief supports diagnosis and choosing a next
  test, but supplies no acceptable tracking-error limit or operational consequence
  of that error. If the intended decision becomes acceptance for aisle service,
  the engineer must provide the relevant operating conditions, allowable deviation,
  and measurement basis. Do not create a pass threshold from the synthetic trace.
- **Early thermal studies:** The links have useful sizing decisions and explicit
  model limits. Keep them as early link studies rather than expanding all three
  into complete product thermal qualification.
- **Prototype handoffs:** Printed parts, jigs, boards, harnesses, and sheet-metal
  packages remain prototypes or review material. Preserving physical fit, part
  selection, manufacturing, and qualification questions is more honest than
  making every example look like a finished production design.
- **Internal test language:** Some source contexts contain historic file-presence
  scoring statements or attempt-recovery notes. These are not the engineering
  purpose or current run status. Keep them out of introductory descriptions;
  retain source history and use actual runtime evidence for status and validation.

No scenario has been replaced. The thirty input packs and ten workflow templates
remain the authority for the work requested. A substantive correction to those
inputs should be separately reviewed and versioned, not folded into this wording pass.
