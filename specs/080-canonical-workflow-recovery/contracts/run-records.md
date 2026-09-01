# Immutable Run, Step, Activity, and Artifact Contract

## Boundary

Runs bind to an exact accepted workflow revision and semantic digest. They never modify workflow definitions, layout documents, proposals, or approvals.

The recovery projection uses this explicit envelope:

| Field | Recovery contract |
|---|---|
| `document_kind` | `workflow-run` |
| `schema_version` | `1.0.0-recovery.1` |
| Subject | `workflow_id`, `workflow_revision`, and `semantic_sha256` must match the accepted definition projected by the host. |
| Unsupported version | Reject with `WFR-RUN-VERSION-UNSUPPORTED` before reading steps or overlays; preserve the unknown input unchanged. |
| Subject mismatch | Reject with `WFR-RUN-SUBJECT-MISMATCH`; never project another revision's activity over the current definition. |

Step, activity, and artifact records in the bounded concept inherit the run
envelope version. A promoted durable event store may version those record kinds
independently, but only through a superseding contract and migration evidence.

## Run lifecycle

The bounded recovery wire states are `idle`, `queued`, `running`,
`needs-input`, `succeeded`, `failed`, `blocked`, and `stale`. The schema closes
every root, step, activity, component-scope, and artifact-record object.
Cancellation and a separate durable `needs_input` spelling remain promoted
runtime design work; they are not accepted by this recovery version. A future
durable source is an append-only event sequence, with summaries rebuilt as
deterministic projections.

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
