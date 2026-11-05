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
| Full merge gate | IN PROGRESS | Image/security passed; occupied port avoided; two formatting findings corrected; complete gate still required |
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

## Managed installation and security (04:06 UTC)

The boundary suite completed with 408 passed and 10 skipped. The same unpublished
wheel then passed actual normal managed installation/start/status/doctor, desktop
MCP connection, stop, restart and reconnect in a fresh isolated Linux ARM64 home.
The normal CLI selected its installed private runtime without a repository launcher.
The owned process was stopped; no live prototype lifecycle changed. Evidence:
`managed-native-1/receipt.json`; the reproducible helper is
`scripts/qualification/qualify-desktop-native.py`. No engineering run occurred.

The full gate initially caught a real fixed High/Critical Debian apt transport
vulnerability. Both image stages now install apt/libapt-pkg7.0 3.0.4 with the
existing other security pins preserved. No waiver or scanner-policy change was
used. Image `wright-desktop-maintained:ba9edc0b` passes the scan; evidence is
`test-results/docker-image-security/20261105T040324Z-bcb39ff5/public`.
Full repository qualification continues; CI and merge are not yet claimed.

## Installed authoring and import correction (04:15 UTC)

The installed browser now exercises a separate disposable workspace through
rename, Undo/Redo, save, title search, reopen, export/download, import inspection
and opening the imported source. It does not edit the retained-history workspace.
The first authoring receipt's PASS was too broad: its screenshot showed the old
file after import. The strengthened exact-path assertion fails on the old wheel
(`installed-authoring-negative/`) and passes after the import callback opens the
destination in the same editor (`installed-authoring-fixed/`). Native file opening
from workspace rows remains available; import no longer treats a native-open
acknowledgement as proof that its destination rendered. The original misleading
receipt and screenshot are preserved as superseded evidence.

The corrected tested wheel is SHA-256
`499cde7b7e05d33e570324feb95b4d5ba7afb3e43c561b8dddc27fb588704222`;
UI is `95bfbff7d17b34eabad7b7cbf23bedf9e989e5637173c01b656cd4ab2ac6992f`.
Thirty-six focused panel/transfer tests and the actual frontend type/format checks
pass. The original and copied engineering files remain unchanged. These are
installed Linux/browser proofs, not actual Windows downloads or host acceptance.
