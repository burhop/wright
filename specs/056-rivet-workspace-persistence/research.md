# Research: workspace persistence

## Decisions

1. Reuse `workspace_service` as the ownership/orchestration boundary; its existing filesystem use cases and path protections are the closest established behavior.
2. Keep canonical content in workspace files, not SQLite. `data_vault` receives only searchable metadata, revision and recovery references.
3. Use generated UUID workflow IDs, normalized slugs, SHA-256 ETags, and monotonically increasing revisions. The API compares expected revision before an atomic replace.
4. Stage to a same-directory temporary file, flush file and directory where supported, then replace. Platform-specific limitations are recorded and tested; recovery scans staged remnants.
5. Recovery is a workspace-local trash area (`workflows/.deleted/<id>/<revision>/`), never global or automatic deletion.
6. The offline condition from 055 does not block storage because this slice ships no Rivet build or Node dependency.

## Open only for implementation validation

Confirm the existing `LocalWorkspaceFiles` abstraction can supply no-follow and atomic primitives; if not, introduce a narrow port/adaptor rather than bypassing `workspace_service`.
