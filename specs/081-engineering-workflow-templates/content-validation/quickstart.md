# Future-agent quickstart

**Use after output generation is complete.** This file is a saved handoff, not an automation. Select the desired Sol model in the future task's settings. The prompt does not change either the agent model or Wright's separate workflow inference model. Do not switch the current task or start a new one merely to save this plan.

## Read in this order

1. [Progress](progress.md), then [plan.md](plan.md), especially G0 and completion criteria.
2. Repository `AGENTS.md`, active `.specify/memory/constitution.md` and then-current branch/dirty-work state.
3. [Output-generation execution state](../dataset-campaign/execution-state.md), its final closeout evidence, [campaign plan](../dataset-campaign/plan.md) and [native lifecycle contract](../dataset-campaign/contracts/native-application-lifecycle.md).
4. [Validation contract](contracts/validation-contract.md), [data model](data-model.md), [research](research.md) and relevant [case seeds](acceptance-cases.md).
5. Current selected-host/binding evidence, including [Modelica selected kit](../dataset-campaign/modelica-selected-kit.md), [heat result inspection](../dataset-campaign/heat-native-result-inspection.md) and later superseding authorized changes.
6. Before editor/UI integration, `docs/contributing/workflow-ui-integration.md`; before native-reader qualification, `docs/mcp-catalog/mcp-server-testing-process.md`.

Paths named without links above are repository-relative. Proposed new paths/commands in the plan may not yet exist. Inspect rather than assume their implementation.

## Activation procedure

Perform CV01 as a read-only audit of existing records. The current `engineering_dataset_campaign.py status` command initializes/exports state; do not assume it is a read-only preflight. Before the new audit CLI exists, use file readers and read-only SQLite connections/backup snapshots plus current service contracts to reconcile exact evidence. Never copy an open SQLite main database alone while ignoring its WAL.

If G0 fails, save the missing prerequisites and stop this deferred implementation. Do not change the active generation campaign or repeatedly poll. If it passes, record exact cohort identities, select appropriate implementation branch/worktree without discarding dirty work, and proceed through the work packages.

Avoid hardcoded ports, process IDs, tool IDs or installed versions from old narrative evidence. Resolve live selected configuration at activation; preserve the original version in the cohort and revalidate if it changes.

## Ready-to-paste implementation prompt

```text
Implement the deferred engineering output-validation plan in specs/081-engineering-workflow-templates/content-validation/plan.md. Read quickstart.md and progress.md there first, then AGENTS.md and the active constitution. This is the 30-case content-validation phase after the existing output-generation campaign.

First perform CV01/G0: independently reconcile all 30 current input/template/definition revisions with completed canonical run/step evidence, every required same-run nonempty output artifact and its hash, and stable/reconciled native lifecycle state. Do not use cumulative dashboard counts as the gate. If any prerequisite is missing, leave this implementation deferred with the exact missing cases/evidence; do not take over generation recovery or poll endlessly.

Once the gate passes, implement the saved plan through CV34. Reuse Wright's assertion/normalizer and workspace/data-vault boundaries, add independent artifact readers and 30 requirement-based acceptance profiles, and persist separate immutable validation attempts. Freeze requirements, source precedence and tolerances before evaluating candidate output. Preserve current selected Modelica/CAD/solver contracts and verify their exact source/parameter identities at activation.

Prove heat-spreader-01 and drill-jig-01 pilots before expanding families. Use small bounded work packages with focused meaningful tests, independently reviewed reference fixtures, targeted defective outputs, valid alternative outputs and applicable boundary/metamorphic cases. Work on preserved artifacts first; do not regenerate workflows or alter their outputs to make tests pass. Record generator repairs as separate findings unless the user has explicitly included that work.

Provide complete requirement-to-test-to-measurement-to-artifact traceability, JSON/CSV/HTML/JUnit reports and the planned read-only dashboard/workspace evidence surfaces. Preserve original campaign history/counters, execution statuses, grants, source authority and public qualification boundaries. Follow current UI integration and clean-container/native lifecycle rules. Never promote a generator boolean, invented citation, skipped check or LLM score into a measured pass.

Keep content correctness, design compliance, evaluation completeness and physical validation separate. Complete the implementation and honest corpus evaluation even if some designs fail. Do not hide missing readers or required reviews as N/A. Retain reproducible findings, limitations, test results, dependencies and compact progress checkpoints across turns. Follow the user's current implementation/review authority and repository push/merge/release rules; this task does not itself authorize external printer/supplier actions, purchases, publication or release.
```

## Work cadence for Sol

- Read the compact checkpoint rather than every historical log each turn.
- Own one bounded task or family checkpoint at a time. Record exact file ownership if delegating.
- Stabilize core/result/RTM contracts before parallel family work; serialize shared native resources.
- Separate source baseline, independently computed reference, extracted observation and generated report claims.
- Run focused unit/contract tests while developing; broaden at milestone gates or when failures/changes justify it.
- After a failed validator, reproduce locally against retained artifacts; determine whether the defect is in the generator, reader, oracle, requirement or report before changing anything.
- Update progress after each material result with evidence paths, precise next task and unresolved decisions. Never weaken thresholds or requirements to clear failures.
- Use existing installed runtimes, lockfiles and repository test scripts. Consult actual CLI `--help` before using the proposed commands once implemented.

## Verification commands after implementation

The following paths are proposed deliverables. Check they exist before running:

```powershell
uv run python scripts/run_engineering_content_validation.py --help
uv run python -m pytest packages/core/tests/test_engineering_output_validation.py
uv run python -m pytest packages/data_vault/tests/test_engineering_validation_repository.py
uv run python -m pytest tests/test_engineering_content_validation_campaign.py
```

Run service/family tests from their actual implemented paths. Use the repository's suite-isolation commands when combining packages, then targeted native-reader and served-workspace tests. The contract defines future audit/validate/report CLI arguments; do not invoke nonexistent commands now.

Before an authorized dev-targeting PR push, read `docs/contributing/dev-push-runbook.md` and run the platform's `scripts/check-dev-push`; merging follows the existing dev/prod merge and release runbooks. No push or merge is required merely to save or execute this local validation plan.
