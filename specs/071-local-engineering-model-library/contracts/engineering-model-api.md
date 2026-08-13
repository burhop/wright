# Contract: Engineering Model HTTP API 1.0

Base path: `/api/v1/engineering-models`. Routes contain no model-library business logic and delegate immediately to an injected `EngineeringModelApplicationPort` owned by `tool_registry`; the workspace composition supplies its implementation. All mutating endpoints require local authentication, role checks, CSRF/origin protections where applicable, and an immutable workspace/session binding when workspace-scoped. Responses never expose raw data-root paths, source tokens, adapter commands/endpoints, or reusable authority.

## Catalog

| Method/path | Purpose |
|-------------|---------|
| `GET /catalog` | Bounded filter/sort/page over cached snapshot; no network side effect |
| `GET /catalog/{model_id}` | Package, variants, evidence facets, limitations, install/readiness projection |
| `POST /catalog/refresh-plans` | Preview remote snapshot refresh; separate confirmation required |

Filters include task, source, maturity, license/readiness/install/evidence state, OS, architecture, accelerator, runtime, and size ceiling. Every response includes active snapshot ID/digest/freshness.

## Effect plans

| Method/path | Purpose |
|-------------|---------|
| `POST /plans` | Create install/import/update/rollback/export/uninstall/purge preview |
| `GET /plans/{plan_id}` | Read exact effects, blockers, expiry, digest |
| `POST /plans/{plan_id}/confirm` | Confirm matching digest once and start durable operation |

Confirmation body contains `plan_digest` and the minimal explicit choices requested by the preview. Changed snapshot/manifest, resources, runtime, license, references, destination, credential availability, or expiry returns `409 plan_invalidated`; it never silently replans.

## Operations

| Method/path | Purpose |
|-------------|---------|
| `GET /operations/{operation_id}` | Durable state/progress/result/failure/cleanup |
| `POST /operations/{operation_id}/cancel` | Request idempotent cancellation |
| `GET /operations/{operation_id}/events` | Authenticated bounded SSE progress with reconnect cursor |

Terminal states are immutable. Unknown/unauthorized operation IDs return the same not-found projection. Events contain sequence, timestamp, state, phase, completed/maximum items/bytes, safe message, trace ID, and optional failure/recovery.

## Installations and testing

| Method/path | Purpose |
|-------------|---------|
| `GET /installations` | List exact local state and reference counts |
| `GET /installations/{installation_id}` | Detail, artifact/adapter/test/evidence health |
| `POST /installations/{installation_id}/test-plans` | Preview standard test resource/runtime effects |
| `GET /installations/{installation_id}/evidence` | Bounded test/verification history |
| `GET /installations/{installation_id}/references` | Explain removal/retention blockers |

Testing is effectful and uses the same plan/confirm operation flow. It cannot be bypassed by setting installation state through an API.

## Workspace bindings

| Method/path | Purpose |
|-------------|---------|
| `GET /workspaces/{workspace_id}/bindings` | List visible model task bindings |
| `POST /workspaces/{workspace_id}/binding-plans` | Preview enable/disable or replacement |

Confirmation runs through `/plans/{id}/confirm`. Enabling requires a ready exact installation, current passing evidence, compatible policy, and declared task. The response includes binding/tool/schema/install/adapter/policy digests used by Rivet review.

## Import and export

- Offline import first uploads or selects a bounded package into an operation-specific staging area, then creates a plan from inspected metadata. Selection alone does not install.
- Export planning reports redistributability blockers and exact contents. Successful download uses an opaque authorized artifact ID with expiry, not a host path.

## Error envelope

```json
{
  "error": {
    "category": "digest_mismatch",
    "message": "One staged artifact did not match the approved digest.",
    "recovery": "Discard the partial content and retry from the pinned source.",
    "trace_id": "...",
    "details": {}
  }
}
```

`details` is bounded and allowlisted. Stable HTTP mapping: malformed/schema `400`; authentication `401`; authorization/policy `403`; hidden resource `404`; stale/conflict/reference/plan invalidation `409`; size/resource `413` or `422`; rate/concurrency `429`; safe internal error `500`; source/runtime unavailable `502`/`503`; deadline `504`.

## Idempotency and pagination

Mutating preview/confirm/cancel requests accept a bounded idempotency key scoped to principal and endpoint. Reuse with different content returns `409`. Lists use opaque cursors and fixed maximum page size. Evidence/event collections have deterministic ordering and response byte ceilings.
