# Rivet Workflow Operations

## Scope

Provide lightweight workflow list/detail/review/run/cancel/history operations
without loading the editor. A run is allowed only when the current
workspace-authored revision has an exact durable approval. History is bounded,
contains only event metadata, and is scoped to the requesting workspace and
session.

## Requirements

- RQ-01: Workflow project and dataset files remain the source of truth;
  SQLite may store only review metadata.
- RQ-02: Approval binds workspace ID, workflow ID, and exact revision. Saving
  a new revision invalidates earlier approval.
- RQ-03: Operations, runner use, and UI are disabled by default and return a
  safe unavailable state when disabled or missing.
- RQ-04: List, review, start, status, cancel, and history cannot cross a
  workspace or session boundary.
- RQ-05: The review index is introduced through a numbered migration and an
  existing workflow index survives its upgrade.
- RQ-06: The workspace tab supports catalog, explicit review, run, bounded
  history, and cancellation without importing the Rivet editor into React.

No second graph editor, schedules, marketplace, secrets in workflow data, or
agent publication are in scope.
