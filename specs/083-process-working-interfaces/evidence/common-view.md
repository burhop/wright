# Common process view evidence

## T019 native component — 2026-09-30

Branch: `codex/083-process-working-interfaces`. This entry proves the native
component and recovery controller. Workspace hosting and actual served-browser
proof are T020–T021 and remain pending.

### Implemented

`CommonProcessView.tsx` composes the public client and kit for declared schema
inputs, units/options, uploaded-image thumbnails, explicit preparation/readiness,
backend-permitted start/cancel, recorded progress, exact results/assessments,
representation preview/download, declared-checkpoint inspection and navigation.
Optional missing ports and read-only views remain visible and disabled. Input
edits invalidate readiness; uploads must finish before preparation. Ready
assessments expire visibly while idle and cannot enable a start after expiry.

The controller reads on mount and follows a saved run; it never prepares, starts,
reviews or cancels on subscription. It uses the existing public `setInputs`,
`checkReadiness`, `start`, `follow`, `cancel`, representation and navigation ports.
There is no graph executor, provider protocol, tool invocation or independent
engineering/job-status authority. Unsupported checkpoint response controls remain
disabled pending T024–T027; this milestone does not claim those capabilities.

`process-view-recovery.ts` stores only compact backend input identities and
request/receipt locators, without input values, file bytes or credentials.
Recovery records are bounded and scoped to session/workspace/path/source revision.
The immutable preparation derives one stable start request ID; cancellation
derives one stable ID from its run. The journal is written and verified before
start submission. A lost acknowledgement preserves that same identity for an
explicit reconciliation; no mutation is retried automatically. Reopening reads
the existing run. Unreadable recovery blocks new preparation rather than
overwriting an uncertain request. A different explicit run does not adopt a
cached receipt. Existing backend scope, fresh readiness and durable receipt
authority continue to control every operation.

Scoped remounts and read generations discard late replies. Closing aborts only
the event observer. An already submitted start can still save its accepted receipt
after close. A cancellation acknowledgement is a request, not confirmation of
stopping. Another view's pending start is checked before draft clearing, before
and after asynchronous preparation, and before writing a start. These guards and
stable immutable-preparation IDs complement backend deduplication; the browser
cache is not a distributed locking or execution authority.

Result pages retain exact identities and reject merging changed snapshot cursors.
Representations use the owning host callback, bound digest and safe public viewer;
the native download uses a Blob URL released on close/replacement. Rendering and
empty findings cannot approve an engineering result. New-run preparation remains
a separate host action after a recorded terminal outcome.

### Verification

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/components/process-interfaces/CommonProcessView.spec.tsx src/components/common/ProcessUIKit.spec.tsx tests/ThreeDViewer.spec.tsx src/services/process-client.spec.ts vite.config.spec.ts
node ../../node_modules/eslint/bin/eslint.js src/components/process-interfaces/CommonProcessView.tsx src/components/process-interfaces/CommonProcessView.spec.tsx src/services/process-view-recovery.ts
```

**124 checks pass**, five files, 4.53 seconds: 30 common-controller/recovery,
30 public kit, four mocked geometry/lifecycle, 45 scoped client and 15 native
configuration/proxy/license checks. ESLint passes with no warnings/errors.
These are component/client/config checks with mocked backend/provider/WebGL
boundaries, not an actual served workspace, live model/MCP or engineering proof.

From the repository:

```text
node apps/web/node_modules/typescript/bin/tsc -p apps/web/tsconfig.app.json --noEmit
node apps/web/node_modules/typescript/bin/tsc -p packages/ui_kit/tsconfig.json
node apps/web/node_modules/typescript/bin/tsc -p packages/process_client/tsconfig.json
.venv/Scripts/python.exe packages/process_client/scripts/generate_contracts.py --check
git diff --check
```

Whole-app and both public-package type checks pass. The owning contract schemas
remain unchanged. Ten original prototype hashes, three protected campaign hashes,
approved feature context and two original startup/router deltas remain preserved.

### Observed corrections and pending scope

- Initial component selectors omitted the schema widget's required suffix;
  corrected selectors and strengthened the blocked downstream-input assertion.
- React 19 refs require explicit initial values; corrected strict type errors.
- An intermediate upload-status insertion matched the wrong JSX button;
  corrected it before the final passing compile/checks.
- Ref callback updates moved into an effect, and observer cleanup uses an explicit
  invalidation callback; the final focused ESLint run is clean.
- A preservation comparison initially used Windows locale decoding; reran it
  with explicit UTF-8 and verified the actual hashes/deltas. No baseline files
  were rewritten to make that check pass.

T020 must wire typed workspace tabs, restoration, exact native host ports and
deep links while preserving the reviewed editor. T021 must prove mocked and
actual served workspace journeys, reconnect and navigation. Authoring through
Wright, scoped hosting, actual digital engineering tools, migration and installed
distribution proofs remain required. No service restart, live model/provider
invocation, physical effect, campaign execution or remote publication occurred
during T019.
