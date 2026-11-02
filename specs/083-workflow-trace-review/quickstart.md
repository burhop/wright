# Feature 083 Handoff

## Implementation State

- Branch: `codex/083-workflow-trace-review`.
- Worktree created for planning: `/tmp/wright-083-workflow-trace-review`.
- Baseline: `dev` at `6c0602a4300da38fa7db62026aff1bd984e4113e`.
- The Trace implementation is present in this worktree and is available through
  saved canonical Workflow history and Rivet run surfaces.
- Engineering validation remains external to Trace. Feature 083 implements the
  producer-neutral envelope in [the evidence contract](contracts/evidence-integration.md).

## Read First

For the September 17 presentation redesign, start with the
[package review](presentation-review-2026-09-17.md),
[new presentation plan](presentation-redesign-plan.md), and
[process execution improvements](process-execution-improvements.md).
The [goal prompt](presentation-redesign-goal.md) is the implementation handoff.
Existing export checks are not user acceptance of the engineering presentation.

1. [Specification](spec.md) and [plan](plan.md), especially the user's results-first correction and validation ownership.
2. [Research](research.md), [data model](data-model.md), and [report/export contract](contracts/report-api-and-export.md).
3. `docs/contributing/workflow-ui-integration.md` before touching workspace entry or workflow-facing UI.
4. Feature-081 campaign checkpoint at `specs/081-engineering-workflow-templates/dataset-campaign/rapid-output-loop-checkpoint-2026-09-14.md` and the ignored portable bundle at `.local-run/feature-083-imports/campaign-081` for the 24 completed-output cases.

## Review The Build

Open `http://127.0.0.1:8094`. Enter a workspace through **Workflows**, expand
**Run details**, then **Trace: previous runs** and a saved run. Results load
first; Process, Evidence, and Run history progressively disclose detail. The
Export review menu offers report-only and full-data ZIPs.

## Generate Campaign Reports

The transferred campaign bundle is runtime evidence and remains outside Git. From
the feature worktree, generate one full-data ZIP and extracted offline report for
all 30 retained examples with:

```bash
.venv/bin/python scripts/export-workflow-trace-campaign.py \
  /home/burhop/repos/wright/.local-run/feature-083-imports/campaign-081 \
  /home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081 \
  --mode full_data
```

Open the generated `index.html` to browse the portable campaign catalog. Generate
report-only packages with `--mode report_only`. Repeat `--case CASE_ID` to export
an explicit subset instead of all 30 cases.

Verify archive membership, extracted bytes, and resource digests with:

```bash
.venv/bin/python scripts/verify-workflow-trace-campaign.py \
  /home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081 \
  --expected 30
```

The command prepares exact run and input revisions read-only. It does not execute
the workflow, activate content validation, or infer missing engineering history.

## Implemented Slice

New canonical and Rivet runs preserve review snapshots incrementally. Historical
runs remain readable without reconstruction. Tests cover completed, failed,
cancelled, interrupted, repeated-path, superseded-output, exact-subject evidence,
and moved offline package cases. Synthetic fixtures are not counted as campaign
acceptance.

## Acceptance Checklist for Implementation

- Enter from a normal workspace Workflow/Workflows control and open a saved run's Trace page.
- Confirm the first screen is results-focused with no open diagnostics or concerns dashboard.
- Open primary files and progressively inspect a prompt, source document, approved requirement, recorded decision, and external validation report where present.
- Inspect blocks, connections, repeated paths, and each attempt's distinct files.
- Inspect partial outputs and exact error/blocker information from a failed or stopped run.
- Confirm later edits and file overwrites do not alter retained run evidence.
- Qualify the actual in-app STEP path, existing STL viewer, and any additional advertised format; record preview/download fallbacks.
- Extract and move both export modes; open `index.html` offline and validate generated links and advertised viewers under file-origin browser restrictions.
- Record an acceptance result for every selected real corpus case; inaccessible data is outstanding, not passed.
- Re-run `.venv/bin/python scripts/validate-workflow-trace-corpus.py .local-run/feature-083-imports/campaign-081` after changing historical adapters or export projection.
- Confirm the campaign inventory remains 30 cases, 24 completed and six failed, with no missing retained artifact bytes.
- Open every extracted report under `file://` with networking blocked; exercise at least one activity detail and inspect desktop/mobile output for every family.
- Repeat existing editor authoring/save/reopen and served-workspace checks required by the integration handoff.

## Boundaries

Do not implement validators, derive new requirements, rerun campaign cases, activate deferred content validation, or add a new approval workflow. Trace displays upstream assertions and decisions without certifying them. Keep comments, comparison, and live monitoring deferred. Pushes, merges, and releases follow the existing repository runbooks when assigned.
