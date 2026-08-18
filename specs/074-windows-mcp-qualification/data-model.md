# Data Model: Windows MCP Qualification

## QualificationAllowlist

An immutable ordered value object containing exactly seven catalog IDs.

- `server_ids`: unique tuple in mandated order
- `policy_version`: stable version included in evidence
- Invariant: denial happens before recipe resolution or any side-effect port
- Invariant: prefix, vendor, alias, and fuzzy matches are forbidden

## WindowsQualificationRecipe

A reviewed declarative recipe for one allowlisted server.

- `schema_version`, `recipe_id`, `server_id`, `publisher`, `source_kind`
- `source_url`, `immutable_revision`, `package_name`, `package_version`
- `license`, `maintenance_expectation`, `locality`, `transport`
- `allowed_network_destinations`: exact HTTPS origins or loopback endpoints
- `credential_requirements`, `host_requirements`
- `risk_findings`: capability, severity, boundary, rationale
- `operations`: typed ordered operations with stage, timeout, byte ceiling, and
  reviewed parameters
- `safe_probe`: optional tool name, arguments digest policy, mode
  (`read_only` or `disposable_brep_geometry`), safety rationale, and confined
  write scope
- `expected_residue`: paths/registrations confined to qualification roots
- `cleanup`: typed stop/remove/unregister operations
- Invariant: no arbitrary shell/PowerShell/cmd text
- Invariant: every executable identity is pinned and allowlisted
- Invariant: a safe probe cannot carry destructive/manufacturing/physical-control
  intent or a path outside the disposable workspace; only `brep-mcp` may use the
  disposable geometry mode and its exact program digest is part of the recipe

## SafetyPreflight

The decision record that authorizes or refuses executable action.

- `server_id`, `recipe_digest`, `reviewed_at`
- `publisher_confirmed`, `canonical_source_confirmed`, `source_current`
- `license_recorded`, `install_hooks_reviewed`, `dependencies_reviewed`
- `filesystem_behavior`, `network_destinations`, `subprocess_behavior`
- `exposed_tool_risks`, `material_concerns`, `residual_risks`
- `decision`: `approved`, `safety_blocked`, `obsolete_or_unavailable`
- `reason_code`, `recovery`
- Invariant: only `approved` may enter an executable operation

## QualificationStageEvidence

One result for one named stage.

- `stage`: `source_current`, `windows_install_passed`, `mcp_started`,
  `protocol_passed`, `safe_probe_passed`, `wright_install_passed`,
  `wright_gateway_passed`, or `cleanup_passed`
- `result`: `passed`, `partial`, `failed`, `safety_blocked`,
  `obsolete_or_unavailable`, `not_applicable`, or `not_tested`
- `reason_code`, `summary`, `recovery`
- `started_at`, `finished_at`, `duration_ms`
- `operation_digest`, `output_digest`, `artifact_digests`
- `observations`: bounded non-sensitive counts/booleans/identities
- `missing_requirements`, `network_destinations_contacted`
- Invariant: raw credentials, environment, private paths, command arguments, and
  unbounded process output are forbidden

## ServerQualificationEvidence

Append-only aggregate for one recipe and native Windows observation.

- Identity: `evidence_id`, `schema_version`, `server_id`, `policy_version`
- Bindings: `recipe_digest`, `source_revision`, `package_version`,
  `package_digest`, `tool_schema_digest`, `machine_digest`,
  `credential_binding_digest`
- Safety: `safety_preflight`
- Results: exactly one entry for each of the eight stage names
- Protocol: server identity/version, negotiated MCP version, tool count/schema
  digest, stdout/shutdown observations
- Side effects: installed-items summary, residue before/after digests
- Audit: attempted-action types and exact catalog IDs, cleanup summary
- Currency: `observed_at`, `maximum_age_hours`, `stale_reasons`
- `terminal_classification`, `limitations`, `residual_risks`, `follow_ups`
- Invariant: all stage names are present even when not attempted
- Invariant: terminal success never implies backend or gateway success

## QualificationRun

The checkpointed ordered program record.

- `run_id`, `policy_version`, `started_at`, `finished_at`
- `next_server_id`, `server_evidence`: seven ordered references/digests
- `installed_items`, `cleanup_events`, `attempted_server_ids`
- `non_allowlist_actions`: must be empty
- `status`: `running`, `completed`, or `failed_infrastructure`
- Invariant: external prerequisites change one server result but do not stop the
  ordered run

## WindowsQualificationSummary

Bounded signed catalog/UI projection.

- `observed_at`, `evidence_path`, `evidence_digest`, `current`, `stale_reasons`
- `source`, `package_or_registration`, `startup`, `protocol`,
  `host_or_backend`, `wright_setup`, `gateway`, `cleanup`
- Each group: result, short label, reason code
- `claim`: optional exact sentence; absent unless evidence supports it
- Invariant: `claim = "Installs on Windows with no problems"` requires passed
  package, startup, protocol, Wright setup, clean shutdown, and cleanup evidence

## State Transitions

```text
catalog_only
  -> source_reviewed
  -> safety_blocked | obsolete_or_unavailable | approved
approved
  -> installing_or_registering
  -> starting
  -> protocol_probing
  -> safe_probe_or_boundary
  -> wright_onboarding
  -> gateway_probing
  -> cleaning
  -> evidence_saved
evidence_saved
  -> current | stale
```

Every failure path transitions through `cleaning` when any owned resource may
exist. A cleanup failure is preserved independently and prevents a no-problems
claim without rewriting earlier stage evidence.
