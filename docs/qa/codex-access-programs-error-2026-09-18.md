# Codex request rejection

Status: diagnosed to the Codex model-request boundary; not fixed locally.

At 2026-09-18 14:45:43 UTC (10:45:43 America/New_York), Codex's local log recorded a turn failure on `/responses`:

```json
{
  "type": "invalid_request_error",
  "code": "unsupported_parameter",
  "message": "The access_programs parameter is not enabled for this organization.",
  "param": "access_programs.cyber"
}
```

HTTP status: 400. The affected turn logged model `gpt-6-astra` and ChatGPT authentication. The turn identifier is intentionally omitted from committed evidence.

This is not the Wright API, MCP runtime, or the separate Vitest teardown error. No `access_programs` reference was found in Wright's apps, packages, .codex or .agents directories, or in the local Codex config. The local config was not edited. No credentials or raw request bodies were collected.

The evidence does not establish why Codex attached this parameter, nor that a reboot or model change would fix it. No documented local override for this exact parameter was found. Do not patch binaries, invent config switches, change accounts, or bypass access controls.

If it recurs, report the timestamp, turn ID, parameter, model and error through Codex feedback or OpenAI support. Official guidance recommends `/feedback`, when available, for suspected Codex false positives: https://learn.chatgpt.com/docs/cyber-safety#false-positives

The requested Luna work queue is saved separately in `docs/qa/luna-two-hour-usability-goal.md`. Select Luna explicitly before submitting it; the prompt itself cannot change the session's model. This investigation did not launch that goal.
