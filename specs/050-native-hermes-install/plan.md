# Implementation Plan: Native Hermes Installation

**Branch**: `050-native-hermes-install` | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/050-native-hermes-install/spec.md`

## Summary

Turn the existing `wright-engineering` helper distribution into Wright's one
public application distribution. The wheel will contain the thin Hermes
entry-point plugin, the complete Python runtime, the canonical MCP catalog, and
the prebuilt web UI. Its base installation remains safe to load inside Hermes;
the plugin installs the same version with a `runtime` extra into a versioned,
isolated environment beneath `HERMES_HOME`, atomically activates it, and starts
the packaged API/UI without a repository or frontend build. A durable lifecycle
manifest, lock, process identity, health challenge, database backup, and retained
predecessor provide idempotent start/stop, update, rollback, uninstall, and
explicit purge behavior.

Wright will require a Hermes release whose supported plugin lifecycle can
install, update, and remove Python entry-point plugins without Git. Current
Hermes 0.19.0 discovers entry-point plugins but its installer only clones Git
repositories. Wright MUST fail its stable release gate until the required Hermes
capability is available and passes the published-artifact acceptance suite; the
legacy Git mirror is migration-only and cannot satisfy native acceptance.

## Technical Context

**Language/Version**: Python 3.11-3.14 for plugin, lifecycle, API, packages, and tests; TypeScript 5 and React 19 only in the release build that produces bundled static UI assets

**Primary Dependencies**: Python standard library for the thin Hermes plugin and lifecycle bootstrap; `packaging` for version/specifier checks; FastAPI, Uvicorn, Pydantic, official `mcp>=1.27.2,<2`, httpx/httpx-sse, structlog, OpenTelemetry, PyYAML, and jsonschema in the isolated runtime extra; existing Wright package modules are bundled in the one public distribution and are not resolved as private index dependencies

**Storage**: Atomic JSON lifecycle manifest and operation lock under the Wright directory inside `HERMES_HOME`; versioned isolated runtime directories; existing SQLite user state and migration ledger in a version-independent data directory; existing filesystem workspaces remain external user data

**Testing**: pytest unit/contract/integration tests; subprocess and clean-venv package tests; candidate wheel install through a Hermes package-plugin fixture matching the accepted upstream contract; real released-Hermes public-artifact verification; Vitest and Playwright; existing provider-neutral MCP suites; release policy tests; `scripts/check-dev-merge.sh` and `scripts/check-prod-merge.sh`

**Target Platform**: Native Windows 11 x64, Ubuntu 22.04/24.04 x64, and macOS Sonoma 14+ combinations that remain jointly claimed by Wright and Hermes; production support is emitted from an evidence-backed matrix rather than inferred. Docker remains Linux amd64 until existing OCI evidence expands it.

**Project Type**: Modular Python application distribution with a thin Hermes plugin, isolated managed web-service runtime, embedded SQLite state, prebuilt React UI, provider-neutral MCP gateway, and parallel Docker appliance release

**Performance Goals**: After the runtime is installed, 95% of first starts reach verified health within 120 seconds on reference hosts; status returns within 5 seconds and doctor within 20 seconds when dependency endpoints respect their bounded probes; lifecycle lock acquisition fails with actionable busy status rather than hanging indefinitely

**Constraints**: No Git, Docker, Node/npm, source checkout, `WRIGHT_REPO_DIR`, or frontend build in native install/start; no runtime dependencies imported into the Hermes process; no shell evaluation; no secret logging; atomic activation; only Wright-owned paths are removable; public feature-branch tests cannot publish; current Hermes Git-only plugin installation is insufficient and must not be treated as passing evidence

**Scale/Scope**: One public Python distribution, one active runtime plus at least one retained rollback predecessor per Hermes profile, multiple concurrent Hermes sessions, existing multi-workspace state, the complete current MCP catalog, three native OS families where jointly supported, and the existing mandatory Docker release

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design against Constitution v2.0.0.*

- **Modular FastAPI boundaries**: Pass. Runtime lifecycle stays in
  `wright_engineering.runtime`; API routes remain transport-only and existing
  package boundaries are bundled, not collapsed.
- **Offline-first**: Pass. Artifact acquisition may use the configured package
  source, but installed core operation, state, catalog, UI, and workspaces remain
  local. Offline cache/index guidance is part of the contract.
- **Production distributions**: Pass. Native Hermes and Docker are both
  mandatory release subjects with terminal verification.
- **Docker thick base**: Pass. This feature does not add host MCP applications
  or change the existing Docker base strategy.
- **Native runtime isolation**: Pass. Hermes imports only the thin bootstrap;
  the application runs from a separate versioned environment and process.
- **Agent abstraction and provider neutrality**: Pass. Hermes owns lifecycle but
  remains one agent adapter; no MCP provider identity enters runtime policy.
- **Embedded state and file vault**: Pass. Lifecycle metadata is atomic local
  state and user application state remains SQLite/filesystem based.
- **Security and identity**: Pass. Runtime paths are contained, process identity
  is challenged before signals, secrets are redacted, and purge is explicit.
- **Engineering protocol**: Pass. The native runtime invokes no GUI-dependent
  tool and does not bundle optional MCP host software.
- **Testing pyramid**: Pass. Unit, integration, UI, system, clean-install,
  lifecycle, platform, and published-artifact release tests are required.
- **Observability**: Pass. Lifecycle events use structured redacted records and
  propagate an operation/correlation identifier into runtime startup.
- **Phase and branch discipline**: Pass. Spec Kit created and validated the
  numbered branch once; the operator pre-authorized continuous phases but not a
  merge into `dev` or `main`.

## Project Structure

### Documentation (this feature)

```text
specs/050-native-hermes-install/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- clean-install-contract.md
|   |-- hermes-package-plugin-contract.md
|   |-- lifecycle-command-contract.md
|   |-- native-release-contract.md
|   `-- runtime-artifact-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/wright_engineering/
|-- cli.py                              # public CLI and runtime management entry
|-- hermes_plugin/
|   |-- __init__.py                     # Hermes entry-point register(ctx)
|   |-- commands.py                     # /wright command projection only
|   `-- compatibility.py                # Hermes/plugin/runtime compatibility
|-- runtime/
|   |-- layout.py                       # contained HERMES_HOME data/runtime paths
|   |-- models.py                       # manifest and lifecycle state models
|   |-- state.py                        # atomic manifest and cross-process lock
|   |-- artifacts.py                    # exact-version candidate/install policy
|   |-- installer.py                    # isolated environment acquisition
|   |-- process.py                      # process identity, launch, stop, probes
|   |-- lifecycle.py                    # install/start/update/rollback/remove
|   |-- diagnostics.py                  # status and doctor result model
|   |-- logging.py                      # structured redacted lifecycle events
|   |-- migrations.py                   # native activation/schema preflight
|   |-- server.py                       # packaged API/UI bootstrap
|   `-- purge.py                        # explicit contained data deletion
`-- static/                             # release-built React UI package data

apps/api/src/api/
|-- config.py                           # explicit packaged data-path resolution
`-- main.py                             # importlib-resource static UI fallback

hermes-plugin-wright/                   # one-release legacy Git mirror wrapper
|-- plugin.yaml                         # migration/deprecation compatibility
|-- commands.py                         # delegates to public distribution
`-- README.md                           # directs users to native package channel

scripts/
|-- build-native-runtime.py             # build UI, assemble and inspect wheel
|-- test-native-hermes-install.py       # clean third-party lifecycle harness
|-- check-dev-merge.sh                  # mandatory candidate native checks
|-- check-prod-merge.sh                 # mandatory full lifecycle checks
`-- release/                            # artifact/evidence/workflow policies

tests/native_runtime/
|-- test_layout.py
|-- test_state.py
|-- test_artifacts.py
|-- test_installer.py
|-- test_process.py
|-- test_lifecycle.py
|-- test_commands.py
|-- test_clean_install.py
|-- test_upgrade_rollback.py
|-- test_uninstall_purge.py
`-- test_package_contents.py

.github/workflows/
|-- native-hermes-pr.yml                # candidate artifact platform matrix
|-- python-quality.yml                  # application-wheel contract
|-- release.yml                         # mandatory native publication/verify
`-- sync-hermes-plugin-mirror.yml       # legacy migration channel only
```

**Structure Decision**: Keep one public distribution (`wright-engineering`) to
preserve the single release identity and avoid publishing private monorepo
packages. The wheel contains those package modules and static resources, while
their standalone project metadata remains private. The base distribution has a
stdlib-safe Hermes entry point; the `runtime` extra declares the full application
dependencies and is installed into an isolated version directory. The current
`hermes-plugin-wright` tree becomes a bounded compatibility mirror and is not a
second public package or a passing native-install subject.

## Implementation Sequence

1. Add failing artifact, compatibility, layout, state-machine, process-identity,
   command, and no-forbidden-tool contracts before lifecycle implementation.
2. Convert root packaging into the one complete application wheel, include all
   private module code and canonical resources, add the runtime dependency extra,
   and build/embed the UI only in candidate build jobs.
3. Add contained cross-platform layout resolution, atomic manifest persistence,
   operation locking, runtime inventory, and compatibility models.
4. Add isolated exact-version runtime installation from local candidates or a
   configured index, with hashes/versions recorded before activation.
5. Add packaged API/UI bootstrap and ensure database, secret, log, catalog, and
   workspace paths are independent from the versioned runtime directory.
6. Replace repository/build behavior in the Hermes command layer with thin
   lifecycle calls for start, status, doctor, stop, update, rollback, uninstall,
   purge, open, and existing catalog commands.
7. Add process ownership and health challenge, idempotent concurrent transitions,
   migration backup, failed-activation recovery, rollback, uninstall, and
   scope-checked purge.
8. Add candidate clean-install and previous-stable upgrade tests on the supported
   platform matrix with PATH/filesystem guards proving no forbidden dependency is
   invoked or discovered.
9. Add package-role, compatibility, operator, recovery, and user documentation;
   retain a one-release legacy mirror migration path without calling it native.
10. Make candidate native tests mandatory in pull requests and add build-once,
    publish, published-artifact lifecycle verification, evidence, and terminal
    dependencies to the unified release train without weakening Docker.
11. Update both merge gates and contributor guidance so any CI-only native failure
    becomes a local contract in the same change.

## Migration and Rollback

- **Existing helper package**: The `wright` CLI remains, but its metadata and
  default guidance change from helper-only to managed application distribution.
  Existing dependency-safe diagnostics stay available from the base install.
- **Existing Git plugin users**: The mirror delegates to the installed public
  distribution when available and provides a bounded migration diagnostic. It is
  not accepted as the clean no-Git production path and is removed only after a
  documented deprecation window.
- **Repository installations**: Development commands continue to use the monorepo;
  native runtime commands never auto-detect or import it.
- **Application data**: On first native start, explicitly configured legacy
  `DATABASE_PATH`, workspace roots, and secret locations are adopted without
  moving external workspaces. Default legacy state may be copied once only after
  a backup and recorded migration decision.
- **Database**: Existing additive migration ledger and backups run before a new
  runtime becomes healthy. Runtime rollback does not silently downgrade a newer
  schema; compatibility metadata declares whether the previous runtime can reopen
  it. When it cannot, activation fails before irreversible migration or requires
  the documented backup-restore recovery path.
- **Runtime rollback**: Activation retains the previous exact runtime and manifest.
  A failed candidate health challenge atomically restores the predecessor.
- **Plugin rollback**: Compatibility is checked before runtime activation. Hermes'
  package-plugin lifecycle must support exact prior plugin restoration or the
  stable release gate fails.
- **Uninstall**: Normal uninstall removes managed runtime versions and process
  state but preserves data/config/workspaces. Explicit purge resolves every
  candidate path beneath Wright-owned roots before deletion and refuses ambiguous
  or external targets.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md),
[contracts/hermes-package-plugin-contract.md](contracts/hermes-package-plugin-contract.md),
[contracts/runtime-artifact-contract.md](contracts/runtime-artifact-contract.md),
[contracts/lifecycle-command-contract.md](contracts/lifecycle-command-contract.md),
[contracts/clean-install-contract.md](contracts/clean-install-contract.md),
[contracts/native-release-contract.md](contracts/native-release-contract.md), and
[quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All Constitution v2.0.0 gates remain passing. The design makes both production
distributions mandatory, uses an isolated native process, keeps internal module
boundaries, uses embedded state, preserves provider neutrality, adds structured
lifecycle evidence, and leaves MCP-specific host software outside both base
installations.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|------------|------------|-------------------------------------|
| Same public wheel installed as a thin base plugin and as an isolated `runtime` extra | Keeps one release identity and one public package while preventing application dependencies from entering Hermes | A second public plugin package duplicates version/promotion policy; installing all runtime dependencies into Hermes violates isolation |
| Versioned runtime directories plus durable active/predecessor manifest | Enables atomic activation, exact rollback, concurrent session safety, and honest recovery | An in-place environment upgrade cannot reliably roll back or distinguish partial installation |
| Required Hermes package-plugin capability | The current Git-only installer cannot meet the literal no-Git install and uninstall contract | Documenting hidden Git, a curl bootstrap, or manual package commands would preserve the wrong product experience |
