# Data model and authority

**Contracts:** [interaction](contracts/process-interaction.md),
[runtime/source](contracts/runtime-and-source.md),
[UI/agent/hosting](contracts/ui-authoring-and-hosting.md).

Use additive SQLite WAL migrations and immutable vault objects. Do not introduce
a server database, replace the existing source-run recorder, or make a derived
interaction snapshot a competing run authority.

| Entity | Required identity and contents | Owner / lifecycle |
|---|---|---|
| ProcessRef | workspace_id, source_path, source_digest; accepted semantic/definition digest where available; supported source contract | Existing source/definition service; accepted source remains authoritative |
| InputSnapshot | snapshot_id, ProcessRef, canonical value/file/provider-choice bindings, provenance/default resolution, created_at, digest | New data_vault repository; immutable after start; a changed preparation creates another snapshot |
| ReadinessAssessment | ProcessRef + input digest + schema/provider revision; per-required-binding classification, blocking reasons, observation freshness, expiry | Workspace-service derived assessment; never a permanent start permission |
| StartReceipt | principal/workspace/process + request_id + payload_digest, run_id, initial outcome | Durable uniqueness before execution; conflicting reuse rejected |
| InteractionSnapshot | contract_version, ProcessRef, optional run_id/input snapshot, monotonically comparable cursor, inputs/outputs/assessments/pending/actions/observations | Derived from owning services; cache may be discarded/rebuilt |
| DeclaredInteraction | accepted step ID, kind, schema/decision set, instructions, upstream subject selectors | Source-owned declaration; schema and semantic digest frozen in checkpoint |
| InteractionResponse | response_id, checkpoint_id/subject_digest, values or decision, actor, reason, request_id, timestamp, response_digest | Immutable data_vault response + existing review records; one-shot continuation claim |
| Continuation v3 | existing source/run/cursor/completed-result identity plus checkpoint_kind, input_snapshot_id/digest, response_id/digest | Existing continuation repository; v2 reads preserved |
| ProcessUI | ui_id, workspace/process association, active saved revision, display title, archived flag | data_vault metadata; save/rollback explicit |
| ProcessUIRevision | revision_id/parent, source/build/manifest hashes, contract/client/kit versions, stable bindings, compatibility report, role/model/adapter/instruction/build provenance | Immutable source/dist/report vault artifacts; draft → built → previewed → saved; invalid/failed/cancelled drafts retained with bounds |
| CodingRoleResolution | role/profile version, prepared instruction digest, actual adapter/model reference, supported invocation constraints | Existing agent config plus role metadata; no secrets or mutation of global model |
| UIAuthoringJob | job_id/request_id, ProcessRef, base UI revision, role resolution, scope, attempt budget, current activity/error, draft revision | Workspace-service backend task; persisted status; generation repair budget ≤2 |
| PresentationBinding | existing presentation/runtime generation/grant IDs plus ProcessRef, ui_revision, permitted attached run, scopes and expiry | Existing surface services/grants; tab metadata is not authority |

## Relationships and constraints

- A run uses exactly one accepted ProcessRef and frozen InputSnapshot. Its step
  outputs remain existing EngineeringResults, with producer attempt/revision and
  artifact/representation hashes; the snapshot does not copy validation truth.
- Start identity is unique within principal/workspace/process; response/action
  identity is unique for its checkpoint. Same identity+payload returns recorded
  outcome; same identity+different payload returns conflict.
- A human-response output carries exact checkpoint/schema/response provenance.
  It is not a fabricated external-action receipt.
- UI revisions bind stable block/port/result-role/assessment selectors rather
  than filenames from a campaign directory. Essential schema/role changes mark
  incompatible; labels/layout may change without invalidating engineering work.
- The server resolves every artifact/file under authorized roots. User file
  upload creates a vault reference and digest; no raw absolute paths in app authority.
- UI files cannot overwrite process source, input packs, other interfaces, secrets
  or historical run outputs. New generation/update revisions get separate roots.
- A saved UI is reused with a new run/input context. Run-specific result IDs must
  not be baked into reusable source; views resolve current bindings through the client.

## State transitions

Run projection: preparing → ready → running → waiting_human / waiting_external /
reconciliation_required / completed / failed / cancelled. Existing underlying
states are mapped explicitly; unavailable progress is null, not invented zero.
Human response/review continuation returns to running on the same run identity.
Cancellation requested is distinct from confirmed cancelled; unknown effects
remain reconciliation_required until evidence resolves them.

Authoring: queued → resolving → generating → validating → building → preview_ready
→ saved, with failed/cancelled alternatives. Diagnostics can return to generating
within the persisted budget. Saving a new revision changes the active UI pointer,
not an accepted process or engineering result. Rollback selects a compatible saved
revision; removed capabilities still need fresh compatibility checks.

## Storage migration and recovery

Add repositories `process_interface_repository.py` and `process_input_repository.py`
under data_vault. Extend existing continuation/execution repositories for receipts
and v3 restoration; avoid a second run table with conflicting lifecycle.
Migration fixtures include old v2 checkpoints, historic run JSON and demo links.
Reads preserve their original digests and recorded decisions. Missing new optional
metadata is represented as legacy/unknown; it never proves current evidence.

Backend restart reconstructs finished/waiting views from records. Interrupted
active work is marked interrupted/reconciliation-required according to existing
leases and known outcome. Durable storage is not proof that an unknown external
operation can safely be executed again.
