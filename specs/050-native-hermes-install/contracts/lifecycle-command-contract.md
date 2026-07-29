# Lifecycle Command Contract

## Common result

Every command returns a structured `LifecycleResult` and a concise
manager-facing projection. Errors are stable codes plus redacted remediation; traceback,
credential, raw environment, and unbounded subprocess output are forbidden.

Mutating commands acquire the lifecycle lock, record intent, execute bounded
checkpoints, and record one terminal state. Repeated identical requests are
idempotent. A competing request receives `lifecycle_busy` with the active
operation ID and does not disappear or corrupt state.

## `/wright start`

1. Validate manager-adapter/runtime/platform/data-schema compatibility.
2. Install the exact compatible runtime if absent.
3. Reconcile an interrupted prior operation.
4. If a challenged healthy instance already exists, return it.
5. Refuse to reuse or kill an unverified PID/port owner.
6. Launch the isolated packaged runtime with stable data/static paths.
7. Poll bounded health and identity endpoints.
8. Mark healthy and return the UI URL only after challenge verification.
9. On candidate activation failure, restore the compatible predecessor where
   safe or return `recovery_required`.

After the manager adapter is installed, start MUST NOT inspect a repository,
`WRIGHT_REPO_DIR`, frontend source, or invoke Git, Docker, Node, npm, or a
frontend build.

## `/wright status`

Returns within the bounded probe window and includes:

- invoking manager adapter, active runtime, predecessor, Python, and compatibility versions;
- lifecycle state and active operation;
- process identity and challenged API/UI health;
- active manager connection, MCP transport, catalog, data-schema, configuration, and
  workspace summary;
- non-secret paths and safe next actions.

Status is read-only and does not install, migrate, start, stop, or delete.

## `/wright doctor`

Runs status plus artifact integrity, environment containment, process ownership,
ports, data permissions/integrity, backup readiness, compatibility, active
manager route, MCP transport/catalog, and secret-permission checks. Optional external
services are reported separately from core native readiness.

## `/wright stop`

- If no verified process exists, return already stopped.
- Signal only the challenged contained runtime process.
- Wait a bounded graceful interval, then use a platform-safe escalation only if
  identity still matches.
- Clear process state after confirmed exit; never stop Hermes, Codex, or another
  port owner.

## `/wright update [version]`

- Resolve only an operator-approved stable/test/local candidate channel.
- Stage and verify the new exact runtime before stopping a healthy predecessor.
- Check compatibility and data schema, back up before migration, activate, and
  challenge health.
- Retain the predecessor and exact evidence after success.
- Restore the predecessor on safe failed activation; otherwise return
  `recovery_required` with backup details.

## `/wright rollback [version]`

- Default target is the recorded predecessor.
- Validate artifact integrity, adapter/runtime compatibility, and data schema before
  stopping the active runtime.
- Never silently restore an older data backup or discard post-update work.
- If target cannot open current data, refuse automatic rollback and provide the
  explicit backup recovery path.

## `/wright uninstall`

- Stop a verified runtime.
- Remove all managed runtime environments, caches, and executable lifecycle state.
- Preserve user data, configuration, secrets, and all workspaces by default.
- Return the preserved data location and reinstall recovery guidance.
- Remain independent of manager adapter removal. For Hermes 0.19, users run this
  command before `hermes plugins remove wright` because Hermes exposes no
  pre-remove callback.

## `/wright purge`

- Is distinct from uninstall and requires an explicit confirmation token or
  non-interactive test flag bound to the displayed path set.
- Resolve and validate every target beneath Wright-owned data roots.
- Reject symlinks, external workspaces, home/root directories, manager-owned
  data, and ambiguous configuration.
- Stop/uninstall first if needed, delete only approved targets, and report an
  auditable redacted manifest of categories removed.

## Existing commands

`/wright open`, catalog, catalog search, info, and MCP registration retain their
public behavior but use the active packaged API. Catalog commands that require a
running API either start it through the lifecycle contract or return an explicit
start instruction; they never fall back to repository detection.
