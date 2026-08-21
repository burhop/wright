# Data Model: Rivet Engineering Scenario Harness

## ScenarioCatalogEntry

Package-owned summary of one published scenario.

| Field | Type | Rules |
|-------|------|-------|
| `scenario_id` | string | Stable lowercase slug, unique in catalog |
| `revision` | integer | Positive, monotonically increasing for material changes |
| `manifest_digest` | SHA-256 | Canonical parsed manifest |
| `title`, `summary` | bounded string | Plain text |
| `domains` | set of enum | CAD, ECAD, FEA, CFD, Python, CAM, Grasshopper, additive, slicing |
| `tier` | enum | `tier1`, `tier2`, `tier3` |
| `resource_class` | enum | `small`, `medium`, `large`, `external` |
| `expected_duration_seconds` | integer | Positive bound |
| `availability` | enum | `ready`, `blocked`, `skipped`, `unsupported` |
| `manifest_resource` | package path | Must remain below catalog root |

## ScenarioManifest

Immutable parsed definition validated by `scenario-manifest.schema.json` and cross-field rules.

Relationships:

- References exactly one package-owned Rivet workflow revision.
- Contains two or more `CapabilityRequirement` records for Tier 1.
- Declares one or more `ArtifactContract` and `AssertionDefinition` records.
- Contains environment, safety, cleanup, and provenance records.

Material changes require a revision change and new digest. Connection commands, URLs, credentials, environments, host paths, and arbitrary install commands are forbidden.

## ScenarioPreflight

Ephemeral projection for one workspace/session and one exact manifest.

| Field | Type | Rules |
|-------|------|-------|
| `preflight_id` | opaque ID | Bounded lifetime; not authority |
| `workspace_id`, `session_id` | identity | Existing authenticated scope |
| `scenario_id`, `revision`, `manifest_digest` | identity | Exact manifest |
| `workflow_digest`, `graph_id` | identity | Exact Rivet definition |
| `binding_set_digest` | optional SHA-256 | Present only when exact bindings resolve |
| `state` | enum | `ready`, `blocked`, `skipped` |
| `capabilities` | bounded list | Requirement, exact binding, schema, validation, reason |
| `environment_checks` | bounded list | Platform/resource/network/credential/application/GPU/hardware |
| `blockers` | bounded list | Stable code and recovery |
| `expires_at` | timestamp | Preflight must be refreshed after material change |

Preflight does not grant execution. Existing workflow review and run authority remain authoritative.

## NormalizedArtifactEnvelope

Versioned typed evidence defined by `artifact-envelope.schema.json`.

| Field | Type | Rules |
|-------|------|-------|
| `artifact_id` | opaque ID | Unique within scenario run |
| `schema_version` | semantic version | Initial supported range 1.x |
| `domain`, `kind` | enum/string | Must map to a registered normalizer/assertion family |
| `source_schema` | name/version/media type | Required |
| `producer` | run/node/call/capability identities | Required |
| `upstream_digests` | bounded SHA-256 list | Correlates input lineage |
| `units` | mapping | Original declarations plus optional canonical dimension |
| `coordinate_system` | optional object | Name, handedness, axes, origin, length unit |
| `content` | bounded JSON | Mutually exclusive with vault reference |
| `vault_reference` | authorized ID/media/digest | Mutually exclusive with inline content |
| `content_digest` | SHA-256 | Required after normalization |
| `validation_state` | enum | `unvalidated`, `valid`, `invalid`, `unsupported` |

## EngineeringAssertionDefinition

Versioned invariant declared by a manifest.

| Field | Type | Rules |
|-------|------|-------|
| `assertion_id` | slug | Unique in manifest |
| `plugin`, `plugin_version` | string/version | Must be registered/supported |
| `artifact_ids` | list | One or more declared artifacts |
| `rule` | enum/object | Exact, membership, range, relational, absolute/relative tolerance, or domain rule |
| `expected` | bounded JSON | Unit declarations required when dimensional |
| `severity` | enum | `error` or `warning`; safety/contract rules always error |
| `guidance` | bounded plain text | Recovery action |

## EngineeringAssertionResult

Immutable evaluation evidence defined by `assertion-result.schema.json`.

| Field | Type | Rules |
|-------|------|-------|
| `assertion_id`, `plugin`, `plugin_version` | identity | Exact definition/plugin |
| `state` | enum | `pass`, `fail`, `skip`, `error` |
| `category`, `reason_code` | stable enum/string | Transport and tool failures are not assertion passes |
| `expected`, `observed` | bounded normalized JSON | Secret/path/script filtering applies |
| `units` | optional object | Original and canonical units/dimension |
| `artifact_digests` | bounded list | Inputs evaluated |
| `producer` | node/capability/call | Failure attribution |
| `message`, `recovery` | bounded plain text | Required for non-pass |

## ScenarioRunReport

Durable report linked one-to-one with an existing workflow run.

| Field | Type | Rules |
|-------|------|-------|
| `scenario_run_id` | opaque ID | Primary key |
| `workflow_run_id` | opaque ID | Unique FK to `workspace_workflow_runs` |
| exact identities | JSON/digests | Scenario, workflow, graph, bindings, schemas, fixtures, inputs, assertions, environment |
| `state` | enum | `preflight`, `running`, `passed`, `failed`, `cancelled`, `blocked`, `error` |
| `artifact_index` | bounded JSON | Metadata/digests/vault IDs only |
| assertion rows | child relationship | Ordered immutable results |
| `cleanup_state` | enum | `not_started`, `clean`, `residue`, `unknown` |
| `residue` | bounded JSON | Process/container/file types and recovery, no raw broad paths |
| `report_digest` | SHA-256 | Canonical finalized report |
| `created_at`, `finalized_at` | timestamps | UTC |

State transitions:

```text
preflight -> blocked
preflight -> running -> passed
                    -> failed
                    -> cancelled
                    -> error
```

Terminal states are immutable. A late child result cannot change them. Rebuilding an absent report is permitted only when every material identity matches durable run evidence.

## SQLite migration 15

`engineering_scenario_runs` stores the scenario/workflow/report identity, state, bounded artifact index, environment/cleanup JSON, report digest, and timestamps. `engineering_scenario_assertions` stores ordered assertion results and their bounded expected/observed/producer JSON. Foreign keys connect to existing workflow runs; no bearer authority or raw artifact is stored.
