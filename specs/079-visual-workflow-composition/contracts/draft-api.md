# Draft API Contract

All routes require existing engineer or administrator authorization before resource lookup. The server flag `WRIGHT_WORKFLOW_COMPOSER_ENABLED=1` is required; disabled requests return the existing feature-unavailable pattern without disclosing draft existence.

## POST `/api/workflow-drafts`

Creates an empty valid draft and returns `201`, the closed draft envelope, and an ETag for revision 1. No released definition is copied or mutated.

## GET `/api/workflow-drafts/{draft_id}`

Returns `200`, the current closed draft envelope, and ETag. `If-None-Match` may return `304` with no body.

## POST `/api/workflow-drafts/{draft_id}/validate`

Accepts one bounded candidate envelope, performs closed schema and semantic validation, and returns either a valid projection identity or diagnostics. It performs zero writes and assigns no revision.

## PUT `/api/workflow-drafts/{draft_id}`

Requires `If-Match` for the current ETag. The server revalidates the complete candidate, assigns the next revision and digests, and atomically advances the current head. A stale precondition returns `412`; invalid content returns `422`; neither changes current state.

## Closed errors

Errors contain only `error_code`, `message`, `recovery_class`, `trace_id`, and optional `diagnostics`. A diagnostic contains `code`, `path`, `affected_semantic_ids`, `explanation`, and `correction`. Payload content, credentials, local paths, and persisted bytes never appear.

Expected classes include unavailable/disabled, not found, invalid, incompatible schema, identity mismatch, stale revision, and local storage failure. Request and response bodies are bounded at 1 MiB.

## Explicit absence

There is no release, publish, apply-to-released, execute, run, MCP, LLM, import-Rivet, export-Rivet, benchmark, or delete-all endpoint.
