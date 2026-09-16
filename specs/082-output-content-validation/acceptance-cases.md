# Acceptance and expansion map

The [earlier 30-case seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md) retain the detailed source analysis. They are requirement seeds, not observed results or complete frozen profiles. Canonical IDs come from `tests/datasets/engineering-workflows/scenarios/**/scenario.json`.

## Version 1 process demonstrations

| Demonstration | Required evidence |
|---|---|
| Local structured output | Ordinary AI creates JSON/CSV with a controlled defect; local reader identifies field/row, expected/observed and owner; AI consumes feedback, writes a new revision, validator passes, consumer receives only the new revision. |
| CAD/MCP output | Jig-producing AI/MCP task creates a deliberately wrong seat location in an isolated example; actual geometry is measured; feedback references feature/datum/tolerance; new CAD revision passes revalidation and releases the consumer. |
| Numerical output | Heat-01 actual candidate/refined fields and balance data are read independently; valid/defective controls exercise the declared analytical/refinement/selection checks; results feed the same report contract. |

A real configured AI must consume the correction packet for the first two demonstrations. An injected fixture can establish the initial failure deterministically, but record that setup honestly. Do not call a hardcoded replacement response a real AI repair. Record tool/model availability and missing prerequisites precisely.

### Initial engineering scopes

**Jig-01:** Start with the bushing-seat location and diameter scope: H1=(30,30), H2=(170,30) mm, ±0.20 mm per axis in the workpiece datum; a 10.0 mm body plus 0.20 mm diametral clearance gives a 10.20 mm seat. Qualify actual circular-center measurement, datum transform, unit/clearance errors and missing features. A pass for these checks is not acceptance of every clamp/fit/manufacturing requirement; publish excluded scope.

**Heat-01:** Start with the simplified conduction sizing scope: both 40/60 mm candidates, actual baseline/refined fields, 4 W, k=200 W/(m·K), 25°C cold boundary, independent analytical temperature-rise comparison, 1% balance and 2% analytical-rise/refinement checks as supported by the current source, and the 45°C selection requirement. The earlier analytical seed predicts about 50°C/41.667°C and selection of 60 mm; rederive from current dimensions and baseline before freezing. An analytical table is not a solver field. This does not establish physical thermal qualification or all CAD/manufacturing requirements.

Read [jig center guidance](../081-engineering-workflow-templates/dataset-campaign/jig-circle-center-guidance.md) and [heat retained-result notes](../081-engineering-workflow-templates/dataset-campaign/heat-native-result-inspection.md). Profile extraction at T023 controls final source-derived methods; do not silently apply an unapproved numerical tolerance.

## All 30 packs: reusable capability map

Each family has cases 01, 02 and 03. T002/T029 reconcile all canonical manifest IDs and sources; no family is silently dropped.

| Family | Reusable capabilities and distinctive constraints | Version 1 / expansion |
|---|---|---|
| printed-replacement-part | Geometry/fit, D-socket/scallops, finger clearance, wedge orientation, slice/material correspondence | Basic geometry reused; full manufacturing/slicer inspection later |
| raspberry-pi-enclosure | Geometry/keepouts, manufacturer interface authority, field/thermal alternatives, fan-curve lineage | Geometry/numerical contracts reused; CFD/source-specific readers later |
| sheet-metal-supplier-handoff | Native/STEP/DXF correspondence, bends/true flats, multipart/quantity completeness, scoped R1/R3/R4 decisions | Generic completeness reusable; native flattening/manufacturing reader later |
| lightweight-equipment-bracket | Geometry/load/restraint identity, fields/reactions/stress/displacement, mesh comparison | Shared geometry/field contracts; FEA-specific reductions later |
| parametric-drill-jig | Datums, seat coordinates/diameters, clearances, keys and clamp exclusions | Jig-01 bounded seat scope now; siblings/full-profile expansion later |
| robot-tracking-diagnosis | CSV/time/frame transforms, masks, metrics and hypothesis evidence | Structured readers now; time-series/diagnosis checks later |
| heat-spreader-sizing | Field/balance/refinement, analytical reference and candidate selection | Heat-01 bounded conduction scope now; siblings/interface-resistance extension later |
| sensor-fan-harness | Connectivity graph, shared trunk currents, voltage drop and cut lengths | Structured/numeric foundation; network-specific checks later |
| sensor-interface-pcb | Exact nets/values, coordinates, power rules, ERC/DRC/native/fab correspondence | Graph/native ECAD readers later; ERC success alone insufficient |
| water-heater-sizing | Approved model/parameters, time integration, target crossing, energy and candidate grids | Numeric foundation; Modelica-specific readers later |

Support states are capability-level `implemented`, `qualified`, `planned` or `unavailable`, with named limitations. Requested mandatory unsupported checks return blocked. A profile cannot declare itself fully supported by silently removing required checks.

Preserve current Modelica derivative and 2 K thermostat/energy semantics, Pi source authority and exact sheet-metal amendment scopes when expanding. No all-30 evaluation or campaign counter changes belong to this initial goal.

## Validator correctness and process reliability

Use independent valid, alternative and targeted invalid controls; defects must reach the intended checker, not merely fail file parsing. Test numerical boundaries/uncertainty, stale hashes, foreign producer output, missing required roles, safe native cleanup, mixed failure/error, authenticated pending review, no-progress/budget exhaustion and resume without budget reset.

A report consumer must reproduce the persisted verdict/values by assessment ID. A newer error or incomplete output cannot inherit an older pass. These are tests of the product; they do not replace the required process demonstrations.
