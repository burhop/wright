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

The machine-readable authority is packaged as `process_validation/profiles/coverage.json` version 2. `qualified` means a frozen bounded profile, independent controls and a retained canonical process demonstration exist. `implemented` means a reusable reader exists but the named pack has no qualified profile. `planned` means the extension recipe is defined but incomplete. `unavailable` means there is currently no trustworthy bounded reader. A scenario is `unsupported` unless all capabilities in its declared bounded profile are qualified; a generic reader does not make the scenario pass-ready.

### Reconciled pack status

| Canonical pack | Scenario status | Capability status | Qualified scope or blocking reason |
|---|---|---|---|
| heat-spreader-sizing-01 | qualified | thermal.conduction=qualified, numerical.refinement=qualified | 40/60 mm conduction fields, analytical rise, heat balance, refinement and 45°C selection only. |
| heat-spreader-sizing-02 | unsupported | thermal.conduction=planned, numerical.refinement=planned | No frozen scenario profile; mandatory requests block until both recipes are implemented and qualified. |
| heat-spreader-sizing-03 | unsupported | thermal.conduction=planned, numerical.refinement=planned | No frozen scenario profile; mandatory requests block until both recipes are implemented and qualified. |
| lightweight-equipment-bracket-01 | unsupported | geometry=planned, structural.fields=unavailable | No frozen profile or qualified structural-field reader. |
| lightweight-equipment-bracket-02 | unsupported | geometry=planned, structural.fields=unavailable | No frozen profile or qualified structural-field reader. |
| lightweight-equipment-bracket-03 | unsupported | geometry=planned, structural.fields=unavailable | No frozen profile or qualified structural-field reader. |
| parametric-drill-jig-01 | qualified | geometry=qualified, fit.datum=qualified | H1/H2 seat centers and diameters in the frozen workpiece datum only. |
| parametric-drill-jig-02 | unsupported | geometry=planned, fit.datum=planned | No frozen scenario profile; the jig-01 selectors cannot be assumed to cover this pack. |
| parametric-drill-jig-03 | unsupported | geometry=planned, fit.datum=planned | No frozen scenario profile; the jig-01 selectors cannot be assumed to cover this pack. |
| printed-replacement-part-01 | unsupported | geometry=planned, manufacturing.slice=unavailable | No frozen profile or qualified slicer/toolpath reader. |
| printed-replacement-part-02 | unsupported | geometry=planned, manufacturing.slice=unavailable | No frozen profile or qualified slicer/toolpath reader. |
| printed-replacement-part-03 | unsupported | geometry=planned, manufacturing.slice=unavailable | No frozen profile or qualified slicer/toolpath reader. |
| raspberry-pi-enclosure-01 | unsupported | geometry=planned, source.authority=unavailable, thermal.cfd=unavailable | Manufacturer-authority and CFD readback are unavailable. |
| raspberry-pi-enclosure-02 | unsupported | geometry=planned, source.authority=unavailable, thermal.cfd=unavailable | Manufacturer-authority and CFD readback are unavailable. |
| raspberry-pi-enclosure-03 | unsupported | geometry=planned, source.authority=unavailable, thermal.cfd=unavailable | Manufacturer-authority and CFD readback are unavailable. |
| robot-tracking-diagnosis-01 | unsupported | structured=implemented, timeseries.frames=planned | Generic CSV/JSON inspection exists; pack-specific clock/frame semantics and profile are not qualified. |
| robot-tracking-diagnosis-02 | unsupported | structured=implemented, timeseries.frames=planned | Generic CSV/JSON inspection exists; pack-specific clock/frame semantics and profile are not qualified. |
| robot-tracking-diagnosis-03 | unsupported | structured=implemented, timeseries.frames=planned | Generic CSV/JSON inspection exists; pack-specific clock/frame semantics and profile are not qualified. |
| sensor-fan-harness-01 | unsupported | structured=implemented, electrical.network=unavailable | Generic structured inspection exists; no qualified connectivity/current/drop reader. |
| sensor-fan-harness-02 | unsupported | structured=implemented, electrical.network=unavailable | Generic structured inspection exists; no qualified connectivity/current/drop reader. |
| sensor-fan-harness-03 | unsupported | structured=implemented, electrical.network=unavailable | Generic structured inspection exists; no qualified connectivity/current/drop reader. |
| sensor-interface-pcb-01 | unsupported | electrical.netlist=unavailable, manufacturing.ecad=unavailable | No qualified native netlist or PCB/fabrication correspondence reader. |
| sensor-interface-pcb-02 | unsupported | electrical.netlist=unavailable, manufacturing.ecad=unavailable | No qualified native netlist or PCB/fabrication correspondence reader. |
| sensor-interface-pcb-03 | unsupported | electrical.netlist=unavailable, manufacturing.ecad=unavailable | No qualified native netlist or PCB/fabrication correspondence reader. |
| sheet-metal-supplier-handoff-01 | unsupported | geometry=planned, manufacturing.sheet_metal=unavailable, bundle=planned | No qualified native flat-pattern reader or frozen cross-format bundle profile. |
| sheet-metal-supplier-handoff-02 | unsupported | geometry=planned, manufacturing.sheet_metal=unavailable, bundle=planned | No qualified native flat-pattern reader or frozen cross-format bundle profile. |
| sheet-metal-supplier-handoff-03 | unsupported | geometry=planned, manufacturing.sheet_metal=unavailable, bundle=planned | No qualified native flat-pattern reader or frozen cross-format bundle profile. |
| water-heater-sizing-01 | unsupported | numerical.timeseries=planned, modelica.model=unavailable | No qualified trajectory reader or Modelica semantic/runtime inspection. |
| water-heater-sizing-02 | unsupported | numerical.timeseries=planned, modelica.model=unavailable | No qualified trajectory reader or Modelica semantic/runtime inspection. |
| water-heater-sizing-03 | unsupported | numerical.timeseries=planned, modelica.model=unavailable | No qualified trajectory reader or Modelica semantic/runtime inspection. |

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

### Extension recipes

Every new pack starts by freezing all mandatory requirements, exact source locators and exclusions. It then binds actual candidate revisions, implements bounded readback, and qualifies valid, alternative, targeted-defect and inclusive-boundary controls before changing `support` to `qualified`. The packaged support map contains exact prerequisites and steps for every capability. The family-specific work is:

| Capability | Required extension |
|---|---|
| geometry / fit.datum | Define semantic features, datum transforms, units and tolerances; inspect every mandatory feature in the actual candidate; qualify missing/topology/datum/clearance defects. |
| manufacturing.slice | Bind model revision, material and slicer settings; read layers/toolpaths; check orientation, print clearance and source/output correspondence. |
| source.authority | Pin versioned manufacturer sources and locators; define conflict/staleness policy; block unavailable or inconsistent authority. |
| thermal.cfd | Bind geometry, mesh, materials, loads and boundaries; read fields; independently check balance, convergence and requirement quantities. |
| manufacturing.sheet_metal / bundle | Bind formed, native-flat, STEP, DXF and inventory revisions; inspect bends/reliefs/thickness and exact multipart/quantity correspondence. |
| structural.fields | Bind geometry, material, load, restraint and mesh; read reactions/stress/displacement fields; check equilibrium, convergence and wrong-boundary controls. |
| structured / timeseries.frames | Freeze JSON/CSV selectors plus unit, clock, mask and frame rules; derive metrics from raw samples; qualify duplicate, offset, dropout and transform defects. |
| electrical.network | Read the actual endpoint/splice graph and wire properties; independently compute shared currents, voltage drop and cut lengths. |
| electrical.netlist / manufacturing.ecad | Read native nets, values, footprints and coordinates; bind native PCB to Gerber/drill/BOM revisions; test wrong content despite clean ERC/DRC. |
| thermal.conduction / numerical.refinement | Freeze dimensions, loads, conductivity and boundaries; bind coarse/fine fields; independently compute analytical rise, balance and sensitivity. |
| numerical.timeseries / modelica.model | Inspect approved equations, parameters and derivative semantics; bind the compiled trajectory; independently check integration, crossings, energy and candidate grids. |

Changing a status requires updating the generated map, adding the frozen profile and readers to the installed package, linking qualification evidence, and passing `test_process_validation_coverage.py`. Copying a sibling profile or observing a tool success flag is insufficient.

## Validator correctness and process reliability

Use independent valid, alternative and targeted invalid controls; defects must reach the intended checker, not merely fail file parsing. Test numerical boundaries/uncertainty, stale hashes, foreign producer output, missing required roles, safe native cleanup, mixed failure/error, authenticated pending review, no-progress/budget exhaustion and resume without budget reset.

A report consumer must reproduce the persisted verdict/values by assessment ID. A newer error or incomplete output cannot inherit an older pass. These are tests of the product; they do not replace the required process demonstrations.
