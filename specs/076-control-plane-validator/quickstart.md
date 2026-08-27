# EPP-F01 Quickstart and Acceptance Journey

This is the intended post-implementation journey. At the planning checkpoint described by this file, the command does not yet exist and must not be represented as available.

## Prerequisites

- A local Wright Git checkout on a supported Windows or POSIX host.
- Git metadata for the committed subject.
- The repository's existing locked Python environment with the `runtime` extra; no network, product runtime, MCP, model, benchmark system, container, or proprietary application is required.
- A clean checkout is required to claim a committed-current result. Dirty checkout observations may be diagnosed but are never approval evidence.

## 1. Validate without writing

From the repository root:

```text
uv run --extra runtime python scripts/validate-engineering-process-program.py validate --source HEAD --format text
```

Expected success behavior:

- exit `0`;
- exact source commit, source tree, program tree, validator identity, and input-manifest digest;
- clean/dirty checkout reported separately from committed evidence;
- all required structural and semantic checks terminal; validator success is independent of whether readiness areas or release eligibility pass;
- four readiness areas shown independently;
- one proven next action or an explicit no-action blocker.

Expected failure behavior:

- nonzero documented exit status;
- stable, deterministically ordered findings with bounded evidence and recovery;
- no authorized next action;
- no changed source or dashboard file.

Machine output is produced from the same report model:

```text
uv run --extra runtime python scripts/validate-engineering-process-program.py validate --source HEAD --format json
```

To validate a committed dashboard container, identify `S` explicitly and either provide `C`:

```text
uv run --extra runtime python scripts/validate-engineering-process-program.py validate --source <S> --container <C> --format text
```

or omit `--container` only while `HEAD` is the intended `C`. The command may infer `HEAD` only when its first parent is `S` and `S..HEAD` changes exactly the declared dashboard output. It never searches for, guesses, or selects another container.

To request a committed-current delivery verdict after the independent verifier has created `D`, supply all three subjects explicitly:

```text
uv run --extra runtime python scripts/validate-engineering-process-program.py validate --source <S> --container <C> --delivery <D> --format text
```

`--delivery` requires resolved `C`. The command never searches descendants or infers `D`; omission yields candidate/non-evidence delivery without invalidating an otherwise valid source report. A supplied `D` must have first parent `C`, change only the fixed delivery-evidence record, and contain a passing `kind=delivery` record from an independent verifier.

## 2. Generate a local candidate dashboard

```text
uv run --extra runtime python scripts/validate-engineering-process-program.py generate-dashboard --source HEAD --output docs/programs/engineering-process-platform/dashboard.json
```

The command validates all sources before writing, builds all four areas for the same exact candidate, validates temporary output, and atomically replaces the target. Its output bytes always remain `candidate_not_evidence`; committing them does not edit that self-description.

For final feature delivery, the implementation candidate is frozen and independently verified first. That candidate-verification record is committed in source `S`; the coordinator commits only the dashboard in successor `C`; the independent verifier then records a passing delivery-only check of `C` in descendant `D`. A validation report run with exact `S`, `C`, and explicit `D` may report delivery `committed_valid` only after it validates that independent envelope and proves the dashboard bytes plus the allowed `S..C` and `C..D` relations. The delivery record does not become an input to the snapshot at `S`, and any new readiness evidence requires regeneration.

On any write, flush, `fsync`, candidate-validation, or replace failure:

- the command returns nonzero;
- the prior dashboard remains byte-for-byte unchanged;
- no temporary residue remains;
- the delivery result says failed/stale without editing the prior snapshot.

## 3. Inspect evidence

For every gate and finding, follow only repository-relative artifact references and exact Git subjects shown in the output. Do not use conversation history, checked task boxes, or the dashboard as replacement authority. A seed, stale, failed, uncommitted, unsupported-version, or source/container-mismatched dashboard is not evidence.

The four areas remain independent:

- product readiness;
- benchmark readiness;
- commercial readiness;
- program health.

Even `100/100` terminal benchmark success leaves release eligibility false when any other area is not passed or exact release approval is absent/stale.

## 4. Interpret empty, stale, blocked, and failed

- `not_started`: required governed evidence does not yet exist; no progress is inferred.
- `in_progress`: valid partial work exists but at least one required gate is not terminally passing.
- `stale`: evidence once existed but no longer binds the candidate/policy/environment or exceeded freshness.
- `blocked`: progress needs an explicit decision, authority, external control, or prerequisite.
- `failed`: current evidence disproves a required assertion.

Status precedence does not average. One failed gate makes its area failed; no other area can compensate. These are truthful derived product states, not validator failures: a schema-valid report may exit `0` while showing blocked/non-passing readiness and `release_eligible=false`.

## 5. Recover safely

1. Preserve the exact failing report and subject IDs.
2. Start with the highest-severity finding in deterministic order.
3. Apply only the bounded recovery named in the finding and only with current lease/authority.
4. Rerun the complete required check set for the affected transition.
5. Respect the two-repair-cycle stable-cause limit; never weaken rules or rerun until green without a cause record.

If Git metadata is absent, a schema version is unsupported, approval is stale, a digest differs, or lifecycle/roadmap/WIP/lease semantics are impossible, stop. Do not fall back to checkout bytes or manual dashboard edits.

## 6. Compatibility and rollback

- Windows and POSIX runs for the same committed blobs must agree semantically even when line endings differ in clean checkouts.
- Only explicitly listed compatible schema/snapshot versions are accepted. Legacy v1 is limited to the closed revision-1-through-9 bootstrap and revision-10-through-19 bridge profiles; revision 20, any later v1 record, and a second v1-to-v2 migration fail closed. Unknown majors and undeclared minors also fail closed.
- Removing the validator restores the README's manual verification path. Source evidence remains unchanged, and any validator-generated snapshot becomes stale/unsupported rather than authoritative.

## Acceptance Commands (implementation phase only)

The approved task plan will freeze the focused commands. At minimum:

```text
uv run pytest tests/program_control_plane
uv run ruff check scripts/program_control scripts/validate-engineering-process-program.py tests/program_control_plane
uv run mypy scripts/program_control
```

Before any push or merge, the repository's documented Wright Git gates remain the source of truth. EPP-F01 implementation approval will not itself authorize push, PR, merge, dev integration, publication, or release.
