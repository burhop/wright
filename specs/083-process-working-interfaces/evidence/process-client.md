# T017 public process client evidence

Date: 2026-09-30, branch `codex/083-process-working-interfaces`.
Owning package: `packages/process_client/`; shell adapter and tests:
`apps/web/src/services/process-client.ts` and `process-client.spec.ts`.

## Implemented scope

The versioned, React-independent public client uses host-injected authenticated
fetch over the actual native route mount. Accepted process/session scope is
fixed at creation. Input/run/receipt replies are checked against that scope.
Inputs are immutable preparations, not source edits. Only explicit `start` sends
work; reads, event subscriptions and closing an observer cannot start or cancel.
Caller-retained request identity and input digest are sent unchanged. Lost start
or cancel acknowledgement reports uncertainty and does not automatically replay.

Recorded SSE attachment supports split chunks, UTF-8, LF/CRLF, bounded frames,
snapshot reconciliation, cursor recovery and finite consecutive reconnects.
Terminal events retrieve full saved snapshots; metadata does not become a
browser executor/status authority. Provider facts remain those projected by the
backend. Failed scope/contract reconciliation stops attachment.

Generated public types and private validator schemas match actual core schemas
and the owning JSON fixture. New unsupported schema keywords fail generation.
Input union discriminators are required. Guards reject non-finite/non-JSON data,
cycles/accessors, malformed closed fields, page/value/depth/size violations and
wrong scopes. Custom backend validators, canonical checksums, freshness,
engineering verification and permission checks retain server authority.

Native implemented categories: snapshots, inputs, readiness, start, attach,
follow, explicit cancellation requests. Response/review/action categories are
reserved and return unavailable without speculative calls until T024–T027.
Representation/navigation ports require trusted owning host services; scoped
representation routes and presentation transport remain later work. No generic
tool/file/shell/admin operation is exposed by the public client.

## Commands and actual results

From the repository unless another directory is specified:

```text
.venv/Scripts/python.exe packages/process_client/scripts/generate_contracts.py --check
node apps/web/node_modules/typescript/bin/tsc -p packages/process_client/tsconfig.json
node apps/web/node_modules/typescript/bin/tsc -p apps/web/tsconfig.app.json --noEmit
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_client_contracts.py packages/core/tests/test_process_interface_contracts.py --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t017-contracts -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check packages/process_client/scripts/generate_contracts.py packages/core/tests/test_process_client_contracts.py --no-cache
git diff --check
```

All passed: 54 Python checks in 0.67 seconds; package and whole-app type checks
returned zero; schema freshness, Ruff and whitespace checks pass.

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/services/process-client.spec.ts vite.config.spec.ts
```

59 passed in 1.61 seconds (44 client tests, 15 Vite/proxy/license checks).
These are controlled transport/contract checks, not a served UI or live MCP/model
acceptance claim. The new checks include wrong process/run/input receipts,
actor injection, lost acknowledgements, pre-aborted submission, cancellation
uncertainty, cursor expiry, bounded reconnects, scope-reconciliation events,
partial frames and pending-reader disposal without cancellation.

From the repository:

```text
npm run build --workspace apps/web -- --outDir D:/repos/wright/.local-run/process-interfaces-083/t017-web-dist-final
```

Production build passed: 908 modules, 1.79-second Vite build, with generated
index/assets/license file in that fresh directory. This is compile/bundle proof;
the native common view and served workspace journey remain T019–T021.

## Observed failures and corrections

- Initial test invocation assumed app-local Vitest; the existing npm workspace
  installs it at the repository root. Corrected the command and the test import
  to the public package; no new package manager was introduced.
- Whole-app type checks initially exposed mock-function tuple types and two
  untyped accumulated update arrays. Typed the fetch mocks and update arrays;
  the final package/app checks pass.
- Offline installation could not obtain an existing locked xyflow transitive
  archive. One authorized bounded install completed in three seconds, with
  scripts disabled. Final root lock changes only add the local client link,
  dependency entry and local package metadata. The pre-existing standalone
  `apps/web/package-lock.json` drift was not silently rewritten; installed
  distribution checks remain T050–T055.
- Normal build could not empty existing `apps/web/dist/assets` (Windows EPERM).
  A fresh output directory then exposed a pre-existing hard-coded license-file
  destination. The license output resolver now honors Vite's actual resolved
  build directory, including CLI overrides, and retains serve/public behavior.
  Two actual plugin-export tests verify both directories. Final build uses a
  new owned directory; the existing served output was not replaced.
- npm warns that installed jsdom 30.0.1 excludes Node 25.2.0 from its declared
  engine range. Focused checks passed on this host, which is the recorded scope.
  Supported installed native/Docker runtime proofs remain later tasks.

Protected campaign hashes, current approved feature pointer, ten original
prototype file hashes and the original startup/router deltas were checked and
preserved. No service was restarted, protected subject resumed, model called,
provider action sent, push/merge/publication performed, or physical effect made.

## Next required work

T018 shared accessible themed kit, T019–T021 common workspace journey;
T024–T027 complete declared interactions/actions; T034 presentation-bound
transport and authoring/hosting; later live model/engineering/distribution proofs.
T017 is an increment in the full goal, not its replacement or completion.
