# AgentCAD Windows native-import reconciliation

Observed 2026-09-12. This records a selected Windows host prerequisite problem,
its bounded reproduction and a qualified startup repair. It does not qualify
the full engineering campaign or change Wright's base image.

## Late heat geometry remains a failed workflow attempt

Heat case 01 attempt 002 ended with `TASK_TIMEOUT` at
`2026-09-12T15:50:55.548349+00:00`. The already-dispatched native AgentCAD operation
subsequently committed version 1 `plates` at
`2026-09-12T15:51:03.395332+00:00`. Two candidate STEP files, reopened geometry
measurements, native combined STEP, source and successful native history exist.
The recorded native script hash matches the authored source exactly.

Two read-only py-spy snapshots after completion showed process 39392 idle:
the main thread polled asyncio I/O, and its AnyIO workers waited. No CAD replay,
host restart or live mutation was used for reconciliation. The original
workflow remains failed; late geometry is not full workflow completion, and
no FE solve is implied. File hashes, timestamps, native status and stack are in
`.local-run/feature-081-live/campaign-execution/heat-attempt-002-late-native-observation.json`.

## Reproduced pending-stdin interaction

Pure NumPy imports in the exact installed interpreter succeeded in about
0.14–0.22 seconds. The same test using the live process's environment succeeded,
including explicit single-thread settings and OCP-first/worker-thread variants.
Fresh complete build123d import succeeded in 2.94 seconds. These checks provided
no evidence of a broken wheel or a need to change numerical thread settings.

A separate bounded child reproduced the actual stall condition: a background
thread blocked in `sys.stdin.readline()` before the first NumPy import. The
import remained blocked until the parent sent a controlled newline after three
seconds, then completed roughly 0.11 seconds later. The control imported NumPy
before creating the stdin reader; its later import completed immediately while
the reader remained blocked. Evidence is retained in
`.local-run/feature-081-live/numpy-blocked-stdin-probe-001.json`.

The installed MCP stdio implementation starts an asynchronous stdin reader
backed by an AnyIO worker. Wright's cancellation path writes a
`notifications/cancelled` message to the same pipe. This is a concrete mechanism
consistent with the observed import release and native completion after the
deadline. The experiment does not identify the underlying Windows DLL/CRT lock,
and it does not establish stderr logging as the cause. AgentCAD's Click runner
also redirects process-global streams, so independent import-only probes were
followed by a complete actual gateway/native CAD qualification.

## Qualified selected-host startup repair

`scripts/engineering/agentcad_windows_bootstrap.py` loads NumPy and the complete
build123d runtime before starting `agentcad.mcp` and its stdin reader. Loading
NumPy alone was insufficient: private qualification attempt 001 then blocked
in `scipy.linalg.blas`'s native extension. That bounded 90-second failure and
read-only stack remain under `agentcad-bootstrap-qualification/attempt-001`.
The final bootstrap loads build123d/SciPy before MCP startup as well.

The final source SHA256 is
`ad166be75f44977ed862c37c3b831002cf6e2ad3eed0f6d3dcc6409237a9e994`.
Its immutable snapshot is
`.local-run/feature-081-live/sources/agentcad-bootstrap-ad166be75f44977e/bootstrap.py`.
The source checks Windows and exact AgentCAD 0.6.0, NumPy 2.5.2 and build123d
0.10.0 prerequisite versions before opening the MCP transport. It does not
execute CAD or open a project during startup.

`scripts/qualification/qualify-agentcad-windows-bootstrap.py` records the exact
candidate command using Python 3.12.11 and those package pins. It initializes
an independent private project, starts MCP with continuous open stdin, performs
direct protocol discovery/context, then creates an actual 2×3×4 mm solid through
native `GatewayService`. Final qualification attempt 002 passed: eleven tools,
a 15,378-byte STEP, native script/history hashes and a successful 0.112-second
CAD call. This is real selected Windows prerequisite evidence, not a Linux
base-container or full campaign qualification. The proof and exact command are
`.local-run/feature-081-live/agentcad-bootstrap-qualification/attempt-002/qualification.json`.
Four bootstrap ordering/failure regressions and Ruff passed.

At the next controlled pause, use the recorded immutable snapshot command for
the selected AgentCAD host and refresh tool/source grants affected by that
installation identity. The existing live host and registry were not changed;
its native modules have now loaded, so a restart was not required for the
ongoing batch. No global environment workaround or dependency reinstall was
applied, and both private qualification processes were closed.

## Fresh heat case preparation

Only heat case 01 was prepared anew as attempt 003, using a fresh normal API
template instance, separate native initialization and the unchanged current
AgentCAD identity. Its original stages remain in the seven-stage graph. Exact
current source, seven tool pins and ten input hashes passed staging checks.
The ready manifest is
`.local-run/feature-081-live/campaign-execution/heat-case01-attempt-003.json`, with
an accompanying staging-verification record. It was not dispatched. Other heat
cases' unstarted attempt-002 sources and the active batch manifest remain intact.
