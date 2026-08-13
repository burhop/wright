# Engineering Scenario API Contract

All routes reuse existing authenticated workspace/session scope and return bounded JSON. They do not accept child MCP URLs, commands, environments, credentials, install commands, host paths, or run authority.

## `GET /api/workspace/engineering-scenarios`

Lists bounded catalog summaries. Optional filters: `domain`, `tier`, `availability`.

Response: `{ "scenarios": ScenarioCatalogEntry[] }`.

## `GET /api/workspace/engineering-scenarios/{scenario_id}`

Returns the exact current manifest projection plus manifest digest. Raw fixture content and workflow child connection data are excluded.

## `POST /api/workspace/engineering-scenarios/{scenario_id}/preflight`

Request: `{ "session_id": string, "seed": integer? }`.

Returns exact workflow/capability/environment checks, blockers, recovery, expiry, and `ready|blocked|skipped`. This is not execution authority and cannot substitute for workflow review.

## `POST /api/workspace/engineering-scenarios/{scenario_id}/runs`

Request: `{ "session_id": string, "preflight_id": string, "review_id": string, "revision": integer, "manifest_digest": sha256 }`.

Starts the exact existing reviewed Rivet workflow and attaches immutable scenario context. Stale preflight, manifest, review, workflow, binding, schema, environment, or workspace identity returns `409` before child invocation.

Response: `{ "scenario_run_id": string, "workflow_run": WorkflowRunResponse, "state": "running" }`.

## `GET /api/workspace/engineering-scenarios/runs/{scenario_run_id}`

Returns report state and the bounded hierarchy of nodes/capabilities, artifact index, assertion results, provenance differences, cancellation, cleanup/residue, and recovery.

## `GET /api/workspace/engineering-scenarios/runs/{scenario_run_id}/export`

Returns portable report metadata/hashes. Credentials, bearer authority, raw host paths, child executable markup, unrestricted URIs, and proprietary/raw artifact payloads are omitted.

## `POST /api/workspace/engineering-scenarios/runs/{scenario_run_id}/cancel`

Delegates to existing workflow cancellation. It revokes authority, cancels the active gateway call, blocks late publication, and updates cleanup/residue truthfully.

## `GET /api/workspace/engineering-scenarios/runs/{left}/compare/{right}`

Returns material identity differences across scenario/workflow/binding/schema/fixture/input/assertion/artifact/environment and per-assertion state changes. It never claims strict reproducibility when a material identity differs.

## Stable error categories

- `scenario_not_found`
- `scenario_manifest_invalid`
- `scenario_version_unsupported`
- `scenario_preflight_stale`
- `scenario_environment_blocked`
- `scenario_capability_missing`
- `scenario_capability_ambiguous`
- `scenario_binding_stale`
- `scenario_artifact_invalid`
- `scenario_assertion_failed`
- `scenario_cancelled`
- `scenario_cleanup_residue`
- `scenario_report_unavailable`
