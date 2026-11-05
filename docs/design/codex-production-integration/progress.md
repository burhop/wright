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

## First-hour checkpoint (03:50 UTC)

Completed the maintained runtime/CLI extraction and installed restart/copy rehearsal.
The retained-results browser journey reached exact image decoding, same-run return
and producing-step availability, then detected two direct HTTP option reads escaping
the desktop transport. Those reads now use a narrow scoped MCP tool forwarding to
the same API/gateway owners. Eleven scope/route tests and fifty UI tests pass;
installed verification of that correction is in progress. The explicit editor
fallback avoids relying on an acknowledged native open as proof of rendering.

The wheel now carries versioned plugin/skill assets as well as the hashed UI;
packaging closure passes. No live plugin/service changes have been made. The scope
still has mandatory engineering and Windows acceptance dependencies, so no honest
completion deadline or production-readiness claim is possible tonight. Independent
packaging, UI regression and repository gates continue. No more user checks requested.

## Qualified installed fallback (03:52 UTC)

The rebuilt wheel passes the complete retained-results browser rehearsal after
runtime restart: title/filename search, acknowledged native-open fallback, exact
source and diagram, selected historical run, visible hash-matched PNG, focus return,
producing-step output availability without false mismatch, same-run return, and
480 px layout without body overflow. This is Linux Chromium with a simulated host.
All files remain byte-identical in both original and copied engineering state.
No engineering run or external tool enumeration occurred. Evidence:
`installed-browser-7/installed-receipt.json` and `installed-browser-7/browser/receipt.json`.
The native UI hash is `1f1badcc5e7d0a86ec6ee44cbf87637b7cf54dcc4bfdfca0f0c6d2f395ca27de`.

Earlier failed rehearsals are retained: missing browser installation, a fallback
callback still pointing at native opening, omitted fixture routes, and missing
copied immutable start/input records. The final rehearsal uses the real owner
records and rejects unscoped, mutation and live-resource-enumeration requests.
It also caught and corrected the real engineering-option HTTP transport gap.
The full original desktop boundary suite is being requalified with its normal
`python -m pytest` invocation; a direct pytest invocation omitted the repository
root from fixture imports and is not treated as a product failure or pass.
