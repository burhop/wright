# Data Model: Workflow Trace and Product Review

These are proposed additive contracts. Preserve existing runtime IDs and records; map them into these report identities through explicit adapters. Domain values belong in `core`, relational storage in `data_vault`, and projection/capture orchestration in `workspace_service`.

## Records

| Record              | Principal fields                                                                                                                                                                                                                  | Relationships and invariants                                                                                                                                 |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RunSnapshot         | schema_version, workspace_id, run_id, source_kind, source_record_ref, source_record_digest, workflow_id, definition_digest, definition_blob_ref, layout_blob_ref, input_baseline_refs, recorded_status, timestamps, capture_state | Definition and inputs describe this execution. Lifecycle comes from the execution producer. Missing legacy snapshots remain missing.                         |
| CaptureEvent        | run_id, sequence, event_id, producer, producer_event_id, occurred_at, event_kind, payload_ref, payload_digest                                                                                                                     | Sequence gives durable ingestion order, not proof of causality. Producer/event key makes ingest idempotent.                                                  |
| StepOccurrence      | occurrence_id, run_id, block_id, attempt_index, parent_occurrence_id, iteration_scope, state, started_at, ended_at, input_version_ids, output_version_ids, prompt_record_refs, tool_record_refs                                   | A block can have many occurrences; retries, rework, nested loops, and parallel branches retain explicit relationships.                                       |
| TraversalOccurrence | traversal_id, run_id, relationship_id, source_occurrence_id, target_occurrence_id, sequence, transferred_version_ids, outcome, producer_event_ref                                                                                 | Requires producer evidence. A configured connection alone does not establish traversal.                                                                      |
| ArtifactVersion     | version_id, run_id, occurrence_id, existing_result_id, output_port, role, display_name, representations, upstream_version_ids, supersedes_version_ids                                                                             | Identity includes occurrence and version, even when the runtime reuses a result ID or filename. Superseding is a link, not deletion.                         |
| Representation      | representation_id, version_id, kind, media_type, format, original_name, blob_ref, digest, byte_size, external_ref, availability, display_of_version_id, metadata_ref                                                              | Separate an original from a screenshot, mesh display conversion, PDF rendition, or cloud link. No generic filename-to-history resolution.                    |
| EvidenceRecord      | evidence_id, run_id, producer, producer_version, kind, recorded_at, subject_refs, statement_ref, recorded_outcome, supporting_refs, supersedes_id, producer_schema_version                                                        | Kinds include requirement, approval, assumption, decision, and validation. The producer owns the statement and outcome; Trace does not derive them.          |
| EvidenceLink        | link_id, relation, from_ref, to_ref, producer, source_event_ref                                                                                                                                                                   | Relations include derived_from, approved_by, justified_by, verifies, used_by, produced_by, display_of, and supersedes. Only recorded relations are asserted. |
| ReportRevision      | report_id, revision, run_id, capture_cursor, evidence_set_digest, renderer_version, schema_version, built_at, outcome, primary_version_ids                                                                                        | Repeatable projection over pinned records. New external evidence yields another revision without rewriting historical run facts.                             |
| ExportManifest      | export_id, report_id, revision, mode, entries, original_to_package_map, omitted_resources, viewer_capabilities                                                                                                                    | Every included entry has relative package path, original identity, size, and digest. Hashing here establishes byte identity, not engineering correctness.    |
| CorpusSelection     | version, source_checkpoint_ref, selected_cases, availability, acceptance_results                                                                                                                                                  | Each of 30 entries names a case and exact run/attempt; completed and incomplete outcomes remain distinct.                                                    |

## Storage and Capture

Use the existing SQLite WAL database for additive indices, occurrence records, evidence links, and report/export metadata. Preserve current run JSON files as authoritative source records for the canonical-source executor. Reuse the canonical execution repository where its producer is actually connected; do not assume every existing run uses that repository. Add an explicit source discriminator and adapter for supported record versions.

Use the workspace file vault for immutable content-addressed or equivalently versioned blobs. Reuse an immutable representation already in the vault instead of duplicating it. Inputs and artifact bytes must be captured at their actual consumption/publication boundary before later writes can replace them. Large directory outputs use an indexed relative-path manifest; the report need not eagerly enumerate every child.

Publication order is blob write to a temporary file, durable promotion, then a transaction recording references and event sequence. A failed or duplicate ingest must not publish dangling references or duplicate occurrences. Unreferenced temporary blobs can be recovered by existing cleanup policy; reports never delete source evidence.

Capture remains independent of HTTP sessions, browser polling, preview rendering, and report export. Metadata writes do not wait on preview generation. Capture failures preserve the original execution result and record an incomplete-capture condition through existing diagnostics; they must not trigger retries of engineering operations. Restart recovery distinguishes durable acknowledgments from in-flight uncommitted work.

## Identities and Historical Imports

- Preserve workspace/run identity, canonical block and relationship IDs, and definition digest from the producer. Store imported source bytes and an adapter-version receipt.
- New occurrence and traversal IDs are generated by the capture producer and reference their parent/run. Nested iteration context is a sequence of named scope/ordinal pairs, not one ambiguous global loop number.
- Legacy reconstruction may map explicit `step_started`, `step_completed`, `design_revision`, `result_ready`, and output events into occurrences. Store the source event offsets and derivation rule. Unprovable transfers or old versions remain unavailable.
- A source digest without retained source text is not sufficient to show today's graph as the executed graph. Use an exact digest-matching historical definition when available; otherwise offer retained steps with a local definition-unavailable notice.
- Byte-identical files may share blob storage while retaining separate occurrence/provenance identities.
- An external validation record bound only to a run may appear at run level. It must not be attached to an arbitrary artifact as if the producer checked that artifact.

## States

Execution state belongs to the source producer. The adapter maps it to `completed`, `failed`, `blocked`, `cancelled`, `interrupted`, or a faithfully labeled retained checkpoint. It preserves the original status alongside the display value. Approval/checkpoint state is not collapsed into execution success; the existing API's review overlay must not erase that distinction.

Capture state is separate: `complete`, `partial`, or `legacy`. Artifact availability is separate: `retained`, `external`, `session_only`, `missing`, or `omitted_from_export`. These states do not mean engineering pass or fail. A succeeded run can have a legacy capture gap without Trace manufacturing an unresolved engineering concern.

Report build state is `queued`, `building`, `ready`, or `failed`. Export build state adds `cancelled`. These are report-generation states, not workflow outcomes. Publishing a report/export is atomic; cancellation does not change the run.

## Access and Future Comments

Resolve files through existing workspace authorization and confinement. Never use a URL-supplied absolute path as a file capability. Keep executable/generated HTML isolated through established renderers and escape data embedded into report HTML. Credentials and transient authentication values are not report payloads; mark intentional redactions without fabricating substitute prompt content.

Stable anchors contain run, report revision, subject kind, and subject ID. Future comments can target these anchors in separate records. This phase does not add comment persistence, edit permissions, assignments, or workflow mutation.
# Campaign Publication Addendum

## Campaign report inventory

Pins `case_id`, workflow family, `attempt_id`, `run_id`, source run path and
SHA-256, dataset/template revision digests, recorded status, produced artifact
counts, stopping reason, and known historical gaps. Completed cases preserve the
reviewed acceptance selection; incomplete cases preserve the latest retained
attempt. The inventory is immutable input to batch publication, not a runtime
status model.

## Campaign report entry

Relates one inventory case to its export mode, standalone ZIP path/digest/size,
and extracted `index.html` path. Entries are grouped by family in the portable
catalog. A failed entry remains failed even when its report package is complete.

## Publication invariants

- One inventory identity maps to one report entry per requested export mode.
- Every included resource matches both its retained digest and extracted bytes.
- Catalog and report links are package-relative and remain below publication root.
- Publication never changes source evidence or invokes workflow/validation code.
