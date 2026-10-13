# Robot Arm Revision 6 Metadata-Cleanup Design and Test Plan

## 1. Scope and design basis

This specification governs completion of the owned SteveCAD robot assembly in document `167ef21f-6679-4e4d-8917-14dc067893d6`, CURRENT revision 6, build `82a810f5-a5f5-481f-84d3-fd997dfaa4bd`. The existing revision-6 B-rep is the geometry design basis. The only prospective CAD revision is one revision-checked batch that:

1. updates per-instance printed metadata to the specified local print orientations and notes; and
2. replaces stale `design_notes.py`/main header comments with concise revision-basis notes.

All modeling operations, numerical arguments, `Design.clearance` entries, exact `Design.contact` declarations, component identities, geometry, placements, axes, poses, clearances, hardware stacks and the 33-sample path shall remain unchanged. No document duplication or geometry-only edit is authorized. Historical files, plans, failures, captures and exports shall be retained. No second edit is permitted after generation.

Revision-6 observations supplied as design-basis evidence are: 110 instances and 110 solids; no component errors; five absolute pose checks CLEAR with zero issues; a 33-sample, 8 s motion study with no new moving collisions; and an independently imported 110-solid STEP with SHA-256 `5dd481d4250251743b5ccec1c63adf1e9625fb4d4f4469393ef156cfde587df3`. All 110 historical diagnostic meshes were closed and matched native rounded world bounds/volumes, with maximum relative tessellation-volume error 0.00041540825. These facts do not pre-accept the prospective revision.

## 2. Requirements

| ID | Supplied mandatory requirement | Responsible stage |
|---|---|---|
| R01 | Preserve revision-6 geometry, operations, arguments, identities, placements, contacts, clearances and kinematics exactly; perform only the single metadata/comment batch. | CAD creation |
| R02 | Maintain an editable articulated assembly of 110 separately identifiable solid instances, including 18 unique/28 instance printed parts and separate purchased references. | Geometric validation |
| R03 | Use millimetres, degrees and the right-handed frame defined in Section 3. | CAD creation |
| R04 | Stationary-group XY footprint shall be at most 200 × 180 mm. This bound excludes the moving arm reach envelope. | Geometric validation |
| R05 | Keep the PCB toward the rear and pedestal toward the front; the actual arm/base shall not overlap the reserved electronics-bay volume in any of the five named fit states. | Geometric validation |
| R06 | Upper-arm and forearm joint-center spacings shall be 100 ±0.1 mm and 90 ±0.1 mm, respectively. | Geometric validation |
| R07 | Main pivots shall retain closed Ø5.4 mm through-X printed bores and Ø5 mm purchased shafts, giving nominal radial gap 0.20 mm and measured/derived minimum at least 0.19 mm. | Geometric validation |
| R08 | Moving printed faces shall retain at least 0.4 mm gap. Genuine printed seats may have zero overlap; no other interference is permitted. | Geometric validation |
| R09 | All five cradle definitions shall retain finite-volume boss webs and each cradle instance shall be one connected solid. A “one body” label alone is insufficient evidence. | Geometric validation |
| R10 | Preserve outward-facing cap-bolt heads, fitted shafts/nuts and the 25 exact M3 bolt/nut stacks; contacts must use explicit component-pair names. | Geometric validation |
| R11 | Joint ranges and named poses shall match Section 5; axes shall be tested as oriented lines by direction and point-to-line distance. | Geometric validation |
| R12 | Repeat the five absolute native `fit_check(motion=False)` states and the bounded 33-sample, 8 s motion path without adding adaptive/full-space claims. | Geometric validation |
| R13 | Each of the 18 unique printed definitions shall remain independently exportable and fit a 220 × 220 × 250 mm build volume in its declared orientation. | Geometric validation |
| R14 | Run one bounded native FDM screen over an explicitly supported printed selection. If scoping is unavailable, retain whole-design scope and classify every finding by exact printed or purchased identity. | Geometric validation |
| R15 | Preserve the official IO-board envelope, mounts, CM5 clearance envelope and provenance in Section 6; do not invent Arduino, connector, cooler or detailed servo geometry. | CAD creation |
| R16 | Purchased servos, boards, horns, metal hardware and standoffs shall remain excluded from printable outputs. | Final review |
| R17 | Capture home isometric, top and front native views once each and produce three derived studio views with the specified visible geometry and appearance. | Presentation rendering |
| R18 | Presentation fidelity means qualitative agreement with the native captures in visible silhouette, feature count, holes, slots, camera and appearance; renderings do not prove dimensions. | Final review |
| R19 | The review shall contain six images, revision/build identity, measurable results, complete BOM/register, stacks, sequence, print directions, supports, export preparation and limitations. | Final review |
| R20 | Do not claim manufacturing, physical fit, payload, strength, stability, continuous collision certification, powered operation, publication or user acceptance. | Final review |

## 3. Coordinate frame and principal geometry

Assembly world coordinates are right-handed: +X right, +Y rear, +Z up; the arm reaches toward −Y. Local coordinates below are native component coordinates and shall not be confused with assembled world coordinates.

| Feature | Supplied world definition, mm |
|---|---|
| Shoulder center S | (0, 45, 75) |
| Elbow center E | `(0, 45−100 cos35°, 75+100 sin35°)` = approximately (0, −36.915, 132.358) |
| Wrist center W | `(0, 45−190 cos35°, 75+190 sin35°)` = approximately (0, −110.639, 183.144) |
| Base-yaw axis | Oriented +Z line through XY = (0,45); any Z coordinate on this line is equivalent |
| Shoulder/elbow/wrist axes | Oriented −X lines through the respective S/E/W YZ coordinates; any X coordinate is equivalent |
| Link section | Upper arm and forearm: 18 mm width/height |
| Link planes | Upper arm/palm plane X = −9.4; forearm plane X = +9.4 |
| Home rotation | X-axis rotation −35° |
| IO board | X[−80,80], Y[90,180], Z[12,13.6] |
| Reserved bay headroom | 25 mm above the actual PCB, checked as volume rather than rendered as a box |

Analytical checks: `|E−S|=100 mm`; `|W−E|=90 mm`; shaft/bore radial gap `(5.4−5.0)/2=0.20 mm`. Axis acceptance compares normalized direction, allowing equivalent representative points such as yaw Z=14 versus Z=40 and pitch X=0 versus X=±9.4.

## 4. Printed definitions and print metadata

The native instance register is authoritative for each definition’s exact quantity, local bounds and instance names; its quantities shall total 28. Those values must be read from revision 6 and placed in the review before the edit, not inferred from failed revision 5. The following table completely defines the metadata change; no geometry transformation is implied.

| Unique printed definition | Native build direction | Required orientation/support note |
|---|---:|---|
| `tray` | −Z | Broad plate Z=6 on bed; connected feet upward after inversion; native local envelope 200×180×10 mm |
| `arm_foot`, `turntable` | +Z | Bottom face on bed |
| `tower` | +Z | Side-access pocket requires removable support and a clear insertion route before final assembly |
| `upper_arm`, `forearm`, `palm`, `finger`, `retainer_large`, `retainer_small` | +X | Align native +X to printer +Z; use broad X cap/side face where available; fingers have no primary pivot |
| `yoke`, `pitch_yoke` | +Z | Bridge-down; removable supports for horizontal bores/cheeks as needed |
| `yoke_mount`, `guide_post`, `guide_cover` | +Z | Bottom face on bed; vertical bores |
| `saddle_large`, `saddle_small`, `saddle_yaw`, `saddle_gripper` | +X | Support negative-X cavity/open-side features, boss webs and ears; remove supports, clean bores and trial-fit |

For every definition, validation shall derive the exact native local X/Y/Z envelope, map it into the declared build orientation and compare each printer-axis extent with 220/220/250 mm. Do not claim measured slice, support-volume, bridge or overhang results unless produced by the bounded screen.

Inherited digital print choices, not verified calibration facts, are FDM PETG, 0.4 mm nozzle, 1.2 mm thin-wall screen, nominal 3 mm structural walls and 4 mm main-pivot ligaments. Native warnings and “not measured” fields shall be retained.

## 5. Kinematics, states and interfaces

| Joint/control | Axis and range, deg | Named-state values |
|---|---|---|
| Yaw | +Z through (0,45), −60…+60 | reach +60; folded −60; home 0 |
| Shoulder | −X through S, −30…+60 | reach −30; folded +60; home 0 |
| Elbow | −X through E, −45…+75 | reach −45; folded +75; home 0 |
| Wrist pitch | −X through W, −45…+45 | reach +45; folded −45; home 0 |
| Gripper opening | Symmetric/coupled, 0…25 mm | reach/open 25; folded/closed 0; home 0 |

The five absolute states are home, reach, folded, gripper-open with other joints zero, and gripper-closed with other joints zero. The retained motion is linear home at 0 s → reach at 2 s → gripper-open at 4 s → folded at 6 s → home at 8 s, with exactly 33 exact-solid samples. This is bounded path coverage only.

Main pivot interfaces use closed Ø5.4 printed bores, Ø5 shafts, outward head/washer and nut/retainer stacks. The exact native M5 quantities, lengths, washer dimensions, nut dimensions and contact-pair names shall be transcribed from the current source register before the edit. Source intent or wildcard contacts are unacceptable substitutes.

## 6. BOM and purchased interfaces

| Class | Item | Quantity/status |
|---|---|---:|
| Printed | 18 definitions listed in Section 4 | 28 instances total; exact per-definition counts from current native register |
| Purchased hardware | Exact M3 bolt/nut stacks | 25 stacks; preserve native sizes, placements and contacts |
| Purchased hardware | Retained M5 pivot stacks | Native exact quantity and stack dimensions; no bare pins |
| Electronics | Official CM5 IO-board reference envelope | 1; 160×90×1.6 mm |
| Electronics | CM5 clearance envelope | 1; 55×40×4.621 mm |
| Servo references | MG996R body envelope | 3 provisional references; 40.7×19.7×42.9 mm |
| Servo references | MG90S body envelope | 2 provisional references; 22.8×12.2×28.5 mm |
| Purchased interfaces | Horns, washers, nuts, shafts and standoffs | Preserve exact native register; non-printable |

IO-board provenance is KiCad SHA-256 `728ec772d1bdf6ff2c9f7a81fd8ff00164c894d002221f522f627ae3f8945026`, 79 footprints and 4670 tracks. Board-local mounting centers are H1(11,8), H6(132.5,77), H7(11,77), H8(132.5,8), transformed by X=pcbX−79 and Y=160−pcbY. World standoffs are (−69,98), (52.5,167), (−69,167), (52.5,98), each 6 mm high. The M2.5/2.7 mm mount profile and 1.6 mm board thickness remain declared reference choices rather than verified drill/thickness measurements.

The CM5 envelope derives from preview import `668a59bf-d3e8-4474-999a-728654f172f3`, manufacturer STEP SHA-256 `6adc64e5f69b2799b65d56c94b3543bad136fa4191cadaba0aa0e49fa345598f`. Its detailed 1076-solid reference is not to be re-exported. Servo ears, axes, splines, horns, transmission, inventory and fit remain physically unverified.

## 7. Seven-stage process and acceptance

1. Design basis: read CURRENT revision/build, exact source, instance/BOM register, contacts, operations, metadata and native local bounds; archive references without resuming the failed revision-5 run.
2. Preconstruction plan: complete the source-derived quantity, hardware-stack, contact and envelope fields; resolve no value by inference.
3. Single CAD edit: apply only the listed metadata and comments, using the larger typed context allowance; save once as one CAS revision.
4. Native validation: inspect actual B-rep, 110-solid/instance count, identities, connected cradles, dimensions, bores, oriented axes, placements, ligaments and five absolute fit states.
5. Kinematic/FDM validation: execute the retained 33-sample path once and one bounded FDM screen. Purchased 1.0 mm washer or 1.15 mm standoff-wall findings shall not authorize hardware changes.
6. Presentation/export preparation: capture three native home views; derive three studio views; identify all 18 exact new-revision printable definitions for later per-body oriented STL acquisition and independent validation. Historical STEP/STLs are not the new print package.
7. Final review: verify requirements and limitations, compare each rendering qualitatively with its source capture and issue no manufacturing or powered-operation authorization.

Acceptance tolerances are exact identity/count equality; link spacings ±0.1 mm; radial pivot gap ≥0.19 mm; other moving printed gaps ≥0.4 mm; zero unenumerated overlap at each named state; printer-volume bounds ≤220×220×250 mm; and axis direction/line coincidence using native geometric tolerance reported by the validator. Missing evidence is UNVERIFIED, never PASS.

Assembly sequence: print and clean parts; trial-fit supported saddles/bores; install board standoffs and removable PCB; bolt tray to arm foot; assemble turntable/tower and yaw reference; install shoulder yoke, servo/horn reference and retained M5 stack; add upper arm, elbow yoke, forearm and retained stacks; add wrist, palm and gripper guide/cover/fingers; install the fifth servo reference and simplified coupled gripper interface; confirm outward heads/nuts; then perform unpowered manual clearance checks. Physical execution is outside this digital scope.

## 8. Presentation and unresolved dependencies

Printed tray/foot/tower/yokes/cradles are matte safety orange `#ed6b20`; links/palm/fingers/cover/caps are charcoal `#323840`; purchased fasteners are brushed metallic; servo envelopes are dark; board/module references are exposed green. These are rendering requirements only, not physical CAD-material assignments. Do not add wires, ports, detailed servos, a raised platform, covered PCB, altered holes, tray reshaping or green tray coloration.

Still UNVERIFIED are real servo/horn mounting, exact inventory, CM5 variant/cooler, connectors, antenna keepout, cables, actuator power, torque, transmission, payload, strength, stability, slicing/support volume, print quality, physical assembly and energized operation. No Arduino model is included or required.