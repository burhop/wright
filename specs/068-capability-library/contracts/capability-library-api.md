# Capability Library API Contract

All routes are under `/api/mcp`. Existing server, tool, credential, and workspace endpoints remain compatible. Routes contain no business logic; they delegate to `McpApiService` and domain services.

## Error envelope

New endpoints use the existing HTTP error handling with a structured detail payload where supported:

```json
{
  "detail": {
    "code": "catalog_signature_invalid",
    "message": "Catalog update signature could not be verified.",
    "recovery": "Keep the current catalog and verify the configured update source.",
    "trace_id": "..."
  }
}
```

Messages and logs never include raw pasted configuration, credential/header values, signatures beyond a short key id, or full private paths.

## Capability discovery

### `GET /capabilities`

Query parameters:

- `search`
- repeated `domain`, `platform`, `evidence_class`, `compatibility`, `risk`, `locality`, `host`, `validation`, `installed`
- `limit` (1-200, default 100)
- opaque `cursor`

Returns:

```json
{
  "snapshot": {
    "snapshot_id": "...",
    "channel": "bundled",
    "sequence": 1,
    "offline": true,
    "updated_at": "2026-08-12T00:00:00Z"
  },
  "capabilities": [],
  "next_cursor": null,
  "total": 70
}
```

The `capabilities` items are `CapabilityView` projections. Cursor order is stable by evidence/installability rank, name, and canonical id.

### `GET /capabilities/{capability_id}`

Returns full permitted detail, current-machine compatibility, validation history summary, alternatives, and allowed actions. `404` covers unknown canonical ids and aliases that cannot be resolved unambiguously.

### `POST /capabilities/{capability_id}/observe`

Performs only approved read-only machine detectors and returns a `MachineCompatibilityObservation` plus derived compatibility. It cannot install, execute an imported command, or contact the vendor endpoint. Host detectors are allowlisted adapters.

## Catalog updates (administrator)

### `GET /catalog/state`

Returns bundled/active/previous ids, active sequence, configured channel state, recent activation history, and any recoverable diagnostic. It never returns private signing material.

### `POST /catalog/updates/preview`

Request chooses exactly one source:

```json
{ "envelope": { "signed": {}, "signature": "..." } }
```

or

```json
{ "configured_channel": true }
```

The configured-channel fetch is administrator-configured, HTTPS-only unless loopback test mode is explicit, size/time bounded, rejects redirects outside the configured origin, and performs no ambient credential forwarding.

Response includes `preview_id`, candidate verification metadata, sorted identity/field diff, risk summary, expiry, and `preview_digest`. Verification failure never creates an activatable preview.

### `POST /catalog/updates/{preview_id}/activate`

Request:

```json
{ "preview_digest": "<64 hex>" }
```

Requires the same authenticated administrator and unexpired active/candidate/diff binding. Returns new state and reconciliation counts. It never installs or enables a server.

### `POST /catalog/rollback`

Request names the currently displayed active and previous snapshot ids to prevent stale UI action. Returns the resulting state and preserved-user-state assertion counts.

## Configuration import and preflight

### `POST /imports/preview`

Request:

```json
{ "configuration": "<JSON text>" }
```

Maximum request is 256 KiB and 100 normalized servers. Response conforms to `import-preview.schema.json`. Raw configuration is never logged or persisted.

### `POST /install-plans`

Request identifies exactly one source:

- `capability_id`
- `import_preview_id` plus `draft_id` and `draft_digest`
- explicit remote/local form normalized by the same parser

It also identifies requested scope and optional workspace id. Response conforms to `install-plan.schema.json`. A blocked plan uses `200` so the UI can display it; malformed identity or stale preview uses `409`/`422`.

### `POST /install-plans/{plan_id}/approve`

Request includes the exact `plan_digest`. Returns the approved plan. Approval requires the applicable role and all non-credential approval gates; credential values are not accepted here.

### `POST /install-plans/{plan_id}/apply`

Request includes `plan_digest`. Rechecks active snapshot, capability digest, machine observation, actor, scope, expiry, and approval before running the adapter. Returns an onboarding run id. A changed plan is `409 install_plan_invalidated`.

### `GET /onboarding-runs/{run_id}`

Returns redacted lifecycle progress, effects, validation state, rollback state, and recovery guidance. Long-running progress can also use the repository's existing event-stream pattern.

### `POST /onboarding-runs/{run_id}/cancel`

Requests cancellation and rollback for cancellable adapter steps. No physical actuation adapter exists in this feature.

## Validation and workspace enablement

### `POST /servers/{server_id}/validation-runs`

Supersedes the new UI's use of the legacy validation endpoint while preserving that endpoint. Runs MCP initialize/discovery and an optional catalog-approved read-only probe through existing lifecycle boundaries. Returns `ValidationEvidence`.

### `POST /workspaces/{workspace_id}/capabilities/{server_id}/enable`

Requires a current accepted validation record and returns the existing workspace capability status. It does not start the server beyond established lifecycle policy and does not grant invocation approval.

## Missing capability reports

### `POST /missing-capability-reports`

Request:

```json
{
  "name": "Requested server",
  "vendor": "Vendor or unknown",
  "source_url": "https://example.invalid/source",
  "domains": ["cad"],
  "expected_task": "Create a parametric feature",
  "platform": "windows_11_x64",
  "host_application": "Example CAD",
  "notes": "Optional",
  "search_context": { "query": "...", "filters": {} }
}
```

Response uses `201` and a report id/state. It does not create an `mcp_servers` catalog row or install action.

## Authorization matrix

| Action | Standard engineer | Administrator |
|--------|-------------------|---------------|
| Search/read catalog | yes | yes |
| Read-only machine observation | yes | yes |
| Preview import/plan | yes | yes |
| Save credential through existing secret endpoint | existing policy | existing policy |
| Install/apply local or global capability | existing install policy | yes |
| Enable one permitted workspace | workspace policy | yes |
| Configure/activate/rollback catalog channel | no | yes |
| Submit missing report | yes | yes |

## Concurrency and idempotency

- Preview creation is idempotent for active snapshot, candidate digest, and actor within its validity window.
- Activation and rollback serialize with `BEGIN IMMEDIATE`; stale previews receive `409`.
- Plan apply is idempotent by `plan_id` and digest; a completed plan returns the existing run result.
- Client retries never produce duplicate install effects or missing reports when an idempotency key is supplied.
