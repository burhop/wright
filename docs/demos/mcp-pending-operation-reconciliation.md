# Exact pending-operation observations

11 October 2026: the bracket exposed an existing runtime gap. SteveCAD returned
an identified queued build, documented same-revision calls as joining that build,
and Wright treated transport success as a completed operation. Its replay guard
then refused the documented poll. The same existing build was independently
reconciled to completion with unchanged identity; no duplicate was created.

The general engineering journey needs bounded observation of a pending solver,
CAD build or other provider operation. The existing runtime remains the executor,
gateway remains access authority, and run events/results remain evidence owners.
Provider protocols stay external. No provider names or pending-status vocabulary
are hard-coded in the new shared owner.

An ordinary MCP task can save a typed `mcp_reconciliation_contracts` object (or
JSON-encoded string for the current editor). Each selected tool's contract names
the pending and terminal status values/path, provider receipt path, request-to-response identity
bindings, fixed arguments and maximum polls. An exact repeated request is allowed
only after a successful response matches this contract and reports pending work.
Subsequent responses must preserve the same receipt and identity. Completion
restores the existing replay guard. Missing/changed identity and exhausted limits
fail without guessing; an uncertain failed transport grants no new retry authority.
Existing action-intent checks, selected tools, gateway grants and task deadlines
still apply. Model prose cannot create or change this authority.

Save a new source revision to adopt the contract. Accepted sources and frozen
runs keep their earlier settings. The existing common view and source/diagram
remain the fallback; a JSON string preserves this setting through the current
editor. Backend observations record actual receipt, pending state, poll count and
request digest, without introducing another job-status owner. Reported pending
work is distinct from engineering compliance, review or human acceptance.

Local qualification includes a different-provider document-job fixture, negative
controls for identity, fixed arguments, limits and replay after completion.
The original SteveCAD queued receipt proved the triggering gap. A subsequent
live accepted-v8 run `de10572a1be84939b766c42003c1da5e` now proves the new runtime's
bounded observation: build `39af23dd-b6df-4d59-81d0-c84fcb8a4035` remained unchanged
through queued (poll 0), running (1), running (2), succeeded (3), from 21:23:09
to 21:25:22 UTC. Creation then completed without a duplicate document. The run
later failed in an independent read-only inspection; retain that failure and
do not describe the entire run as successful. A substantially different existing
live workflow remains required before broad integration. This is scoped local work.
