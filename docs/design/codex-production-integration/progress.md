# Maintained desktop integration — implementation checkpoint

5 November 2026 UTC. Branch `codex/codex-production-integration`, based on
`4f370caa9743f869f769f8c8e2332b6b63be438b`.

## Completed slice

- Accepted the existing plan and screen/action map; preserved the planning files and original worktree.
- Moved desktop transport/composition and its content-hashed editor asset into the installed API package. Legacy prototype imports delegate to it for compatibility.
- Added opt-in authenticated normal-runtime composition and `wright mcp desktop`. The CLI selects the existing managed runtime; it does not install another harness or expose credentials in arguments.
- Qualified a clean installed wheel outside the checkout: create, save, exact reopen, MCP resource serving, disconnect, runtime restart and exact reopen.
- Rehearsed migration using only copied engineering files/source metadata/drafts/history, with original and copied hashes checked. Reopened the retained completed block run and its exact PNG bytes before and after restart. No engineering workflow executed; no credentials copied.

## Evidence and limits

| Check | Result | Boundary |
| --- | --- | --- |
| Existing desktop boundary + maintained composition/profile/import tests | PASS: 414, 10 skipped | Local Python; skips retained explicitly in log |
| Wheel content closure | PASS: 2 | Actual locally built wheel |
| Gate-selection/security policy regression | PASS: 63 | Local tests |
| Installed create/save/reopen/restart | PASS | Linux ARM64 private candidate |
| Copied source/draft/completed-run/image preservation | PASS | Installed candidate; historical originals unchanged |
| Automatic native file viewer choice | FAIL | User observed all three files as text on installed 0.38.1 |
| Manual viewer for unregistered `/tmp` controls | FAIL | Saved-context rejection; diagnostic controls were not workspace-owned |
| New candidate Windows UI/download/chat restore | NOT TESTED | No authorized Windows capture/control available tonight |
| Full merge gate | IN PROGRESS | First attempt stopped at required missing candidate image; build exact committed image next |
| Complete handle engineering journey and changed-input rerun | NOT TESTED | Reviewed analysis basis/provider readiness still required |

The controls' context failure must not be fixed by weakening workspace validation.
Future viewer tests use registered disposable workspace files. Neither a tool receipt
nor Linux browser rendering establishes native Windows acceptance.

Exact private logs and hashes: `.local-run/production-integration/evidence-index.json`,
`extraction-final-tests.log`, `gate-contract-recheck.log`, `installed-restart/`,
`copied-state/`, `native-observation.md`. The installed proof precedes a subsequent
docstring-only cleanup; the next committed candidate is rebuilt for full gates.
No installed plugin, existing service, account, Windows pilot or Roadster was changed.
