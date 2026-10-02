# Installed historical navigation after prototype retirement

**Date:** 2 October 2026. **Scope:** native installed, isolated read-only history.
T048/T049 and the full feature remain incomplete.

## Artifact and environment

Built current source commit `021c3a083fff189c617ebf10b2e4fc570724c2dd` with a fresh
production frontend, staged away from the checkout's packaged assets. Installed
`wright_engineering-0.1.9-py3-none-any.whl` into a dedicated native Python 3.13.5
environment without downloading dependencies or installing a compiler/model.

- Wheel SHA-256: `bdf22b705bade14132c75ead42e92ad8020f23d77e01b783b05b021ccaabdcae`.
- Frontend manifest SHA-256: `cbb9e5aa238ec88bf29f4b0ff8b8f10bb9bae340fa3e37af951f7c39bdce2f1a`.
- Owning API/core/storage/agent/workspace/registry/native modules import from
  the dedicated installed environment. Cached third-party dependencies are
  available without processing the checkout's editable-install pointers.
- The aggregate wheel passes the repository's native distribution inspector.
  Both retired prototype workspace modules are absent from the archive and
  are not importable by the installed host.
- Owning native bootstrap supplies the workspace root and same-site hostname.
  Provider autostart is disabled; compiler discovery is unavailable.
- Fresh database/workspace copies retain the failed canonical run
  `a87d84b40a244bcaa035d9ed8308ac5a`. This does not test the original user workspace
  or establish compatibility with every historical prototype data shape.

## Observed journey and authority

Six diagnostic-strict browser checks pass through the normal workspace:
Workflows entry, preserved editor with no vendor demo button, exact historical
link and original failure/eleven outputs, return to the same workflow, reopen
history, and open its exact saved recorder in a Wright file tab. No process
start, generation, tool operation, review response or external action is submitted.

Eight retired URLs separately return HTTP 410 `PROTOTYPE_RETIRED` from the
installed API; historical reads return HTTP 200 for the exact recorded identity.
No provider is contacted by those handlers. The saved source/run hashes and
all five scoped UI/authoring/continuation table hashes remain unchanged. Original
campaign/context and privately preserved prototype bytes also remain intact.

The final browser has zero unexpected failed responses and zero page errors.
One expected `/api/agent/models` 503 and its console messages remain disclosed:
the fixture intentionally has no model service. This is not silent-console proof.
S03 was visually inspected; it shows the read-only historical result and saved
artifact links. This is evidence navigation, not full editor/design acceptance.

## Retained failures and fixture correction

Attempt 001 could not launch cached Chromium inside the sandbox and never
navigated. Its pending report and explicit launch-failure record remain intact.
Attempt 002 passed five history/editor checks before stopping on settings/MCP
500s and model 401s. Server evidence traced these to the fixture's default
host credential directory and unrelated default agent service. No UI repair,
database substitution or provider retry was made to hide those failures.

The exact owned host was stopped after confirming the configuration errors.
Fresh fixture 002 uses supported `WRIGHT_SECRETS_PATH`, explicit fixture-local
Hermes config/home/env paths, and a checked unused loopback agent endpoint.
It reads no host credentials and invokes no model. Attempt 003 then passed all
six checks. Configuration isolation is a fixture change, not a claim that the
product's default user-level settings paths are incorrect.

## Evidence and remaining work

Artifacts are in `artifacts/process-interfaces/083/20261002-installed-history-retirement-001`
through `003`. The final walkthrough structure validator passes. Actual bearer
and cookie values were scanned against all public report/script/screenshot bytes;
authenticated traces remain private. Final verification records exact wheel,
frontend, installed module identity, unchanged hashes and diagnostic scope.

The successful report is
`artifacts/process-interfaces/083/20261002-installed-history-retirement-003/workspace-walkthrough/report.html`.
The isolated installed fixture is on port 8035; it is not a production/device
test or an authoring-ready host. Earlier native/Docker saved-interface proofs
refer to their own earlier candidate and retain their separate identities.

Independent provider qualification, transitive dataset/jig slicing dispositions,
actual original prototype data compatibility, full engineering/common-tailored
parity and editor acceptance remain open. Both retained second-run reviews
remain unanswered. No public artifact, catalog promotion or release is implied.
