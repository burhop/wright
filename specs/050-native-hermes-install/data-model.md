# Data Model: Native Agent-Manager Installation

## 1. Installation Manifest

Durable source of truth for one Wright installation shared by manager adapters.
It is stored outside every versioned runtime and every manager-owned directory,
and is updated atomically.

### Fields

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | Positive; readers reject unsupported future versions |
| `installation_id` | UUID string | Generated once per Wright-owned home |
| `wright_home` | absolute path | Canonical Wright-owned root used to validate all managed paths |
| `data_root` | absolute path | Stable across upgrades and runtime rollback |
| `active_runtime_id` | string or null | Must reference a healthy installed runtime |
| `predecessor_runtime_id` | string or null | Must reference a retained compatible runtime |
| `desired_runtime_version` | normalized version or null | Set during install/update intent |
| `lifecycle_state` | enum | One of the states below |
| `current_operation` | Operation Record or null | Present only during/recovering a mutation |
| `process` | Process Identity or null | Present only when a verified instance may exist |
| `runtimes` | map of Runtime Installation | Keyed by immutable runtime ID |
| `last_result` | Lifecycle Result or null | Last terminal operation summary |
| `created_at`, `updated_at` | UTC timestamp | Monotonic update ordering |

### Lifecycle states

```text
not_installed
  -> installing -> stopped
  -> failed | recovery_required

stopped
  -> starting -> healthy | degraded | failed
  -> updating -> stopped | healthy | failed | recovery_required
  -> rolling_back -> stopped | healthy | failed | recovery_required
  -> uninstalling -> not_installed | recovery_required
  -> purging -> not_installed | recovery_required

healthy | degraded
  -> stopping -> stopped | recovery_required
  -> updating -> healthy | failed | recovery_required
  -> rolling_back -> healthy | failed | recovery_required
  -> uninstalling -> not_installed | recovery_required

failed | recovery_required
  -> installing | rolling_back | stopping | uninstalling | purging
```

Only a lock-owning lifecycle operation may enter a transitional state. Every
transition records intent before side effects and records one terminal result.

## 2. Runtime Installation

One exact `wright-engineering[runtime]` installation in an isolated environment.

| Field | Type | Rules |
| --- | --- | --- |
| `runtime_id` | string | Hash of distribution/version/Python/platform identity |
| `version` | normalized version | Exact, never a mutable range |
| `distribution` | string | Exactly `wright-engineering` |
| `artifact_filename` | string | Wheel or approved source artifact used |
| `artifact_sha256` | 64-char hex | Verified before installation |
| `source_channel` | enum | `local_candidate`, `test`, or `stable` |
| `environment_path` | absolute path | Must be a direct contained child of `runtimes` |
| `python_version` | string | Supported runtime interpreter version |
| `platform_tag` | string | Evidence-backed OS/architecture tag |
| `runtime_compatibility` | specifier string | Must admit the invoking adapter's requested runtime version |
| `adapter_protocol` | string | Public lifecycle/MCP protocol understood by the runtime |
| `data_schema_min`, `data_schema_max` | integer | Inclusive schema range the runtime can open |
| `installed_at`, `verified_at` | UTC timestamp | `verified_at` set only after artifact and import checks |
| `status` | enum | `staged`, `verified`, `active`, `predecessor`, `failed`, `removable` |
| `failure_code` | string or null | Stable redacted diagnostic code |

### Invariants

- At most one runtime is `active`.
- At most one runtime is `predecessor` for automatic rollback.
- `active_runtime_id` references a `verified` or `active` runtime only.
- Activation never changes artifact identity or environment contents.
- Failed/staged runtimes can be removed only while not referenced by a process.

## 3. Compatibility Contract

Versioned metadata shipped in the public distribution and exposed without
importing runtime dependencies.

| Field | Type | Rules |
| --- | --- | --- |
| `contract_version` | integer | Schema for compatibility metadata |
| `runtime_version` | normalized version | Must equal the public product version for this design |
| `runtime_specifier` | version specifier | Compatible runtime versions |
| `python_specifier` | version specifier | Matches package metadata |
| `platforms` | list | Each entry has executable clean-install evidence |
| `data_schema` | min/max integers | Range supported by the runtime |
| `manager_protocols` | map | Manager ID to supported thin-adapter protocol and optional host version range |

Compatibility is checked before install, before activation, and by doctor. A
missing or malformed contract fails closed.

## 4. Operation Record

Crash-recoverable intent for one mutating lifecycle request.

| Field | Type | Rules |
| --- | --- | --- |
| `operation_id` | UUID string | Correlation ID for logs and child process |
| `kind` | enum | `install`, `start`, `stop`, `update`, `rollback`, `uninstall`, `purge` |
| `requested_by` | string | Redacted manager/adapter/session identity |
| `started_at` | UTC timestamp | Written before first side effect |
| `from_state`, `target_state` | lifecycle state | Must be a valid transition |
| `candidate_runtime_id` | string or null | Used for install/update/rollback |
| `checkpoint` | stable enum/string | Last durable completed step |
| `backup_manifest` | path or null | Contained data-vault backup evidence |
| `recovery_action` | string or null | Deterministic resume/rollback instruction |

The manifest retains an interrupted operation so the next lifecycle command can
recover or report `recovery_required`; it never silently starts a new mutation.

## 5. Process Identity

Evidence that a PID and port belong to the active Wright runtime.

| Field | Type | Rules |
| --- | --- | --- |
| `pid` | positive integer | OS process ID |
| `started_at` | UTC timestamp | Compared with OS process creation time where available |
| `runtime_id` | string | Must equal active runtime |
| `executable_path` | absolute path | Must be contained by the runtime environment |
| `host`, `port` | string/integer | Host defaults to loopback; valid port range |
| `instance_id` | UUID string | Unique per start |
| `challenge_hash` | hash string | Hash of an unlogged random challenge, never the raw secret |
| `operation_id` | UUID string | Start correlation |
| `health_verified_at` | UTC timestamp or null | Set only after expected health response |

Signals are allowed only after PID metadata, executable containment, runtime ID,
and health challenge agree. A mismatch is `recovery_required`, not permission to
kill the process.

## 6. Lifecycle Result

Stable command response shared by slash commands, CLI, logs, and tests.

| Field | Type | Rules |
| --- | --- | --- |
| `operation_id` | UUID string | Correlates with Operation Record |
| `command` | string | User-facing command name |
| `ok` | boolean | True only for the requested terminal state |
| `state` | lifecycle state | Actual resulting state |
| `code` | stable string | Machine-testable result/error code |
| `summary` | string | Redacted concise result |
| `details` | map | Allowlisted non-secret diagnostic fields |
| `remediation` | list of strings | Ordered safe next actions |
| `started_at`, `finished_at` | UTC timestamp | Operation duration evidence |

## 7. Wright-Owned Data Scope

Resolved paths that lifecycle deletion is permitted to manage.

| Category | Default location | Normal uninstall | Explicit purge |
| --- | --- | --- | --- |
| Runtime environments | `<WRIGHT_HOME>/runtimes` | Delete | Delete |
| Runtime cache/wheelhouse | `<WRIGHT_HOME>/cache` | Delete | Delete |
| Process/log state | `<WRIGHT_HOME>/state`, `logs` | Delete after terminal record | Delete |
| SQLite/config/secrets | `<WRIGHT_HOME>/data` | Preserve | Delete after confirmation |
| Default managed workspaces | `<WRIGHT_HOME>/data/workspaces` | Preserve | Delete after confirmation |
| External workspaces | Any path outside owned root | Preserve | Never delete |
| Hermes and Codex configuration/data | Outside `WRIGHT_HOME` | Preserve | Never delete |

Every deletion target is resolved without following an untrusted symlink and
must remain beneath the expected Wright-owned root. Broad roots, home itself,
filesystem roots, and ambiguous paths are always rejected.

## 8. Native Release Evidence

Extension of the existing release evidence for one native subject.

| Field | Type | Rules |
| --- | --- | --- |
| `product_version`, `source_commit` | string | Match root release identity |
| `manager_adapters` | map of adapter evidence | Hermes Git identity and each other publicly claimed adapter artifact/profile |
| `runtime_artifact` | artifact evidence | Same distribution identity plus runtime-extra lock evidence |
| `compatibility_contract_hash` | hash | Exact installed contract |
| `manager_versions` | map | Released manager versions used for public verification |
| `platform_results` | list | One result per claimed native platform |
| `lifecycle_results` | map | install/start/update/rollback/uninstall/purge result IDs |
| `prerequisite_probe` | result | Proves manager prerequisites are used only by their adapter phase |
| `stable_channels` | map | Published manager adapter and runtime identities |
| `result` | enum | `passed` or `failed`; missing evidence is failure |

The final GitHub Release requires a passing Wright runtime subject, every
publicly claimed manager-adapter subject, and the existing passing
Docker/Python/documentation evidence.

## 9. Manager Adapter Profile

Description of one external manager's supported integration without importing
that manager into Wright lifecycle core.

| Field | Type | Rules |
| --- | --- | --- |
| `manager_id` | string | Stable identifier such as the currently supported `hermes` or `codex`; future adapters define additional identifiers when delivered |
| `adapter_protocol` | string | Versioned lifecycle/MCP projection contract |
| `install_source` | enum | `git`, `plugin`, `marketplace`, `npm`, `mcp-config`, or release archive |
| `prerequisites` | list | Documented manager-owned prerequisites only |
| `mcp_transport` | enum | `stdio` or `streamable-http` |
| `runtime_home` | path reference | Always resolves to `WRIGHT_HOME`, never manager state |
| `claimed_support` | boolean | True only with real host and packaged-runtime evidence |

Manager adapter removal never implies Wright data purge. Adapter-specific
configuration is outside Wright's deletion scope.
