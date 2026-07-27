# Feature Specification: Security Control Plane and Workspace Confinement

**Feature Branch**: `codex/042-security-control-plane-and-workspace-confinement`  
**Created**: 2026-07-10  
**Status**: Approved for implementation by the operator prompt

## Scope

Feature 042 closes SEC-01 and SEC-02 from `docs/gpt5-6plan.md`. It introduces
an authenticated local control plane, configured browser and WebSocket origins,
and one workspace path capability used for ordinary files, backups, and
workspace-local scratch data. Secret-provider, container, migration, gateway
protocol, packaging, and Hermes changes belong to later features.

## Requirements

- **FR-001**: Health and setup-status discovery may remain public; mutating,
  code-execution, settings, logs, MCP lifecycle, gateway-call, and workspace
  data routes MUST require an authenticated local principal.
- **FR-002**: Administrative control-plane operations MUST require the admin
  role. The initial local token represents an admin; the dependency contract
  MUST permit later non-admin principals without changing routes.
- **FR-003**: Authentication MUST use constant-time token comparison and MUST
  not place tokens in URLs or logs.
- **FR-004**: CORS origins MUST be an explicit configured allowlist. Wildcard
  origins are forbidden.
- **FR-005**: WebSocket connections MUST validate both origin and bearer token
  before acceptance.
- **FR-006**: Enforced mode MUST fail closed when no token is configured.
  A clearly named temporary compatibility mode may disable auth for one
  migration release and MUST emit an explicit warning.
- **FR-007**: Remote bind configuration MUST be rejected unless enforced auth
  is enabled and a token is configured.
- **FR-008**: A single `WorkspacePath` capability MUST resolve workspace file,
  backup, and scratch paths and reject traversal, absolute paths, different
  Windows drives, UNC paths, and symlink/reparse-point escapes.
- **FR-009**: Backup identifiers MUST be exactly lowercase SHA-256 hex strings.
- **FR-010**: Scratch paths MUST live under `.wright/tmp`; global `/tmp` access
  is forbidden.
- **FR-011**: Existing safe workspace files and backup IDs MUST continue to
  work. Unsafe legacy scratch references MUST fail with an actionable error.

## Acceptance

- Cross-origin and unauthenticated HTTP/WebSocket requests fail before reaching
  handlers; authenticated allowed-origin requests retain their response shape.
- Traversal, absolute backup IDs, symlink escapes, UNC/drive paths, and global
  temporary paths are rejected while valid workspace files/backups succeed.
- Focused security tests and the repository dev merge gate pass.
- Threat-model, configuration, migration/rollback, and operator quickstart
  documentation describe actual behavior.

## Rollback

Set `WRIGHT_AUTH_MODE=compat` only for a time-limited local migration rollback.
There is no compatibility switch for path traversal or global temporary-file
access. Operators must move required scratch artifacts into `.wright/tmp`.
