# Definition-only workflow transfer

Implemented 2026-10-08 in `core.workflow_bundle`,
`workspace_service.workflow_bundles`, and the authenticated
`/api/workspace/workflow-bundles` router. No live services were restarted and no
external engineering actions were performed.

## User journey and contract

The editor can export the exact saved source and a dependency manifest, or a
bundle selecting declared workspace reference files and saved working interfaces.
The destination workspace inspects the bundle before importing at a fresh source
filename. Import creates a local source revision using the existing confined
source store. Embedded instruction bodies are never materialized from destination
defaults. Unmigrated legacy source retains an explicit dependency on its old local
instruction defaults rather than acquiring silently changed behavior.

POST `/export`: `session_id`, `path`, `expected_storage_digest`, `mode` (`source`
or `bundle`), optional `selected_reference_paths`, `selected_ui_ids`.
Returns `bundle` and `bundle_digest`.

POST `/inspect`: `session_id`, `bundle`, `destination_path`.
Returns `bundle_digest`, `can_import`, `can_run:false`, `diagnostics`,
`external_dependencies`, `requirements`. An importable definition is not an
execution readiness certificate. The existing preparation/gateway/validator and
model adapter retain readiness and execution authority.

POST `/import`: inspection fields plus `expected_bundle_digest`.
Returns the fresh `source` document, `imported_paths`, and its `inspection`.
Apply re-inspects the exact submitted bundle and destination; a stale caller
digest or existing destination blocks publication.

## Preserved and deliberately external data

- Source, instruction versions/bodies/body digests, and layout are copied exactly.
- Selected declared reference files carry exact SHA-256 digests and bounded bytes.
- Validator configuration, pinned profile and its embedded requirements baseline
  are snapshotted. Workspace profiles also carry their exact file bytes. Packaged
  profiles remain runtime package dependencies: a missing/different pinned package
  requires installation or deliberate source migration, not silent substitution.
- Provider requirements retain source binding and schema identities. A gateway
  catalog can add observed provider operation/schema identities at export. A
  server UUID or title cannot qualify an imported binding. Local registry review
  and ordinary runtime preflight remain mandatory.
- Model requests retain the source's requested model/default and output format.
  Destination adapter capability/resolution is explicitly external; import does
  not fabricate actual model resolution or authorize compatible substitution.
- Selected saved UIs retain exact source, manifest, bindings and interaction/
  client/kit versions. They are imported as **inactive editable candidate files**
  with original provenance references, not activated saved builds. Local rebinding,
  the existing builder, preview/review and saved-revision owner must establish a
  new trusted revision. The common working view remains usable. Unsupported kit/
  client versions produce an explicit compatibility warning.
- No active runs, waiting checkpoints, input answers, approval receipts, authoring
  jobs, build trust, principal grants, registry configuration or credential store
  records transfer. Known credential configuration keys and private key locations
  are rejected. Arbitrary user-authored text/files are not a universal secret
  detection boundary; selected content should already be suitable to share.

## Filesystem and transport bounds

The format is closed bounded JSON (`wright.workflow-bundle/1`), not a ZIP archive.
Reference archive bytes are opaque; the importer never decompresses or executes
them. Source has a 1 MiB UTF-8 limit; assets have an 8 MiB limit each and the whole
canonical bundle a 20 MiB serialized limit. API request collection is bounded
before JSON materialization. Asset paths reject absolute/UNC/drive/ADS names,
traversal, backslashes, hidden authority directories, Windows reserved names,
credential locations, case aliases, duplicates and file/directory collisions.

Existing source-store pinned directory capabilities own reads and write-once
publication, including reparse point checks and concurrent reservation. Imports
never overwrite existing sources/assets. Required dependency manifests are
recomputed from source instead of trusting a supplied inventory. Unlisted assets,
omitted dependencies, mismatched hashes/profile baselines and unsupported metadata
are rejected. Definition publication occurs last. A disk/race failure may leave
new immutable candidate/assets already written; it cannot create a run or grant
approval. There is no cross-file transaction or automatic destructive cleanup.

## Verification

Focused core, workspace and authenticated transport suites:
**35 passed, 1 skipped**, 2 existing Starlette deprecation warnings.
The combined run including the existing source-store regression suite reports
**93 passed, 3 skipped**, with the same 2 deprecation warnings.
The skipped Windows test could not create a symlink on this host. Path policy and
the existing storage owner's reparse-point protections remain exercised separately
by their established storage tests; this result does not claim a new live junction
attack demonstration. Ruff checks for the six new Python files pass; diff check
reports no whitespace errors.

Proven: two isolated workspace source transfer; exact instruction A preserved
despite a different local default B; fresh revision identity; selected reference
and both packaged/workspace profile snapshots; pinned baseline rejection;
provider schema and requested model requirements; retained valid layout; inactive
UI source/bindings/versions without trusted build; legacy defaults dependency;
no overwrite; omitted/injected manifest/asset rejection; source hash, base64,
size, path, duplicate/case alias and stale digest rejection; authenticated owning
session scope, no-store headers, closed request schema and 413 body bound.

The editor integration and a human-repeatable served UI export/import walkthrough
remain the frontend owner's work. No claim of user acceptance is made here.

## 8 October authenticated transport follow-up

The normal served export/import path exposed two additional transport defects.
Imported source responses omitted the scoped API envelope; the router now returns
authenticated `workspace_id` and `metadata_authority: wright_host` consistently
with ordinary source routes. No authority transfers in the package.

A live fresh dependency probe also found that tampered embedded asset content
triggered a Pydantic `ValueError` in request validation, but the API handler tried
to serialize that exception in `ctx` and produced HTTP 500 instead of useful
JSON 422. Bundle validation now uses the existing bounded error serializer with
private-field redaction and `no-store` headers. Invalid asset/source digests,
duplicate assets and traversal are rejected without echoing full instruction
source, base64 assets, private paths or exception objects. The focused combined
core/service/API suite passed **39 tests**, with the same one host symlink skip
and two existing deprecation warnings. Import validation was not weakened.

The normal authenticated dependency proof uses separate existing isolated origin
and import workspaces and fresh unique paths. It transfers a declared synthetic
reference and an unchanged existing Robot Tracking Diagnosis validation profile;
this is a dependency/identity transport fixture, not an engineering assessment.
Missing/tampered references, absent profile bytes and changed pinned profile or
baseline identities must fail before any source/assets are published. Complete
import must retain exact instruction text, bytes and pins. No model request,
provider activation, execution or decision is part of this proof. Its script and
bounded report are retained under
`.local-run/process-interfaces-083/instruction-portability/prove-bundle-dependencies.py`.
After the parent-owned reload (API process 51856), all **8 served cases passed**
through the authenticated source/export/inspect/import endpoints. Cases include
complete qualification, missing reference, mismatched reference digest, missing
workspace profile bytes, changed profile version, changed baseline version,
omitted validation dependency and normal import/readback. Tampered digest returns
structured HTTP 422; dependency mismatches return inspect diagnostics with
`can_import: false`. No incomplete import published a source or profile file.
Successful import retained exact source/instruction text, scoped source metadata,
reference bytes and a loadable matching profile/baseline. Evidence:
`.local-run/process-interfaces-083/instruction-portability/bundle-dependency-proof.json`.
The initial HTTP 500 remains a recorded finding, rather than being erased by the
successful rerun.
