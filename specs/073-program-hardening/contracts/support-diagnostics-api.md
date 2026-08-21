# Support Diagnostics API Contract

Base path: `/api/workspace/support-diagnostics`

Authentication and workspace access use the existing Wright local identity and
workspace authorization dependencies. Routes contain no projection, redaction,
grant, or persistence logic.

## `POST /preview`

Request:

```json
{
  "workspace_id": "workspace-1",
  "scope": {"session_id": "session-1", "scenario_run_id": "run-1"}
}
```

The caller may narrow scope but cannot request arbitrary fields. Unknown keys,
path-like values, excessive identifiers, and a scope outside the authorized
workspace are rejected.

Response `200`:

```json
{
  "snapshot": {},
  "snapshot_digest": "sha256:...",
  "confirmation_token": "opaque-one-time-value",
  "expires_at": "2026-08-13T12:05:00Z",
  "filename": "wright-support-workspace-1-20260813T120000Z.json"
}
```

The snapshot validates against `support-diagnostic-snapshot.schema.json`.
Preview performs no filesystem write and no network request.

Errors: `400 INVALID_SCOPE`, `401 UNAUTHENTICATED`, `403 WORKSPACE_FORBIDDEN`,
`413 DIAGNOSTIC_SCOPE_TOO_LARGE`, `422 INVALID_REQUEST`.

## `POST /export`

Request:

```json
{
  "workspace_id": "workspace-1",
  "snapshot_digest": "sha256:...",
  "confirmation_token": "opaque-one-time-value"
}
```

Response `200` returns the exact previewed canonical JSON bytes with:

- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="wright-support-...json"`
- `Cache-Control: no-store`
- `X-Content-Type-Options: nosniff`

The grant is consumed atomically. The service rejects wrong principal,
workspace, scope/digest, stale, replayed, invalidated, or unknown grants without
revealing which comparison failed.

Errors: `401 UNAUTHENTICATED`, `403 DIAGNOSTIC_EXPORT_DENIED`,
`409 DIAGNOSTIC_PREVIEW_STALE`, `410 DIAGNOSTIC_PREVIEW_EXPIRED`,
`413 DIAGNOSTIC_EXPORT_TOO_LARGE`.

## Non-goals

- No upload endpoint, remote support destination, archive/ZIP output, arbitrary
  log inclusion, user-selected raw fields, or background export.
- No token, prompt, path, command, tool argument/result, model feature,
  engineering artifact body, or reusable run authority may appear.

