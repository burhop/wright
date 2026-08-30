# Data Model: EPP-F02 Process Definition

## ProcessDefinition

- `schema_version`: exact supported version (`1.0.0` initially)
- `process_id`: stable lowercase identity
- `revision`: immutable positive revision
- `title`, `purpose`: customer-readable text
- `content_sha256`: canonical identity excluding this field
- ordered `phases`; closed registries of `actions`, `ports`, `gates`, `feedback_paths`, and `artifacts`

Validation: maximum 1 MiB; strict UTF-8 JSON; no BOM, duplicate keys, non-finite or non-integer numbers; supported version; every string already NFC; exact `wright-process-json-v1` digest; one global ID namespace; every reference resolves exactly once.

## Phase

`id`, `title`, `purpose`, ordered non-empty `action_ids`. Every action belongs to exactly one phase.

## Action

`id`, `title`, `purpose`, and lists of input/output port, gate, feedback, and expected-artifact IDs. Empty lists are valid and display as “none declared.”

## Port

`id`, `name`, `direction`, `value_type`, `description`, `owner_action_id`, and nullable `source_port_id`. Input lists reference only input ports owned by that action; output lists reference only output ports owned by that action. An internal input names exactly one earlier output of the same `value_type`; an external input uses `null`.

## Gate

`id`, `title`, `condition`, `owner_action_id`, `pass_target_id`, `fail_target_id`. Both targets are actions. Pass is strictly later in phase/action order; failure is strictly earlier. The owning action references the gate exactly once, and the failure target has exactly one matching feedback edge from the gate.

## FeedbackPath

`id`, `from_id`, `to_id`, `reason`. `from_id` is exactly one gate and `to_id` is its earlier failure-target action; the gate and owning action reference the edge reciprocally; self-loops are invalid.

## ExpectedArtifact

`id`, `name`, `artifact_type`, `purpose`, `produced_by_action_id`. Producer and artifact references are reciprocal. This declares an expectation, not runtime evidence.

## ProcessDefinitionEnvelope

Validated `definition`, `source_kind` (`installed` or `packaged_fallback`), allowlisted logical `source_id`, `source_sha256`, `source_available`, `etag`, and `supported_schema_versions`. `source_id` is never an absolute path or URL and is limited to the fixed package-relative identity `process-definitions/product-definition-v1.json`. `etag` is the SHA-256 of the canonical complete envelope excluding `etag` and the request-specific trace header; it therefore changes when either semantic content or the raw source bytes change.

## Closed reference invariants

- IDs are globally unique across process, phases, actions, ports, gates, feedback paths, and artifacts.
- Phase order plus `action_ids` defines the only action order; each action belongs to exactly one phase.
- Port ownership, direction, type, and internal-source relations are reciprocal and type-equal.
- Gate pass/fail targets and feedback edges obey the strict ordering and reciprocity above.
- Every artifact is referenced by and produced by exactly one action; `artifact_type` and `value_type` use the schema's closed vocabularies.
- The frozen sample and expected trace are `contracts/product-definition-v1.sample.json`: `customer-needs` → `capture-requirements` → `requirements-baseline` → `define-product` → `product-model` → `definition-approval` → `release-product-definition` → `released-definition-package`; failure returns to `define-product`.

There are no mutable transitions in EPP-F02. A definition is unavailable, rejected before presentation, or returned as one immutable envelope.
