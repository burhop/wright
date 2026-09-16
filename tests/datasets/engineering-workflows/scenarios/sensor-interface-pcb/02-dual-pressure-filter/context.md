# Dual pressure input brief
Original fictional prototype requirements.
## Business, circuit and assumptions
Brookforge is building six clean-water pump rigs. The board only filters low-voltage analog signals; it does not power a pump or control a safety function. Regulated 5 V ±5% comes from J1 and can supply 100 mA total. Each external sensor requires at most 20 mA. The downstream ADC accepts 0..5 V and has input impedance at least 1 MΩ; these are supplied system assumptions that must be listed in the output.
Channel A: RAW_A from J2 pin 2 passes R1=1 kΩ to ADC_A; C1=100 nF connects ADC_A to GND. Channel B uses RAW_B, R2=1 kΩ, ADC_B and C2=100 nF identically. C3=1 µF and C4=100 nF decouple 5V to GND. Test points TP1/TP2 expose RAW_A/ADC_A, TP3/TP4 expose RAW_B/ADC_B and TP5 is GND. No filter capacitor may be placed between channels.
## Pinout and mechanical arrangement
J1 is a vertical 1x04 2.54 mm THT header at left, pin order 5V, ADC_A, ADC_B, GND. J2 and J3 are vertical 1x03 2.54 mm THT headers at upper right and lower right, each pin order 5V, RAW, GND. Use connector geometric centers J2=(34.0,19.5) mm and J3=(34.0,10.5) mm so their complete courtyards remain clear of the right-side mounting holes; these are center coordinates, not footprint-origin coordinates. Specify exact real connector records before production; the generic headers are prototype requirements. Orient each pin 1 consistently toward the top board edge. Keep test pads at least 1.5 mm diameter and probe-accessible with 2.5 mm clearance to tall parts. Label channels A/B in silkscreen and separate their signal routing.

Retained-board route qualification for the prototype geometry proved this exact fixed placement set on the 40 × 30 mm outline: J1 footprint origin=(4.5,18.81) mm, rotation 180°; C3 footprint origin=(8.0,23.0) mm, rotation 90°; C4 footprint origin=(12.0,23.0) mm, rotation 0°. These are footprint-origin coordinates, not connector centers. The proof routed all seven nets with zero unconnected items, zero copper-edge-clearance errors, zero courtyard overlaps, zero shorts and zero solder-mask bridges. Use these coordinates as the starting placement for the next fresh prototype attempt and preserve them through routing; if a native geometry error contradicts the proof, record it and stop rather than substituting an unqualified position.
## Board and shop requirements
Board outline: 40.0 × 30.0 mm rectangular, origin lower left, 1.6 mm nominal two-layer FR-4, 35 µm nominal copper. Four non-plated mounting holes Ø2.5 mm at (3,3), (37,3), (3,27), (37,27) mm. Copper clearance from mounting-hole edges: 1.0 mm. Minimum track/clearance: 0.25/0.25 mm. Minimum via drill: 0.30 mm. Place all components on the front, label connector pin 1, and keep assembly-readable reference designators. These are fictional internal prototype design rules, not a supplier capability certification.
Use the supplied netlist as the approved connectivity input for this scenario. Component-library.csv describes internal prototype component requirements; exact purchasable connector selection and datasheet evidence must be resolved by the workflow before release. Do not substitute pinouts or claim approvals that are not provided. Schematic approval in this fictional input is design intent, not authorization to order boards.
## Deliverables
Return editable .kicad_sch and .kicad_pcb files, bom.csv, Gerber copper/outline layers, a .drl drill file, ERC and DRC reports. Keep native sources and fabrication exports from the same revision. Presence checking is the initial automation scope; no test run constitutes electrical qualification or production release.

Retained-board qualification for attempt016 placement recovery: the failed attempt015 board was copied to disposable KiCad MCP qualification candidates after the build-stage approval boundary. Moving C2 to footprint origin (23.0,18.5) mm at rotation 0 degrees and TP1 to footprint origin (10.0,14.0) mm at rotation 0 degrees eliminated the H3-C2 and TP1-J3 courtyard overlaps; the full native placement audit returned zero errors. Preserve the qualified J1, C3 and C4 origins above and use these C2/TP1 origins as fixed hints in the next fresh build.

Qualified coordinate shorthand for workflow bindings: C2 origin=(23.0,18.5) mm, rotation 0 degrees; TP1 origin=(10.0,14.0) mm, rotation 0 degrees.

## Attempt016 C3 recovery qualification

The fresh attempt016 build reached `pending_approval` with the expected 40 x 30 mm board, six nets, 14 components and 27 assigned pads, but KiCad reported the fixed C3 hint at `(8.0,23.0)` mm, rotation 90 degrees as off-board/overlapping. The run stopped before any placement mutation, preserving the evidence.

A disposable native qualification copied that failed board and moved only C3 on five candidate copies. The candidate C3 footprint origin `(8.0,23.0)` mm at rotation 0 degrees returned `audit_status=ok` with zero errors and zero courtyard overlaps. The exact receipt is `pcb02-attempt016-c3-qualification.json`; the next fresh attempt must use C3 rotation 0 degrees and must not repeat the failed 90-degree hint.
Selected recovery hint: C3 footprint origin=(8.0,23.0) mm at rotation 0 degrees; this is the qualified PCB02 attempt017 placement.

## Attempt018/019 connectivity recovery

Attempt018 reached schematic connectivity with the qualified placement hints but
the model repeated the completed `schematic` operation after saving
`connected/design.kicad_sch`. The runtime rejected that duplicate call before
board creation, so the attempt has no fabrication-output credit. The save is a
terminal mutation: after it succeeds, return the coverage report immediately
and make no further schematic, connect, load, inspection or validation call.
Attempt019 is the fresh recovery run using the same qualified coordinates and
the strengthened terminal instruction.

## C4 build-observation qualification

Attempt019's real-board build reported `placement_hint_offboard` for C4 at the
qualified origin `(12.0,23.0)` mm, rotation 0°, before any footprint mutation.
Disposable native qualification on that preserved board tested C4 at
`(12.0,23.0)`, `(12.0,22.0)`, `(12.0,21.0)`, `(14.0,23.0)` and `(16.0,23.0)`
mm, all rotation 0°. Every candidate returned zero native audit errors. The
next fresh attempt must treat the build warning as an initial observation and
make one first `move_footprint` call at the already-qualified `(12.0,23.0)`
origin before continuing; it must not substitute a new coordinate or repeat the
move.
