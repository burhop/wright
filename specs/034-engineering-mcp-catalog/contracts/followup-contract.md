# Follow-Up Contract

## Trigger

A follow-up record is required when validation status is `failed` or when an entry is explicitly classified as `non_working`.

## Local Record Format

Follow-up records live under `docs/mcp-catalog/followups/` and use stable names:

```text
<server_id>.md
```

Required sections:

- Title
- Server ID
- Source URL
- Verification state
- Current installability tier
- Environment
- Observed failure
- Expected behavior
- Reproduction steps
- Missing context or dependencies
- Suggested next action
- GitHub PR/issue URL, when available

## Deduplication Rule

If a record already exists for the same server and failure signature, update or link the existing record instead of creating another one.

## Secret Handling

Follow-up records must redact credentials and environment values that look like tokens, secrets, or passwords.
