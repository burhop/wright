# EPP-F01 Quickstart and Acceptance Journey

This is the implemented local EPP-F01 validation and snapshot journey. It validates and projects existing committed evidence only; it does not authorize integration, benchmark execution, EPP-F01B implementation, or release work.

## Prerequisites

- A local Wright Git checkout on a supported Windows or POSIX host.
- Git metadata for the committed subject.
- The repository's existing locked Python environment with the `runtime` extra; no network, product runtime, MCP, model, benchmark system, container, or proprietary application is required.
- A clean checkout is required to claim a committed-current result. Dirty checkout observations may be diagnosed but are never approval evidence.

## 1. Validate without writing

From the repository root:

```text
python scripts/validate-engineering-process-program.py validate --source HEAD --format text
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
python scripts/validate-engineering-process-program.py validate --source HEAD --format json
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
python scripts/validate-engineering-process-program.py generate-dashboard --source HEAD --output docs/programs/engineering-process-platform/dashboard.json --format text
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

### Known committed-history correction

The immutable history contains one known stable cause, `EPP-F01-US1-COMMITTED-IDENTITY-001`: six v2 transition output-digest mismatches and 31 wrong-tree field occurrences across state revisions 1–26. Do not edit those records. Until exact V4 approval exists, the validator must report the affected artifact, exact JSON pointer, recorded and Git-authoritative values, correction ID, and `resolution_status=unresolved`, emit no implementation authority, and stop.

After V4 approval, only `COR-EPP-F01-US1-COMMITTED-IDENTITY-001` may resolve the cause. A valid run recomputes `37/37`, retains the original findings with `resolution_status=resolved` and the correction reference, and proves that the four readiness areas, benchmark 0–100 counters, freshness, gates, candidate identity, approvals, and release eligibility are unchanged. Any missing/extra/substituted target, profile digest mismatch, non-ancestor target, forbidden readiness/authority target, or unsupported validator version fails closed. There is no manual acceptance flag and no recovery path that edits TR-0023 through TR-0025 or state revisions 1–26.

TR-0027 has one separate known input-origin defect: `/inputs/3` names the planning approval at source `c3012733`, although Git proves that approval first appears with TR-0027 in container `88481d57`. Do not edit either artifact. Until exact V5 approval, validation must retain the finding and stop. After approval, only `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001` may dispose it, after exact `1/1` source-absence/container-introduction proof. Any broader exception or change to authority/readiness results fails closed.

The failed first T066 candidate exposed one later repair-evidence cause: state revisions 45 and 46 use an underscore-form stable cause identifier that violates the closed grammar, and TR-0044 truncates the exact TR-0043 SHA-256 at `/inputs/1/sha256`. Do not edit those records. Only `COR-EPP-F01-REPAIR-EVIDENCE-001`, after exact V7 approval, may dispose the two ordered claims. A valid reader must rehash the exact Git blobs, prove exactly two affected cause-ID occurrences and the full 64-character TR-0043 digest, retain the original findings, and leave state, lifecycle, lease, authority, all four readiness areas, benchmark counters, candidate, delivery, and release results unchanged. Until then, stop before T070–T072 or any T066 retry.

## 6. Compatibility and rollback

| Input or environment | Supported result |
| --- | --- |
| Current v2 contracts and exact committed runtime bundle | Validate and project |
| Frozen v1 revisions 1–9, then 10–19 | One ordered bridge to v2 only |
| Revision 20+ v1, second migration, unknown major/minor | Fail closed with compatibility exit `6` |
| Windows/POSIX checkout line-ending difference | Same committed-blob semantics |
| Missing/removed validator | Manual inspection only; existing snapshot is stale/unsupported |

- Windows and POSIX runs for the same committed blobs must agree semantically even when line endings differ in clean checkouts.
- Only explicitly listed compatible schema/snapshot versions are accepted. Legacy v1 is limited to the closed revision-1-through-9 bootstrap and revision-10-through-19 bridge profiles; revision 20, any later v1 record, and a second v1-to-v2 migration fail closed. Unknown majors and undeclared minors also fail closed.
- The committed-identity correction profile is an explicit compatibility boundary. Older readers that do not understand it fail closed; they must not silently ignore it or show a green historical result.
- Removing the validator restores the README's manual verification path: inspect `program-state.json`, `roadmap.json`, the referenced transition/approval records, and every recorded Git blob/digest; recompute the sole next action without editing source evidence. Any validator-generated snapshot becomes stale/unsupported rather than authoritative.

## Acceptance commands

Run from the repository root with the existing locked environment:

```text
python -m pytest tests/program_control_plane -q -p no:cacheprovider --basetemp <writable-temp-directory>
python -m ruff check scripts/program_control tests/program_control_plane
python -m ruff format --check scripts/program_control tests/program_control_plane
```

Before any push or merge, the repository's documented Wright Git gates remain the source of truth. EPP-F01 implementation approval will not itself authorize push, PR, merge, dev integration, publication, or release.

## V8 planning-only preflight and committed-byte recipe

The current committed subject is intentionally fail-closed. Reproduce it without writing:

```text
D:\Users\markb\miniconda3\python.exe scripts/validate-engineering-process-program.py validate --source HEAD --format text
D:\Users\markb\miniconda3\python.exe -m pytest tests/program_control_plane/test_evidence_walkthrough.py -q -p no:cacheprovider --basetemp D:\repos\wright\.tmp-epp-v8
```

Expected before V8 implementation: four fatal validator rows and three walkthrough test failures representing two walkthrough causes. The separately failing roadmap-policy inversion test is recorded but excluded.

For committed Markdown identity, never use `Get-FileHash`, `Get-Content`, or another checkout/text pipeline. Resolve the blob with `git rev-parse <subject>:<path>` and hash the raw bytes returned by `git cat-file blob <blob-id>`. For a staged file, resolve `git rev-parse :<path>` first. PowerShell text pipelines and checkout bytes can normalize line endings and reproduce the wrong TR-0047 values.

Post-approval acceptance requires exact `3/3` disposition, a one-field gate-evidence rebind, all three walkthrough tests passing from the two authorized causes, deterministic repeated output, and full non-interference at honest `0/100` plus the isolated non-empty synthetic unit fixture. These are six authorized targets. The fixture creates no process, qualification, attempt, dashboard progress, or benchmark evidence. Stop on any authoritative benchmark change, seventh target, generic waiver, dependency, dashboard generation, lease expansion, or excluded action. Stop after V8 verification; T066 remains separately blocked.

## V9 planning-only preflight

V8 implementation is interrupted. Preserve the unfinished T073 working copy in its reversible stash and do not apply it. Inspect the two immutable targets from Git objects, never checkout-normalized bytes:

```text
git rev-parse c12eb00308cb72d96977846c4ae876dc0baa7e7e:docs/programs/engineering-process-platform/evidence/verification/EPP-F01-V8-discovery.json
git rev-parse c12eb00308cb72d96977846c4ae876dc0baa7e7e:docs/programs/engineering-process-platform/evidence/transitions/TR-0051.json
git diff-tree --no-commit-id --name-only -r c12eb00308cb72d96977846c4ae876dc0baa7e7e
```

The first target may be validated only by the exact-value external `v8-discovery-evidence.schema.json`; the immutable blob still has no `$schema`, and that original finding remains visible. The second must prove all 35 recorded paths are unique and exactly equal the containing commit's changed set, with only the transition self path at recorded index 34 instead of sorted index 9. Do not generalize either rule.

Pre-implementation planning acceptance is schema validity, exact `2/2` profile identity, planning/promoted byte equality, state/archive equality, independent omission review, and read-only Spec Kit analysis. Runtime validator success is not expected or claimed. T077–T080 require fresh V9 approval. T073–T076, the roadmap-policy repair, T066–T068, EPP-F01B, dependencies, benchmarks, external changes, integration, publication, and release remain blocked.
