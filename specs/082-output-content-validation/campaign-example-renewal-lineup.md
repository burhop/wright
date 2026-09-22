# Proposed renewed 30-example lineup

Date: 21 September 2026. Work package: R1. Decision status: **approved on
22 September 2026**. The approval record is
`campaign-example-renewal-decision.md` and `.json`.

## Recommendation

Keep the 30 recognizable subjects, but make every one a complete engineering
job. The proposed result is **30 of 30 digitally verified design packages** and
no decision-only exceptions. The six original Robot and water-heater tests remain
valuable upstream stages and regression assets; they no longer stand alone as the
demonstration's final result.

This is deliberately a lineup decision, not a claim of completion. “Verified”
means the eventual workflow must check the exact selected digital design against
the agreed digital requirements. It does not mean printed, fabricated, proof
loaded, electrically safe, food safe, certified, purchased, supplier accepted,
or physically commissioned.

## Proposed family contracts

| Family | Proposed application chain and real handoffs | Final design package | Digital verification and limits | Availability basis |
| --- | --- | --- | --- | --- |
| Printed replacement part | Blender creates the native mesh; the existing mesh-repair service consumes its STL; Bambu Studio consumes the repaired STL and emits the actual sliced 3MF/G-code package. | Saved native design, source and repaired STL, dimensional report, orientation/support evidence, sliced 3MF and previews. | Interface dimensions, required features, manifold/normal/degeneracy checks, build-volume fit and successful nonempty slice. Physical fit, strength and printing remain pending. | Existing pinned Blender, repair and Bambu Studio bindings; exact renewed workflow still needs R3 execution. |
| Lightweight bracket | AgentCAD/build123d creates native/source geometry and STEP; CalculiX consumes that exact STEP/mesh and returns fields and reactions; the selected revision is re-exported. | Editable source, selected STEP, mesh/solver deck, stress/displacement/reaction evidence and design decision. | Loads, interfaces, material basis, mass target, stress/displacement limits, selections and mesh sensitivity. No proof load or fatigue certification. | Existing AgentCAD and pinned CalculiX binding with recorded-field extension; provider health must be rechecked. |
| Raspberry Pi enclosure | Primary manufacturer references define interfaces; AgentCAD creates two matching CAD/fluid-domain variants; Gmsh/OpenFOAM consumes each domain; the selected exact CAD is packaged. | Selected native/source CAD, STEP/STL, fluid domain, thermal-flow fields, comparison and service/fit report. | Board envelope/mounting/connector access, clearances, heat inputs, boundary conditions, convergence/balance and temperature/flow comparison. No physical environmental qualification. | Existing manufacturer retrieval, AgentCAD and OpenFOAM paths; exact branch and current service health require R3 proof. |
| Sensor-interface PCB | KiCad authors the schematic and board; FreeRouting consumes the board interchange and returns routing; KiCad reopens the routed revision, runs native ERC/DRC and produces fabrication files. | Native KiCad project plus schematic, routed board, BOM, drill/Gerber package and checks tied to one revision. | Nets, pin assignments, board outline, clearance/current rules, ERC/DRC, routing/fabrication completeness and cross-file identity. No fabricated-board test or regulatory approval. | Existing pinned KiCad MCP, FreeRouting path and native-rule-check extension. |
| Heat spreader | AgentCAD creates candidate and selected STEP geometry; the OASiS MCP executes the pinned scikit-fem conduction solver on geometry-derived meshes; the result selects and freezes the final part. | Editable/source CAD, selected STEP, manufacturing dimensions, FE fields, heat balance, mesh comparison and requirements table. | Fixed interfaces/material/contact/loss assumptions, temperature and mass/space limits, heat balance and mesh sensitivity. No physical thermal test. | Existing AgentCAD and OASiS/scikit-fem binding; exact geometry-to-mesh correspondence must be requalified. |
| Parametric drill jig | AgentCAD creates parametric source, STEP, STL and governed hole-layout DXF; Bambu Studio consumes the exact final STL for print preparation. | Editable source, STEP/STL, hole-layout DXF, dimension report and sliced 3MF with orientation/support evidence. | Datum, hole coordinates, bushing seats, clearances, plate envelope, feature presence, topology and actual slice. Bushing press fit, drilling safety and physical accuracy remain pending. | AgentCAD and the Bambu slicer are currently exposed and the pinned executable exists. The current slicer wrapper is printed-part-specific; R2 needs a separately confined jig binding and R3 needs an actual jig slice. |
| Sensor/fan harness | WireViz consumes connector/wire/component records to create the harness YAML, diagram, BOM and cut list; KiCad consumes the released pin/net table as an independent interconnect-check schematic and runs ERC; governed calculations check voltage drop, ampacity and bend/service constraints. | WireViz source/diagram, released pin-net table, KiCad verification schematic/ERC, BOM, cut list, labels and assembly/verification report. | Pin-to-pin continuity intent, connector separation, wire sizing, voltage drop, derating, shielding, bend radius and service length. Crimp quality, insulation, EMC and physical installation remain pending. | WireViz and KiCad are currently exposed. R2 must add the adapter and an independent table-to-schematic correspondence check; ERC alone is insufficient. R3 must prove valid, swapped-pin and omitted-net cases. |
| Sheet-metal handoff | Solid Edge creates and unfolds the native sheet-metal part; AutoCAD MCP Pro's qualified headless DXF backend reopens the actual flat DXF for independent layer/entity/dimension inspection and a manufacturing review drawing; supplier-rule checks consume the same revision. | Native PSM, folded STEP, flat DXF, inspected/annotated review DXF, bend/feature report and supplier-ready package. | Folded/flat correspondence, material/thickness, extents, bends/reliefs, holes/cutouts, minimum features and supplier-rule findings. No supplier acceptance or fabrication. | Solid Edge is currently exposed on the licensed Windows host. U-C4N AutoCAD MCP Pro 3.4.7 passed clean-container headless DXF authoring/reopen but is not active in this workspace. Exact Solid Edge DXF preservation must be qualified. This is not desktop AutoCAD automation. |
| Water-heater thermal package | OpenModelica selects the lowest setting meeting the transient heat-up/energy requirement; AgentCAD consumes that selected power plus approved envelope/interfaces to create the vessel/heater/insulation package; OASiS/scikit-fem consumes the selected geometry for a steady thermal-gradient/hot-surface screen. | Modelica study, editable CAD, selected STEP, thermal fields and a final thermal-package requirements report. | Existing transient target/energy/stability checks plus new envelope, heater contact, insulation, wall-temperature/gradient and correspondence checks. Electrical safety, pressure, food contact and physical boiling tests are excluded. | Existing pinned OpenModelica kit, AgentCAD and OASiS paths; new cross-family integration and new requirements require R2/R3 proof. |
| Mobile-cart corrective design | ROSBag MCP and the existing robot operations consume the recording and produce bounded observations; independently governed site/interface measurements plus those observations define the corrective design requirement; AgentCAD creates the corrective hardware; CalculiX consumes the exact STEP for load/stiffness verification. | Diagnosis/calibration evidence, editable corrective CAD, STEP, FEA package, drawing/dimensions and an installation/test plan. | Preserve observation versus cause. Verify geometry, interfaces, static/inertial load, stiffness and line-of-sight where applicable. Final causal confirmation and on-robot commissioning remain pending. | Existing ROSBag, AgentCAD and CalculiX paths; the corrective-design handoff is new and must be qualified. Robot 010 remains untouched. |

Supporting Wright scripts may stage files, calculate governed metrics and compare
artifacts. They are not presented as additional engineering applications.

## The 30 proposed jobs

The chain column uses the exact family contract above; the row states the
case-specific engineering purpose, handoff and authority change.

| ID | Engineering job and why it matters | Proposed chain and decisive handoff | Final result and principal checks | Scope decision |
| --- | --- | --- | --- | --- |
| PRINT-01 | Replace an observatory focus wheel with a cold-weather scalloped grip that preserves the D-shaft interface. | Blender → mesh repair → Bambu Studio; repaired, dimension-checked STL is the slicer input. | Focus-wheel native/mesh/print package; shaft fit, 38 mm reference size, grip features, topology and slice. | Retain; styling and support orientation discretionary, interface fixed. |
| PRINT-02 | Replace a broken repair-cart bow handle while preserving mounts and gloved-finger clearance. | Blender → mesh repair → Bambu Studio; final repaired handle STL feeds slicing. | Handle native/mesh/print package; 96 mm reference span, mounting and hand clearance, topology and slice. | Retain; grip/blend styling discretionary, mount and keepout fixed. |
| PRINT-03 | Recreate a removable synthesizer tilt foot that fits the instrument and preserves its styled stance. | Blender → mesh repair → Bambu Studio; the verified foot STL feeds slicing. | Foot native/mesh/print package; 38 mm reference interface, contact/retention features, topology and slice. | Retain; exterior styling and support orientation discretionary. |
| BRACKET-01 | Reduce the mass of a conveyor vision-camera cantilever without losing alignment under load. | AgentCAD → CalculiX; exact revised STEP and load-pad identities feed FEA. | Selected bracket CAD/STEP and FEA; interfaces, 100 N load, ≥20% mass reduction, ≤120 MPa and ≤0.5 mm, mesh sensitivity. | Retain; topology within fixed interfaces/loads is discretionary. |
| BRACKET-02 | Lighten a pump-test instrument outrigger while keeping the instrument position stiff under combined load. | AgentCAD → CalculiX; revised STEP feeds the recorded static solve. | Selected outrigger package; four mounts, [60,0,-80] N load, ≥15% mass reduction and shared strength/stiffness limits. | Retain; topology discretionary. |
| BRACKET-03 | Lighten a warehouse dock-sensor yoke without losing lateral alignment. | AgentCAD → CalculiX; exact yoke STEP feeds the solver. | Selected yoke package; four mounts, 100 N lateral load, ≥25% mass reduction and shared strength/stiffness limits. | Retain; topology discretionary. |
| PI-01 | Design a quiet, serviceable desktop Raspberry Pi 5 case and choose a passive vent strategy. | Manufacturer references → AgentCAD variants → Gmsh/OpenFOAM → selected CAD. | Final riverstone enclosure; board/interface fit, access, 6 W thermal comparison, convergence/balance and selected geometry identity. | Retain; external styling/vent pattern discretionary inside fixed envelope/interfaces. |
| PI-02 | Design a protected greenhouse gateway enclosure that remains serviceable in a 35 °C environment. | Manufacturer references → AgentCAD variants → Gmsh/OpenFOAM → selected CAD. | Final gateway enclosure; board/sensor interfaces, access, 8 W thermal comparison and selected geometry identity. | Retain; vent/chimney solution discretionary; no ingress-rating claim. |
| PI-03 | Design a compact edge-vision computer case and select the better forced-flow path. | Manufacturer references → AgentCAD variants → Gmsh/OpenFOAM → selected CAD. | Final forced-flow enclosure; fit/access, fan-path comparison at 11 W, convergence/balance and exact final CAD. | Retain; internal guide geometry discretionary; fan definition fixed. |
| PCB-01 | Produce a manufacturable coffee-roaster thermistor interface board from the stated sensor/control requirements. | KiCad schematic/PCB → FreeRouting → KiCad native checks/fabrication export. | One native/fabrication revision; nets, pinout, outline, ERC/DRC, routing, BOM and Gerbers/drill. | Retain; placement/routing discretionary inside fixed circuit/interfaces. |
| PCB-02 | Produce a dual pressure-sensor filter board with the required channels and filtering interfaces. | KiCad → FreeRouting → KiCad checks/export; routed board returns to KiCad. | One native/fabrication revision; connectivity, channel separation, outline/rules, ERC/DRC and exports. | Retain; placement/routing discretionary. |
| PCB-03 | Produce a fan-tachometer service board that can be assembled and diagnosed. | KiCad → FreeRouting → KiCad checks/export. | One native/fabrication revision; fan/tach/service nets, outline/rules, ERC/DRC, BOM and fabrication data. | Retain; placement/routing discretionary. |
| HEAT-01 | Design the lightest practical conduction strap that keeps a silent e-ink sign controller within its temperature limit. | AgentCAD candidates → OASiS/scikit-fem → selected exact STEP. | Final strap CAD/STEP and thermal package; interfaces, material, temperature, mass/space, heat balance and mesh comparison. | Improve; fixed thermal/interface basis retained, cross-artifact identity strengthened. |
| HEAT-02 | Design a thermal link from an inspection camera to a cooled frame without violating the camera/frame interfaces. | AgentCAD candidates → OASiS/scikit-fem → selected exact STEP. | Final link package; interface/keepout, cold-wall boundary, temperature/gradient, mass and numerical checks. | Improve; geometry choices discretionary within fixed interfaces. |
| HEAT-03 | Design a copper calibration-lamp heat link while explicitly accounting for contact resistance. | AgentCAD candidates → OASiS/scikit-fem → selected exact STEP. | Final copper-link package; contact model, geometry/material, temperature, heat balance and mesh sensitivity. | Improve; contact basis fixed, geometry discretionary. |
| JIG-01 | Produce a repeatable two-hole furniture-rail jig that is ready to print and fit with bushings. | AgentCAD → governed DXF/dimension checks → Bambu Studio; exact final STL is sliced. | Native CAD, STEP/STL, hole DXF and 3MF; datums, two hole centers, bushing seats, clearances, topology and slice. | Improve; approve additive manufacture as the intended process; physical fit pending. |
| JIG-02 | Produce a top-face drilling saddle for rectangular extrusion with four controlled holes and chip access. | AgentCAD → governed checks → Bambu Studio. | Native CAD, STEP/STL, hole DXF and 3MF; fences, four centers, chip window, bushings, clearances and slice. | Improve; approve additive manufacture and fixed workpiece/process envelope. |
| JIG-03 | Produce a keyed six-hole jig for an indexable circular fixture plate. | AgentCAD → governed checks → Bambu Studio. | Native CAD, STEP/STL, hole DXF and 3MF; key/datum, six centers, bushings, clamp cutouts and slice. | Improve; approve additive manufacture and fixed workpiece/process envelope. |
| HARNESS-01 | Design an assembly-ready desktop-incubator fan/sensor harness with unambiguous connectors and acceptable voltage drop. | Component records → WireViz → released pin/net table → KiCad interconnect/ERC cross-check. | WireViz/KiCad source, diagram, BOM, cut list and verification report; pins, wire sizing/drop, bend/service and connector separation. | Improve; approve KiCad as independent connectivity check; physical crimp/installation pending. |
| HARNESS-02 | Design a long-branch growth-rack ventilation harness that cannot be cross-connected during service. | Component records → WireViz → pin/net table → KiCad cross-check. | Final assembly package; long-run voltage drop/derating, labels, captive routing, reach, pins and ERC. | Improve; approve KiCad handoff and governed reach assumptions. |
| HARNESS-03 | Design a dual-zone air-sampler harness with shielded pressure pairs and zone-proof service connections. | Component records → WireViz → pin/net table → KiCad cross-check. | Final assembly package; pins, shielding, drop/derating, 40 mm bend radius, zone separation, labels and ERC. | Improve; approve KiCad handoff; EMC/physical installation pending. |
| SHEET-01 | Produce a supplier-ready bent-aluminum wall dock for a barcode reader. | Solid Edge folded/native → flat DXF → AutoCAD MCP headless DXF review → supplier-rule report. | PSM, STEP, flat/review DXF and DFM evidence; reader/cable clearance, bends, slots, notch, material/thickness and flat/folded correspondence. | Improve; approve independent headless DXF stage, not desktop AutoCAD; supplier acceptance pending. |
| SHEET-02 | Produce a supplier-ready four-bend cable trough for a test-station frame. | Solid Edge → flat DXF → AutoCAD MCP headless review → supplier rules. | PSM, STEP, flat/review DXF and DFM evidence; spans, 45 mm clear depth, four bends, returns, slots and flat/folded identity. | Improve; no end-cap, welding or grounding claim. |
| SHEET-03 | Produce a supplier-ready two-piece instrumentation chassis while preserving styled cutouts and service clearance. | Solid Edge base/lid → two flat DXFs → AutoCAD MCP headless review → supplier rules. | Two native/folded/flat part sets and DFM evidence; 80 mm exterior/75 mm keepout decision, cutouts, vents, clearances and identity. | Improve; existing conflict resolution retained; supplier acceptance pending. |
| WATER-01 | Design a compact single-cup brewer thermal package, not merely pick a heater setting. | OpenModelica transient selection → AgentCAD vessel/heater/insulation CAD → OASiS/scikit-fem thermal screen. | Study plus final CAD/STEP/thermal package; 0.350 kg, 20→90 °C in ≤180 s, energy/numerics, envelope, contact and hot-surface/gradient limits. | Expand. Add governed heater interface, materials, insulation, mounting/keepouts and temperature limits; no electrical/food/pressure claim. |
| WATER-02 | Design a portable field-brewer thermal package that respects inverter and usable battery energy. | OpenModelica power/energy selection → AgentCAD packaged design → OASiS/scikit-fem thermal screen. | Study plus final CAD/STEP/thermal package; 0.600 kg, ≤360 s, ≤800 W inverter, declared battery budget, envelope/contact and temperature limits. | Expand. Add governed component envelopes/interfaces/materials; battery safety and physical runtime remain pending. |
| WATER-03 | Design a pilot batch-dispenser thermal package robust to the declared heat-loss range. | OpenModelica 9-case grid → AgentCAD vessel/heater/insulation CAD → OASiS/scikit-fem thermal screen. | Study plus final CAD/STEP/thermal package; 1.5 kg, ≤400 s, power/loss grid, numerical stability, envelope/contact and temperature limits. | Expand. Add governed physical-design requirements; no pressure/food/certification claim. |
| ROBOT-01 | Diagnose a cart tracking disturbance at a measured floor joint, then design a transition cover that reduces the geometric step while carrying wheel load. | ROSBag analysis + independent seam survey → AgentCAD transition CAD → CalculiX static/contact-load approximation. | Diagnosis, editable transition design, STEP/drawing, FEA and installation/test plan; preserve non-causal log conclusion, then check fit, slope/clearance, wheel load, stress/deflection and anchors. | Expand. Add independent seam profile, traffic/interface/load/anchor requirements. Robot 010 stays historical/pending. |
| ROBOT-02 | Commission an external tracking station by correcting time/frame calibration and designing a stable, adjustable calibration-target mount. | ROSBag time/frame analysis → approved calibration transform/config → AgentCAD mount/target CAD → CalculiX stiffness check. | Calibration/config evidence plus mount CAD/STEP/drawing and FEA; timing/transform residuals, adjustment range, line-of-sight, interface, load and deflection. | Expand. Add tracker/mount survey, target/FOV, adjustment and load requirements. Do not pretend the mount itself fixes clock offset. |
| ROBOT-03 | Diagnose external-pose loss behind a tote and design a raised cart fiducial mast that restores the governed visibility envelope. | ROSBag gap/occlusion analysis + independent visibility envelope → AgentCAD mast CAD → CalculiX inertial/static check. | Diagnosis, mast CAD/STEP/drawing, FEA and commissioning plan; preserve missing data, check line-of-sight, cart interface, height/keepout, mass, stress and deflection. | Expand. Add target geometry, camera/obstacle envelope, cart interface and inertial-load requirements. On-cart confirmation remains pending. |

## Fixed requirements versus permitted design choices

Across all cases, user/site interfaces, loads, temperatures, electrical nets,
materials when specified, coordinate frames, manufacturing limits and acceptance
methods are fixed inputs. Wright may choose shape, topology, placement/routing,
vent pattern, support orientation or other explicitly named design variables. It
may not silently change a fixed requirement to obtain a pass.

The six expanded jobs need new independently authored synthetic inputs before
implementation:

- Water: selected component envelopes, vessel/heater contact, material and
  insulation stack, mounting/keepouts, allowable wall/hotspot/gradient limits and
  the exact claim boundary.
- Robot 01: measured seam profile, allowable ramp/slope/height, traffic envelope,
  wheel/contact load, anchoring and floor interface.
- Robot 02: tracker and wall/stand interfaces, survey datum, calibration target,
  field-of-view, adjustment range, loads and permissible residuals.
- Robot 03: cart mounting interface, fiducial target, camera/obstacle visibility
  envelope, height/keepout/mass limits and inertial load case.

These will be clearly labeled fictional campaign requirements, not measurements
inferred from the existing recordings. The concrete proposed values and permitted
design choices are in `campaign-example-renewal-engineering-input-proposal.md`
and its JSON companion. R2 must not begin by guessing or changing them.

## Tool feasibility and honest naming

- Reuse the currently bound/pinned versions where available; capture exact current
  version/digest and service identity during implementation preflight.
- Bambu Studio is a new downstream application for the three jig jobs, but is
  already used by the printed-part family.
- KiCad is a new independent connectivity checker for the harness family. It
  consumes a released pin/net table; it does not replace WireViz or constitute a
  physical continuity test.
- The sheet-metal second stage is specifically the U-C4N **AutoCAD MCP Pro**
  headless DXF backend demonstrated in clean-container evidence. It must be labeled
  as headless DXF processing, not as licensed desktop AutoCAD automation.
- The water and Robot extensions reuse current OpenModelica, ROSBag, AgentCAD,
  OASiS/scikit-fem and CalculiX capabilities, but their new cross-tool handoffs are
  unqualified until R3.
- MATLAB/Simulink, Isaac Sim and other unavailable licensed/GPU hosts are not part
  of this lineup.

## Exact approval requested

Approval of this R1 proposal means:

1. Use this exact set of 30 jobs and target 30 design-package outcomes (minimum
   acceptance remains 24 if a genuine implementation blocker later requires an
   explicitly reviewed exception).
2. Preserve all original evidence and retain the original Robot/Modelica stages,
   but prospectively expand the six scenarios as described.
3. Adopt the proposed numerical water and Robot inputs in
   `campaign-example-renewal-engineering-input-proposal.md`, author them as
   synthetic-but-governed scenario sources, subject them to normal source review,
   and never infer or revise them from candidate outputs or logs.
4. Add the three cross-family application handoffs: jig→Bambu Studio,
   WireViz→KiCad, and Solid Edge flat DXF→headless AutoCAD MCP review.
5. Proceed to R2 only after this decision; implementation and isolated
   qualification may discover a real blocker, but must report it rather than
   substitute a fake tool or weaken requirements.

The machine-readable companion is
`campaign-example-renewal-lineup.json`; the supporting read-only capability check
is `campaign-example-renewal-feasibility.md`. Approval is recorded in
`campaign-example-renewal-decision.md` and `.json`.
