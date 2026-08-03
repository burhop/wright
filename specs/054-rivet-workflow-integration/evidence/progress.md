# Rivet integration program progress

| Slice | Status | Umbrella merge | Evidence / note |
|---|---|---|---|
| 055 compatibility spike | Complete | `b38942f` | Conditional go: Node runner, cancellation, and editor seam proved; Windows offline upstream source build cache remains blocked. |
| 056 workspace persistence | Complete | `af7c54a` | Workspace-authoritative revisioned project and dataset persistence, feature-disabled APIs, and metadata migration verified. |
| 057 headless runner | Complete | `ba728f8` | Default-off supervised Node lifecycle fixture, immutable revision binding, session/generation scope, cancellation, cleanup, and absence behavior verified. Durable run history remains owned by workflow operations. |
| 058 editor host adapters | Complete | `0352986` | Local manifest/checksum catalog plus opaque workspace/session/workflow grants and persistence adapters verified. Real editor assets remain deliberately unavailable until offline package evidence is closed. |
| 059 workspace tab | Complete | `5c1736f` | Default-off workspace Workflows tab chrome is present; the real retained editor stays unavailable pending verified offline assets. |
| 060 Wright nodes | Complete with hardening follow-up | `f3cd5de` | Gateway bridge carries run/workspace/session scope and forces server-side approval policy; runner-to-bridge execution wiring and durable provenance remain hardening work. |
| 061 workflow operations | Complete | `4725e75` | Exact workspace/revision review is required before launch; catalog, review, run, cancellation, and bounded scope-checked history are default-off. Migration 11 preserves earlier metadata. See `specs/061-rivet-workflow-operations/evidence.md`. |
| 064 retained editor host | Complete | `cdbf110` (restored by `5dac57e`) | Pinned offline Rivet artifact, bounded localhost host, isolated retained workspace surface, stable re-open declaration, and browser-only import/export disclosure are verified. Disabled or missing editor paths cannot declare or start a process. See `specs/064-retained-editor-host/evidence.md`. |
| Agent publication (optional P2) | Deferred | — | Requires a separate explicit approval; it does not block MVP completion. |
| Release hardening | Deferred with execution program | — | The editor-tab MVP does not include a Node runner, governed execution, provenance, or execution packaging. Those concerns require a separately approved future program. |

No slice has been pushed, proposed to a remote pull request, merged to `dev` or
`main`, published, or released. The unresolved Windows offline package-cache
finding is a release-hardening gate and does not authorize a production Rivet
runtime bundle.

## Umbrella validation

- `scripts/check-dev-merge.sh` passed locally on 2026-08-03 for the scoped
  editor-tab MVP. The umbrella branch remains unmerged into `dev`.
