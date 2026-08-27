# EPP-F01 CLI Contract

## Entrypoint

```text
python scripts/validate-engineering-process-program.py <command> [options]
```

The command is local, non-interactive, offline, and deterministic for one committed subject after declared observation fields are excluded. It never runs product code, benchmark cases, MCPs, models, applications, network requests, Git mutations, approvals, integrations, or release actions.

## Commands

### `validate`

```text
validate --source <git-commit-ish> [--container <git-commit-ish>] [--delivery <git-commit-ish>] [--program-root <relative-path>] [--format text|json]
```

- Default source: `HEAD`.
- Default program root: `docs/programs/engineering-process-platform`.
- Default format: `text`.
- Reads authoritative readiness inputs only from resolved `S`; reads dashboard bytes from resolved `C` and the fixed delivery-evidence record from explicit `D` only to prove the external delivery relation.
- `--container` resolves the exact dashboard-containing commit `C`. When omitted, the command may infer only `HEAD`, and only when `HEAD` has first parent `S` and `S..HEAD` changes exactly the declared generated outputs. Otherwise container resolution is absent/unresolved and no committed-current delivery may be reported.
- `--delivery` resolves exact delivery-evidence commit `D`. It is valid only when `C` resolves, `D` has first parent `C`, and `C..D` changes exactly `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-dashboard-delivery.json`. `D` is never inferred, searched for, or selected from multiple descendants; omission leaves delivery resolution absent and prevents `committed_valid` without making the source validation invalid.
- Reports checkout representation separately when invoked inside a worktree.
- Does not write any file.

### `generate-dashboard`

```text
generate-dashboard --source <git-commit-ish> --output <repository-relative-path> [--format text|json]
```

- Output must resolve to the declared dashboard target inside the repository and may not traverse symlinks or escape.
- Validates the complete source before constructing output.
- Writes one candidate transactionally. The dashboard bytes always remain `candidate_not_evidence`; a later `validate` result may report committed-current delivery only from exact `S`/`C` proof plus independent descendant-`D` delivery evidence.

## Result Model

Text and JSON are renderings of the same schema-valid validation report. Text is concise and includes:

1. validator verdict, exact source identity, closed validator source-bundle digest, explicit/`HEAD`-inferred/absent container resolution, and explicit/absent delivery resolution;
2. checkout representation/cleanliness;
3. highest-severity findings in deterministic order;
4. four readiness areas in fixed order;
5. release eligibility and exact approval status;
6. sole next action or blocker;
7. smallest recovery step.

The JSON report additionally carries complete derived gate rows including per-gate `fresh`, the benchmark summary, exact release-approval result, `release_eligible`, and an external delivery envelope that identifies `C` and explicit `D` plus its independent passing evidence when committed-current status is proven; these are the same semantic values summarized in text. Validator `verdict=passed` means the requested subject was structurally and semantically validated and its states were derived; readiness areas may truthfully remain blocked, stale, in progress, or not started, and release eligibility may remain false.

JSON validates against `validation-report.schema.json`. Machine output is UTF-8/LF with sorted keys and a trailing newline. Only `observed_at` and explicitly identified filesystem-delivery observations may differ between otherwise identical runs.

## Exit Status

| Code | Meaning |
|---:|---|
| `0` | Validation and derivation succeeded; readiness/release may still be non-passing; generation, if requested, atomically replaced the local candidate successfully |
| `2` | Input/CLI usage invalid |
| `3` | Structural or schema validation failed |
| `4` | Semantic, authority, or eligibility derivation is invalid, contradictory, or ambiguous; a legitimately derived non-passing readiness area alone is not an exit-4 condition |
| `5` | Dashboard delivery failed; prior snapshot preserved |
| `6` | Unsupported schema/policy/generator compatibility |
| `70` | Bounded internal failure; no raw exception or sensitive value emitted |

Any nonzero result emits no authorized next action. Multiple safe independent findings retain the exit class of the highest-precedence failure.

## Stable Finding Requirements

Every finding contains a stable code, severity, repository-relative artifact identifier, invariant, bounded digest/ID evidence, consequence, and smallest safe recovery. Sorting is severity rank, code, artifact, invariant. Examples of mandatory classes include:

- `JSON_DUPLICATE_KEY`
- `SCHEMA_MAJOR_UNSUPPORTED`
- `SCHEMA_MINOR_UNSUPPORTED`
- `STATE_DIGEST_MISMATCH`
- `TRANSITION_EDGE_ILLEGAL`
- `ROADMAP_CYCLE`
- `NEXT_ACTION_AMBIGUOUS`
- `APPROVAL_STALE`
- `LEASE_IDENTITY_MISMATCH`
- `DASHBOARD_CONTAINER_MISMATCH`
- `DASHBOARD_DELIVERY_UNRESOLVED`
- `DASHBOARD_DELIVERY_RELATION_INVALID`
- `VALIDATOR_RUNTIME_SUBJECT_MISMATCH`
- `OUTPUT_REPLACE_FAILED`

Codes are contract surface. Renaming or changing their meaning requires a schema-major or explicitly compatible migration decision.

## Privacy and Path Rules

Outputs are assembled from approved labels, IDs, counts, relative paths, and digests. Never render raw source values, JSON Schema instance values, raw exception text, commands/arguments, environment values, credentials, bearer strings, prompts, logs, private endpoints, proprietary payloads, engineering artifact bodies, reusable authority, drive paths, UNC paths, or absolute POSIX paths.

Git is invoked by argument array with `shell=False`. User-provided revisions and paths are validated before invocation. No command may invoke a shell or a mutating Git subcommand.

## Compatibility

Only explicitly listed producer/consumer versions are accepted. Legacy v1 is limited to `epp-bootstrap-v1-r1-r9` and the enumerated `epp-bridge-v1-r10-r19`; no later v1 record and no second v1-to-v2 migration is accepted. Unknown major and undeclared newer minor versions fail closed. Seed and generated dashboard bytes never claim committed validity; only the external validation delivery envelope can prove it.
