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

## Browser departure cleanup — current shared host

Later actual model-created saved interfaces and installed native/Docker proofs
supersede the narrow initial observations above within their recorded scopes;
see the live authoring, distribution, Heat and printed proof records. A real
open-view capacity stop then revealed that full-document navigation could abort
ordinary asynchronous unmount cleanup, retaining issued/active presentations.

The native ProcessInterfaceView now handles noncached pagehide by releasing its
exact presentation through the existing authenticated owner endpoint with a
bounded keepalive request. Ordinary unmount/StrictMode cleanup remains deferred
and happens once. Cached documents retain their mounted view; pending opens are
released if their response arrives while the document can execute cleanup.
No process execution, cancellation, review or independent lifecycle is added.

The [current departure evidence](../../../artifacts/process-interfaces/083/20261003-presentation-departure-verified/README.md)
records twelve actual browser checks on both saved engineering interfaces, three
reloads each plus departure. Prior exact presentation states become closed while
all 57 baseline run/output/bundle files and authoring/revision records remain
unchanged. The browser diagnostics are empty. The two interfaces still match
their eighteen and nineteen exact results. Preflight closed eight earlier owned
proof views through the normal API; no limits were raised or database records edited.

The affected frontend group passes 63 tests, the current backend static-host/
presentation/start-association/API-authority group passes 73 tests, and the app
typecheck exits 0. Counts overlap retained suites. The first typecheck fixture
typing error and pre-navigation Chromium sandbox EPERM are preserved. The fresh
walkthrough structure validator passes. These checks cover healthy opened views;
abrupt browser/OS termination is unqualified, and back-forward-cache/late-reply
behavior has component evidence only. Full T034/T037 acceptance remains subject
to the final hosting/handshake and installed-scope audit, not this correction alone.

The subsequent [installed-host audit](hosting-audit.md) closes T034's exact
static-runtime/internal-manifest scope. Its current two modules match the actual
retained native/Docker qualification wheel byte for byte; the current tests and
browser evidence are inspected separately. T037's remaining theme/handshake
audit, newer installed frontend acceptance and the complete feature remain open.

The subsequent [theme/handshake audit](theme-handshake.md) closes T037's scoped
transport/theme/navigation obligation. Current tests, the shipped receiver,
eight real two-process theme/reconnect checks and fresh packaging are recorded
separately from the older installed build. Complete UI/editor and feature
acceptance remain open.
