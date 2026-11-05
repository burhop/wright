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

## Normal build and dependency-light update (04:56 UTC)

The normal package gate regenerated stale checked-in main-app assets and the
runtime-extra lock hash. The earlier direct-built wheel qualified its desktop
bundle but is superseded for the complete installed-app claim. Normal-build wheel
`6e356e931d0af0f9552702fbbe8436b94bf4fd86f6438657d16b147184482e77` passes the
installed browser and managed lifecycle proofs; both retained failures and all
previous artifacts remain preserved.

Actual deployment preparation then found that the dependency-light CLI imported
vault/runtime dependencies during update (`ModuleNotFoundError: structlog`). The
full gate was stopped and recorded incomplete before correcting this product
fault. The migration owner now uses the confined active runtime for schema reads
and verified candidate runtime for activation; it invokes the same vault migration
methods, preserving their backup, compatibility and operation-identity checks.
No heavy runtime dependencies were added to the manager. Child errors remain
failures; no fallback or tracebacks containing database content enter CLI evidence.

The native regression suite passes: 147 tests, 7 existing skips. Eleven new
boundary cases cover installed selection, exact inputs, invalid state/path/schema,
child failures and backup confinement. Fake-installer lifecycle fixtures explicitly
retain the actual in-process migration owner because they contain no executable
runtime. The installed proof uses a real dependency-light CLI without structlog,
starts the prior wheel, saves a disposable workflow, restarts, updates to corrected
wheel `faa5bf561e93529ce01ede7ab2492f465db27bfb2160fce28bcf99f3670bf277`, and
reopens identical source. Evidence: `light-manager-update/receipt.json`.

PR #190 coordination is recorded in comment 6649945546. Its startup/readiness
policy remains untouched; shared lifecycle change is constructor plumbing only.
A fresh owned candidate has been prepared outside repository and temporary paths;
original prototype services/data are preserved. Named plugin activation and the
fresh full gate remain pending at this checkpoint. No engineering run occurred.

The bare `.wflow` control also violates the existing accepted-source path contract
(`workflows/<name>.workflow.wflow`). It must not be used as proof of saved-workflow
rendering. Two canonical controls are now registered in a disposable candidate
workspace. This corrects the experiment, not host automatic viewer selection.

## Named activation, installed navigation and browser qualification (5 November)

Only `wright-desktop-gb10-prototype` was updated to wrapper 0.39.0 after local
qualification. Its command now uses the dependency-light manager and owned state
under `~/.local/share/wright-desktop-maintained-candidate`, with no repository
launcher or temporary build path. The prior service, cache and data remain.
The current chat still reports the older binding; no fresh visual acceptance or
desktop restart was claimed. Evidence: `named-plugin-update.json`,
`stable-candidate-profile-check.json`, `current-chat-connection-observation.json`.

Full gate 7 completed FAIL, not pending: all preceding backend/security/docs and
2,310 frontend tests passed, followed by 164 browser passes, 15 skips and 36
missing-browser failures. Firefox now passes 19 existing tests with an isolated
API. After scoped dependency repair, WebKit still aborts before any Wright page.
Debugger evidence identifies its 16 KiB page ceiling on this 64 KiB GB10 host.
No kernel, browser binary, security option or test policy was changed. The failed
full gate remains blocking; no push/CI or merge is claimed.

P09's installed screenshot review found indistinguishable duplicate files and
internal run records in the main list. A narrow presentation correction adds
folder captions/accessibility names only for duplicates and collapses canonical
run records into searchable technical details, retaining normal JSON files.
The first screenshot caught wrapping file-type labels; a non-wrapping type cell
and a rendered text-rectangle assertion correct and cover that defect. The
normal wheel and sdist were rebuilt and the final installed journey passed with
all retained files unchanged. Evidence: `file-list-focused.log` (21 tests),
`file-list-final-proof/` (actual installed package, simulated Linux host), and
`file-list-final-lint.log`. No engineering work was run.


## Current installed candidate and additional qualification (5 November)

The named 0.39.0 wrapper now launches normal-build wheel
`9b03e94d95ab5fe742d9f1b3b6d96013d28bc47a483b2488ca774ce7c6d4a2b8`
from the owned maintained candidate. Actual MCP profile/resource verification and
exact-image Docker checks pass; image ID
`635a9c835da4b760d2190d9b6be35ed40d868b0edacf4eb8b254c39595083129`.
No unrelated lifecycle/configuration or Windows pilot change occurred.

Gate 9 at `de0886b9` passes with the repository's documented local browser-host
exception. Complete current-head CI remains required, including browsers. The
strict CLI/release type check passes; the existing broad warning-mode mypy check
still reports duplicate test `conftest` modules, not a clean broad type check.
The earlier failed gates remain retained; none is relabeled.

Installed first-contact creation and exact-scoped chat handoff, reference-byte
portability/collision rejection, and genuine edited-source mismatch/Undo now have
separate receipts. The negative draft test's original read-only helper correctly
rejects a newly added draft; its separate strict audit confirms that one exact
observed draft is the only addition and all preexisting files remain unchanged.
See acceptance for precise scopes and evidence. No real engineering run or new
Windows observation was performed. Full handle/Robot, required human review and
Windows acceptance remain mandatory and unfinished.

## First PR qualification cycle (5 November, 07:35 UTC)

Draft PR [#191](https://github.com/burhop/wright/pull/191) contains head
`01ad105f`; the normal pre-push gate passed without skip flags, including 48
editor/process and 6 MCP onboarding browser checks. The full merge receipt
remains at product head `de0886b9` with its documented WebKit host exception.
Native installed smoke passed on Windows, macOS and Linux in CI. These are
packaged-runtime checks, not native Codex UI or file-delivery acceptance.

Two first-cycle findings are being corrected together. The native lifecycle job
lacked an explicit Python setup and its runner default could not install the
pinned Hermes 0.19.0. It now selects the same 3.13 interpreter as the native
platform matrix; the shared gate policy rejects missing, late or incompatible
setup. All lifecycle commands and dependency versions remain intact.

CodeQL identified an environment-backed public sign-in mode flowing into
configuration provenance. The existing owner already rejects every value except
`authorization_code` and `device_code`; it now maps accepted input to those fixed
literals before storing/hashing public metadata. Credential handling, the shared
canonical digest, and scanner rules are unchanged. Invalid input is rejected
before persistence without echoing its value. The focused desktop suite passes
25 tests; workflow/native/correction policy suites pass 31. The initial sandboxed
ASGI attempt stalled and was interrupted; only the subsequent authorized loopback
run is counted.

Exact CI findings and focused logs are retained in private
`.local-run/production-integration/ci-correction-diagnosis.json`. Remaining
first-cycle jobs and correction qualification are pending. No second push,
installed-candidate update, engineering run, dev merge or release is claimed.
