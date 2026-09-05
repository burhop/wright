# Combined native implementation checkpoint

Production candidate: `997e561088c6b39344aee77856b909f7cd69cbe2`.
The existing standalone implementation dashboard remains at
http://127.0.0.1:8765/. Earlier checkpoint results remain historical evidence.

## Current capabilities and actual verification

The local feature build can create/configure/connect/save/reopen a native
definition, execute it through the shared UI/HTTP CLI service, inspect actual
artifact bytes and provenance, and preserve a failed run while creating a linked
correction. The native language is the semantic authority for programmatic
clients, Inspector, canvas and runtime. This path is independent of Rivet.

On the combined candidate, 60 focused tests passed in 29.50 seconds: native
authoring/execution/route-ID API tests, application startup tests, runtime
positive/negative/recovery tests, immutable run persistence and artifact tests.
The command used the existing Python environment with this worktree's source
paths and isolated disposable data. One existing Starlette TestClient
deprecation warning was reported.

Chromium passed 10 tests in 43.2 seconds against the same production candidate:
eight explicitly simulated service/runtime journeys and two real server
journeys. The latter downloaded and hashed actual outputs for all three
examples, including `Mass: 135 g`; injected a range failure with blocked
dependents; saved a correction; and verified the linked rerun, unchanged failed
snapshot, reopening and history. The correction journey had no page errors or
serious/critical automated accessibility findings. Simulated journeys cover
keyboard authoring, precise identities, undo, stale-writer recovery, narrow and
zoomed views, 20 warm opens of a 25-step fixture, invalid artifact bytes and
reconnection/cancellation. These automated results are not human study results.

[Actual browser run records](native-browser-runs-997e5610.json) retain all five
real run snapshots. The maintained live Playwright test was uncommitted during
this observation; production sources matched the candidate above. Its command
was `PLAYWRIGHT_INCLUDE_LIVE=1 PLAYWRIGHT_BASE_URL=http://127.0.0.1:5188
WRIGHT_NATIVE_LIVE_SESSION=native-validation-session playwright test
tests/ui-integration/native-process.spec.ts
tests/ui-integration/native-process-live.spec.ts --project=chromium --workers=1`.

## Independent review closure

The independent API reviewer closed all three integration findings on the exact
combined candidate with eight focused probes: shutdown waits for the actual
startup worker even when its caller is cancelled; cross-origin artifact access
exposes `X-Content-SHA256`; and canonical `/documents` resources preserve valid
IDs including `bindings`, `runs`, `documents`, `contract`, `examples` and `check`.
Static actions and legacy aliases retain their meanings. Original failing probes
were preserved; the startup closure probe explicitly releases its barrier while
shutdown is waiting. No new actionable gap was found in that review.

Earlier independently closed runtime, MCP and telemetry findings and the two
actual local stdio tests remain recorded in
[runtime and tool proof](native-runtime-correction-and-tool-proof.md). The full
tool process produced actual `{"value":1.25}` bytes, retained provenance and
verified child teardown. This is a disposable integration fixture, with no
engineering catalog or benchmark qualification.

## Process recovery and installed package evidence

The committed OS process-death test passed on Windows: a second owner was denied,
the actual owner process was terminated, its persisted unfinished run survived,
and the next owner interrupted it while retaining indexed artifacts and cleaning
generated orphans. A linked corrected run succeeded. Its deliberately blocking
adapter is simulated; the separate stdio proof supplies real tool evidence.

The installed-wheel probe used production `e4c58d952b1415321b9a5c6921da025fdf14c54f`
and wheel SHA-256
`2450fbd5a30b21fff4300008f5f1eea74ebce827f92052eb52adbe4e329b32ad`.
Three fresh isolated Python processes created a real API run, reopened it after
restart, and reopened it after relocating the same extracted package. All 282
Wright module imports resolved from the extracted wheel; real artifact bytes,
digest and immutable evidence were retained with outbound networking denied.
[Observed phase records](native-installed-phases-e4c58d95.json) are retained.
The first full pytest invocation used a workspace under the protected checkout
and correctly failed confinement. Reusing that built wheel with data outside
the checkout passed all three phases. This is not a green full packaging suite,
a different-version upgrade, a freshly packaged frontend browser test, Docker
evidence, or Linux/macOS evidence.

## Remaining acceptance

Tasks T001–T026 are implemented. Verification and dev integration remain
separate. Complete the independent candidate review, required full push/merge
gates, remaining distribution and legacy checks, real human usability, dev PR
integration, deployed-build verification and final dashboard reconciliation.
The remote dev baseline was freshly checked and remains
`7404a549ae244cc05d89e062c60276e8862f53c9`. No native PR or dev merge exists yet.
The three development examples receive zero qualified benchmark credit (0/100).
Rivet migration/retirement, editable DSL syntax and autonomous AI authoring remain
separate future work.
