# Research: Native Agent-Manager Installation

## Decision 1: Use `wright-engineering` as the one public application distribution

**Decision**: Repurpose `wright-engineering` from a helper-only wheel into the
complete Wright application distribution. It contains all Wright Python
modules, the canonical MCP catalog, manager-profile contracts, and release-built
UI. A `runtime` extra declares the full isolated application environment. Thin
manager adapters are separate integration artifacts and do not create a second
Wright runtime distribution.

**Rationale**: Wright's release train already treats the root product version and
`wright-engineering` hashes as the Python release identity. One distribution
avoids publishing private monorepo packages, prevents package-role ambiguity, and
lets the plugin install the exact same version into an isolated runtime.

**Alternatives considered**:

- Publish a second application runtime under `hermes-plugin-wright`: rejected
  because it creates two runtime identities, compatibility, and promotion
  surfaces. The Git plugin remains a thin adapter with its own immutable adapter
  identity, not an application distribution.
- Publish every internal package: rejected because those packages are private
  implementation boundaries and would greatly expand public compatibility.
- Keep the helper package and download a repository archive: rejected because it
  retains the ambiguous package role and risks repository-layout dependencies.

## Decision 2: Use each manager's real installation interface

**Decision**: Hermes installs the thin Wright adapter through its supported Git
plugin command. The adapter is standard-library-only and bootstraps the exact
`wright-engineering` application artifact into Wright-owned storage; it never
imports application dependencies into Hermes. Codex uses its own MCP
configuration surface and connects directly to the same Wright MCP service
rather than routing through Hermes. OpenClaw is deferred to future work.

**Rationale**: Hermes 0.19.0 explicitly installs plugins from Git. Git is a
Hermes prerequisite and is therefore valid during the adapter-install/update
phase. Codex can bundle MCP configuration. Making Wright core emulate manager
installers would couple independent products. OpenClaw research is retained as
future design input only, not as a current support claim.

**Primary evidence**:

- [Hermes CLI commands](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/cli-commands.md)
- [Hermes plugin discovery](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md)
- Released Hermes 0.19.0 `plugins_cmd.py`: `_install_plugin_core` clones Git and
  `plugins update` performs `git pull`.
- [Codex MCP configuration](https://developers.openai.com/codex/mcp/) and plugin
  packaging document bundled MCP server configuration.
- [OpenClaw plugin CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/plugins.md)
  and [MCP CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/mcp.md)
  document npm/ClawHub/Git plugin sources and STDIO/HTTP MCP profiles.

**Alternatives considered**:

- Require new Hermes package commands: rejected because Hermes is a third-party
  product and Wright must use its released interface.
- Copy Hermes behavior into Codex/OpenClaw adapters: rejected because their
  documented installation and MCP surfaces differ.
- Bundle Wright into Hermes core: rejected because Wright should remain a plugin
  and would couple independent release schedules.

## Decision 3: Isolate the application runtime by version

**Decision**: The Hermes-loaded Git adapter uses only the standard library. It
downloads and installs an exact `wright-engineering` bootstrap into a contained
Wright environment, then invokes the public Wright lifecycle. Wright installs
`wright-engineering[runtime]==<exact version>` into
`WRIGHT_HOME/runtimes/<version>-<python>-<platform>`. Codex invokes the same
lifecycle/MCP entry points without importing runtime dependencies into its
process.

**Rationale**: Hermes and Wright have large, independently evolving dependency
graphs. Separate environments prevent resolver collisions, allow exact rollback,
and keep runtime failure outside the Hermes process.

**Alternatives considered**:

- Install runtime dependencies in the Hermes environment: rejected for isolation,
  collision, rollback, and uninstall risks.
- Use Docker behind `/wright start`: rejected because native Hermes explicitly
  cannot require Docker.
- Ship a platform-specific frozen executable immediately: rejected for the first
  iteration because Wright is currently a pure-Python application with a
  supported Python matrix, while freezing would multiply signing and native build
  surfaces. It remains a future optimization if wheel startup evidence is poor.

## Decision 4: Build the frontend once and package it as immutable data

**Decision**: Candidate build jobs run the existing locked frontend build, copy
only inspected `apps/web/dist` output into `wright_engineering/static`, and record
its content manifest in Python artifact evidence. Runtime resolves static files
with package resources before importing the API.

**Rationale**: Users receive the same tested UI without Node/npm or source files.
Build-once evidence binds UI bytes to the application wheel.

**Alternatives considered**:

- Build on first start: explicitly forbidden and unreliable.
- Download UI separately at runtime: rejected because it creates a second mutable
  compatibility subject and weakens offline operation.
- Serve a development UI: rejected because it requires Node and source layout.

## Decision 5: Separate versioned runtime, lifecycle state, and user data

**Decision**: Under the resolved `WRIGHT_HOME`, Wright owns `runtimes`, `state`,
`logs`, `cache`, and `data`. Runtime versions are disposable. The lifecycle
manifest and locks live in `state`; SQLite, secrets, configuration, and default
workspaces live in `data`; external workspaces and all manager-owned state remain
outside purge scope.

**Rationale**: Update and uninstall must never couple executable removal to user
data. A single contained root also makes deletion policy testable.

**Alternatives considered**:

- Store data inside each runtime: rejected because update/uninstall would risk
  data loss.
- Store data below `HERMES_HOME`, Codex state, or OpenClaw state: rejected because
  it prevents one runtime from serving several managers and makes manager removal
  a data-deletion risk.

## Decision 6: Use an atomic manifest plus an inter-process lifecycle lock

**Decision**: A schema-versioned manifest records installed runtimes, active and
predecessor identities, compatibility, process metadata, operation status, data
schema bounds, and last recovery result. Writes use create/write/fsync/replace in
the same directory. A bounded cross-platform file lock serializes mutations;
read-only status uses a consistent snapshot.

**Rationale**: Multiple Hermes sessions can issue lifecycle commands. Durable
intent and terminal state are needed to recover from process or host interruption.

**Alternatives considered**:

- PID file only: rejected because PIDs are reused and convey no installation or
  transition state.
- SQLite for lifecycle state: rejected because runtime/environment recovery must
  work even when the application database is incompatible or unavailable.

## Decision 7: Challenge process identity before reuse or termination

**Decision**: Start generates an unlogged random instance token, passes it to the
runtime through a protected environment value, and expects a hash/nonce-bound
identity in the local health response. Manifest process metadata also records PID,
start time, executable path, runtime version, port, and operation ID. Stop signals
only a process that matches both OS metadata and the health challenge.

**Rationale**: Port checks and PID files alone can mistake unrelated services for
Wright or terminate a reused PID.

**Alternatives considered**:

- Trust `/api/health` text only: rejected because another Wright version or
  unrelated compatible endpoint could answer.
- Kill any process on port 8000: rejected as unsafe.

## Decision 8: Back up before migration and gate runtime rollback on data compatibility

**Decision**: Candidate activation inspects its supported schema bounds, backs up
existing SQLite state with the existing data-vault lifecycle, runs additive
migrations, and verifies integrity before health. The predecessor is retained,
but automatic runtime rollback occurs only if it supports the resulting schema;
otherwise recovery uses the recorded backup with explicit diagnostics.

**Rationale**: Rolling executable files back is unsafe if a newer schema cannot be
opened by the predecessor. Wright already has checksummed migrations and backup
support that should be reused.

**Alternatives considered**:

- Always restore the database during rollback: rejected because it could discard
  legitimate user work created after upgrade.
- Always run the old runtime against new data: rejected because it can corrupt or
  misinterpret state.

## Decision 9: Normal uninstall preserves data; purge is a separate contained operation

**Decision**: Wright's explicit uninstall command stops Wright and removes
versioned runtime, cache, and process/lifecycle artifacts while preserving
`WRIGHT_HOME/data` and external workspaces. Removing a manager adapter removes
only that adapter. Purge is explicit, reports resolved paths, rejects symlinks
and roots outside Wright ownership, and never follows external workspace or
manager-owned paths.

**Rationale**: Safe default removal and deliberate data destruction match the
product requirement and make reinstall recovery possible.

**Alternatives considered**:

- Delete all Wright paths on plugin removal: rejected as unexpected data loss.
- Preserve runtime environments by default: rejected because uninstall would not
  actually remove the product and stale vulnerable code could remain.

## Decision 10: Validate candidates without production publication

**Decision**: Pull requests build a wheel with the UI and install the real Hermes
Git adapter from an immutable local Git subject. The adapter bootstraps the exact
candidate from a local wheelhouse, after which Git is removed from PATH and the
complete Wright lifecycle runs. Codex contract tests load its native MCP profile
shape against the same packaged bridge. Production verification
uses the published Hermes Git tag and published runtime artifact.

**Rationale**: PR tests must exercise real packaging while remaining incapable of
publishing stable artifacts. Release tests must not fall back to repository code.

**Alternatives considered**:

- Mock the installer entirely: rejected because package contents, resolver
  behavior, entry-point discovery, and static resources would be unverified.
- Publish prereleases from every PR: rejected for supply-chain and channel safety.

## Decision 11: Make native evidence terminal in the unified release train

**Decision**: The unified workflow builds the application candidate once, tests
the real Hermes Git adapter plus the runtime extra and manager-neutral MCP
profiles, publishes the exact files through existing protected Python stages,
tags the immutable Hermes adapter subject, and runs public adapter/install and
Wright lifecycle verification. The claimed Codex adapter becomes terminal
release subjects when their production packages are introduced. Final evidence
and GitHub Release jobs require every claimed native adapter plus Docker.

**Rationale**: Native Hermes is the majority path and Docker is a required
alternative; neither may be optional or merely warning-level.

**Alternatives considered**:

- Keep the mirror workflow independent: rejected because independent success can
  leave a release partially distributed.
- Treat native verification as post-release monitoring: rejected because the
  user explicitly defines it as release completion.

## Decision 12: Repair Spec Kit shell portability as part of tooling validation

**Decision**: Add repository attributes/tests that keep Bash scripts LF-normalized
and verify the Spec Kit scripts from supported developer hosts. The current CRLF
checkout caused `setup-plan.sh` to fail before execution, so this defect receives
an explicit task and regression test.

**Rationale**: Spec Kit and both merge gates are Bash-based and are authoritative;
Windows checkout conversion must not make them unexecutable.

**Alternatives considered**:

- Continue manually emulating scripts: rejected because it hides a recurring
  cross-platform contributor failure.

## Decision 13: Separate manager adapters from agent engines

**Decision**: Manager installation/profile adapters are distinct from Wright's
`BaseAgentEngine` chat adapters. Manager adapters install or connect to Wright
and project the public lifecycle/MCP contract. `BaseAgentEngine` remains the
runtime abstraction used when the Wright UI itself hosts an agent conversation.

**Rationale**: Codex can consume Wright's MCP service without Wright hosting its
chat runtime. The same separation preserves a future OpenClaw seam without
making OpenClaw part of this delivery. Conflating installation, MCP hosting, and
chat-engine selection would reproduce the Hermes coupling this clarification
removes.

**Alternatives considered**:

- Add manager-specific branches to `NativeLifecycle`: rejected because lifecycle
  state does not depend on the invoking manager.
- Treat every MCP client as a `BaseAgentEngine`: rejected because an external MCP
  host need not expose Wright's internal chat/session API.
