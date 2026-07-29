# Implementation Plan: Native Agent-Manager Installation

**Branch**: `050-native-hermes-install` | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/050-native-hermes-install/spec.md`

## Summary

Turn `wright-engineering` into Wright's one public application distribution and
make its lifecycle/MCP boundary independent of the invoking agent manager. The
wheel contains the complete Python runtime, canonical MCP catalog, and prebuilt
web UI. A standard-library-only Hermes adapter is installed through Hermes
0.19's real Git plugin interface, bootstraps the exact Wright artifact into a
Wright-owned environment, and delegates every command to the public lifecycle.
Codex consumes the same installed runtime through its supported MCP
configuration surface rather than routing through Hermes. OpenClaw remains a
future adapter and is not part of this delivery or its release gate. A
durable lifecycle manifest, lock, process identity, health challenge, database
backup, and retained predecessor provide idempotent start/stop, update,
rollback, uninstall, and explicit purge behavior beneath `WRIGHT_HOME`.

## Technical Context

**Language/Version**: Python 3.11-3.14 for plugin, lifecycle, API, packages, and tests; TypeScript 5 and React 19 only in the release build that produces bundled static UI assets

**Primary Dependencies**: Python standard library for the thin Hermes plugin and lifecycle bootstrap; `packaging` for version/specifier checks; FastAPI, Uvicorn, Pydantic, official `mcp>=1.27.2,<2`, httpx/httpx-sse, structlog, OpenTelemetry, PyYAML, and jsonschema in the isolated runtime extra; existing Wright package modules are bundled in the one public distribution and are not resolved as private index dependencies

**Storage**: Atomic JSON lifecycle manifest and operation lock beneath manager-neutral `WRIGHT_HOME`; versioned isolated runtime directories; existing SQLite user state and migration ledger in a version-independent data directory; existing filesystem workspaces and manager configuration remain external user data

**Testing**: pytest unit/contract/integration tests; subprocess and clean-venv package tests; real Hermes 0.19 Git-plugin install with a local immutable candidate adapter; post-install PATH audit; Codex profile contract and direct MCP probe; published Hermes tag and Wright artifact verification; Vitest and Playwright; existing provider-neutral MCP suites; release policy tests; `scripts/check-dev-merge.sh` and `scripts/check-prod-merge.sh`

**Target Platform**: Native Windows 11 x64, Ubuntu 22.04/24.04 x64, and macOS Sonoma 14+ combinations that are claimed by Wright and the manager adapter under test; production support is emitted from an evidence-backed per-adapter matrix rather than inferred. Docker remains Linux amd64 until existing OCI evidence expands it.

**Project Type**: Modular Python application distribution with thin external manager adapters, isolated managed web-service runtime, embedded SQLite state, prebuilt React UI, provider-neutral MCP gateway, and parallel Docker appliance release

**Performance Goals**: After the runtime is installed, 95% of first starts reach verified health within 120 seconds on reference hosts; status returns within 5 seconds and doctor within 20 seconds when dependency endpoints respect their bounded probes; lifecycle lock acquisition fails with actionable busy status rather than hanging indefinitely

**Constraints**: Manager-specific installation prerequisites are allowed only in that adapter phase (Git for Hermes; documented package/plugin prerequisites for other managers). Wright bootstrap/start uses no Git, Docker, Node/npm, source checkout, `WRIGHT_REPO_DIR`, or frontend build; no runtime dependencies enter a manager process; no shell evaluation; no secret logging; atomic activation; only Wright-owned paths are removable; public feature-branch tests cannot publish

**Scale/Scope**: One public Python distribution, one active runtime plus at least one retained rollback predecessor per Wright home, concurrent sessions from multiple manager adapters, existing multi-workspace state, the complete current MCP catalog, three native OS families where supported, and the existing mandatory Docker release

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design against Constitution v3.0.0.*

- **Modular FastAPI boundaries**: Pass. Runtime lifecycle stays in
  `wright_engineering.runtime`; API routes remain transport-only and existing
  package boundaries are bundled, not collapsed.
- **Offline-first**: Pass. Artifact acquisition may use the configured package
  source, but installed core operation, state, catalog, UI, and workspaces remain
  local. Offline cache/index guidance is part of the contract.
- **Production distributions**: Pass. The shared native Wright runtime, every
  publicly claimed manager adapter, and Docker are mandatory release subjects
  with terminal verification.
- **Docker thick base**: Pass. This feature does not add host MCP applications
  or change the existing Docker base strategy.
- **Native runtime isolation**: Pass. Hermes imports only its standard-library
  bootstrap; Codex connects through MCP; the application runs from a
  separate versioned Wright-owned environment and process.
- **Agent abstraction and provider neutrality**: Pass. Wright owns lifecycle;
  Hermes and Codex are thin external adapters and no manager identity
  enters runtime or MCP policy.
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
|   |-- manager-adapter-contract.md
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
|-- manager_profiles.py                 # manager adapter/profile contracts
|-- runtime/
|   |-- layout.py                       # contained WRIGHT_HOME data/runtime paths
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

hermes-plugin-wright/                   # production Hermes Git adapter
|-- plugin.yaml                         # released Hermes compatibility and commands
|-- bootstrap.py                        # stdlib-only exact artifact bootstrap
|-- commands.py                         # subprocess projection to public lifecycle
`-- README.md                           # real Hermes install/update/remove flow

integrations/
`-- codex/                              # Codex MCP profile and usage example

scripts/
|-- build-native-runtime.py             # build UI, assemble and inspect wheel
|-- test-native-hermes-install.py       # real Git adapter + lifecycle harness
|-- check-dev-merge.sh                  # mandatory candidate native checks
|-- check-prod-merge.sh                 # mandatory full lifecycle checks
`-- release/                            # artifact/evidence/workflow policies

tests/native_runtime/
|-- test_layout.py
|-- test_state.py
|-- test_artifacts.py
|-- test_process.py
|-- test_lifecycle_start.py
|-- test_lifecycle_stop.py
|-- test_commands_operate.py
|-- test_commands_update.py
|-- test_commands_remove.py
|-- test_clean_install.py
|-- test_update.py
|-- test_rollback.py
|-- test_uninstall.py
|-- test_purge.py
|-- test_manager_profiles.py
|-- test_codex_manager_profile.py
`-- test_package_contents.py

.github/workflows/
|-- native-hermes-pr.yml                # candidate artifact platform matrix
|-- python-quality.yml                  # application-wheel contract
|-- release.yml                         # mandatory native publication/verify
`-- sync-hermes-plugin-mirror.yml       # immutable Hermes Git adapter release
```

**Structure Decision**: Keep one public Wright application distribution
(`wright-engineering`) and separate thin manager adapters that contain no Wright
business logic. The wheel contains application modules and static resources;
the `runtime` extra declares the full environment. `hermes-plugin-wright` is the
production Git-installed bootstrap. The Codex profile projects the same
STDIO/HTTP MCP service and public lifecycle without duplicating it. OpenClaw is
deferred.

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
6. Replace repository/build behavior in the Hermes Git adapter with a
   standard-library bootstrap and subprocess calls to the public lifecycle;
   add a manager-neutral profile for Codex MCP consumption.
7. Add process ownership and health challenge, idempotent concurrent transitions,
   migration backup, failed-activation recovery, rollback, uninstall, and
   scope-checked purge.
8. Add real Hermes Git install plus candidate lifecycle tests and
   previous-stable/first-release predecessor tests on the supported platform
   matrix. Permit Git only during Hermes adapter install/update, then remove it
   from the audited runtime PATH. Add a Codex MCP profile probe.
9. Add package-role, compatibility, operator, recovery, and user documentation
   with separate prerequisite and installation instructions for each manager.
10. Make candidate native tests mandatory in pull requests and add build-once,
    publish, published-artifact lifecycle verification, evidence, and terminal
    dependencies to the unified release train without weakening Docker.
11. Update both merge gates and contributor guidance so any CI-only native failure
    becomes a local contract in the same change.

## Migration and Rollback

- **Existing helper package**: The `wright` CLI remains, but its metadata and
  default guidance change from helper-only to managed application distribution.
  Existing dependency-safe diagnostics stay available from the base install.
- **Existing Git plugin users**: The official Git adapter upgrades in place
  through `hermes plugins update wright`. Its bootstrap state is independent of
  the plugin checkout, and runtime update/rollback remains a Wright lifecycle
  operation.
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
- **Adapter rollback**: Hermes adapter provenance records a tag/commit and may be
  restored using the documented Git ref. Wright runtime rollback is independent
  and uses its retained immutable predecessor. Codex configuration rollback is
  manager-owned.
- **Uninstall**: Normal uninstall removes managed runtime versions and process
  state but preserves data/config/workspaces. Explicit purge resolves every
  candidate path beneath Wright-owned roots before deletion and refuses ambiguous
  or external targets.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md),
[contracts/hermes-package-plugin-contract.md](contracts/hermes-package-plugin-contract.md),
[contracts/manager-adapter-contract.md](contracts/manager-adapter-contract.md),
[contracts/runtime-artifact-contract.md](contracts/runtime-artifact-contract.md),
[contracts/lifecycle-command-contract.md](contracts/lifecycle-command-contract.md),
[contracts/clean-install-contract.md](contracts/clean-install-contract.md),
[contracts/native-release-contract.md](contracts/native-release-contract.md), and
[quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All Constitution v3.0.0 gates remain passing. The design makes the shared native
runtime, claimed manager adapters, and Docker mandatory; uses an isolated native
process; keeps internal module boundaries; preserves provider neutrality; adds
structured lifecycle evidence; and leaves MCP-specific host software outside
base installations.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|------------|------------|-------------------------------------|
| Stdlib-only manager adapter plus one public Wright runtime wheel | Uses each manager's real installer without importing application dependencies into the manager process | Installing the wheel into Hermes or copying lifecycle code into each adapter violates isolation and portability |
| Versioned runtime directories plus durable active/predecessor manifest | Enables atomic activation, exact rollback, concurrent session safety, and honest recovery | An in-place environment upgrade cannot reliably roll back or distinguish partial installation |
| Manager-specific adapter packages/profiles | Hermes and Codex deliberately have different installers and configuration formats; OpenClaw is future work | Requiring one invented cross-manager installer would couple Wright to capabilities the third-party products do not provide |
