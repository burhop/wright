# Clean Install and Lifecycle Acceptance Contract

## Environment baseline

Each native platform case starts in a disposable user/profile boundary with:

- no Git executable or common Git installation path;
- no Docker socket/client;
- no Node.js, npm, npx, pnpm, or frontend build tools;
- no Wright source checkout, repository parent, editable install, or source-tree
  `PYTHONPATH`;
- no `WRIGHT_REPO_DIR`;
- no installed Wright distribution, plugin, data, runtime, or process;
- a supported released Hermes installation or the candidate package-plugin
  fixture for pull-request tests.

The harness records every child process executable and fails if Wright install or
runtime lifecycle invokes a forbidden executable. Merely hiding commands from
PATH is insufficient; common absolute locations and source-import leakage are
also checked.

## Candidate artifact setup

- Build the exact wheel once with prebuilt UI.
- Serve it from a temporary local wheelhouse/simple index or pass it as an exact
  local artifact through the Hermes package-plugin interface.
- Disable production publication credentials and assert no stable registry,
  release, documentation, or Hermes channel mutation occurs.
- Record filename, version, hash, and content-manifest hash.

## Required sequence

1. Install Hermes or activate the supported clean Hermes fixture.
2. Install and enable the candidate through Hermes' third-party package-plugin
   interface.
3. Assert base plugin import works and runtime dependencies are not in the Hermes
   environment.
4. Run `/wright start`; assert the exact runtime extra was installed into a
   contained isolated environment automatically.
5. Verify challenged API identity, UI/index/assets, Hermes connection, MCP
   transport initialization, and canonical catalog.
6. Create a workspace and second Hermes session, issue concurrent status/start,
   persist representative configuration/catalog choices, stop, restart, and
   reopen the workspace.
7. Install the previous stable public version in a separate clean profile, create
   representative data, then update to the candidate through Hermes and verify all
   retained state.
8. Inject pre-activation and post-activation failure; verify predecessor recovery
   or honest `recovery_required`.
9. Exercise successful rollback when the schema contract permits it and refused
   rollback when it does not.
10. Uninstall through Hermes; verify plugin/runtime/process removal and default
    data preservation.
11. Reinstall and reopen preserved data.
12. Explicitly purge; verify all and only Wright-owned data targets are removed.

## Failure scenarios

The automated suite covers interrupted download/install, hash mismatch,
incompatible Hermes/plugin/runtime, lock contention, concurrent starts, stale
manifest, reused PID, occupied port, failed health challenge, failed migration,
missing rollback artifact, permission failure, symlinked purge target, and network
unavailability with/without a valid cache.

## Platform matrix

The matrix is generated from the compatibility contract and public support
documentation. Each claimed platform must run the complete sequence natively.
Skipped, emulated-only, or fixture-only results cannot become stable support
evidence. The current intended matrix is Windows 11 x64, Ubuntu 22.04/24.04 x64,
and macOS Sonoma 14+ where both Wright and the selected Hermes release claim
support; exact runner architecture is recorded.

## Pass criteria

- All required steps and failure cases pass.
- No forbidden executable or source import is observed.
- No secret appears in logs or evidence.
- No required case uses an acceptance skip flag.
- Runtime dependencies exist only in the Wright environment.
- User data retention/deletion counts are exact.
- Candidate and installed artifact identities match.

