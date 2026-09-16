# Engineering workflow input datasets

This is the input corpus for the current feature-081 Spec Kit testing cycle:
three realistic fictional briefs for each of the ten existing templates, thirty
dataset/template pairs in total. These are engineering jobs, not usability tasks.

Each scenario contains a person and their working role, a copy/paste prompt,
company goals and manufacturing capabilities, internal requirements, useful
engineering tables or reference documents, and an original sketch/concept.
People, companies, measurements and operating logs are synthetic test inputs.
They are not observations of actual products, certified designs, or evidence of
compliance with a published standard. Source links marked `not_retrieved` are
research inputs that the workflow must retrieve and cite before relying on them.

Read `scenario.json` to see the files to upload. Paste `prompt.txt`, then attach
the profile, context documents, tables and image. The `.svg` files are editable
originals; accompanying `.png` files are suitable for the current Wright image
input. Units and assumptions appear in the documents instead of hidden test-only
parameters. `input_bindings` is reserved for a reviewed binding to canonical
workflow input blocks; an empty map does not mean the runtime is ready.

## Start the progress dashboard

From the repository root:

```powershell
uv run python scripts/engineering_dataset_campaign.py serve --port 8771
```

Open <http://127.0.0.1:8771>. The service rescans complete input packs and output
receipts every two seconds and persists counters and time-series events in SQLite
WAL. It begins with a real zero snapshot; subsequent points record observation
time. It never invents earlier creation dates. Restarting reuses the same history.

On Windows, use scripts/windows/start-engineering-dataset-dashboard.ps1 to start
it hidden and retain its logs/process identity. The dashboard has a browsable
output tree and links to each original human input file.

```powershell
uv run python scripts/engineering_dataset_campaign.py scan
uv run python scripts/engineering_dataset_campaign.py status
uv run python scripts/engineering_dataset_campaign.py configure --approval-mode manual
uv run python scripts/engineering_dataset_campaign.py configure --approval-mode auto
```

The mode can also be changed on the dashboard. It is an integration-test policy;
it does not bypass production approvals or make the current incomplete runtime
execute. The goal plan includes connecting it to durable canonical execution.

## Outputs and counters

Campaign data lives under `artifacts/engineering-workflow-datasets/`. For every
real attempt, the runner must write:

```text
output/<scenario-id>/<attempt-id>/
  run.json                 # immutable attempt/definition/input identity and status
  artifacts/               # actual workflow-created output files
  logs/                    # redacted trace/events
  approvals/               # digest-bound decisions, explicitly manual or test-auto
```

`run.json` records `scenario_id`, `attempt_id`, `run_id`, `dataset_digest`,
`template_digest`, `execution_kind: live | integration`, `accepted_by_runtime: true`,
`definition_digest`, `status`, `started_at`, `finished_at`, and
`produced_files: [{artifact_id, path, sha256}]` (paths relative to `artifacts/`).
A full completion also has `terminal_step_reached: true`,
`all_required_steps_succeeded: true`, and
`external_effects: none | test_destinations`. An integration run executes the
actual engineering chain but routes printer/supplier effects to explicit test
destinations. It can earn a completed integration-process count, with that scope
displayed, but cannot establish live printer/supplier qualification. Whole-chain
fixture playback, synthesized CAD outputs, and a local-phase-only run cannot
earn completion. Every receipt lists the actually executed operation bindings.

Counters are cumulative unique scenario IDs for this campaign, capped at thirty:

1. **Datasets created:** complete manifests and all declared human input files.
2. **Dataset/process combinations run:** the canonical runtime accepted a live or integration
   run for this dataset and definition revision. Preflight failures do not count.
3. **Processes completed with outputs:** full live or integration process terminal state plus
   all expected nonempty output file roles. Logs, input copies, staged fixtures,
   summaries and simulated receipts do not substitute for engineering outputs.
   Test-destination receipts are allowed only for declared external handoff roles.
4. **Processes with valid data:** zero. Engineering correctness is not measured
   in this cycle. Existing runtime safety/identity checks still apply.

Retries retain separate attempt directories and do not inflate these counts.
Inputs and template digests are recorded so changed data does not silently
inherit a previous pass. Earlier cumulative achievements remain in history;
the dashboard also shows whether a pass belongs to the current revision.
No command in this helper dispatches MCP tools, contacts a printer/supplier,
starts model inference, or increments a success counter from planned artifacts.

See `specs/081-engineering-workflow-templates/dataset-campaign/goal.md` for the
unattended implementation and execution prompt and `plan.md` beside it for
the remaining runtime work.
