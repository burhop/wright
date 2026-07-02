# Contract: Validation CLI And Evidence

## Commands

```text
uv run python -m tool_registry.validation_cli plan <server-id>
uv run python -m tool_registry.validation_cli validate <server-id> --container ubuntu-x64
uv run python -m tool_registry.validation_cli validate <server-id> --executor mock
```

## Execution Rules

- Default fast tests may use the mock executor only.
- Docker clean-container execution is explicit and operator-invoked.
- A Docker executor that does not run must produce skipped/follow-up evidence, not passed evidence.

## Evidence Outputs

For each validation ID:

- `<server-id>-validation.json`
- `<server-id>-validation.md`

JSON is canonical. Markdown is a human review summary.

## Redaction Requirements

Evidence writing redacts:

- credential values
- secret-like assignments
- full environment maps
- command arguments
- tool arguments
- subprocess output
- diagnostics
