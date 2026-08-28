# Program Status Read API Contract

## `GET /api/program-status`

Returns the latest completely validated `ProgramStatusBundle`. The route is read-only and protected by Wright's existing local-session security boundary.

### Request

- Optional `If-None-Match`: exact quoted bundle ETag from a prior success.
- Optional `X-Trace-Id`: handled by existing tracing middleware.

### Success

`200 application/json`: body conforms to `program-status-bundle.schema.json`; `ETag` is the quoted `bundle_id`; `Cache-Control: no-cache, private`; `X-Program-Status-Observed-At` is server observation time, not evidence freshness; `X-Trace-Id` is present.

`304 Not Modified`: returned only when the request ETag matches the current validated bundle. It has no body and does not regenerate or reinterpret evidence.

### Typed failures

- `404 PROGRAM_STATUS_UNAVAILABLE`: no valid installed or packaged fallback exists.
- `409 PROGRAM_STATUS_IDENTITY_MISMATCH`: envelope, body, snapshot, or delivery identity does not bind exactly.
- `422 PROGRAM_STATUS_INVALID`: installed data violates schema or allowlist.
- `503 PROGRAM_STATUS_READ_FAILED`: bounded local read failed.

Failures include a recovery class and trace ID, never evidence content or private paths. The browser retains its last valid bundle after any failed refresh and marks it stale/failed; without one it shows unavailable values.

The packaged fallback is read only when the installed bundle is absent. An installed bundle that is corrupt, invalid, unsupported, or identity-mismatched produces the applicable failure above and MUST NOT silently fall back to an older packaged snapshot.

## Refresh behavior

The full endpoint's ETag/304 behavior is the only committed-evidence identity contract. Implementations MUST NOT add a second evidence-identity endpoint unless analysis proves this bounded route misses the target and the contract is amended before implementation.

## `GET /api/program-status/publisher`

Returns only bounded operational publisher state conforming to `#/$defs/publisher` in the bundle schema: mode, active/inactive/failed/unavailable state, last observed committed identity, last attempt/success times, failure code, and recovery. It uses `Cache-Control: no-store`, never claims readiness or authority, and is excluded from `bundle_id`. Changes to this operational response MUST NOT advance the main bundle ETag or create a history observation.

The route is protected by the same engineer/admin read policy as the bundle route and delegates to the typed `tool_registry` reader. `200` returns the closed publisher object; missing state returns `404 PROGRAM_STATUS_PUBLISHER_UNAVAILABLE`; invalid state returns `422 PROGRAM_STATUS_PUBLISHER_INVALID`; bounded read failure returns `503 PROGRAM_STATUS_PUBLISHER_READ_FAILED`. Publisher failures never cause the bundle route to mutate, regenerate, or discard its last valid view. The contributor watcher polls committed identity every two seconds by default; the browser polls this endpoint at its five-second refresh cadence.

## Security and bounds

- Maximum file size: 4 MiB.
- Maximum 250 points per metric series, 250 correction/finding disclosures, 100 risk records, 100 decision records, 100 catalog stories summarized, and 50 integration events.
- Every evidence link targets an internal detail entry bound to an exact allowlisted path/digest. Optional exact-commit HTTPS GitHub evidence/PR/check links are secondary, limited to 1,000 characters, and rejected when malformed even if they share an allowed prefix; unavailable raw content is labeled rather than fetched.
- Credentials, cookies, tokens, prompts, raw commands/arguments/logs, engineering bodies, reusable authority, and private absolute paths are forbidden.
- GET performs no Git operation, subprocess, benchmark, product action, filesystem mutation, external request, or telemetry upload.

## Compatibility

- The `1.0.0` contract is closed: unknown fields are rejected. Any additive shape requires a new explicitly supported schema version and compatibility fixtures before use.
- Removing/renaming required fields or changing semantics requires a major schema and explicit compatibility decision.
- Unsupported major versions fail closed while preserving the last valid view.
