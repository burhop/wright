# Implementation plan: engineering output content validation

**Status:** Planned; execution deferred. **Prepared:** 2026-09-13 UTC.
**Parent feature:** 081 Engineering Workflow Templates.
**Current planning branch:** `codex/081-engineering-workflow-templates`.
**Intended implementer:** A future agent, likely Sol; no agent or workflow is started by this document.

## User request and activation

The user requested an implementation plan for independent output-content checks and requirements traceability across the **30 current input packs**, to run **after all process flows create data**. Scope is ten existing families with three cases each. This plan supplements [the parent plan](../plan.md) and follows, rather than replaces, [the output-generation campaign](../dataset-campaign/plan.md).

**This turn authorizes planning and saving the handoff only.** Do not implement this plan, change validation counters, launch a monitor, rerun workflows or activate a goal merely because this file exists. A later user assignment to implement this saved plan supplies implementation authority; do not require the user to approve it again if that assignment already does so.

### G0: mandatory start gate

Before CV02 or any validation implementation, the future agent must perform CV01, a bounded read-only reconciliation, and save `evidence/start-gate.json` with a dated report. Source data are the then-current campaign inputs, normal runtime records, retained receipts/artifacts and lifecycle evidence.

All of these must hold:

1. Exactly 30 distinct expected scenario IDs exist: the ten current templates × three cases. Every current pack has valid retained source bytes and its input/normalization map.
2. For **every current input/template revision**, an explicitly selected completed attempt belongs to the intended canonical definition revision, has a real runtime run ID, terminal-step and complete required-step evidence, and accepted same-run artifact records. Use the latest intended source/binding identity documented by campaign recovery; do not choose an older passing definition simply to pass the gate.
3. Reopen and hash every declared output file for the selected attempt. Every required role resolves to nonempty same-attempt files. An old cumulative count, a filename, a generator's success message or a partial native solve is insufficient. Include all variants/parts already required by the execution contract.
4. Reconcile relevant workers and native application leases so retained outputs are stable. No selected output is being overwritten, no selected operation has an unknown mutation outcome, and no borrowed user session is commandeered. Existing Wright/dashboard services need not be stopped.
5. The output-generation campaign's 30/30/30/0 conclusion is reconciled against those per-case facts. Historical `valid_data=0` stays intact. If a separately authorized validation phase already exists, reconcile it and avoid duplicate implementation rather than resetting state.
6. Record hashes for corpus inputs, each selected run receipt, definition/template/binding identity, output manifest and relevant campaign closeout evidence. Record checkout/commit plus dirty-file identities where uncommitted work matters. These are activation evidence, not engineering acceptance.

If G0 fails, report exactly which cases or lifecycle facts are missing and leave this work **deferred**. Do not take over the output-generation campaign or poll repeatedly. Wait for a later assignment or meaningful prerequisite change. Do not require future content correctness to pass G0; that would be circular.

Once G0 passes, freeze the selected cohort. Later input/definition changes require a new per-case source revision and eligibility check; they do not erase prior evidence or require restarting unaffected cases.

## Outcome and boundaries

Deliver a reusable independent validation service, file readers, 30 acceptance profiles, qualified validator fixtures, retained evaluations, and a generated requirements traceability view. Run validation against existing outputs first. Development must not depend on redoing expensive CAD/solver generation unless specific evidence is missing or a separate workflow repair is authorized.

Keep four outcomes distinct:

- **Execution complete:** the flow produced required data.
- **Content verified:** required integrity, evidence, measurement and calculation checks are conclusive and correct for the declared model.
- **Requirements compliant:** all applicable mandatory design requirements pass; preferences/objectives are reported separately.
- **Physical validation:** actual performance/fit/manufacturing evidence exists for a named scope.

A report that correctly establishes no feasible candidate can pass content verification and fail design compliance. It must not be called a successful design. No outcome here automatically promotes a template/MCP server, qualifies a physical product or releases manufacturing.

### Functional requirements

| ID     | Requirement                                                                                                                                  |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| CVR-01 | Enforce G0 and freeze/revalidate exact current cohort identities.                                                                            |
| CVR-02 | Define versioned atomic requirements from all authoritative input sources, including images, tables and applicable amendments.               |
| CVR-03 | Keep requirements, test definitions and measured observations separate; generated reports and test-auto approvals cannot amend requirements. |
| CVR-04 | Compose shared versioned validators by artifact kind/capability; case/template IDs select data profiles, never bespoke runtime dispatch.     |
| CVR-05 | Independently read actual native/export/solver/data files and bind measurements to exact artifact/reader identities.                         |
| CVR-06 | Check semantic correspondence across native CAD, exports, meshes/decks, fields, reports and handoff bundles.                                 |
| CVR-07 | Use explicit units, frames, tolerances, applicability, aggregation and measurement uncertainty; reject invalid or nonfinite data.            |
| CVR-08 | Provide all ten families and all 30 case profiles described in acceptance-cases.md; no family can be silently omitted.                       |
| CVR-09 | Prove each required validator with independently reviewed positive, defective, boundary and applicable metamorphic controls.                 |
| CVR-10 | Persist append-only validation attempts, failures, cleanup and review evidence independently of execution records.                           |
| CVR-11 | Represent pass/fail/inconclusive/blocked/justified-not-applicable and validator errors without accepting missing evidence.                   |
| CVR-12 | Generate JSON/CSV/HTML traceability and test-runner output from one result model, with exact claim-to-evidence links.                        |
| CVR-13 | Show current content verification, requirement compliance, coverage and pending review separately from historical execution achievements.    |
| CVR-14 | Support read-only replay, cancellation/restart, bounded native-reader resources and cache invalidation by all relevant identities.           |
| CVR-15 | Preserve workspace authority, confinement, existing UI authoring, external-action policy and native/Docker boundaries.                       |
| CVR-16 | Leave a reproducible final corpus report, limitations, test evidence, reproducible findings and a compact future-agent checkpoint.           |

## Technical context

- **Languages:** existing Python 3.11–3.14 backend; existing TypeScript/React only for necessary workflow evidence display. Recheck supported versions at activation.
- **Primary dependencies:** current core/scenario models and assertion/normalizer registries, workspace artifact/run services, data-vault SQLite WAL, existing CLI test harness, pytest. Qualify optional readers in isolated selected environments.
- **Storage:** input and output vault references plus a separate validation state root; new additive data-vault-owned tables. Reuse canonical JSON/digest primitives.
- **Platforms:** offline pure checks on supported native and Docker paths; native application readers restricted to explicitly qualified hosts. No extra CAD/MCP software in the base image solely for tests.
- **Performance:** publish tested limits for parser bytes/entities, wall time, memory and concurrency. Cheap schema/profile tests run in ordinary CI; native CAD and full solver-field readers run in designated integration lanes. UI reads materialized summaries, never raw solver fields synchronously.
- **Scale:** 30 profiles initially; multiple parts/candidates/refinements per profile; one shared engine. Requirement count is measured after extraction, not invented in advance.
- **Interfaces:** first a thin development CLI and a read-only dashboard projection; integrate results through existing workspace run/artifact surfaces. No new workflow language or external database.

## Architecture

`frozen input requirements + selected output cohort → independent readers → normalized measurements → registered assertions → immutable validation results → traceability/report/UI projections`

1. **Pure contracts in core.** Add validation-specific versioned entities with an explicit bridge to existing scenario assertions. Current scenario statuses are not identical to workflow assertion statuses; preserve their old semantics.
2. **Independent readers in workspace-service.** Read actual confined files or invoke pinned read-only native operations via current GatewayService/lifecycle boundaries. Emit small measurements with file/reader lineage. Registered summary schemas alone do not prove independent inspection.
3. **Generic evaluation.** Reuse `EngineeringAssertionRegistry` and numerical/unit logic via an adapter. Extend shared checks for semantic geometry, field reduction, graph equivalence, requirement coverage and uncertainty. Do not route canonical `.wflow` runs through legacy Rivet scenario execution.
4. **Persistence in data-vault.** Own additive migrations and immutable validation records. A validation attempt references an existing workflow run without rewriting its status, artifact bytes or approvals.
5. **Thin harness.** Proposed `scripts/run_engineering_content_validation.py` only loads policy/profile/cohort references and invokes services. It is not another executor. Protocol is in [the contract](contracts/validation-contract.md).
6. **Profiles outside source packs.** Use `tests/datasets/engineering-workflow-validation/` for requirement baselines, case profiles and test fixtures so adding validation does not alter the 30 generation-pack fingerprints. Reusable production validation code remains in packages.
7. **Evidence display.** Extend the existing dataset dashboard with a versioned validation projection, retaining all four historic campaign series unchanged. Show a distinct current-cohort view that can decrease when evidence becomes stale. Provide a run-linked read-only validation view in the existing workspace UI; preserve the latest reviewed authoring implementation.

### Proposed source locations

Exact filenames may be adjusted to match the then-current checkout, while preserving ownership:

```text
packages/core/src/core/engineering_output_validation.py
packages/core/tests/test_engineering_output_validation.py
packages/data_vault/src/data_vault/engineering_validation_repository.py
packages/data_vault/tests/test_engineering_validation_repository.py
packages/workspace_service/src/workspace_service/engineering_output_validation/
  service.py, readers/, profiles.py, reporting.py
packages/workspace_service/tests/test_engineering_output_validation*.py
scripts/run_engineering_content_validation.py
scripts/engineering-dataset-dashboard.html                 # additive projection
tests/datasets/engineering-workflow-validation/
  requirements/, profiles/, fixtures/, catalog.json
tests/test_engineering_content_validation_campaign.py
tests/external/engineering_output_validation/              # qualified native checks
tests/ui-integration/engineering-output-validation.spec.ts
tests/e2e/test_engineering_output_validation.py
artifacts/engineering-workflow-validation/                 # generated, separate state
```

Existing surfaces to assess before adding code:

- `packages/core/src/core/engineering_scenarios.py`
- `packages/workspace_service/src/workspace_service/engineering_scenario_assertions.py`
- `packages/workspace_service/src/workspace_service/engineering_scenario_artifacts.py`
- `packages/workspace_service/src/workspace_service/workflow_engineering_assertions.py`
- `packages/workspace_service/src/workspace_service/workflow_dxf_verification.py`
- `packages/workspace_service/src/workspace_service/workflow_additive_manufacturing.py`
- `packages/workspace_service/src/workspace_service/workflow_enclosure_cfd.py`
- `packages/data_vault/src/data_vault/engineering_scenario_repository.py`
- `scripts/engineering_dataset_campaign.py`, `scripts/engineering_dataset_evidence.py`
- Existing workflow artifact-review/run-record services and the latest reviewed Workflow/Workflows UI.

## Implementation sequence

Every task below is **unstarted**. Task IDs are local to this deferred supplement. Use [quickstart.md](quickstart.md) for handoff and checkpoints. These work packages are executable planning detail; do not accidentally run parent-feature task generation against the active campaign when intending this supplement.

### M0 — Activate and freeze the acceptance basis

| Task | Dependencies                    | Deliverable and exit test                                                                                                                                                                                                            |
| ---- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CV01 | Later implementation assignment | Read-only G0 audit; 30 explicitly selected current attempts and all rehashed outputs, or precise deferred report.                                                                                                                    |
| CV02 | CV01 pass                       | Record current branch/dirty work, package boundaries, existing implementations and selected native/model contracts. Preserve unrelated work; create isolated feature worktree only when appropriate.                                 |
| CV03 | CV02                            | Extract requirement baseline for all 30 packs with source locators/digests, image observations, amendment links, classifications, applicability and required output/candidate coverage. Independently compare baseline to originals. |
| CV04 | CV03                            | Freeze test methods, expected quantities, tolerance provenance and uncertainty policy before candidate evaluation. Resolve genuine source conflicts; record reviewed assumptions and planned human-review rubric.                    |
| CV05 | CV04                            | Catalog all 30 profiles, shared validator families and reader capabilities; record exact host/dependency licensing/isolation requirements and qualification plan.                                                                    |

**M0 gate:** no undocumented input exclusions, arbitrary tolerance defaults or silent source overrides. Unresolved source questions stay visible; do independent work around them, but dependent tests cannot claim a pass.

### M1 — Contracts and reusable engine

| Task | Dependencies | Deliverable and exit test                                                                                                                                                                                                               |
| ---- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CV06 | CV04         | Implement core schema/profile validation and explicit legacy status mapping. Test duplicate IDs, invalid tolerance/unit/frame, unsupported operators and incomplete requirement links.                                                  |
| CV07 | CV06         | Add data-vault migrations, immutable evaluation/finding/review/assessment records and idempotent cache keys. Prove migration compatibility, terminal retry vs resume, late-review revisions and deterministic current-result selection. |
| CV08 | CV06         | Implement confined reader registry and normalized measurement contract; reject foreign paths, stale hashes, unsafe archive members, unsupported versions and excessive resources. Never modify originals.                               |
| CV09 | CV06–CV08    | Compose existing evaluators with measurement/uncertainty/requirement aggregation. Reject empty evidence, nonfinite fields and crash-to-pass conversions. No arbitrary code in profiles.                                                 |
| CV10 | CV07–CV09    | Implement thin CLI, start-gate/cohort import, cancellation, restart/checkpoints and structured trace propagation; prove no workflow/device dispatch during revalidation.                                                                |
| CV11 | CV09–CV10    | Generate JSON/CSV/HTML/JUnit from one record set. Test missing requirements, AND dependencies, mixed failure/blocked/error outcomes, justified N/A, late review/stale reports and count/link reconciliation.                            |

**M1 gate:** one synthetic fixture can be evaluated, persisted, replayed and displayed without touching workflow state; defects fail their intended checks. Fixture evidence is never corpus success.

### M2 — Two real pilots and validator qualification pattern

| Task | Dependencies | Deliverable and exit test                                                                                                                                                                                   |
| ---- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CV12 | M1, CV05     | Implement independent thermal-field/geometry reader and heat-spreader-01 analytical/balance/refinement checks; validate actual boundary/load identities.                                                    |
| CV13 | M1, CV05     | Implement independent STEP/mesh/DXF feature readers for drill-jig-01; validate datum transform, bushing seats and clamp exclusion.                                                                          |
| CV14 | CV12–CV13    | Qualify both pilots using independent known-good fixtures, valid alternatives, exact/below/above tolerance controls, targeted defects and applicable unit/frame transformations. Record expected failures.  |
| CV15 | CV14         | Evaluate preserved real outputs for both pilots; reconcile every requirement and report value. Retain real failures separately from validator defects; prove repeated validation creates no generation run. |

**M2 gate:** generic contracts are stable, measurements are independently bound to real artifacts, and reviewers can follow requirement → check → observation → file. A real design failure does not fail framework qualification if the verdict is proved correct.

### M3 — Expand across the remaining families

For each task CV16–CV25, create **five bounded checkpoints**: A profile/source freeze; B independent reader/reference qualification; C case assertions; D positive/defect/boundary/metamorphic tests; E retained-output evaluation and traceability. Never mark the family done on only A or a green mocked test. Within a family, prove one case before sibling expansion.

| Task | Dependencies | Scope                                                                                                                                                                                        |
| ---- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CV16 | M2           | Remaining heat-spreader cases 02/03, including total vs area-specific contact resistance and all candidates.                                                                                 |
| CV17 | M2           | Remaining drill-jig cases 02/03, chip/keepout regions, flange stackups, asymmetric key and correct coordinate tolerances.                                                                    |
| CV18 | M2           | All three robot cases: raw/bag normalization evidence, frame/time correction, valid sample masks, independent metrics and grounded diagnosis.                                                |
| CV19 | M2           | All three harness cases: logical/physical connector view mapping, graph equivalence, shared-current voltage drop, source-backed ratings, cut lists and assembly instructions.                |
| CV20 | M2           | All three PCB cases: native sources, exact netlists, current ERC/DRC, dimensions/clearances, BOM and reopened fabrication equivalence.                                                       |
| CV21 | M2           | All three printing cases: source/repaired meshes, feature fidelity, justified orientation/supports, selected material/process and actual slice/toolpaths; simulated receipts remain labeled. |
| CV22 | M2           | All three bracket cases: actual mesh/deck/fields, force vector and reactions, protected geometry, mass, fixed stress evaluation region and refinement.                                       |
| CV23 | M2           | All three heater cases: latest approved Modelica kit/source/parameter readback, complete power/loss grid, target crossing, energy accounting and numerical refinement.                       |
| CV24 | M2           | All three Pi cases: source-backed interfaces, design/CAD/domain/mesh/field lineage, vents/fan condition, comparable thermal cases and documented limitations.                                |
| CV25 | M2           | All three sheet-metal cases: authorized amendments, source/native stock mapping, developed DXF, measured DFM/forming assumptions and multi-part/quantity correspondence.                     |

CV16–CV25 may proceed independently after M2 only with disjoint file ownership and proven native resource isolation. Shared API/core/schema changes stay with one owner. Prefer small local work packages for Sol; a second lane must not interfere with CAD/solver sessions or borrowed user work.

### M4 — Product evidence and complete corpus evaluation

| Task | Dependencies | Deliverable and exit test                                                                                                                                                                                                                                                                                                                                                                            |
| ---- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CV26 | M1, M2       | Add versioned validation dashboard projection with requirement coverage, content verification, compliance, stale/inconclusive/blocked results and current/historical distinction. Preserve old counters and events.                                                                                                                                                                                  |
| CV27 | CV26         | Add read-only validation access through existing workspace run/artifact surfaces; use thin authenticated service boundaries and current UI primitives.                                                                                                                                                                                                                                               |
| CV28 | CV27         | Component, mocked page and real served-workspace verification through Workflow/Workflows; preserve authoring, source/save/reopen/undo, artifact actions and evidence access.                                                                                                                                                                                                                         |
| CV29 | CV16–CV25    | Freeze all 30 reader/profile identities and run full retained-output evaluation. Export per-case and aggregate RTM; record every failure with a reproducible command and exact evidence.                                                                                                                                                                                                             |
| CV30 | CV29         | Independent review of all high-impact verdicts and reference fixtures; calibrate human/document rubric and distinguish preferences from required evidence. A separately recorded competent checker/agent may review where criteria permit; only expressly human-required judgments need human approval. Corrections require new validator/profile or assessment revisions and affected revalidation. |

### M5 — Reliability, regression and handoff

| Task | Dependencies | Deliverable and exit test                                                                                                                                                                          |
| ---- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CV31 | CV29         | Test stale inputs/profile/readers, foreign artifacts, missing variants, nonfinite/empty content, reader errors, cancellation/restart, native working-copy cleanup and immutable replay.            |
| CV32 | CV30–CV31    | Validate supported offline/native/Docker reader matrix and resource budgets, dependency boundaries, packaging and relevant security checks. Narrow host-specific qualification is labeled exactly. |
| CV33 | CV28, CV32   | Run applicable focused/full integration gates; publish coverage reconciled across 30 profiles, negative controls, current results and UI evidence. No broad reruns without new changes/failures.   |
| CV34 | CV33         | Write final completion/limitations report and compact resume checkpoint. Separate generator repair backlog, unsupported/deferred physical checks and optional future tooling.                      |

## Completion criteria

**Framework implementation complete** requires:

- G0 recorded; all CV02–CV34 deliverables exist and their relevant tests pass.
- 30 profiles with a complete source/requirement inventory and qualified readers for every in-scope automatic check; no missing family hidden as a blanket N/A.
- Every distinct hard-check mechanism has known-good and targeted defective controls, threshold behavior and a supported uncertainty policy; meaningful valid alternatives are accepted.
- A retained, reproducible evaluation is attempted for all 30 current selected cases; every applicable requirement has a disposition and evidence/reason. Reader implementation gaps remain incomplete implementation, not ordinary design failures.
- JSON/CSV/HTML/JUnit and the UI reconcile with immutable records and retain current/stale/history distinctions.
- Required engineering judgments are recorded or visibly pending; no unperformed review is marked accepted. The report states exactly which acceptance claims remain open.
- Original output-generation receipts, inputs, artifacts, historical metrics and external-action permissions are preserved.

**Corpus evaluation complete** additionally requires no infrastructure error or missing mandatory measurement/review for the selected cohort. Conclusive design failures are valid evaluation results.

**All designs compliant** requires every applicable mandatory design requirement to pass. This is a distinct milestone, not a requirement to fabricate 30 green results. Repairing workflows/designs is a separately scoped follow-up unless explicitly included by the user at activation.

**Physical validation and public qualification** remain outside this phase except for honestly recording any supplied evidence. No automatic template/server promotion or production release.

## Constitution check

Pre-design and post-contract review against constitution v3.1.1: **PASS by design**.

- Core/service/storage ownership is explicit; no business logic in routes.
- Offline inspection, file-vault artifacts and SQLite WAL are retained; no cloud dependency or external database is introduced.
- Readers obey selected-host and native-runtime boundaries; no MCP-specific base-image additions.
- Existing local identity, origin/RBAC, confined files and source authority remain.
- Code-driven readers use existing engineering tool contracts and cached sourced evidence.
- UI work requires current workflow integration guidance and all three testing tiers.
- Validation phases, readers, storage and report operations carry trace IDs and structured observations.
- Planning is isolated from implementation. Current active campaign remains authoritative until the activation gate. Push/merge/release follow existing runbooks only if separately authorized.

## Plan bundle and implementation handoff

- [Research and decisions](research.md)
- [All 30 acceptance-case seeds](acceptance-cases.md)
- [Data model](data-model.md)
- [Validation and CLI contract](contracts/validation-contract.md)
- [Future-agent quickstart and ready-to-paste prompt](quickstart.md)
- [Progress checkpoint](progress.md)

The current branch contains unrelated active changes. Save only this planning bundle and small navigation references now. Do not commit, stage, switch branches or update the active feature selector as part of saving it.
