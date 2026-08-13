# Contract: Model-Enabled Engineering Scenario 1.1

## Compatibility

Scenario manifest `schema_version: "1.1"` extends the 1.0 contract in a new `scenario-manifest-1.1.schema.json` resource. The existing 1.0 schema/resource remains immutable and readers continue to inspect 1.0 manifests. New model-enabled manifests write 1.1. Validation selects the exact schema by the declared version; unknown versions or provider fields fail closed.

## Manifest changes

- `domains` adds `model`.
- Each capability adds required `provider_kind: mcp | engineering_model`.
- A model capability uses the existing static `tool_name` shape and must begin with `wright_model__`; an MCP capability must not.
- A model-enabled scenario contains at least two MCP capabilities from independent fixture providers plus at least one engineering-model capability.
- `resource` may add `model_ram_mib` and `model_timeout_seconds`; both are preflight ceilings, not observed promises.
- `artifacts.kind` adds `candidate-batch`, `model-result-batch`, and `chatter-advisory-report`.
- `assertions.plugin` adds `chatter_advisory` through the duplicate-safe public registry.
- `safety` adds `executable_machine_instructions: false`.

## Cross-field rules

1. Every capability node exists exactly once in the Rivet graph and has the same static tool name.
2. Provider kind is supplied by gateway discovery and must match the manifest expectation.
3. The candidate producer is an MCP node; the candidate consumer is an engineering-model node; the advisory producer receives only their correlated authorized artifacts.
4. Candidate identity and order are unchanged from CAM receipt through model result and report.
5. A preferred/selected-for-review candidate requires every declared non-model invariant to pass and model applicability to be `in_population` with no threshold review.
6. The manifest and workflow contain no command, process arguments, endpoint, server URL, credential, environment variables, host path, install instruction, model payload, or reusable authority.
7. Tier 1 requires no network, credential, proprietary application, GPU, hardware, large download, license prompt, host mutation, or interactive prompt.
8. Physical actuation and executable machine instructions are false. Violations are catalog errors, not runtime warnings.

## Report contract

The scenario report adds a bounded `advisory` object:

- `simulation_only: true`
- `score_semantics: uncalibrated_model_score`
- `selected_for_review: <candidate-id> | null`
- `candidate_outcomes[]`: candidate, invariant, applicability, threshold-review, selection and rejection facts
- `human_review_required: true`
- `machine_authority: none`
- `provider_evidence[]`: closed MCP/model identity union
- `material_digest` and separate `observations`

No advisory object exists for a failed or cancelled run. The JSON and every authorized artifact are scanned for forbidden machine commands, endpoints, authority, credentials, paths, private rows, and model bytes.

## Extension rule

A later model-enabled scenario registers manifests, artifact normalizers and assertion plugins through the existing collision-safe registries. The generic gateway, Rivet runner, scenario service and UI may inspect provider-neutral fields but may not branch on a model ID, adapter ID, Chatter feature name, or Chatter scenario ID.
