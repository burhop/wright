# Clean Install and Lifecycle Acceptance Contract

## Environment baseline

Each manager case starts in a disposable user boundary with only that manager's
documented prerequisites. The Hermes case includes released Hermes and Git for
the adapter-install phase. It begins with:

- no Docker socket/client;
- no Node.js, npm, npx, pnpm, or frontend build tools;
- no Wright source checkout, repository parent, editable install, or source-tree
  `PYTHONPATH`;
- no `WRIGHT_REPO_DIR`;
- no installed Wright distribution, data, runtime, or process.

The harness installs the Hermes adapter using the real Git CLI. It then removes
Git from the Wright runtime PATH, records every child executable, and fails if
runtime bootstrap/lifecycle invokes Git or any other forbidden runtime tool.

## Candidate artifact setup

- Build the exact Wright wheel once with prebuilt UI.
- Create an immutable local Git subject for the thin Hermes adapter.
- Serve the Wright wheel from a temporary wheelhouse/simple index configured for
  the adapter bootstrap.
- Disable production publication credentials and assert no stable registry,
  release, documentation, or manager channel mutation occurs.
- Record adapter commit, wheel filename/version/hash, and content-manifest hash.

## Required Hermes sequence

1. Install released Hermes in a clean profile with Git available.
2. Run the real `hermes plugins install <immutable-git-subject> --enable` flow.
3. Assert plugin import/registration is standard-library-only and does not
   import Wright application dependencies.
4. Remove Git from the audited PATH.
5. Run `/wright start`; assert the exact runtime was installed beneath
   `WRIGHT_HOME` automatically.
6. Verify challenged API identity, UI/index/assets, Hermes connection, MCP
   transport initialization, and canonical catalog.
7. Create a workspace and second Hermes session; exercise concurrent
   status/start, stop/restart, and workspace reopening.
8. Update from a previous immutable native artifact, or for the first native
   release from a lower immutable candidate, while retaining representative
   data.
9. Exercise pre/post-activation failure and successful/refused rollback.
10. Run `/wright uninstall`; verify runtime/process removal and data preservation.
11. Remove the Hermes adapter and prove Wright data plus external workspaces
    remain.
12. Reinstall, reopen preserved data, then explicitly purge and verify that only
    Wright-owned targets are removed.

## Codex sequence

Load the supported Codex MCP profile against
the same packaged Wright runtime. Complete MCP initialize, list tools, and at
least one read-only call over the claimed transport. Verify the profile contains
no Hermes path or intermediary and resolves the same runtime/product identity.

## Failure scenarios

The automated suite covers interrupted download/install, hash mismatch,
incompatible adapter/runtime, lock contention, concurrent starts, stale
manifest, reused PID, occupied port, failed health challenge, failed migration,
missing rollback artifact, permission failure, symlinked purge target, and
network unavailability with/without a valid cache.

## Platform matrix

The matrix is generated from the compatibility contract and public support
documentation. Each claimed manager/platform combination must run its required
adapter/profile proof plus the shared Wright lifecycle sequence. Fixture-only or
emulated results cannot become stable support evidence.

## Pass criteria

- All required steps and failure cases pass.
- Git is observed only in the Hermes adapter install/update phase.
- No Docker, frontend tool, source import, or manager-owned state is used by
  Wright runtime lifecycle.
- No secret appears in logs or evidence.
- Runtime dependencies exist only in Wright-owned environments.
- User data retention/deletion counts are exact.
- Adapter and runtime artifact identities match the release subjects.
