# Wright process client

`@wright/process-client` is the public TypeScript view of one accepted Wright
process revision. It has no React dependency and imports no private application
code. The host supplies authentication and a fixed process/session context.
Wright's existing executor, gateway, recorder and verification services retain
authority; the client does not run a graph or evaluate engineering acceptance.

## Native host

```ts
import { createNativeProcessClient, ProcessClientError } from '@wright/process-client';
const client = createNativeProcessClient({
  process: acceptedProcessRef,
  sessionId: workspaceSessionId,
  fetch: authenticatedHostFetch,
});

const inputs = await client.setInputs([
  { kind: 'value', input_id: 'design-intent', value: 'A small replacement focus wheel' },
]);
const readiness = await client.checkReadiness(inputs);
// Enable a start control from backend actions/readiness; rechecks occur on start.
if (readiness.state === 'ready') {
  // Persist this ID and the exact inputs before sending. Never replace it on retry.
  const requestId = crypto.randomUUID();
  const receipt = await client.start(inputs, requestId);
  for await (const update of client.follow({ runId: receipt.run_id })) {
    if (update.type === 'snapshot') renderBackendSnapshot(update.snapshot);
  }
}
```

The example shows application wiring, not automatic execution on mounting a
view. Starting work requires an explicit user/workflow-authorized action.
`ProcessClientError.reason` contains the user message and next step. Raw HTTP
failures are not rendered as user-facing diagnostics. `OUTCOME_UNKNOWN` retains
`requestId`: reconcile or retry the identical request with that same ID. There
is no automatic mutation retry or new request-ID generation in the client.

## Read and reconnect

- `getSnapshot()` prepares a read; `attach(runId)` reads an existing saved run.
- `follow({runId, cursor?, signal?, maxReconnects?})` attaches to recorded SSE
  metadata, returning snapshots, event pages, connection and reconciliation
  updates. It uses fetch so existing browser and desktop authentication works.
- Chunked UTF-8, LF/CRLF, bounded frames and incomplete disconnections are handled.
  Reconnect uses the last recorded cursor. A rejected cursor reads a full snapshot
  and attaches without it. Events may replay; use their run/sequence identity when
  displaying event history. Snapshots remain authoritative presentation facts.
- Up to three consecutive reconnects are attempted by default (configurable
  zero through five); healthy long-running observation is not time-limited.
- Abort or close the iterator to dispose the observer. This never calls cancel.
  `cancel(runId, requestId)` is a separate explicit operation. Its receipt records
  `cancellation_requested`, not an observed successful stop.
- Returned process/run/input identities are checked against the host scope.
  App requests cannot set a principal, workspace, destination or provider tool.
  Backend services independently enforce all scope, currentness and authority.
- `assertProcessReference(value)` checks the owning reference shape and confined
  relative-locator rules before a native host restores a tab or parses a link.
  It validates a locator, not permission to read or run that process; the normal
  scoped server operation must still authorize it.

## Public operation coverage

Implemented native routes: snapshots, immutable inputs, readiness, explicit
start, attach, recorded follow and cancellation requests. Native `uploadInput`
saves a file against a declared input, then returns an immutable reference;
it does not prepare or start a process. `getRepresentation(reference, {runId})`
or `{inputSnapshotId}` delegates to the exact recorded result or prepared-input
owner, which checks the stored bytes against the recorded SHA-256. Downloads
are bounded to 100 MB, uploads to 32 MB; smaller configured server limits apply.
Incomplete downloads and changed subjects fail explicitly. HTML/SVG are inert
downloads, not executable previews. These operations use the same host
authentication and scoped process as the rest of the client, not a general file API.

Native `navigate(target)` first resolves the exact source/block/run/result/
assessment/evidence through the scoped server operation, then passes a validated
`NavigationResolution` to the trusted workspace host. The host selects an existing
matching document/run tab or opens one in that workspace. Step navigation retains
open source drafts. Assessment navigation separates the checked result identity
from its recorded assessment-file identity. If no host is available, the client
reports capability unavailable before making a request; source changes and absent/ambiguous evidence remain
explicit. Navigation never starts or replays work.

Native `respond({checkpointId, subjectDigest, value, requestId})` submits a
declared input to `/interactions/{checkpoint_id}/response`. The server derives
the run and actor, freshly qualifies source/frozen inputs/upstream evidence, and
retains the schema-valid answer before continuing the same run. Keep the exact
request/value on an uncertain acknowledgement; an identical retry reads its
retained answer rather than replaying completed work. Follow that answer's
`run_id` to observe execution. Answer acceptance is distinct from run completion.
No public response body can set review authority or an integration-test flag.

Native `decide({checkpointId, subjectDigest, decision, reason, requestId})` submits
an exact action approval or terminal artifact review to
`/interactions/{checkpoint_id}/decision`. The server derives the actor and run,
checks the current source and actual reviewed artifacts, and retains the request
identity in the existing review owner. A returned `PendingInteraction.decision`
is recorded evidence, not dispatch permission. Keep the same request on an
uncertain acknowledgement; changed identities or decisions conflict. Review
acceptance alone does not submit an external action. Terminal output reviews
update the existing run recorder without executing completed steps again.

Native `requestAction({actionId, subjectDigest, requestId})` submits only the exact
approved action to `/actions/{action_id}`. The backend derives run and principal
and supervises the existing executor independently of the HTTP observer. Its 202
snapshot acknowledges retained authorization; `action_receipt.submission` and
actual provider observations separately establish acceptance and completion.
Closing the view does not stop the operation. Keep the exact request after a lost
acknowledgement and explicitly reconcile it; uncertain consumed actions cannot
be blindly dispatched again. A completed identical retry is read-only.

The isolated presentation transport remains a later Feature 083 task and
reports `CAPABILITY_UNAVAILABLE`. Trusted native hosts may
provide alternate representation/navigation ports through their owning authorized services;
no generic file/tool/shell/admin operation is exposed. Full feature completion
requires those later capabilities and their backend/browser proofs.

## Shared contract generation

`src/contracts.generated.ts` and the private validator schemas come from actual
`core.process_interfaces.contract_schemas()` and its owning fixture. Run from
the repository Python environment:

```text
.venv/Scripts/python.exe packages/process_client/scripts/generate_contracts.py
.venv/Scripts/python.exe packages/process_client/scripts/generate_contracts.py --check
```

The generator rejects new schema features until the client validator supports
them. API input unions require explicit `kind` discriminators. Runtime guards
check closed shapes, local owning references, enums, finite numbers, field/page
bounds and finite UTF-8 JSON. Inline JSON is limited to 64 KiB/depth 24; aggregate
replies are bounded separately at 64 MiB and SSE data at 64 KiB. File input uses
exact vault references, not embedded file data. Custom backend validators,
canonical digests, readiness, permission and engineering checks remain backend
authority: transport shape validation cannot replace them.

The repository uses its existing npm workspace/local-file dependency and root
lockfile. No additional package manager or installed runtime framework is needed.
