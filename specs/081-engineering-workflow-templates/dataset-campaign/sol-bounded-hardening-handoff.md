# Sol bounded-hardening checkpoint — 2026-09-14

## Outcome

The bounded pass is complete at its limits: six fix/test cycles and two full
Pi03 pilots. No further work may launch under this checkpoint. The dashboard is
live at `http://127.0.0.1:8771/?view=recovery`.

## Changes

- Dashboard startup now serves persisted state before background reconciliation;
  incremental scans reuse unchanged artifact identities, while explicit full
  audits and freshness/error state remain available.
- Model/tool execution accepts only schema-declared successful terminal-operation
  receipts, ends after that proof, and preserves replay/unknown-outcome guards.
- AgentCAD source contracts validate exact confined paths, filenames, flags,
  UTF-8 source, project/build layout, and expected outputs before native work.
- Retry episodes now persist baselines, corrections, evidence hashes, attempt
  grants, outcomes, and the two-correction cap. Usage events persist request/model
  data and record unavailable token counts as unknown.
- API startup exposes bounded stage diagnostics and disables eager MCP startup;
  MCP servers still start lazily when used.
- Pi MCP-task stages cap connected reference inlining at 12,000 bytes. Larger
  durable files remain connected by path, SHA-256, and byte count; their contents
  remain on disk for the exact tool call.

## Verification

Final combined focused suite: **212 passed in 14.66s**. Focused Ruff check:
**passed**. Dashboard reconciliation is `current`/`incremental` with
**30 datasets / 30 combinations / 21 processes with outputs / 0 valid data**
and **20 current-revision completions**. Content validation is disabled.

## Pilots and usage

- Attempt 045: blocked after 6 stages at `prepare_cfd_case`; its 62.2 KB prompt
  exceeded the bridge item limit. Preserved outcome: 35 observed requests,
  34 usage reports, token counts unknown.
- Attempt 046: **completed** (`d3e6f8ead48d4626a40af9fdf2a58ce5`). All 11/11
  required stages succeeded, the local-review approval was retained, both native
  solver runs completed, and 42 files were exported. Usage: 40/40 requests
  reported; runtime labels `hermes`/`wright-hermes`; token counts unavailable and
  therefore unknown. The verified Wright selection before launch was
  `openai-codex::gpt-5.6-sol`.

## Remaining blockers

The overall campaign is not complete: 9 scenarios lack historical output credit
and 10 lack current-revision completion. Content correctness remains intentionally
unmeasured. Attempt 046's local runner state retains a stale transient
`evidence_error` string about a changing snapshot even though its authoritative
runtime/export status and retry-ledger outcome are completed; clean this field
before treating it as an operator alert. Broader Solid Edge/provider, remaining
flagship/sibling, lifecycle, and served-UI qualification tasks remain open.

## Recommended next task

Run one bounded continuation for the highest-priority ready current-revision
scenario, reusing these contracts and retry ledger without reopening Pi03.
