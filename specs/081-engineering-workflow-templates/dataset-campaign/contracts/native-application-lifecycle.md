# Native application ownership, reuse and shutdown

Approved September 12, 2026; part of the focused feature-081 recovery amendment.
Applies initially to Solid Edge and Blender, with a reusable lifecycle contract
for native hosts. Closing an MCP transport does not establish that its native
application or documents have closed. This document specifies planned behavior;
it is not evidence that cleanup has already been implemented or performed.

## Implementation boundaries

Reuse the existing gateway/native-launcher ownership patterns after checking
their suitability for desktop CAD. Relevant existing seams are:

- `packages/tool_registry/src/tool_registry/lifecycle.py`: MCP runner lifetime.
- `packages/workspace_service/src/workspace_service/surfaces/process_windows.py`
  and `runtime_reconciliation.py`: process identity/reconciliation patterns.
- `scripts/windows/blender-mcp-host.py`: selected Blender addon/config bootstrap.
- `scripts/prepare-solid-edge-campaign-host.py`: selected Solid Edge provider setup.
- `scripts/run_engineering_dataset_campaign.py`: case outcomes, unresolved
  resources and campaign startup/exit.

Keep general native-host management behind tool-registry/application services
and app-specific adapters, with records in data_vault SQLite WAL. The campaign
runner requests resources and observes receipts; it cannot invent application
ownership or become an alternate CAD executor. Keep routes thin and operations
CLI/MCP accessible. Do not rely on a human clicking a dialog for routine cleanup.
Do not apply kill-on-close process jobs blindly to desktop applications.

## Ownership and durable records

Persist a `NativeApplicationSession` record before dispatch: session ID, app
kind/version, host, owned/borrowed/unknown classification, executable path,
PID plus process creation time, parent/containment identity where available,
native session/endpoint identity, launch receipt, last heartbeat, policy and
current lease. Redact credential-bearing arguments and environment values.

Ownership requires evidence that the manager created the dedicated application
or explicit authorization to adopt that exact instance. A PID file, application
name, title, successful COM attachment, or lack of a visible window is not proof.
Enumerate the baseline before launch and reconcile the native session to the
actual process. COM may attach to a user-opened instance; classify it as borrowed.

Persist owned document/scene identities separately: exact native ID and path,
case/attempt, whether it preexisted, dirty state, recovery path/hash and close
result. A borrowed application can host an owned campaign document, but may not
be quit by campaign cleanup. Never close unrelated documents or reset a user's
Blender scene. Prefer a dedicated app instance/config/profile where supported.

Lease states are `available`, `leased`, `reconciling`, `quarantined`, `released`.
Application observations distinguish `starting`, `healthy`, `idle`, `closing`,
`exited`, `unresponsive`, `unknown`, `cleanup_blocked`. Leases bind owner,
case/attempt and application identity. Stale heartbeat expiry prompts
reconciliation; it never proves that a native mutation stopped.

## Acquire, reuse and release

1. Acquire exclusive ownership for mutating work and reserve all shared native
   resources in stable order. Reject a second lease or unknown prior operation.
2. Validate process creation time/executable, endpoint ownership, native health,
   application version, absence of modal state, and known document/scene state.
   A running PID alone is insufficient. Prove reconnect after an idle shutdown.
3. Reuse a healthy idle owned instance for an imminent case only after closing
   previous owned documents and checkpointing output files. Default idle grace
   is 60 seconds after the final lease; keep warm only for work scheduled within
   that grace. A borrower releases only its connection and owned documents.
4. On success, failure, cancellation or case timeout, enter idempotent cleanup
   or reconciliation in a finally path. API/worker shutdown and startup recovery
   must discover outstanding sessions. A worker crash is handled by subsequent
   persisted reconciliation; no claim that finally ran after an OS crash.

Initial configurable bounds: 120 seconds for startup, 30 seconds for document
close, and 30 seconds for graceful application exit. Validate these against the
selected hosts; native CAD/solver operation deadlines remain independent.
Expiration triggers diagnostics/reconciliation, not blind termination or retry.
Persist selected timeouts and their observed outcomes.

## Cleanup and escalation

Save produced outputs and recoverable owned work to the attempt's approved
paths, verify saved identities, release active document/COM references, close
owned documents/scenes through supported native APIs, and request graceful quit
only for a wholly owned application. Run this while its MCP/native control
channel is still available, then stop the owned transport if appropriate.
Verify actual process/endpoint exit and release the lease. Repeated cleanup must
be safe and must not rewrite immutable completed engineering artifacts.

If saving or close/quit fails, capture bounded diagnostics: process/session
identity, responsiveness, active/unknown operation, document ownership/dirty
state, recovery receipt, listener owner, native error and timeout. Set
`cleanup_blocked` and quarantine the affected resource when ownership or outcome
is ambiguous. Continue unrelated ready work.

PID-specific forced termination is a last-resort eligible action only after
rechecking PID + creation time + executable and containment, proving that every
affected app/child is campaign owned, and proving that no unrelated or unsaved
work can be lost. First save recoverable campaign work or document an existing
explicit discard policy for disposable campaign-created documents; no implicit
discard of user documents. An unresolved native operation still requires outcome
reconciliation before a retry even if its owned process was terminated.

Never use image/process-name-wide kills, guessed PIDs, global COM quits,
recursive kills containing unowned children, or an OS reboot as cleanup. If an
eligible action is rejected by platform approval review, preserve the evidence,
report that rejection and continue unaffected work. Do not bypass the control.

At campaign completion or intentional stop, close owned native sessions and
publish final cleanup receipts. Keep the requested Wright/Hermes/dashboard
services running unless the user asks to stop them. Leaving a known borrowed
user session open is correct and should be identified as such.

## Evidence and acceptance

Store append-only lifecycle events and an idempotent cleanup receipt with app
identity, case/attempt, ownership, lease transitions, document save/close
receipts, last activity, idle deadline, graceful/forced result and blocker.
Expose these diagnostics next to run status. Engineering-run outcome and
cleanup outcome are separate; cleanup success does not imply engineering
success and a teardown failure does not erase previously earned file evidence.
The campaign cannot be declared fully handled with an unresolved owned native
resource, even if the four output counters have reached their target.

Test both applications against success, native failure, cancellation,
timeout/unknown outcome, worker/API restart, warm reuse, idle shutdown,
preexisting user sessions, dirty documents, PID reuse, mismatched endpoints,
double cleanup and lease contention. Include denied/unsafe termination tests.
Use meaningful native disposable-project probes after isolated unit tests.
Three consecutive create/run/close cycles must return to the expected owned
process/document/listener baseline, preserve a preexisting user session, and
support a fresh run afterward. Preserve exact version and cleanup evidence.

The separate Blender preferences error was already repaired. The outstanding
Blender script-guard decision remains outstanding: this lifecycle amendment
does not authorize disabling `BLENDER_MCP_SAFE_MODE`, changing unrelated user
preferences, or bypassing its restrictions through another transport.
