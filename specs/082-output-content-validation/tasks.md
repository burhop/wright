# Tasks: Engineering Output Content Validation

**Input**: [spec.md](spec.md), [plan.md](plan.md), adopted design/model/contracts and [case seeds](acceptance-cases.md).
**Status**: All 74 implementation checkpoints unstarted. Current preparation is not a G0 pass.
**Tests**: Explicitly required by the specification. Add meaningful tests before implementation of their behavior; prove targeted defects reach the intended check.
**Format**: T### is the execution checkpoint; CV## retains the earlier work-package mapping. [P] means eligible for independent work only after listed prerequisites, with disjoint files and native resources.

## Phase 1: Setup

T001 is the only implementation checkpoint eligible before G0. The new branch and documentation exist, but T002 still requires dependency/runtime reconciliation after activation.

- [ ] T001 Perform the complete bounded read-only G0 audit and save `artifacts/engineering-workflow-validation/evidence/start-gate.json` plus a source-root/cohort manifest, or exact missing prerequisites in `specs/082-output-content-validation/progress.md`; derive all 30 IDs from scenario manifests, use WAL-aware read-only records, hash every selected artifact and reconcile native stability. No new validation code or generation dispatch before pass. (CV01; FR-001)
- [ ] T002 After T001 passes, reconcile selected checkout/dirty identities, existing components, Python/release lanes, reader hosts and authoritative model/binding contracts in `specs/082-output-content-validation/evidence/implementation-baseline.md`; isolate writable runtime roots and ports. (CV02; FR-014/015)

## Phase 2: Foundations

Depends on T001–T002. Keep one owner for shared core, storage and catalog changes. T003 operates one source pack at a time and records all 30 completion rows; it must not be marked done on a pilot subset.

- [ ] T003 Extract all 30 complete source inventories and atomic requirements in `tests/datasets/engineering-workflow-validation/requirements/`, including images, tables, source locators/digests, authorized amendment scope, classifications and candidate coverage; compare each baseline independently with originals. (CV03; FR-002/003/008)
- [ ] T004 Freeze verification methods, tolerance provenance, unit/frame/uncertainty rules, near-zero/bound inclusivity, source-conflict decisions and review rubrics in `tests/datasets/engineering-workflow-validation/requirements/` before reading candidate outcomes; explicitly reconcile heater first crossing versus thermostat/energy horizon. (CV04; FR-003/007)
- [ ] T005 Catalog exactly 30 case profiles and shared capabilities in `tests/datasets/engineering-workflow-validation/catalog.json` and `specs/082-output-content-validation/evidence/reader-matrix.md`; pin supported formats/hosts/licenses, byte/entity/time/memory/concurrency bounds and qualification controls. (CV05; FR-004/008/009/014)
- [ ] T006 Implement pure schema/identity/state/profile contracts in `packages/core/src/core/engineering_output_validation.py` with meaningful tests in `packages/core/tests/test_engineering_output_validation.py` for duplicate IDs, incomplete links, invalid units/frames/tolerances, nonfinite data and explicit legacy states. (CV06; FR-003/007/011)
- [ ] T007 Implement additive ledger/migrations and append-only review/assessment/current-sequence semantics in `packages/data_vault/src/data_vault/engineering_validation_repository.py` with `packages/data_vault/tests/test_engineering_validation_repository.py`; test old DB compatibility, idempotence, terminal retry versus unchanged nonterminal resume, newer non-pass visibility and late-review immutability. (CV07; FR-010/013/014/017)
- [ ] T008 Implement confined capability readers in `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/` and source-root resolution in `packages/workspace_service/src/workspace_service/engineering_output_validation/sources.py`; add `packages/workspace_service/tests/test_engineering_output_validation_readers.py` covering foreign paths, unsafe archives, hashes, format/version limits, bounded resources and disposable native copies/leases. (CV08; FR-005/006/014/015)

## Phase 3: US1 — Measured verdict and two pilots (P1 / MVP)

Depends on foundations. **Independent test**: positive/alternative/defective pilot controls and two retained actual outputs produce reproducible evidence-linked reports without generation or source mutation.

- [ ] T009 [US1] Implement registry-backed evaluation and requirement aggregation in `packages/workspace_service/src/workspace_service/engineering_output_validation/evaluation.py` with `packages/workspace_service/tests/test_engineering_output_validation_evaluation.py`; explicitly preserve evaluator exceptions as error, unjustified legacy skip as inconclusive, known failures with incomplete evaluation, and uncertainty-boundary behavior. (CV09; FR-004/007/011/017)
- [ ] T010 [US1] Implement `packages/workspace_service/src/workspace_service/engineering_output_validation/service.py`, `packages/workspace_service/src/workspace_service/engineering_output_validation/cohort.py`, `packages/workspace_service/src/workspace_service/engineering_output_validation/reviews.py` and thin `scripts/run_engineering_content_validation.py` with `tests/test_engineering_content_validation_campaign.py`; cover audit, lint, validate, status, report, review, cancellation/resume, trace propagation, authenticated reviewer context, CLI exit precedence and no generation/device dispatch. The bootstrap audit becomes a regression fixture; status remains read-only. (CV10; FR-001/010/014/015/017)
- [ ] T011 [US1] Implement one-model JSON/CSV/HTML/JUnit RTM exports in `packages/workspace_service/src/workspace_service/engineering_output_validation/reporting.py` and `packages/workspace_service/tests/test_engineering_output_validation_reporting.py`; reconcile unique requirements, AND dependencies, explicit N/A denominator, mixed fail/error/blocked, stale/late reviews, formula/HTML escaping and exact artifact links. (CV11; FR-011/012/013)
- [ ] T012 [US1] Implement shared geometry/thermal field measurements in `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/thermal_fields.py` and `tests/datasets/engineering-workflow-validation/profiles/heat-spreader-sizing/01.json`; inspect real fields, boundary/load/material identities, analytical temperature rise, heat balance and refinement. (CV12; FR-005/006/007/009)
- [ ] T013 [US1] Implement shared STEP/mesh/DXF feature measurement in `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/geometry.py` and `tests/datasets/engineering-workflow-validation/profiles/parametric-drill-jig/01.json`; check original datum, seat diameter/centers, flange/clamp exclusions and circular arc-center versus curve-point regression. (CV13; FR-005/006/007/009)
- [ ] T014 [US1] Qualify both pilots with independently reviewed reference fixtures in `tests/datasets/engineering-workflow-validation/fixtures/heat-spreader-sizing/` and `tests/datasets/engineering-workflow-validation/fixtures/parametric-drill-jig/`, with `packages/workspace_service/tests/test_engineering_output_validation_pilots.py`; accept valid alternatives, detect intended defects, and prove exact/below/above bounds and applicable unit/frame transformations. (CV14; FR-009)
- [ ] T015 [US1] Evaluate frozen retained heat-spreader-sizing-01 and parametric-drill-jig-01 outputs into `artifacts/engineering-workflow-validation/pilots/`; reconcile every requirement and evidence link, prove replay adds no generation run, and record engineering failures separately from checker defects in `specs/082-output-content-validation/progress.md`. (CV15; FR-012/014/016)

**Milestone M2 review**: Show two qualified readers, immutable evidence and traceable real verdicts before family expansion. Follow current human milestone authority.

## Phase 4: US2 — All families (P1)

Depends on T015 and its milestone review. **Independent test per family**: A–E complete, targeted controls prove correct verdicts, and all three real cases have full dispositions. Heat/jig 01 pilot evidence is reused without pretending fixtures are real evaluations.

Each five-task block executes A→B→C→D→E. Profile work marked [P] has disjoint family files; shared readers/assertions and catalog remain single-owner. Within a family, prove one case before expanding siblings. Implement capability-based readers/assertions, never case-ID runtime dispatch.

### heat-spreader-sizing — CV16

- [ ] T016 [P] [US2] A: Freeze heat-spreader-sizing profiles (02/03; retain pilot 01) in `tests/datasets/engineering-workflow-validation/profiles/heat-spreader-sizing/` against T003/T004; preserve all widths, 0.15 K/W total contact resistance with per-candidate area conversion, 2% rise comparison, balance and refinement. (CV16A; FR-002/003/007/008)
- [ ] T017 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/thermal_fields.py` for the actual retained heat-spreader-sizing formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV16B; FR-005/006/015)
- [ ] T018 [US2] C: Compose heat-spreader-sizing rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/thermal.py` and `tests/datasets/engineering-workflow-validation/profiles/heat-spreader-sizing/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV16C; FR-004/006/007/008/011)
- [ ] T019 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/heat-spreader-sizing/` and `packages/workspace_service/tests/test_output_validation_heat_spreader_sizing.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV16D; FR-009)
- [ ] T020 [US2] E: Evaluate retained heat-spreader-sizing cases into `artifacts/engineering-workflow-validation/families/heat-spreader-sizing/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV16E; FR-008/012/016)

### parametric-drill-jig — CV17

- [ ] T021 [P] [US2] A: Freeze parametric-drill-jig profiles (02/03; retain pilot 01) in `tests/datasets/engineering-workflow-validation/profiles/parametric-drill-jig/` against T003/T004; preserve chip/clamp keepouts, flange/body stackup, original coordinate frame, asymmetric key and radial versus diametral clearances. (CV17A; FR-002/003/007/008)
- [ ] T022 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/geometry.py` for the actual retained parametric-drill-jig formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV17B; FR-005/006/015)
- [ ] T023 [US2] C: Compose parametric-drill-jig rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/geometry.py` and `tests/datasets/engineering-workflow-validation/profiles/parametric-drill-jig/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV17C; FR-004/006/007/008/011)
- [ ] T024 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/parametric-drill-jig/` and `packages/workspace_service/tests/test_output_validation_parametric_drill_jig.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV17D; FR-009)
- [ ] T025 [US2] E: Evaluate retained parametric-drill-jig cases into `artifacts/engineering-workflow-validation/families/parametric-drill-jig/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV17E; FR-008/012/016)

### robot-tracking-diagnosis — CV18

- [ ] T026 [P] [US2] A: Freeze robot-tracking-diagnosis profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/robot-tracking-diagnosis/` against T003/T004; preserve raw/bag normalization, translation and +0.150 s correction exactly once, valid masks including 14–16 s dropout, wrapped yaw, independent metrics and grounded diagnosis. (CV18A; FR-002/003/007/008)
- [ ] T027 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/timeseries.py` for the actual retained robot-tracking-diagnosis formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV18B; FR-005/006/015)
- [ ] T028 [US2] C: Compose robot-tracking-diagnosis rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/timeseries.py` and `tests/datasets/engineering-workflow-validation/profiles/robot-tracking-diagnosis/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV18C; FR-004/006/007/008/011)
- [ ] T029 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/robot-tracking-diagnosis/` and `packages/workspace_service/tests/test_output_validation_robot_tracking_diagnosis.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV18D; FR-009)
- [ ] T030 [US2] E: Evaluate retained robot-tracking-diagnosis cases into `artifacts/engineering-workflow-validation/families/robot-tracking-diagnosis/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV18E; FR-008/012/016)

### sensor-fan-harness — CV19

- [ ] T031 [P] [US2] A: Freeze sensor-fan-harness profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/sensor-fan-harness/` against T003/T004; preserve pin/view mapping, topology, shared-trunk simultaneous currents, separate returns/shield, temperature-adjusted resistance, source-backed ratings and cut allowances. (CV19A; FR-002/003/007/008)
- [ ] T032 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/electrical_graph.py` for the actual retained sensor-fan-harness formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV19B; FR-005/006/015)
- [ ] T033 [US2] C: Compose sensor-fan-harness rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/electrical.py` and `tests/datasets/engineering-workflow-validation/profiles/sensor-fan-harness/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV19C; FR-004/006/007/008/011)
- [ ] T034 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/sensor-fan-harness/` and `packages/workspace_service/tests/test_output_validation_sensor_fan_harness.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV19D; FR-009)
- [ ] T035 [US2] E: Evaluate retained sensor-fan-harness cases into `artifacts/engineering-workflow-validation/families/sensor-fan-harness/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV19E; FR-008/012/016)

### sensor-interface-pcb — CV20

- [ ] T036 [P] [US2] A: Freeze sensor-interface-pcb profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/sensor-interface-pcb/` against T003/T004; preserve actual native connectivity, approved centers versus footprint origins, current ERC/DRC, dimensions/clearance, BOM and reopened fabrication correspondence. (CV20A; FR-002/003/007/008)
- [ ] T037 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/ecad.py` for the actual retained sensor-interface-pcb formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV20B; FR-005/006/015)
- [ ] T038 [US2] C: Compose sensor-interface-pcb rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/electrical.py` and `tests/datasets/engineering-workflow-validation/profiles/sensor-interface-pcb/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV20C; FR-004/006/007/008/011)
- [ ] T039 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/sensor-interface-pcb/` and `packages/workspace_service/tests/test_output_validation_sensor_interface_pcb.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV20D; FR-009)
- [ ] T040 [US2] E: Evaluate retained sensor-interface-pcb cases into `artifacts/engineering-workflow-validation/families/sensor-interface-pcb/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV20E; FR-008/012/016)

### printed-replacement-part — CV21

- [ ] T041 [P] [US2] A: Freeze printed-replacement-part profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/printed-replacement-part/` against T003/T004; preserve source/repaired feature fidelity, actual closed meshes, D socket/scallops, mounting/finger clearances, wedge/recess/notch, justified orientation/supports/material and real slice/toolpaths with simulation labels. (CV21A; FR-002/003/007/008)
- [ ] T042 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/manufacturing.py` for the actual retained printed-replacement-part formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV21B; FR-005/006/015)
- [ ] T043 [US2] C: Compose printed-replacement-part rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/geometry.py` and `tests/datasets/engineering-workflow-validation/profiles/printed-replacement-part/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV21C; FR-004/006/007/008/011)
- [ ] T044 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/printed-replacement-part/` and `packages/workspace_service/tests/test_output_validation_printed_replacement_part.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV21D; FR-009)
- [ ] T045 [US2] E: Evaluate retained printed-replacement-part cases into `artifacts/engineering-workflow-validation/families/printed-replacement-part/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV21E; FR-008/012/016)

### lightweight-equipment-bracket — CV22

- [ ] T046 [P] [US2] A: Freeze lightweight-equipment-bracket profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/lightweight-equipment-bracket/` against T003/T004; preserve actual deck/mesh/field lineage, exact load vectors and reactions, protected geometry, mass targets, fixed stress region, <=120 MPa, <=0.50 mm and <5% refinement response change. (CV22A; FR-002/003/007/008)
- [ ] T047 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/fea_fields.py` for the actual retained lightweight-equipment-bracket formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV22B; FR-005/006/015)
- [ ] T048 [US2] C: Compose lightweight-equipment-bracket rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/structural.py` and `tests/datasets/engineering-workflow-validation/profiles/lightweight-equipment-bracket/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV22C; FR-004/006/007/008/011)
- [ ] T049 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/lightweight-equipment-bracket/` and `packages/workspace_service/tests/test_output_validation_lightweight_equipment_bracket.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV22D; FR-009)
- [ ] T050 [US2] E: Evaluate retained lightweight-equipment-bracket cases into `artifacts/engineering-workflow-validation/families/lightweight-equipment-bracket/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV22E; FR-008/012/016)

### water-heater-sizing — CV23

- [ ] T051 [P] [US2] A: Freeze water-heater-sizing profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/water-heater-sizing/` against T003/T004; preserve approved source/parameter readback, full power/loss grid, lowest feasible choice, first crossing, defined energy horizon, inverter efficiency and baseline/refined time series. (CV23A; FR-002/003/007/008)
- [ ] T052 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/modelica.py` for the actual retained water-heater-sizing formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV23B; FR-005/006/015)
- [ ] T053 [US2] C: Compose water-heater-sizing rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/thermal.py` and `tests/datasets/engineering-workflow-validation/profiles/water-heater-sizing/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV23C; FR-004/006/007/008/011)
- [ ] T054 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/water-heater-sizing/` and `packages/workspace_service/tests/test_output_validation_water_heater_sizing.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV23D; FR-009)
- [ ] T055 [US2] E: Evaluate retained water-heater-sizing cases into `artifacts/engineering-workflow-validation/families/water-heater-sizing/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV23E; FR-008/012/016)

### raspberry-pi-enclosure — CV24

- [ ] T056 [P] [US2] A: Freeze raspberry-pi-enclosure profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/raspberry-pi-enclosure/` against T003/T004; preserve manufacturer/image interfaces, body versus ears, CAD/domain/mesh/field lineage, all heat sources, vents/fan-curve condition, comparable alternatives and model limitations. (CV24A; FR-002/003/007/008)
- [ ] T057 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/cfd_fields.py` for the actual retained raspberry-pi-enclosure formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV24B; FR-005/006/015)
- [ ] T058 [US2] C: Compose raspberry-pi-enclosure rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/thermal.py` and `tests/datasets/engineering-workflow-validation/profiles/raspberry-pi-enclosure/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV24C; FR-004/006/007/008/011)
- [ ] T059 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/raspberry-pi-enclosure/` and `packages/workspace_service/tests/test_output_validation_raspberry_pi_enclosure.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV24D; FR-009)
- [ ] T060 [US2] E: Evaluate retained raspberry-pi-enclosure cases into `artifacts/engineering-workflow-validation/families/raspberry-pi-enclosure/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV24E; FR-008/012/016)

### sheet-metal-supplier-handoff — CV25

- [ ] T061 [P] [US2] A: Freeze sheet-metal-supplier-handoff profiles (01/02/03) in `tests/datasets/engineering-workflow-validation/profiles/sheet-metal-supplier-handoff/` against T003/T004; preserve narrow R1/R3/R4 authority, sourced stock/native mapping, bend/relief assumptions, genuinely developed DXF, measured interior clearances and all base/lid/quantity correspondence. (CV25A; FR-002/003/007/008)
- [ ] T062 [US2] B: Extend and qualify shared `packages/workspace_service/src/workspace_service/engineering_output_validation/readers/sheet_metal.py` for the actual retained sheet-metal-supplier-handoff formats, candidate coverage and independent reference measurements; pin host/version/resource evidence in `specs/082-output-content-validation/evidence/reader-matrix.md`. (CV25B; FR-005/006/015)
- [ ] T063 [US2] C: Compose sheet-metal-supplier-handoff rules via shared `packages/workspace_service/src/workspace_service/engineering_output_validation/assertions/manufacturing.py` and `tests/datasets/engineering-workflow-validation/profiles/sheet-metal-supplier-handoff/`; bind every requirement to real measurements, explicit applicability and full part/variant/refinement coverage. (CV25C; FR-004/006/007/008/011)
- [ ] T064 [US2] D: Qualify controls in `tests/datasets/engineering-workflow-validation/fixtures/sheet-metal-supplier-handoff/` and `packages/workspace_service/tests/test_output_validation_sheet_metal_supplier_handoff.py`; include independent good/alternative references, intended-check defects, boundaries and applicable metamorphic relations; record fixture review. (CV25D; FR-009)
- [ ] T065 [US2] E: Evaluate retained sheet-metal-supplier-handoff cases into `artifacts/engineering-workflow-validation/families/sheet-metal-supplier-handoff/`; reconcile requirements/RTM/evidence, retain true design failures and reproducible findings, and update `specs/082-output-content-validation/progress.md` only after A–D and all case evidence exist. (CV25E; FR-008/012/016)

## Phase 5: US3 — Workspace evidence (P2)

May start after T015; full closure needs family results. **Independent test**: all views reconcile, stale/current outcomes differ correctly, and the real served Workflow/Workflows entry preserves existing authoring.

- [ ] T066 [US3] Add a versioned materialized projection in `packages/workspace_service/src/workspace_service/engineering_output_validation/projection.py` and `scripts/engineering-dataset-dashboard.html`; keep old four-series metrics/events intact and show separate current content/compliance/coverage/review/staleness. Test projections in `packages/workspace_service/tests/test_engineering_output_validation_projection.py`. (CV26; FR-013)
- [ ] T067 [US3] Integrate read-only validation evidence through `apps/api/src/api/routers/workspace.py`, `apps/web/src/services/workspace-service.ts`, `apps/web/src/prototypes/workflow-recovery/EngineeringValidationView.tsx` and existing WorkflowRunHistory/WorkflowRecoveryPage surfaces; preserve current auth, context, authoring and artifact actions, use tokens and stable test IDs, keep routes thin. Read `docs/contributing/workflow-ui-integration.md` first. (CV27; FR-012/013/015)
- [ ] T068 [US3] Add component state tests in `apps/web/src/prototypes/workflow-recovery/EngineeringValidationView.spec.tsx`, mocked journey in `tests/ui-integration/engineering-output-validation.spec.ts` and served-system evidence in `tests/e2e/test_engineering_output_validation.py`; verify workspace entry, evidence links and existing create/configure/drag/connect/invalid-source/undo/save/reopen behavior, recording exact served build and screenshots under `artifacts/engineering-workflow-validation/ui/`. (CV28; FR-013/015; SC-006)

## Phase 6: US4 — Full corpus and authoritative review (P2)

Depends on T016–T065. **Independent test**: all 30 frozen cases replay with complete traceability; authorized late review adds a new report while prior attempts remain unchanged.

- [ ] T069 [US4] Freeze the complete catalog/profile/reader/cohort set and evaluate all 30 cases into `artifacts/engineering-workflow-validation/corpus/`; generate aggregate and per-case RTMs, exact reproducers and typed findings, preserving old campaign metrics and all known failures. (CV29; FR-001/008/012/016)
- [ ] T070 [US4] Independently review high-impact verdicts, fixtures and rubric judgments; exercise `packages/workspace_service/src/workspace_service/engineering_output_validation/reviews.py` with `packages/workspace_service/tests/test_engineering_output_validation_reviews.py` for unauthorized/stale actor/subject rejection and append-only late assessments; retain signed/attributed decisions under `artifacts/engineering-workflow-validation/reviews/`. Only actual human-required decisions need human action; permitted competent checker/agent review stays accurately labeled. (CV30; FR-009/010/015/017)

## Phase 7: Reliability, gates and handoff

- [ ] T071 Test stale source/profile/reader keys, missing variants, foreign artifacts, nonfinite content, reader errors, source mutation races, cancellation/restart and owned native cleanup in `tests/test_engineering_content_validation_campaign.py` and `tests/external/engineering_output_validation/`; retain byte/record comparisons proving originals unchanged. (CV31; FR-010/011/014/015)
- [ ] T072 Verify qualified offline/native/Docker reader matrix, resource bounds, package boundaries, installation/packaging and relevant security behavior in `tests/external/engineering_output_validation/` and `specs/082-output-content-validation/evidence/reader-matrix.md`; label unsupported hosts accurately and require in-scope readers to be implemented. (CV32; FR-014/015)
- [ ] T073 Run appropriate focused then required integration/merge-gate checks, trace propagation and UI checks; save commands/results and all-30/fixture/requirement coverage in `specs/082-output-content-validation/evidence/verification.md`. Follow `docs/contributing/dev-push-runbook.md` if pushing a dev PR; use authoritative gate scripts for any separately authorized merge. No needless repeated broad runs. (CV33; FR-009/015/016)
- [ ] T074 Write `specs/082-output-content-validation/completion.md` and refresh `progress.md`/`quickstart.md` with framework/corpus/compliance states, commands, limitations, authentic review evidence and separate generator-repair backlog; do not mark missing readers/reviews complete or force 30 compliant designs. (CV34; FR-016)

## Dependencies and parallel examples

- Setup: T001 → T002. Foundations: T003 → T004 → T005 → T006; T007 and T008 can be implemented independently after T006 with agreed contracts, but shared changes stay serialized.
- US1: T009 needs T007/T008; T010 → T011; T012 and T013 use stable contracts, then T014 → T015. Example: qualify thermal and geometry fixtures in separate directories once reader interfaces are stable.
- US2: ten independent A–E chains after T015 review. Example: robot A at T026 and harness A at T031 can run together; capability readers such as geometry/thermal/electrical have one owner even when used by multiple families.
- US3: T066 → T067 → T068 after T015. Example: projection unit tests and view component tests may be developed in separate files after the projection contract is frozen.
- US4: T069 needs every family E; T070 follows T069. Example: independent review of two completed families can proceed using separate review records with a shared frozen rubric.
- Closure: T071 after T069; T072 after T070/T071; T073 after T068/T072; T074 last.
- These are work-partition examples. Do not spawn agents unless current user/skill authority allows it. No shared writable runtime database, ports, output directory or native lease between concurrent tasks.

## Requirement and success-criterion coverage

| Requirement | Task coverage |
|---|---|
| FR-001 | T001, T010, T069 |
| FR-002 | T003 and every US2 A |
| FR-003 | T003, T004, T006 and every US2 A |
| FR-004 | T005, T009 and every US2 C |
| FR-005 | T008, T012, T013 and every US2 B |
| FR-006 | T008, T012, T013 and every US2 B/C |
| FR-007 | T004, T006, T009 and every US2 A/C |
| FR-008 | T003, T005, T016–T065, T069 |
| FR-009 | T005, T012–T014, every US2 D, T070, T073 |
| FR-010 | T007, T010, T070, T071 |
| FR-011 | T006, T009, T011, every US2 C, T071 |
| FR-012 | T011, T015, every US2 E, T067, T069 |
| FR-013 | T007, T011, T066–T068 |
| FR-014 | T002, T005, T007, T008, T010, T015, T071, T072 |
| FR-015 | T002, T008, T010, every US2 B, T067, T068, T070–T073 |
| FR-016 | T015, every US2 E, T069, T073, T074 |
| FR-017 | T007, T009, T010, T070 |
| SC-001 | T001, T003–T005, T069 |
| SC-002 | T014 and every US2 D |
| SC-003 | T011, T066–T070 |
| SC-004 | T007, T009, T010, T070, T071 |
| SC-005 | every US2 E, T069, T070, T074 |
| SC-006 | T068, T072, T073 |

## Implementation strategy

MVP is foundations plus US1, not a completed feature. Show its evidence for the constitution's milestone review, then expand one qualified family at a time. Update progress after each checkpoint with exact files, commands, verdicts and the next task. Check a task only when its exit evidence exists. Keep actual output failures as findings; fixes to generators require separate scope. Finish all 74 tasks and state remaining evidence limitations honestly.
