# Workspace Surfaces Policy Defaults

This document defines the safe baseline used when a source omits an optional
limit or an administrator has not supplied a narrower deployment policy. The
defaults are part of contract version 1 and therefore require an explicit
compatibility review when changed.

## Precedence and Enforcement

The effective value is the most restrictive applicable value from:

1. a non-bypassable Wright hard limit;
2. administrator deployment and workspace policy;
3. an approved source declaration; and
4. the version-1 default in this document.

A source can narrow a value but cannot broaden an administrator or hard limit.
Omission never means unlimited. Invalid or contradictory limits fail declaration
with `SURFACE_POLICY_INVALID_LIMIT`; they are not silently clamped.

Every surface descriptor and diagnostic projection identifies whether each
effective control is `enforced`, `degraded`, or `unavailable`, without exposing
secret policy inputs. A control marked `required` by hard or administrator
policy makes launch ineligible when the platform adapter cannot enforce it.
Otherwise Wright may run in a visibly degraded state only after administrator
policy explicitly permits that class of degradation. Process-tree containment,
workspace/target isolation, credential separation, and authority revocation are
always required and have no permissive fallback.

## Version 1 Runtime and Transport Defaults

| Limit | Default | Hard maximum / rule |
|---|---:|---|
| Wright-owned apps per workspace | 8 | 32 |
| Concurrent starts per workspace | 2 | 8 |
| Processes in one owned tree | 32 | 256 |
| CPU per owned app | 2.0 logical cores | 64 logical cores |
| Memory per owned app | 2,048 MiB | 65,536 MiB |
| Automatic restarts | 2 in 5 minutes | 20 in 1 hour; then circuit open |
| Readiness/startup bound | manifest probe, capped at 30 s | 300 s |
| Graceful shutdown interval | 5 s | 30 s |
| Escalated cleanup/reconciliation interval | 5 s | 30 s |
| Total ordinary stop bound | 10 s | 60 s |
| Header count | 100 | 200 |
| Header bytes | 64 KiB | 1 MiB |
| One request body | 16 MiB | 1 GiB |
| One non-streamed response body | 64 MiB | 1 GiB |
| Decoded/decompressed body | 64 MiB and at most 8x encoded size | 1 GiB |
| Buffered proxy/app output | 4 MiB | 1 GiB |
| Connections per app | 128 | 10,000 |
| Requests per presentation | 300/minute, burst 60 | 100,000/minute |
| Stream throughput per connection | 8 MiB/second, burst 16 MiB | 1 GiB/second |
| Privileged bridge messages | 60/minute, burst 20 | 100,000/minute |
| WebSocket message | 4 MiB | 64 MiB |
| WebSocket messages | 100/second, burst 200 | 100,000/second |
| First byte | 30 s | 300 s |
| Ordinary HTTP idle | 60 s | 1 hour |
| WebSocket/SSE heartbeat idle | 90 s | 1 hour |
| One live connection lifetime | 8 hours, renewable only with current authority | 24 hours |
| Captured app logs | 10 MiB, rotating | 1 GiB |
| Captured log rate | 256 KiB/second, burst 1 MiB | 64 MiB/second |
| Display representations | 12 | 12 |
| Display envelope, encoded | 16 MiB | 64 MiB |
| Native graph points per series | 100,000 | 1,000,000 under administrator policy |
| Retained stateful panel hosts | 6 per workspace | 16 |
| Bootstrap token TTL | 60 s, single use | 5 minutes |
| Presentation revocation propagation | 2 s | 5 s |

Streaming HTTP and SSE are not accumulated into a response buffer. They remain
subject to connection lifetime, byte-rate, decoded-chunk, idle, cancellation,
and current-authority checks. Limit errors use the `SURFACE_LIMIT_*` family and
identify the limit name, effective non-secret value, retryability, and
correlation ID.

CPU and memory enforcement use native facilities when supported. Sampling alone
is not presented as hard enforcement. The platform capability projection states
the enforcement method; administrator policy decides whether a degraded
resource-only control is acceptable. This exception never applies to process
ownership or security boundaries.

## Race-Safe Endpoint Ownership

Wright allocates only loopback endpoints for command-launched applications.
Allocation uses this order:

1. Prefer an inherited listening socket or platform handle so the reservation
   remains owned continuously from allocation through child startup.
2. If a framework cannot accept an inherited listener, hold a reservation until
   immediately before spawn, attempt launch at most five times, and use a new
   port and runtime generation for every retry.
3. Before readiness can succeed, prove that the listener belongs to the expected
   PID creation-time identity and its process group, Job Object, container, or
   remote adapter; then connect using the immutable numeric target pin.
4. If another process acquires the endpoint, fail that attempt with
   `SURFACE_TARGET_OWNERSHIP_MISMATCH`; never probe, proxy, stop, or expose the
   unrelated listener.

Two concurrent instances have separate reservation, target-pin, generation,
presentation, log, and cancellation records. Per-source single-instance policy
serializes declaration/start and returns the existing starting/ready instance;
isolated policy creates separate generations deliberately.

## Process Stop and Recovery Semantics

The manifest may select a supported graceful signal; otherwise POSIX uses
`SIGTERM` for the owned process group and Windows requests the adapter's
documented graceful application stop before closing/terminating the Job Object.
After the graceful interval, Wright escalates the entire owned group/job. It then
reconciles descendants, listeners, credentials, grants, streams, and target pins
for the remaining interval.

An ordinary stop succeeds only when all owned descendants and listeners are gone
and applicable authority is revoked. Otherwise the runtime becomes `failed` with
`SURFACE_RUNTIME_CLEANUP_INCOMPLETE`, the surviving non-secret evidence is
recorded, and the UI offers diagnostics/reconcile rather than claiming success.
Unknown or unprovable processes are never killed or adopted.

API startup reconciliation completes before new surface starts or presentations
are accepted. API shutdown rejects new commands, revokes presentations and
surface registrations, cancels messages/streams, stops and reconciles owned
runtimes, flushes the SQLite/vault outbox and diagnostics, and only then shuts
down the MCP gateway, workspace executor, telemetry provider, and database/vault
adapters.

## Reference Evidence Protocol

`SC-003`, `SC-006`, and `SC-007` use a recorded reference profile with at least
4 logical CPU cores, 8 GiB RAM, local SSD storage, and no competing workload.
Tests use the packaged production UI and wheel, a loopback reference app, a
current supported Chromium build, and release-default limits. Every evidence
record includes OS/build, CPU, RAM, storage, browser, Wright artifact digests,
configuration, and raw timing/cleanup observations.

After one unmeasured warm-up, `SC-003` runs 100 independent trials. Display time
starts when the producer receives the accepted ingestion response and ends when
the renderer emits its visible-ready mark. Managed-app time starts when the
declared readiness probe first succeeds and ends when the browser fixture's
interactive-ready mark is actionable. Browser launch time and application work
before readiness are reported separately.

`SC-006` uses 100 simultaneously scheduled interactions distributed across at
least two instances with deliberately colliding route/tool names and exercises
HTTP, WebSocket, and SSE in the same run. `SC-007` runs 100 cycles for each
supported process adapter and applies the 10-second ordinary stop bound unless a
narrower declared value applies. Zero-leak evidence checks descendants,
listeners, target pins, presentation cookies/tokens, instance grants, pending
messages/streams, and retained registrations after every cycle.
