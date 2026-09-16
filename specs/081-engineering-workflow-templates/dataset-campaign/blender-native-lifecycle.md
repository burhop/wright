# Blender native lifecycle implementation and evidence

Implemented the bounded Blender ownership adapter and fixed lifecycle helper in
`packages/tool_registry/src/tool_registry/native_application_blender.py` and
`native_application_blender_host.py`. The native helper exposes only inspect,
create an empty owned document, save, close and quit. It has no arbitrary-code,
addon-installation, printer or mesh-execution operation. `BLENDER_MCP_SAFE_MODE`
is mandatory and remains true. Existing user Blender instances are never attached
for mutation or quit.

Each dedicated launch receives a fresh profile and separate user resources,
scripts, extensions and datafiles directories. The exact helper source is copied
into the session directory and hashed. The launch receipt records the prior
Blender process baseline, new PID/creation time/executable, native session ID,
profile/resource paths, helper hash and endpoint proof. A request/response pair
belongs to that native session; stale PID, endpoint and profile identities fail
closed. Unknown mutating outcomes persist in the control directory across adapter
restarts and block further mutations.

The adapter uses Wright's existing native lifecycle repository and service for
exclusive leases, owned document registration, recovery save/hash verification,
graceful close/quit and durable cleanup receipts. Recovered `.blend` paths must
stay within approved roots. Cleanup cannot overwrite another existing file or
close a borrowed/unknown document. Native dirty state remains authoritative;
an observed post-save edit still prevents close. The host hides only windows
owned by its own PID.

## Proven correction

The first native probe exposed a real integration bug: a blocking background
file-IPC loop prevented Blender's normal window-manager save notifications from
being handled. Saves produced real recovery files, but the native dirty flag
remained true, so Wright correctly refused close. Reopening the saved checkpoint
within that same background loop did not resolve it.

The working helper runs a persistent `bpy.app.timers` callback in a dedicated
hidden normal Blender event loop and handles one request per callback. Blender
processes its own save notification before the next inspection, and its dirty
flag clears normally. No dirty flag is reset or suppressed. This is consistent
with Blender's [native dirty-state implementation](https://raw.githubusercontent.com/blender/blender/blender-v4.5-release/source/blender/makesrna/intern/rna_main.cc)
and [file-notification implementation](https://raw.githubusercontent.com/blender/blender/blender-v4.5-release/source/blender/windowmanager/intern/wm_files.cc).
The helper inspects the supported
[window modal-operator collection](https://docs.blender.org/api/4.5/bpy.types.Window.html)
and uses [native quit](https://docs.blender.org/api/4.5/bpy.ops.wm.html#bpy.ops.wm.quit_blender).

## Acceptance

At September 13, 2026 01:59:39 UTC, the selected Blender **4.5.10 LTS** completed
three consecutive create/save/close/native-quit cycles. Each wrote a real,
nonempty `.blend` recovery and returned to an exited process/endpoint state.
Duplicate cleanup returned the identical receipt. A separately launched dirty
scene, presented as a borrowed witness to the adapter, was preserved throughout
all three cycles and was cleaned up afterward using its original owner authority.
This is a controlled witness, not a claim that a user's open production scene was
used in the test.

All four final cleanup receipts completed, stderr was empty, and the final host
inventory contained zero Blender processes. All ten Blender session records from
the failed and successful probes are exited with released leases and no remaining
blocker. The four earlier background instances required individually revalidated
PID-specific disposal after their exact blank-scene recoveries had been hashed
and successfully reloaded through native Blender. That exceptional disposal is
recorded separately; the final event-loop proof used graceful native quit only.
No process-name-wide or process-tree kill was used.

Evidence is under
`artifacts/engineering-workflow-datasets/diagnostics/recovery-20260913/`:

- `blender-lifecycle-proof-004/acceptance.json`: three final cycles and witness.
- `blender-lifecycle-proof-004/*/recovery.blend`: actual saved blank scenes.
- `blender-lifecycle-proof-004/*/blender-lifecycle-host.py`: exact tested helper.
- `blender-lifecycle-proof-003/acceptance.json`: first successful event-loop probe.
- `blender-blank-recovery-audit.json`: native reload proof for retired helpers.
- `blender-old-probe-termination-plan.json` and
  `blender-old-probe-termination.json`: exact ownership, recovery and disposal.
- `native-lifecycle.sqlite3`: shared SQLite WAL session/lease/cleanup history.

Thirty-three focused tests passed: fifteen Blender adapter/helper tests and
eighteen native lifecycle tests. Ruff passed for both implementation modules,
their tests and `scripts/probe_blender_native_lifecycle.py`. The repeatable native
probe accepts explicit executable/database/output paths and one to three cycles;
all diagnostic receipts explicitly exclude campaign completion credit.

## Remaining integration boundary

This proves the native lifecycle component and its blank-scene control path.
The adapter deliberately does not enable the selected mesh MCP addon. The
printing script-guard decision and actual mesh/support/slice workflow remain
unresolved, and the original `scripts/windows/blender-mcp-host.py` is unchanged.
Workflow orchestration must use the lifecycle service and this owned session
before adding a compatible guarded mesh binding. These lifecycle probes do not
advance the thirty-scenario engineering counters.
