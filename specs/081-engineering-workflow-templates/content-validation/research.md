# Research and design decisions

Prepared 2026-09-13 UTC for the deferred [content-validation plan](plan.md). The earlier recommendation was based on the user-confirmed 30 input packs, not 300. This bundle preserves the relevant findings in the repository so a future agent does not depend on conversation history or a host-specific visualization file.

## Decision record

### D01 — Separate post-run validation from execution

**Decision:** A new application service inspects completed canonical-run artifacts and writes a separate immutable validation ledger. It never reinterprets a failed workflow as a completed generation run.

**Rationale:** `scripts/engineering_dataset_campaign.py` deliberately hardcodes `valid_data=0`, and its first three achievement counts are cumulative. `completed_current_revision` checks current dataset/template identity but does not independently establish every intended definition/binding and actual artifact. `engineering_dataset_evidence.py` already provides run/step/receipt/export lineage to consume.

**Alternatives rejected:** Flip the presence flag; use cumulative count 30 as activation; rewrite execution receipts with validation status; dispatch legacy Rivet scenarios around canonical runs.

### D02 — Reuse generic predicates, add independent observations

**Decision:** Adapt `EngineeringAssertionRegistry`, `NormalizedArtifact` and the normalizer registry. Add qualified actual-file readers and source-bound measurements.

**Rationale:** Current scenario rules consume structured summaries; many normalizer source schemas have no deep validator. Existing workflow booleans such as watertight/converged/profile-compatible cannot by themselves prove file content. `workflow_dxf_verification.py` demonstrates bounded actual-file inspection and explicitly limits its claim to contour/file integrity.

**Alternatives rejected:** Treat a report's boolean as evidence, compare whole CAD files byte-for-byte, or write ten independent validators containing the same logic.

### D03 — Add validation-specific contracts without breaking old states

**Decision:** Pure new core models and an explicit legacy adapter. Keep check verdict, validation lifecycle, content correctness, design compliance and physical validation separate.

**Rationale:** Existing scenario assertions use pass/fail/skip/error; workflow assertions use pass/fail/inconclusive. Existing `engineering_scenario_repository.py` provides useful immutable-finalization patterns, but its schema is bound to legacy workflow IDs and is not a drop-in multiple-revalidation ledger.

**Alternatives rejected:** Repurpose skip as acceptable N/A; overload a workflow-run status; reuse old repository constraints without migration analysis.

### D04 — Freeze requirements outside generation inputs

**Decision:** Requirements and 30 profiles live under a separate validation dataset root, with explicit source hashes/locators, amendment scope, units/frame, mandatory/objective/preference/assumption/deferred classification, tolerance and uncertainty.

**Rationale:** Modifying existing scenario manifests can change generation fingerprints and grants. Human input packs contain meaningful differences: radial versus diametral fits, intentionally unresolved dimensions, approved stock alternatives, controller-only star points and optional styling preferences. A generated design review or auto-approval cannot silently amend them.

**Alternatives rejected:** Infer acceptance from the candidate output, turn all profile prose into hard requirements, impose one global numerical tolerance, or widen thresholds after observing failures.

### D05 — Qualify checkers with independent reference fixtures

**Decision:** Known-good references, valid alternative representations, targeted defective fixtures, threshold controls and applicable metamorphic tests are prerequisites to trusting real verdicts.

**Rationale:** A test that rejects every file can still detect a defect. Tests must prove both admissible outputs and intended defect detection. A malformed test file that fails parsing does not prove the missing-hole detector works.

**Alternatives rejected:** Use only the current generated output as golden reference, mutate production artifacts in place, or accept aggregate mutation scores without coverage of important failure mechanisms.

### D06 — Use the latest authorized physical model

**Decision:** At activation, reconcile current selected kit/source/parameters and subsequent authorized changes, then freeze them.

**Rationale:** The preliminary proposal mentioned possible CoffeeMachine API limits. [The selected Modelica contract](../dataset-campaign/modelica-selected-kit.md) already documents `wright-water-heater-v1@0.1.0`, parameter ranges, fixed water heat capacity, a 2 K thermostat hysteresis assumption, baseline/refined DASSL controls, actual result exports and power/loss comparison support. Those capabilities are recorded integration evidence, not future independent content validation.

The uploaded first-crossing/shutoff intent and actual thermostat behavior need explicit compatibility analysis. An independent first-crossing reference may be applicable before crossing; whole-horizon energy cannot assume the heater remains off afterward. Never preselect feasible powers from an unverified alternative model.

[Heat native-result inspection](../dataset-campaign/heat-native-result-inspection.md) preserves real VTU/CSV/report outputs and explicitly leaves independent correctness pending. New readers inspect those fields rather than accepting provider reports or removing the pending-critic warning without appropriate evidence.

**Alternatives rejected:** Reuse stale discovery assumptions, assume a newly selected kit is automatically qualified for all purposes, or replace required native solver runs with analytical code.

### D07 — Pilot deterministic references first

**Decision:** Heat-spreader-01 and drill-jig-01 prove numerical and geometric measurements, uncertainty, RTM and retained-output replay. Expand after the contract stabilizes.

**Rationale:** The current heat briefs define one-dimensional reference solutions; jig CSVs provide exact datum features and clear tolerances. Robot cases then prove frame/time/data-mask behavior. Electrical, manufacturing and higher-fidelity solver families reuse those contracts.

**Alternatives rejected:** Build the hardest CFD/sheet-metal reader first, or expand all native integrations before one trustworthy verdict exists.

### D08 — Requirements matrix and UI are projections

**Decision:** JSON results are authoritative; RTM CSV/HTML/JUnit and existing UI read those records. Use separate current-validation metrics and preserve original four-series execution history.

**Rationale:** Traceability requires source → test → actual measurement → artifact, with valid required-check aggregation. A matrix row alone is no proof; historical passing evidence can become stale.

**Alternatives rejected:** Manually curate a spreadsheet disconnected from checks, use a single percentage for execution/content/compliance, or make a detached report route the sole UI completion evidence.

### D09 — Narrow dependencies and physical claims

**Decision:** Use current Python test/recording machinery; qualify only required readers. Consider OCCT, trimesh and broader DXF readers where existing qualified primitives are insufficient. NIST STEP analysis is supplemental. A requirements product is optional, not a prerequisite.

**Rationale:** No single package supplies trustworthy CAD, CFD, ECAD, numerical and requirements validation for these cases. The repository already has most orchestration/status scaffolding. Native readback and solver-field parsing carry real platform and licensing constraints.

**Alternatives rejected:** Add a large mandatory ALM stack, install every engineering package in the base image, or classify a simulation-only result as physical qualification.

## External reference basis

These primary sources informed the preceding recommendation. Their capabilities are not claims that the tools are installed or qualified in Wright; recheck chosen versions at implementation activation.

- [NASA requirements verification matrix](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/): unique requirements, source identity and planned verification approach.
- [NASA spatial convergence guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html): grid-refinement assessment and limits of numerical convergence.
- [Original metamorphic-testing paper](https://arxiv.org/abs/2002.12543): relationships between test executions when exact expected outputs are difficult to specify.
- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/): property-based test generation.
- [Open CASCADE shape validity](https://occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html): geometry/topology inspection primitives.
- [trimesh documentation](https://trimesh.org/trimesh.html): mesh inspection and measurements, with explicit unit provenance still required.
- [ezdxf document management](https://ezdxf.readthedocs.io/en/stable/drawing/management.html): a possible broader DXF reader; preserve originals and distinguish repair from validation.
- [NIST STEP Analyzer](https://www.nist.gov/services-resources/software/step-file-analyzer-and-viewer): exchange-format/PMI/validation-property diagnostics, not design compliance.
- [KiCad CLI documentation](https://docs.kicad.org/9.0/en/cli/cli.html): native ERC/DRC/export capabilities for a documented release.
- [StrictDoc traceability guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide-TRACE.html): optional requirements management; test-report integration is documented as experimental.

## Planning execution notes

- Read the current feature plan/spec, active constitution v3.1.1 and planning template.
- `.specify/feature.json` resolves to `specs/081-engineering-workflow-templates`; preserve it because generation work is active. The deferred supplement uses the parent context without replacing its plan.
- Read the Spec Kit setup script before running it. The Windows WSL Bash bootstrap returned `Bash/Service/CreateInstance/E_ACCESSDENIED`. Resolve existing feature paths from the selector/branch manually; no escalation is needed to write this additive documentation bundle.
- Checked `.specify/extensions.yml`: before_plan optional `/speckit-git-commit`; after_plan optional `/speckit-git-commit` and `/speckit-agent-context-update`. All optional hooks were skipped. No mandatory before/after-plan hook applies. Preserve active dirty work and add only a small deferred-plan navigation reference.
- Two independent read-only planning reviews covered architecture/status/persistence and acceptance/sequence. Incorporated current-vs-cumulative G0, reader independence, legacy state mapping, separate validation history, supported Modelica model behavior and implementation-vs-design-compliance criteria.
- No workflow/native CAD/solver operation, implementation test suite, commit, push, automation or goal was started by this planning task.

## Remaining decisions at activation

These are prescribed evidence checks rather than unresolved architectural choices: exact then-current output/format/tool identities, source amendments, reader host/version availability, actual field schemas and source-backed requirement tolerances. CV01–CV05 resolve and freeze them before dependent candidate evaluation. Unsupported capabilities and genuinely ambiguous source requirements remain explicit blockers; the agent can continue unrelated packages without weakening them.
