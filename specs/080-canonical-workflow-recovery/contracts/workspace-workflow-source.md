# Workspace Workflow Source Contract

## Purpose

Persist one engineer-authored workflow definition as one visible file inside an
active Wright workspace while keeping canonical validation and storage-control
metadata rigorous and non-authorable. This contract stores opaque UTF-8 source;
semantic parsing, lowering, validation, and command acceptance remain the
canonical workflow layer's responsibility.

## Visible artifact

- Exact shape: `workflows/<safe-slug>.workflow.wflow`
- One workflow has exactly one visible definition file.
- A workspace may contain several named workflows. **New workflow** performs an
  exclusive create with a fresh workflow identity; **Open workflow** selects an
  existing safe path. A filename collision never replaces the earlier file.
- A plain read never creates the file, a workspace, or a default workflow.
- Entering **Workflows** within an active workspace is the explicit product-level
  intent to ensure the default file exists and open it immediately. Ordinary
  workspace entry and global navigation are not creation intent.
- Layout, viewport, selection, proposal preview, run state, attachments, and
  produced outputs are not written into this file.
- The authoring grammar does not contain definition/storage revisions, parent
  revisions, digests, absolute paths, locks, compare-and-set tokens, or opaque
  canonical IDs.

## Document response

```json
{
  "workspace_id": "workspace-id",
  "path": "workflows/mounting-bracket.workflow.wflow",
  "storage_revision": 3,
  "storage_digest": "64-lowercase-hex-sha256",
  "definition_revision": 4,
  "metadata_authority": "wright_host",
  "size_bytes": 6810,
  "source": "workflow mounting_bracket\n  ...\nend\n",
  "layout": null,
  "layout_revision": 0,
  "layout_status": "missing"
}
```

All fields other than `source` are host-produced. The client may display
relevant values read-only under Technical details but may not place them into
the engineer source.

## Operations

### Read

`GET /api/workspace/workflow-sources?session_id=<session>&path=<path>`

- Resolves workspace ownership from the active session.
- Returns the exact source document with `Cache-Control: no-store`.
- Returns 404 when the file does not exist and performs no write.

### Exclusive create used by idempotent workspace bootstrap

`POST /api/workspace/workflow-sources`

```json
{
  "session_id": "active-session",
  "path": "workflows/mounting-bracket.workflow.wflow",
  "source": "workflow mounting_bracket\n  ...\nend\n"
}
```

- The client calls this boundary only after the engineer enters **Workflows**
  inside an active workspace. No separate empty-state confirmation is required:
  that workspace-scoped action is explicit creation intent.
- The create call is exclusive: if the file is absent, it atomically stores the
  validated default and returns the created document; if the file already
  exists, it fails without replacing source or advancing storage or definition
  identity.
- Idempotence belongs to the workspace-entry orchestration. The client first
  reads; after a 404 it calls exclusive create. If create loses a concurrent
  first-entry race, the client performs one scoped read and opens the winning
  existing document byte-for-byte. If that read still does not return a valid
  document, bootstrap fails closed with Retry rather than guessing or looping.
- The host assigns definition revision `1` only to a newly created file; the
  client cannot author or seed this identity.
- The canonical editor must have validated the exact default source candidate
  before calling create. The storage service remains an opaque-byte
  authority rather than a second workflow parser. An existing file is never
  compared to or replaced by the request's default candidate.

### Compare-and-set save

`PUT /api/workspace/workflow-sources`

```json
{
  "session_id": "active-session",
  "path": "workflows/mounting-bracket.workflow.wflow",
  "source": "workflow mounting_bracket\n  ...\nend\n",
  "expected_storage_revision": 3,
  "expected_storage_digest": "64-lowercase-hex-sha256",
  "semantic_change_validated": true
}
```

- Both expected values must identify the current stored bytes.
- Every changed byte sequence advances storage revision exactly once.
- Definition revision advances exactly once only when the trusted canonical
  application layer attests `semantic_change_validated: true`; formatting-only
  writes may attest `false` and retain the definition revision.
- A no-op source returns the current document without advancing identity.
- Run-only activity never calls this operation. The 2026-09-02 authoring extension
  may send an independently versioned layout with unchanged source; that leaves
  source storage/definition identities untouched.

### Optional, separately versioned layout

`PUT` may include `layout` (the closed `RecoveryLayout` shape) and
`expected_layout_revision`. Supplying layout without its expected base fails
validation. This does not insert presentation data into the visible source or
change canonical semantics.

- The same source transaction lock checks both source CAS and layout CAS before
  any publication. A stale layout save returns the existing conflict envelope;
  the editor retains unsaved source and positions.
- Layout records are immutable hidden generations with a checked head pointer,
  finite/bounded coordinates, bounded object counts/size, and explicit source
  digest plus semantic-revision binding. Layout-only saves advance only their
  own revision. Source-plus-layout saves rebase layout to the committed subject.
- Legacy callers that omit layout leave its bytes and revision untouched. A
  well-formed layout belonging to another source digest **or definition revision**
  returns `layout_status: stale`, no applied layout, and the current readable
  source. Returning to previously used source bytes does not revive an obsolete
  layout from an earlier definition revision.
- Malformed layout metadata, a head/record mismatch, or invalid bounds fail
  closed. Synchronous publication failures roll back the transaction; injected
  exception tests are not proof of recovery from every process/power-loss point.
- The client hydrates only current canonical object positions. It removes
  deleted-object positions and deterministically places new/missing objects.

### Input-file choices

`GET /api/workspace/workflow-sources/input-files?session_id=<session>` returns the
registered workspace identity and bounded `{path, name}` choices. Resolution
uses the exact registered session without legacy fallback to another root.
Hidden/managed directories and unsafe link/reparse-point paths are excluded.
This is metadata listing only: it neither reads document content nor executes,
uploads, approves, or installs anything.

The Inspector stores real typed text or a relative file reference in canonical
scalar configuration. A configured reference is not evidence of execution or
current file contents. Any future opening/reading operation must re-resolve and
re-authorize the workspace/path; earlier listing is not a lasting access grant.

## Conflict contract

A stale save returns HTTP 409:

```json
{
  "error_code": "workflow_source_conflict",
  "message": "The workflow source changed after it was read",
  "trace_id": "trace-id",
  "details": {
    "current_storage_revision": 4,
    "current_storage_digest": "64-lowercase-hex-sha256"
  }
}
```

The server preserves the current stored bytes. The client preserves the local
unsaved source and exposes an explicit retry/reload-resolution path; it never
silently replaces either side.

## Validation and failure boundary

- UTF-8 source is limited to 1 MiB by encoded byte count.
- Only a safe slug and `.workflow.wflow` extension are accepted.
- Absolute paths, traversal, unsafe separators/names, symlink or reparse-point
  escapes, and paths outside the resolved workspace fail before write.
- The visible source and committed head use flushed same-directory atomic
  replacement. Revision entries are exclusive-create, hash-chained, and
  contiguous; the head binds the latest entry to the exact visible bytes.
- A synchronous failure while publishing the visible bytes, immutable journal
  entry, or committed head restores the prior source and removes an uncommitted
  journal entry before the transaction lock opens. A process or host crash may
  instead leave an incomplete transaction that the next read rejects as
  `workflow_source_integrity` rather than silently accepting.
- Same-path transactions are serialized by an in-process lock plus an OS file
  lock held across read/CAS/write, so concurrent local API processes using one
  base cannot both win. This is not a distributed multi-host lock and no
  distributed-lock claim is made.
- A committed `head.json` and retained hash-chained journal detect replacement
  of the visible file or rewind to historical visible bytes. They are a local
  integrity authority, not an external trust anchor against an actor able to
  replace the complete hidden metadata tree as well.
- Missing workspace/session scope, unsupported input, and storage errors use
  the existing typed Wright error envelope and include a trace identity without
  leaking secrets or host filesystem paths.

## Semantic boundary

The store deliberately treats `source` as opaque. Before bootstrap, the
canonical editor validates the complete default definition. Before save, it
parses the contextual source against the exact accepted base, lowers supported
changes to the closed command set, validates the complete candidate, and
retains the last-valid graph on failure. The
`semantic_change_validated` value is an application-layer attestation, not
independent server-side semantic proof. Storage success is therefore not proof
of workflow semantic validity outside that caller boundary, and the API must
not be described as a second canonical model.
