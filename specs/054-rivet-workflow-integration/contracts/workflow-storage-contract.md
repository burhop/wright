# Contract: Workspace-Owned Rivet Storage

**Owner slice**: `rivet-workspace-persistence`

**Consumers**: editor adapters, headless runner, workflow operations, optional agent publication

## Contract Goals

- A workflow is portable with and isolated to one Wright workspace.
- Browser profile state and global Rivet directories are never authoritative.
- Saves are atomic, revision-aware, auditable, and safe under concurrency.
- Authored content remains inspectable and source-control friendly.
- Operational payloads, secrets, and ephemeral authority use their existing Wright owners.

## Canonical Layout

```text
<workspace>/
|-- workflows/
|   `-- <workflow-slug>/
|       |-- workflow.rivet-project
|       |-- workflow.rivet-data          # when the selected Rivet format uses a sidecar
|       |-- datasets/                     # host-managed dataset representations
|       `-- assets/                       # author-owned allowlisted attachments
|-- artifacts/                            # existing Wright artifact conventions
`-- .wright/
    `-- rivet/                            # private recoverable editor metadata/index hints
```

The persistence slice may refine file names after the compatibility spike identifies exact formats. It must preserve the ownership classes and document migrations. User-provided paths are never concatenated directly onto the workspace root.

## Operations

Every operation receives authenticated Wright context server-side; request bodies cannot select authority.

| Operation | Required inputs | Result |
|---|---|---|
| List workflows | bound workspace, pagination/filter | bounded metadata only |
| Create | title/slug, optional approved template | workflow metadata and initial revision |
| Open | workflow ID | project, dataset manifest, revision/ETag |
| Save | workflow ID, expected revision, validated content | new revision or conflict |
| Save as | source revision, new title/slug | new workflow identity and revision |
| Rename | workflow ID, expected revision, new slug/title | atomic metadata/path update |
| Delete | workflow ID, expected revision | policy-defined soft delete/tombstone; no artifact erasure by implication |
| Recover | workflow ID/recovery identity | explicit preview/apply flow, never silent overwrite |
| Dataset get/put/delete | workflow ID, dataset ID, expected revision | bounded dataset revision |

## Save Semantics

1. Authenticate and bind user/session/workspace.
2. Resolve workflow ID through the repository; never trust a request path.
3. Validate permissions, format/schema, size, project references, paths, plugin manifest, and requested capabilities.
4. Compare expected revision/ETag to current revision.
5. Stage all related writes below a server-controlled workspace staging location.
6. Flush and atomically replace according to a documented supported-platform algorithm.
7. Commit/update the metadata index only after authored files are durable; reconcile detectable partial states after crash.
8. Return the exact new revision and digest.

A stale save returns a structured conflict containing current metadata but not protected content the caller could not otherwise read. Last-writer-wins is prohibited.

## Confinement

The storage implementation rejects:

- absolute, UNC, device, drive-relative, or URI paths;
- `..`, encoded traversal, alternate separators, reserved device names, or invalid Unicode normalization;
- symlink/junction/reparse-point escapes at every traversed component;
- hard-link behavior that violates workspace ownership where detectable;
- project references, datasets, or attachments resolving outside the owning workflow/workspace;
- unsupported future formats, unbounded decompression, oversized fields/files/counts, or unexpected executable content;
- secret or credential fields prohibited by Wright policy.

Confinement is rechecked on every open and save, not only at creation.

## Consistency and Recovery

- The workspace files are the source of truth for authored content; indexes can be rebuilt.
- A run consumes an immutable revision/digest and dataset manifest, never a mutable working file handle.
- Crash recovery distinguishes complete current revisions, recoverable staged writes, and corrupt/ambiguous states. Ambiguous content is quarantined for explicit recovery rather than guessed.
- Moving a workspace preserves relative identities. Deleting/disconnecting a workspace revokes editor/runner access and initiates owned lifecycle cleanup.
- Read-only workspaces allow list/open and prohibit save/rename/delete with actionable errors.

## Secret and Metadata Rules

- Project files may contain logical secret-reference names but never resolved secret values, reusable bearer tokens, approval grants, session IDs, or debugger credentials.
- `.wright/rivet` may hold bounded recovery state, selected workflow, and compatibility metadata; it may not hold live process authority.
- Run inputs containing protected values use access-controlled references/digests according to existing Wright artifact and audit rules.

## Compatibility

The physical Rivet format and Wright metadata schema each carry an explicit version. Readers reject unsupported future versions without modification. Supported migrations create a backup/recovery point and are independently reversible or permit safe feature disable with old files preserved.

## Required Contract Tests

- Two-workspace isolation across every operation.
- Concurrent save and stale ETag conflict.
- Atomic multi-file save with injected failures at every boundary.
- Traversal, symlink/junction, project-reference, malformed, oversized, and future-version cases.
- Read-only, moved, disconnected, and deleted workspace behavior.
- Restart/reindex/recovery from staged and partially indexed states.
- No secret, token, approval, process, port, or credential persistence.
- Identical behavior from browser, Hermes, native, Docker, and installed artifacts where applicable.
