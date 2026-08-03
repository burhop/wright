# Workflow Persistence API Contract v1

The API is a thin authenticated delegate to `workspace_service`. Requests use workflow IDs and `If-Match`/expected revision; responses emit opaque IDs, ETag, revision, and typed problem codes (`feature_disabled`, `not_found`, `revision_conflict`, `invalid_workflow`, `unsupported_version`, `workspace_violation`). It exposes no editor bootstrap, runner, or Rivet dependency.
