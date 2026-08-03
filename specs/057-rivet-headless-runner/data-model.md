# Data Model

`WorkflowRun`: opaque ID, server-derived workspace and session IDs, immutable
workflow/revision IDs, runtime generation, state, runtime identifier, and
terminal reason. `WorkflowRunEvent`: opaque run ID, monotonically increasing
sequence, lifecycle kind, and scalar redacted payload. Events are bounded to
256 per in-memory run projection; the existing process supervisor independently
bounds raw logs. `RunnerAvailability`: enabled/missing/incompatible/degraded.

This slice intentionally does not add a durable run/event migration: those
retention, provenance, and recovery policies are owned by the later workflow
operations slice. Authored workflow files remain the only durable content here.
