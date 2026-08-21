# Contract: Safe Run Result Projection

## Input boundary

The projection accepts either:

- the final Rivet runner `outputs` mapping; or
- an already-sanitized `GatewayToolResult` returned by `sanitize_gateway_result`.

It never accepts raw child transport envelopes after the gateway boundary.

## Projection order

1. Apply recursive secret-key and URL-query redaction using the existing Rivet evidence policy.
2. Normalize supported values into named result items.
3. Compute the SHA-256 digest and serialized byte size of the complete redacted value.
4. Retain the complete value when it fits the applicable limit.
5. Otherwise retain a deterministic type-aware preview and mark the item incomplete with the original size, retained size, digest, and reason.
6. Preserve only workspace-authorized artifact references.

## Limits

| Origin | Complete-value budget | Initial UI rendering |
|---|---:|---:|
| Final workflow outputs | Existing 1 MiB run-output limit | 64 KiB or 200 visible rows per expanded value |
| Intermediate MCP result | 64 KiB per child call | 32 KiB or 100 visible rows per expanded value |
| Text preview | 4 KiB | 4 KiB |
| History | 20 default, 50 maximum | 20 rows |
| Steps/events | Existing 256/1000 evidence bounds | 200 rows before progressive reveal |

An oversized output does not change `succeeded` to `failed`. The record sets `output_truncated`, and the UI states that only a retained preview is available.

## Type normalization

- Strings become `text`.
- Objects become `structured`.
- Arrays become `list`.
- Null becomes `null` and is shown explicitly.
- Authorized `wright://artifact/{workspace_id}/...` resource links become `artifact`.
- Safe HTTP(S) resource links become `link` only when the existing renderer policy allows them.
- Image/audio blocks become `media` metadata; raw binary/base64 is not copied into run history.
- Unsupported values become `unknown` with a bounded string preview.

## Completeness and redaction

- `complete=true` means the full redacted value available to Wright is retained.
- `complete=false` always includes `truncation_reason` or an unavailability reason.
- Redacted values display `[redacted]` and increment `redaction_count`.
- Copy and export use the retained safe value, never the pre-redaction input.
- Digests describe the complete redacted value, not a secret-bearing raw value.

## Backward compatibility

Old run records without result metadata are projected as complete only when their retained JSON is within bounds and no stored truncation flag is set. Old child-call records without a result projection show “Intermediate result was not retained for this historical run.” They are never represented as empty successful output.

