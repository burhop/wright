# EPP-F01 CLI Contract

## Entrypoint

```text
python scripts/validate-engineering-process-program.py <command> [options]
```

The command is local, non-interactive, offline, and deterministic for one committed subject after declared observation fields are excluded. It never runs product code, benchmark cases, MCPs, models, applications, network requests, Git mutations, approvals, integrations, or release actions.

## Commands

### `validate`

```text
validate --source <git-commit-ish> [--program-root <relative-path>] [--format text|json]
```

- Default source: `HEAD`.
- Default program root: `docs/programs/engineering-process-platform`.
- Default format: `text`.
- Reads committed inputs only from the resolved Git commit.
- Reports checkout representation separately when invoked inside a worktree.
- Does not write any file.

### `generate-dashboard`

```text
generate-dashboard --source <git-commit-ish> --output <repository-relative-path> [--format text|json]
```

- Output must resolve to the declared dashboard target inside the repository and may not traverse symlinks or escape.
- Validates the complete source before constructing output.
- Writes one candidate transactionally and reports it as non-evidence until the required source/container commit relationship is proven.

## Result Model

Text and JSON are renderings of the same schema-valid validation report. Text is concise and includes:

1. verdict and exact source identity;
2. checkout representation/cleanliness;
3. highest-severity findings in deterministic order;
4. four readiness areas in fixed order;
5. release eligibility and exact approval status;
6. sole next action or blocker;
7. smallest recovery step.

JSON validates against `validation-report.schema.json`. Machine output is UTF-8/LF with sorted keys and a trailing newline. Only `observed_at` and explicitly identified filesystem-delivery observations may differ between otherwise identical runs.

## Exit Status

| Code | Meaning |
|---:|---|
| `0` | Validation passed; generation, if requested, committed its local replacement successfully |
| `2` | Input/CLI usage invalid |
| `3` | Structural or schema validation failed |
| `4` | Semantic, authority, eligibility, or readiness validation failed/blocked |
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
- `OUTPUT_REPLACE_FAILED`

Codes are contract surface. Renaming or changing their meaning requires a schema-major or explicitly compatible migration decision.

## Privacy and Path Rules

Outputs are assembled from approved labels, IDs, counts, relative paths, and digests. Never render raw source values, JSON Schema instance values, raw exception text, commands/arguments, environment values, credentials, bearer strings, prompts, logs, private endpoints, proprietary payloads, engineering artifact bodies, reusable authority, drive paths, UNC paths, or absolute POSIX paths.

Git is invoked by argument array with `shell=False`. User-provided revisions and paths are validated before invocation. No command may invoke a shell or a mutating Git subcommand.

## Compatibility

Only explicitly listed producer/consumer versions are accepted. Unknown major and undeclared newer minor versions fail closed. The seed dashboard and uncommitted candidate are never accepted as committed evidence.
