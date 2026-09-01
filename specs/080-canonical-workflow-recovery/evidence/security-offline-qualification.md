# T057 security and offline qualification

**Date**: 2026-09-01

**Exact implementation subject**: commit `ba5ca8d03dcaf42fad832fbd2ed3f69b8a990f5b` / tree `17a0f5a0537f5ab6b713736e5e1996011a33e68d`

**Task status**: **PASS**. This qualification covers the locally owned canonical workflow definition, layout, command, run, capability-grant, workspace/session, resource, and offline boundaries. It does not grant external runtime authority, release authority, or customer readiness.

## Qualified controls

| Control | Evidence | Result |
|---|---|---|
| RBAC and exact authority | A mutating workflow grant is exact to source/version, workflow identity, base revision, workspace, user, instance, and operation; it is consumed after one use. Administrator-only target attachment is denied to an engineer. | Pass |
| Runtime isolation | Existing workflow operations return a run only for its exact workspace and session and hide cross-workspace or cross-session lookup as not found. | Pass |
| Definition secret boundary | Canonical validation rejects secret-shaped keys and recognizable bearer/assignment or credential-bearing URL material before semantic hashing or persistence. Recovery promotion applies the same check to its exact source envelope. | Pass |
| Immutable evidence secret boundary | Canonical run, step, activity, artifact, and opaque recovery-run envelopes reject secret material before immutable storage. Public recovery decoding keeps a generic safe error while retaining the precise rejection as its internal cause. | Pass |
| Resource bounds | A command batch above 1,000 commands fails Pydantic validation. A definition envelope above 4 MiB is rejected before the definition sidecar is created. Existing model and SQLite bounds cover layouts, runs, activities, steps, and artifacts. | Pass |
| Store isolation | Definition, layout, and run records remain in three independent SQLite sidecars; no primary database is created by these repositories. Separate workspace roots cannot read one another's run IDs. | Pass |
| Offline restart | Definition promotion, layout promotion, run/step/activity/artifact persistence, state transitions, repository reconstruction, and reconnect complete while `socket.create_connection` and `socket.getaddrinfo` are hard-failed. | Pass; zero network calls |

## Test evidence

```text
Focused T057 security + offline qualification: 10 passed
Broad canonical/RBAC/security/offline regression: 88 passed
Ruff on changed source and qualification tests: passed
```

The broad command used Wright's declared `engineering-models` extra because the
complete `tests/security/` directory includes three NumPy-backed Chatter
contract tests. The first run without that optional extra reported 74 passes
and three import failures (`ModuleNotFoundError: numpy`). Rerunning with the
declared extra installed one package and passed all selected tests; this was an
environment dependency correction, not a product-code repair.

## Failed-first evidence

The initial focused run reported four failures. Three exposed real missing
fail-closed checks: secret-shaped definition configuration, secret material in
the recovery promotion source, and secret-bearing immutable activity/artifact
text. The production repair extends the existing shared secret-material guard
and invokes it at canonical definition and run-record validation boundaries.

The fourth failure was a test assumption that a SQLite directory would contain
only the three database filenames. WAL mode truthfully creates `-wal` and
`-shm` companions; the corrected assertion permits only those companions and
still rejects any unrelated or cross-workspace store.

## Boundary statement

The data-vault repositories remain storage primitives and do not invent a
second authorization model. Human/administrator authority continues through
Wright's existing workspace/session and exact capability-grant layers. The
canonical models fail closed before immutable bytes are accepted. AI proposal
content still has no direct mutation, run, approval, or external-write path.

T056 remains open for a real screen-reader session and moderated representative
engineer sessions. T058 remains at `0/100` until independent engineering-oracle
evidence passes. No push, merge, publication, release, or external action was
performed.

The refreshed dashboard verifier passed at `2026-09-01T05:07:52.020Z`: recovery
is 56/60 with T056 still visibly open, the exact approved UI subject and manifest
remain bound, all eight gallery images load, desktop/mobile overflow is zero,
browser diagnostics are empty, evidence requests return 200, both traversal
probes return 403, benchmark remains 0/100, and customer readiness remains false.
