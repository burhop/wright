# Data Model: Rivet Compatibility Spike

**Branch**: `055-rivet-compatibility-spike`

This model describes evidence records only. It does not create a Wright runtime schema or durable user data.

## Candidate Baseline

| Field | Meaning | Validation |
|---|---|---|
| `baseline_id` | Human-readable immutable candidate label | Unique in the spike report |
| `source_repository` | Upstream source location | HTTPS Git URL only |
| `source_revision` | Immutable commit hash | Full hash matches fetched source |
| `source_archive_digest` | Archived source integrity value | Recomputed in reproduction run |
| `package_resolutions` | Application/core/Node/executor versions and integrity values | Exact, no semver ranges |
| `lockfile_digest` | Source lockfile digest | Matches source revision |
| `node_version` | Runtime version used for build and fixture | Meets upstream and Wright matrix |
| `patch_set` | Ordered patch identities/digests | Applies cleanly to this revision only |
| `build_command` | Reproducible command declaration | Does not contain user path/token |
| `asset_manifest_digest` | Generated static asset inventory | Matches offline trial |
| `disposition` | candidate / selected / rejected | Required after probe |

## Compatibility Fixture

| Field | Meaning | Validation |
|---|---|---|
| `fixture_id` | Stable fixture label | No user/workspace identifiers |
| `project_digest` | Immutable graph/project content | Contains mock-only data |
| `dataset_digest` | Immutable sample dataset | Bounded and non-sensitive |
| `mock_workspace_id` | Synthetic isolation identity | Distinct in dual-instance test |
| `mock_host_operation` | External-call name and typed mock behavior | No live tool or credential |
| `expected_capabilities` | Required probe actions | Maps to spec requirement |
| `expected_prohibitions` | Actions that must fail or be absent | Maps to policy boundary |

## Probe Run

| Field | Meaning |
|---|---|
| `probe_id` | Opaque evidence run identity |
| `baseline_id`, `fixture_id` | Inputs |
| `environment` | OS, architecture, Node/package-manager/browser versions |
| `phase` | acquire / editor / runner / offline / supply-chain |
| `command_digest` | Normalized reproducible command identity |
| `started_at`, `finished_at` | Timing |
| `network_policy` | normal / denied / recorded |
| `result` | passed / failed / unsupported / blocked |
| `output_manifest_digest` | Referenced generated outputs |
| `trace_log_ref` | Redacted structured evidence file |

## Capability Finding

| Field | Meaning |
|---|---|
| `finding_id` | Stable row identity |
| `capability` | IO, dataset, native API, persistence, runner, cancellation, debugger, external call, build, offline, license, platform, etc. |
| `context` | browser / Hermes / native / Docker / offline |
| `disposition` | supported / adapter-required / prohibited / unresolved / blocked |
| `evidence_refs` | Probe IDs and digest links |
| `risk_level` | informational / low / medium / high / critical |
| `required_control` | Constraint owned by a later slice or N/A |
| `owner_slice` | persistence / runner / editor adapters / nodes / hardening / umbrella amendment |

## Supply-Chain Finding

| Field | Meaning |
|---|---|
| `component` | Direct or transitive source/package/asset |
| `version`, `integrity` | Exact identity |
| `license` | Detected and reviewed license |
| `security_status` | scan source/version/result/exception |
| `ship_decision` | allow / replace / exclude / block |
| `notice_requirement` | Required attribution/distribution material |
| `update_owner` | Named future maintenance owner |

## Go/No-Go Decision

| Field | Meaning |
|---|---|
| `decision_id` | Versioned decision record |
| `baseline_id` | Candidate evaluated |
| `outcome` | go / conditional-go / no-go |
| `mandatory_criteria` | Complete pass/fail list |
| `conditions` | Enforceable next-slice requirements, if any |
| `blocked_requirements` | Umbrella FR/SC references if no-go |
| `approver` | Human approval record |
| `next_action` | Start named slice / amend umbrella / stop |

## Relationships

```text
Candidate Baseline 1--* Probe Run *--1 Compatibility Fixture
Candidate Baseline 1--* Capability Finding
Candidate Baseline 1--* Supply-Chain Finding
Candidate Baseline 1--1 Go/No-Go Decision
Capability Finding *--* Probe Run
```

## Validation Rules

- Every finding references at least one probe run and an umbrella question/feature requirement.
- `supported` requires two reproducible clean-environment probe results unless the finding is explicitly exploratory and excluded from the go decision.
- `conditional-go` requires a safe default, a named owner slice, and an enforceable control; it cannot waive workspace isolation, governed execution, offline, licensing, or packaging.
- Evidence contains no real workspace, user, session, tool credential, token, private path, or payload.
- Generated reports are immutable by digest; human summaries link to rather than rewrite raw evidence.
