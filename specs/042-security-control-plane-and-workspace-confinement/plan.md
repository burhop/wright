# Implementation Plan: Security Control Plane and Workspace Confinement

Implement two incremental seams: `api.security` owns authentication, roles,
origin policy, and startup validation; `core.workspace_path` owns confined path
resolution. Add characterization/security tests before replacing router-local
checks. Preserve public health/setup discovery and existing response schemas.

## Order

1. Record the refreshed baseline and reconcile Specs 039-041.
2. Add failing SEC-01 and SEC-02 regression tests.
3. Add API security configuration/dependencies and WebSocket preflight checks.
4. Add `WorkspacePath`, delegate `WorkspaceManager` path/backup operations to
   it, and remove router-local backup joins/global `/tmp` fallback.
5. Update deployment/security docs and run focused, then full merge gates.

## Boundaries

No publication, container hardening, secret-store migration, database migration
framework, or MCP protocol redesign is included. Those remain Features 043-046.
