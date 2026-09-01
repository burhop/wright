# Immutable Run, Step, Activity, and Artifact Contract

## Boundary

Runs bind to an exact accepted workflow revision and semantic digest. They never modify workflow definitions, layout documents, proposals, or approvals.

## Run lifecycle

Allowed projected states are `queued`, `running`, `needs_input`, `succeeded`, `failed`, `blocked`, `cancelled`, and `stale`. The durable source is an append-only event sequence. A summary is a deterministic projection and may be rebuilt.

Required run facts include run/workflow/revision/digest identity, execution mode, request identity, registered/connected/first-event/first-output/terminal/cleanup timestamps as applicable, and typed terminal cause.

## Step contract

Each executable block projects four engineer-facing sections:

- **Inputs**: artifact/value identity, origin, type, requiredness, redaction/truncation, and readiness.
- **Outputs**: produced value/artifact identity, type, lineage, preview/action availability, and completeness.
- **Activity**: current state, elapsed/last activity, progress summary, attempts, cancellation/deadlines, and bounded technical evidence.
- **Diagnosis**: consequence, typed cause, affected identities, dependents that did not run, recovery action, and whether external intervention is required.

## Active overlays

An active block uses at least text/icon and structural emphasis in addition to color. An active connection uses animation or repeated directional marks plus an accessible active label. Reduced-motion mode replaces animation with a static directional pattern and text.

## Needs-input recovery

A needs-input record identifies the missing semantic port/artifact/configuration and offers only bounded actions supported by the workflow authority. Supplying input creates a new activity/input record; it does not rewrite the workflow definition.

## Artifacts

Produced artifact records expose exact producer step/run, upstream lineage, type/media/digest/size, local storage reference, preview availability, allowed open/download actions, ownership/lifetime/expiry, and cleanup. Intended artifact contracts and actual artifact records remain distinct.

## Recovery concept limitation

Spec 080 uses deterministic simulated records to validate the interaction grammar. It does not claim live MCP/tool execution, executor integration, run persistence, cancellation, or reconnect implementation. Those remain production slices after product approval.

