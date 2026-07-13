# Codex MCP compatibility

Verified on 2026-07-11 with `codex-cli 0.144.1`, Windows x64, model
`gpt-5.6-sol`, `mcp 1.28.1`, and Wright protocol target `2025-11-25`.

The executable harness at `scripts/run_codex_mcp_compatibility.py` created a
temporary migrated database and explicit workspace binding, supplied the Wright
STDIO server to Codex through non-persistent inline configuration, and used an
ephemeral read-only Codex session. Codex discovered and called
`wright__workspace_status`; its structured result contained the exact bound
`codex-workspace` and `codex-session`. Exit status was zero. Evidence is written
under `test-results/feature-046/codex-compatibility` and is deliberately not a
published artifact.

Run it locally with:

```powershell
uv run python scripts/run_codex_mcp_compatibility.py `
  --model gpt-5.6-sol `
  --output test-results/feature-046/codex-compatibility
```

Official SDK contract tests additionally verify list/call/read, structured and
stable error results, protocol cancellation, workspace-scoped list-change
notifications, two-session isolation, Streamable HTTP reconnect identity, and
100 concurrent serialized STDIO responses. These behaviors are protocol evidence;
they do not extend the tested Codex platform claim beyond Windows x64.
