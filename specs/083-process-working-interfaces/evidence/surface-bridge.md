# Managed process transport checkpoint

Date: 2026-10-01. Branch: `codex/083-process-working-interfaces`.
Parent: `5534fc0dcea829eefe04e52a331e05d77d17048e`.

## Implemented and checked scope

T035 and T036 add closed process capabilities to the existing managed manifest
and grant services, and a reserved `/__wright/process` transport on the existing
preview router. Existing presentation cookies and pinned route authority derive
principal, workspace, session, instance/generation, UI/revision, accepted process
and attached run. The immutable build and exact grants are checked before access.
Request selectors are compared with that scope; they do not establish authority.

The bridge delegates the existing native handlers and process owners for inputs,
uploads, readiness, durable start, attachment/events, declared answers, decisions,
actions, cancellation, representations and navigation. No additional executor or
generic tool invocation is exposed. A preparation presentation cannot borrow a
run. After a verified start receipt, a fresh native presentation must attach that
run; the current presentation's binding does not silently broaden. Preview grants
deny all mutations. POST requests require the exact presentation origin. JSON is
bounded, closed and duplicate/nonfinite fields are rejected without raw-input echo.

Optional internal run constraints now apply in the existing receipt, snapshot and
artifact owners. Bound receipts require the exact source digest. Native workspace
callers retain their existing multi-run scope. Stream chunks recheck live exact
grants, expiry, revocation and pinned presentation/generation without repeatedly
reading the verified static bundle. MCP App same-server grants remain separate.

T034 has an installed-module static asset server and fixed internal manifest
factory. The server exposes only verified distribution files and fixed runtime
assets on numeric loopback, with restrictive CSP and no source/workspace access.
The managed supervisor/presentation creation integration is still pending.

T037 has the isolated-origin public client transport and a fixed compiled client
factory/mount entry. The fixed runtime reads the server context, mounts read-only
previews, reports an exact loaded-preview observation and follows attached-run
snapshots. The loaded observation API is fixture tested, **not actual browser
proof**. Native theme/navigation/start-rebinding handshake and tab integration
remain pending. Runtime source and real compilation are checked; this does not
prove an actual managed browser preview.

## Verification

The retained [checkpoint manifest](../../../artifacts/process-interfaces/083/20261001-surface-bridge/checked-scope.json)
pins owned source hashes, commands, logs and preservation observations.

- Backend/API group: **262 passed**, zero skips, 124.31 seconds. Includes real
  immutable file-set/grant/process owners behind controlled model/compiler and
  pinned-route fixtures, native run/review/action/artifact/checkpoint regressions,
  existing preview security/MCP App tests and real local fixed compilation.
- Public native/presentation client group: **90 passed**, 6.74 seconds, two test
  files. Public client and presentation-test TypeScript checks also pass.
- Ruff and whitespace checks pass. The earlier 56-case static/grant group had two
  existing Windows symlink privilege skips; this larger group does not include
  those skipped cases and does not supersede that recorded platform limitation.

Earlier API attempts exposed missing fixture migrations/workspace registration,
an intentionally read-only manifest used by a working-input fixture, and the
expected incompatibility status for corrupt bytes. The first combined run had
256 passes and three failures: an old token fixture lacked source version, an
authoring test incorrectly expected no draft directory, and a diagnostic regex
did not match its safe message. The qualified run fixes those fixture/assertion
issues, retains the failures and checks all 262 cases. Authority checks were not
weakened to make them pass.

No new live-model inference, live MCP engineering run, hardware/supplier dispatch,
served workspace authoring journey, managed preview/save/update, installed wheel/
Docker acceptance, or human engineering/product acceptance occurred here. T021,
T032, remaining T034/T037–T042 integration, M4 and M5 are still required.
