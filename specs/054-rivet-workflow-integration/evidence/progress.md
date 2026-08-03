# Rivet integration program progress

| Slice | Status | Umbrella merge | Evidence / note |
|---|---|---|---|
| 055 compatibility spike | Complete | `b38942f` | Conditional go: Node runner, cancellation, and editor seam proved; Windows offline upstream source build cache remains blocked. |
| 056 workspace persistence | Complete | `af7c54a` | Workspace-authoritative revisioned project and dataset persistence, feature-disabled APIs, and metadata migration verified. |
| 057 headless runner | Complete | `ba728f8` | Default-off supervised Node lifecycle fixture, immutable revision binding, session/generation scope, cancellation, cleanup, and absence behavior verified. Durable run history remains owned by workflow operations. |
| 058 editor host adapters | Complete | `0352986` | Local manifest/checksum catalog plus opaque workspace/session/workflow grants and persistence adapters verified. Real editor assets remain deliberately unavailable until offline package evidence is closed. |
| Workspace tab | Next | — | Must consume the adapter boundary as a retained isolated `LiveAppSurface`; no React-tree import. |

No slice has been pushed, proposed to a remote pull request, merged to `dev` or
`main`, published, or released. The unresolved Windows offline package-cache
finding is a release-hardening gate and does not authorize a production Rivet
runtime bundle.
