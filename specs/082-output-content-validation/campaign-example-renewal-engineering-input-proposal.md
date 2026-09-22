# Proposed engineering inputs for the six expanded examples

Date: 21 September 2026. R1 status: **approved on 22 September 2026**.

These values close the remaining engineering-authority gap in the three water
and three Robot examples. They are approved prospective fictional campaign
requirements, not observed customer facts, standards claims, physical
measurements, or results inferred from a candidate design.

## Common governance

- Preserve every original input, test, attempt and result. Add a prospective
  scenario revision instead of editing historical evidence.
- The input package, not the AI-generated candidate, owns these requirements.
- Use SI units in calculations and show engineer-facing units in outputs.
- A failed requirement remains a failure or a reviewed redesign; do not change a
  limit to obtain green status.
- Digital checks do not authorize mains wiring, heating, robot operation, floor
  drilling, fabrication, installation, purchasing or certification.

## Water 01 — single-cup brewer thermal package

The existing 0.350 kg, 20→90 °C, 180 s Modelica requirement and 350/500/700 W
candidate set remain fixed. A lumped-model preflight predicts 700 W is the only
candidate meeting 180 s, but that is not a baseline answer: the actual pinned
Modelica run must select the power.

| New fixed input | Proposed value |
| --- | --- |
| Useful vessel geometry | 76 mm internal diameter; at least 77 mm useful liquid depth; 15 mm minimum freeboard |
| Product envelope | 120 mm maximum outside diameter × 155 mm maximum height |
| Vessel | 304 stainless steel; 0.8 mm cylindrical wall; 1.0 mm base; thermal conductivity 16 W/(m·K) |
| Heater carrier | 6061-T6 aluminum; 70 mm maximum contact diameter; thermal conductivity 167 W/(m·K) |
| Insulation design range | 8–15 mm; isotropic conductivity 0.040 W/(m·K) for this synthetic screen |
| Interfaces | Heater centered within 0.5 mm of vessel axis; three M4 chassis mounts on 96 mm bolt circle; 8 mm radial wiring keepout at carrier edge |
| Thermal cases | Case A: selected Modelica power through heater contact with water-side boundary supplied by the 90 °C endpoint. Case B: 90 °C wetted wall/base with 20 °C ambient and 12 W/(m²·K) effective external film coefficient. |
| Limits | Heater-carrier peak ≤180 °C in Case A; accessible outer shell peak ≤60 °C in Case B; no insulation overlap with vessel, heater, mounts or wiring keepout |
| Package mass | ≤0.75 kg dry for vessel, carrier, insulation and outer shell |

Wright may choose carrier thickness/profile, insulation thickness in the allowed
range, shell wall and non-interface styling. It may not change fill volume,
power candidates, envelope, material properties, interfaces or limits.

## Water 02 — battery-limited field brewer thermal package

The existing 0.600 kg, 20→90 °C, 360 s requirement, 400/600/800 W candidates,
800 W inverter limit and 70 Wh battery-side planning target remain fixed. A
lumped preflight predicts 600 W is the lowest time-compliant candidate and about
67.5 Wh battery-side after the declared 0.88 inverter efficiency; native results
remain authoritative.

| New fixed input | Proposed value |
| --- | --- |
| Useful vessel geometry | 100 mm internal diameter; at least 76 mm useful liquid depth; 20 mm minimum freeboard |
| Product envelope | 155 × 155 × 190 mm maximum, excluding removable carry handle |
| Vessel/carrier | 304 stainless vessel, 0.8 mm wall and 1.0 mm base, k=16 W/(m·K); 6061-T6 carrier, 92 mm maximum heater-contact diameter, k=167 W/(m·K) |
| Insulation design range | 10–20 mm, k=0.040 W/(m·K) for this synthetic screen |
| Interfaces | Four M4 base mounts on 118 × 118 mm pattern; 35 × 20 × 15 mm cable-exit keepout; removable handle interfaces 120 mm apart |
| Thermal cases | Same two-case method as Water 01, using the actual selected power and this scenario's 20 °C ambient/90 °C endpoint |
| Limits | Heater-carrier peak ≤180 °C; handle interface ≤50 °C; other accessible outer shell ≤65 °C; no keepout/interference violation |
| Package mass | ≤1.25 kg dry, excluding the separately modeled fictional battery/inverter |

Wright may choose carrier/shell geometry, insulation thickness and handle shape.
Battery chemistry, inverter, wiring, protection and physical runtime are outside
the digital package and remain explicit release blockers.

## Water 03 — pilot batch-dispenser thermal package

The existing 1.500 kg, 20→90 °C, 400 s requirement, 1200/1500/1800 W candidates
and low/nominal/high UA grid remain fixed. A lumped preflight predicts 1500 W is
the lowest candidate meeting 400 s in all three loss cases; the actual nine native
runs and numerical refinement remain authoritative.

| New fixed input | Proposed value |
| --- | --- |
| Useful vessel geometry | 140 mm internal diameter; at least 97 mm useful liquid depth; 25 mm minimum freeboard; atmospheric vent path at least 80 mm² |
| Product envelope | 225 × 225 × 270 mm maximum, including vented lid but excluding the non-modeled dispensing tube |
| Vessel/carrier | 304 stainless vessel, 1.0 mm wall and 1.2 mm base, k=16 W/(m·K); 6061-T6 carrier, 128 mm maximum heater-contact diameter, k=167 W/(m·K) |
| Insulation design range | 15–30 mm, k=0.040 W/(m·K) for this synthetic screen |
| Interfaces | Four M5 chassis mounts on 170 × 170 mm pattern; 45 × 25 × 20 mm wiring/terminal keepout; vent cannot intersect insulation or wiring region |
| Thermal cases | Case A at actual selected power and 90 °C water-side boundary. Case B at 90 °C wetted surfaces, 20 °C ambient, 12 W/(m²·K) external film; screen nominal and high-loss packaging interpretations without changing Modelica UA values. |
| Limits | Heater-carrier peak ≤200 °C; accessible outer shell ≤70 °C; vent and all keepouts clear; no closed or pressure-bearing volume |
| Package mass | ≤3.0 kg dry for the modeled package |

Wright may choose carrier/shell geometry and insulation thickness. The result is
not a pressure-vessel, food-contact, potable-water, sterilization, electrical or
regulatory design.

## Robot 01 — floor-seam transition

The existing recording remains a diagnosis input only. It may correlate the
tracking disturbance with the annotated crossing, but it does not prove the seam
caused the disturbance. The following independent fictional survey defines the
design job.

| New fixed input | Proposed value |
| --- | --- |
| Surveyed joint | 20 mm open width; 6 mm floor-height difference; straight across the 1.5 m test lane; survey tolerance ±0.5 mm |
| Cart/interface | 32 kg unloaded cart; 75 mm wheel radius; 420 mm track; 560 mm maximum outside wheel width |
| Transition envelope | Full lane width 1500 mm; travel-direction length ≤260 mm; installed protrusion outside ramp ends ≤1.5 mm |
| Ramp geometry | Maximum slope 1:15; no local upward step >2 mm in the wheel paths; central 600 mm wheel band free of fastener heads |
| Material | 6061-T6 aluminum, E=69 GPa, ν=0.33, density 2700 kg/m³; allowable von Mises stress 95 MPa |
| Structural case | 400 N downward wheel-patch load over 30 × 20 mm at the worst supported location; floor support and fastener conditions must be stated and sensitivity checked |
| Limits | Deflection ≤0.5 mm under the design load; part mass ≤4.0 kg; six M6 countersunk anchor zones outside the central wheel band |

Wright may choose plate section, ribs and anchor-zone placement within the fixed
constraints. Installation, trip-risk acceptance, anchor selection and a repeated
robot run remain human/physical work.

## Robot 02 — tracking-station calibration and adjustable mount

The original survey transform and +150 ms header offset remain the evidence for
the configuration correction. The mechanical mount does not repair the clock;
the final package contains both a corrected calibration configuration and a
separately verified stable mount.

| New fixed input | Proposed value |
| --- | --- |
| Tracker | 1.2 kg; center of mass 120 mm from mounting wall in nominal position; 100 × 80 mm base envelope |
| Wall interface | Four M6 holes on 80 × 60 mm rectangular pattern; survey datum at pattern center; no wall/floor modification in the workflow |
| Adjustment | Yaw ±10°, pitch ±10°, vertical ±25 mm; scales/resolution ≤0.5° and ≤2 mm |
| View/target | Preserve unobstructed 60° horizontal × 45° vertical cone; provide a 200 × 200 mm planar calibration-target drawing referenced to the survey datum |
| Material/load | 6061-T6 aluminum with the properties/95 MPa allowable above; independently apply 50 N in each principal direction at the tracker center of mass |
| Mechanical limits | Tracker-point deflection ≤0.25 mm in each load case; mount mass ≤0.8 kg; adjustment locks must remain inside the view cone keepout |
| Calibration limits | Apply x_map=x_tracker−1.000 m, y_map=y_tracker+2.000 m and −0.150 s timestamp correction exactly once; aligned check residual ≤10 mm position, ≤0.5° yaw and ≤10 ms timing on the supplied synthetic data |

Wright may choose bracket topology and adjustment mechanism. It may not adjust
the supplied transform/clock correction to hide residuals or claim the mount
itself fixes time alignment. Physical survey and commissioning remain pending.

## Robot 03 — occlusion-resistant cart fiducial mast

The missing 14.0–16.0 s samples remain missing evidence. The following independent
fictional interface/visibility envelope turns the observation into a bounded
corrective-design job without filling the gap.

| New fixed input | Proposed value |
| --- | --- |
| Cart deck | Deck height 450 mm above floor; four M6 holes on 100 × 80 mm pattern; 220 × 180 mm clear mounting footprint |
| Fiducial target | 160 × 160 × 6 mm plate; 0.25 kg including marker; target plane normal horizontal in nominal position |
| Occluder envelope | Tote top 950 mm above floor in the annotated event zone; target bottom must be at least 100 mm above that top in nominal running position |
| Height/keepout | Target-center adjustment 1130–1230 mm above floor; total assembly height ≤1320 mm; assembly must stay inside 240 × 200 mm horizontal envelope |
| Material/load | 6061-T6 aluminum with the properties/95 MPa allowable above; 50 N horizontal design load at target center in either cart transverse direction |
| Limits | Target-center deflection ≤2.0 mm; mast/package mass ≤1.2 kg; no interference with the supplied cart keepout or marker face |
| Visibility check | The complete target outline must remain above the governed tote envelope for the event-zone side views; this geometric check is not a claim of camera detection probability |

Wright may choose mast section, adjustment mechanism and target bracket. Actual
camera visibility, vibration, robot dynamics and a repeated figure-eight run
remain pending.

## Required prospective source files

R2 should encode these agreed values as small engineer-readable CSV/Markdown
inputs beside each scenario, with provenance `synthetic_reviewed_requirement`:

- Water: `physical-design-requirements.csv`, `materials.csv`,
  `component-interfaces.csv`, and `thermal-screening-cases.csv`.
- Robot 01: `site-survey.csv`, `cart-interface.csv`, and
  `transition-design-requirements.csv`.
- Robot 02: `tracker-interface.csv`, `mount-design-requirements.csv`, and
  `calibration-acceptance.csv`.
- Robot 03: `cart-interface.csv`, `visibility-envelope.csv`, and
  `mast-design-requirements.csv`.

The machine-readable companion is
`campaign-example-renewal-engineering-input-proposal.json`.
