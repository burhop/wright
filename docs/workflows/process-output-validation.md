# Validate Process Outputs

Wright process validators check the exact output revision created by an earlier workflow step. They measure that output against a pinned requirement baseline and profile, save an immutable assessment, and release downstream work only when the current revision passes. A noncompliant assessment includes measured findings and correction targets that an eligible producing AI step can use for a bounded retry.

This is a runtime process control. It does not claim that every file in a project was checked, replace engineering judgment, or turn a successful tool call into an engineering pass.

For pixel residuals against photographs or other rasters, see
[image-coordinate validation](image-coordinate-validation.md). Pixel checks bind
the exact reference image and coordinate convention; they do not establish a
physical scale or camera calibration.

## Add a validator in Workflows

Open a workspace and select **Workflows**. In the editor:

1. Add **Review → Validate output** after the step that creates the artifact.
2. Select a validation profile. Wright saves the profile and requirement-baseline versions and SHA-256 digests in the workflow.
3. For every required subject role, choose the exact connected producer output.
4. Connect the validator to downstream work with a **pass** approval route. Keep the ordinary data connection from the producer when the consumer also needs the original artifact.
5. Leave **Maximum corrected revisions** at `0` to hold and report. To allow correction, choose the eligible producer and set a limit from `1` to `3`.
6. Save and run the workflow.

The run drawer shows **Output held for correction**, **Repairing output**, or **Correction budget exhausted** when those states occur. Open **Technical log and telemetry**, then choose **Open validation assessment** to inspect the saved JSON evidence for a check. A recovered run exposes the same assessment path.

The complete runnable structured process is `tests/datasets/process-validation/processes/structured-loop.workflow.wflow`. The source contract, including required task and port fields, is `specs/082-output-content-validation/contracts/process-source.md`.

## What a validator binds

A validator configuration contains four kinds of identity:

- `profile` pins the check definitions and their digest.
- `baseline` pins the requirements and their digest.
- `subjects` maps every profile role to one connected input port. Wright never searches neighboring files or guesses which output to inspect.
- `budget` bounds bytes, entities, time, and memory.

Profiles are closed data documents. They may declare selectors, readers, comparison operators, units, frames, tolerances, scope exclusions, and limitations. They cannot contain executable predicates or commands. The packaged schema is `specs/082-output-content-validation/contracts/schemas/ValidationProfile.schema.json`.

Packaged profiles are immutable application resources. A workspace-owned profile must be a confined workspace-relative `.json` file. In either case, save the references returned by the loader; do not calculate profile pins from the candidate output.

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python -m workspace_service.process_validation_cli profile `
  --profile structured-demo
```

The command returns the complete profile plus `profile_ref` and `baseline_ref`. A changed profile or baseline requires a deliberate workflow update with new pins.

## Reader prerequisites and limits

| Reader                 | Inputs and prerequisites                                                                                                     | Qualified scope                                                                               | Does not establish                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `structured@1`         | Inline values or bounded JSON, CSV, text, Markdown, or HTML files; explicit selectors, types, units, and row rules           | Generic structured content checks; the packaged `structured-demo` profile                     | Document semantics that the profile does not declare                   |
| `step-seat-geometry@1` | An actual bounded ISO-10303-21 STEP snapshot containing the declared circle placements, roles, units, and workpiece datum    | Seat centers and diameters for `parametric-drill-jig-01`                                      | General CAD correctness, manufacturability, collision, or physical fit |
| `thermal-field@1`      | Actual bounded CSV/JSON field, balance, candidate, and refinement files with source/load/material lineage and declared units | Analytical rise, heat balance, refinement, and selection checks for `heat-spreader-sizing-01` | A solver run, CFD qualification, or physical thermal acceptance        |

These readers work offline and do not require AgentCAD, build123d, CadQuery, OCP, or a solver in the Wright runtime. A producing MCP server or engineering application remains separately owned and qualified. Provider-backed subjects must include the provider, resource, revision, and readback identity expected by the registered reader.

For an exact JSON artifact containing another JSON document as a string, the
optional `structured-json-container@1` reader accepts the profile parameter
`json_container_pointer`, such as `/content/0/text`. The check's `selector`, unit,
frame and uncertainty pointers then address the decoded inner document. Both
documents use the strict finite, duplicate-free JSON parser and bounded structure
checks. Evidence retains the original outer artifact hash and both selector paths;
no rewritten intermediate report becomes the subject. The ordinary `structured`
reader and saved profiles keep their existing interpretation.

This reader performs one explicitly selected decode, with no provider-specific
envelope detection or implicit search through other messages. Missing containers,
non-string values and malformed JSON hold the output. A provider success flag
alone remains insufficient: the profile must check the actual observations and
relevant failure indicators. For example, a dimensional check still selects the
inner `/length_mm` observation and evaluates it against its pinned constraint;
an outer `status: pass` flag cannot substitute for that measurement.

If a required reader, role, format, datum, unit, or source revision is unavailable, Wright returns a blocked or needs-input assessment. It does not reinterpret the missing capability as a defect in the product. The machine-readable map at `packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json` lists qualified, implemented, planned, and unavailable capabilities. Qualification is per declared profile scope; it is never inherited by a related scenario.

## Correction policy

Every check first writes its assessment evidence. Downstream work remains held unless the assessment is current and `summary.release_eligible` is true.

For ordinary AI-produced text or structured output, bounded correction may target only the single preceding producer that owns all checked subjects. That producer must use indexed output policy. Wright sends at most 20 prioritized findings in a 16 KiB feedback packet, includes passing constraints to preserve, creates a new output attempt, reruns the complete profile, and invalidates downstream results from the replaced segment.

The runner stops when the output passes, the configured limit is exhausted, the same output and defect fingerprint make no progress, validation needs input, a reader fails, or the run is cancelled. Budgets survive resume. An older passing assessment never releases a newer revision.

MCP file correction requires an explicitly compiled `revision_policy: create_new_files` segment with indexed expected files and one exact file mapping per output. It does not authorize in-place application edits, overwrite policy, arbitrary back-edges, unrelated tool calls, external actions, or physical operations.

## Run an offline CLI example

The CLI evaluates only a registered producer output. The preparer below creates a fresh local workspace, registers one exact structured output revision, and writes a request pinned to `structured-demo`:

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
$root = ".local-run/process-validation-example"
uv run python examples/process-output-validation/prepare_example.py `
  --workspace $root `
  --length-mm 100

$result = uv run python -m workspace_service.process_validation_cli evaluate `
  --workspace $root `
  --workspace-id validator-example `
  --db "$root/validation.sqlite3" `
  --request request.json `
  --profile structured-demo | ConvertFrom-Json

$result.release_eligible
$result.assessment_id
```

The expected verdict is `True`. Change `--length-mm` to `98` to produce a measured failure. `evaluate` exits `0` for a release-eligible assessment, `2` for a completed noncompliant assessment, and `1` for invalid input or an operation error.

Use the returned assessment ID with the same workspace and database:

```powershell
$assessment = $result.assessment_id

uv run python -m workspace_service.process_validation_cli get `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" --assessment $assessment

uv run python -m workspace_service.process_validation_cli read `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" --assessment $assessment `
  --cursor 0 --limit 20

uv run python -m workspace_service.process_validation_cli export `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" --assessment $assessment `
  --format markdown | Set-Content -Encoding utf8 "$root/assessment.md"

uv run python -m workspace_service.process_validation_cli export `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" --assessment $assessment `
  --format csv | Set-Content -Encoding utf8 "$root/traceability.csv"
```

`get` returns the complete report envelope. `read` pages actionable findings. `export` supports `json`, `markdown`, and `csv`; the CSV is the requirements traceability matrix.

Readable reports include each requirement's review obligation and the recorded
numerical uncertainty allowance beside its observations. The allowance uses the
observed unit and datum frame. Zero can be a default, so it is not proof of zero
measurement error or physical accuracy. Missing and non-numeric observations are
identified explicitly. CSV exports retain this context in the appended
`review_required`, `measurement_uncertainties`, and `uncertainty_note` columns;
the original assessment and engineering verdict remain authoritative.

## Consume validation reports

All projections come from one `wright.process-validation-report/1` document. A consumer determines the effective verdict with both fields:

```text
currentness.is_current AND assessment.summary.release_eligible
```

Keep every traceability row, its requirement source, expected constraint, observations, units, frames, evidence references, subject digest, producer attempt, finding IDs, and action. Show excluded scope, limitations, and `physical_validation`. A historical pass can remain visible, but it cannot be presented as the current release decision.

Authenticated workspace routes are:

```text
GET /api/workspace/process-validations/{assessment_id}?session_id={session}
GET /api/workspace/process-validations/{assessment_id}/findings?session_id={session}&cursor=0&limit=20
GET /api/workspace/process-validations/{assessment_id}/export?session_id={session}&format=json|markdown|csv
POST /api/workspace/process-validations/{assessment_id}/reviews
```

The review body contains `session_id`, `requirement_id`, `decision`, `rationale`, and nonempty `evidence_refs`. Wright derives the reviewer and authority from the authenticated request, appends a new assessment, and preserves the original.

Treat finding text and requirement text as untrusted display data. Preserve opaque `wright://` evidence references, escape rendered content, and neutralize spreadsheet formulas. The full report boundary is `specs/082-output-content-validation/contracts/report-consumer.md`; schema-valid examples are in its sibling `examples/` directory.

## Reproduce the retained demonstrations

The structured loop requires a configured, healthy Hermes-compatible model endpoint and refuses to overwrite an evidence directory:

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python scripts/run_process_validation_structured_loop.py `
  --output-dir artifacts/process-validation/structured-loop/<new-UTC-run-id>
```

The engineering demonstration additionally launches its isolated selected MCP dependency set and uses the retained heat inputs read-only:

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python scripts/run_process_validation_engineering.py `
  --output-dir artifacts/process-validation/engineering/<new-UTC-run-id>
```

These are demonstration commands, not normal runtime prerequisites. The retained qualifying evidence and independent verifiers are listed in `specs/082-output-content-validation/progress.md`.
