# Security Checklist

- [x] Server-derived workspace identity.
- [x] Path traversal and symlink containment required.
- [x] No secrets/session authority in project, sidecar, or index metadata.
- [x] Typed validation/conflict errors do not leak cross-workspace content.
- [x] Recovery is workspace-local and auditable.
