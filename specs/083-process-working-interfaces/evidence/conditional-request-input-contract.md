# Conditional Request input qualification

**Date:** 7 October 2026. **Status:** implemented bounded version 3 contract and
synthetic backend/source/runtime verification. Served editor and live engineering
workflow qualification remain separate work under the approved goal.

The accepted process can deliberately ask for its fixed fields only if a bound
requirements-analysis result reports those fields unresolved. This adds no
arbitrary graph condition, expression evaluator, model-authored form or new runner.
It uses the same durable question and response path as unconditional input.

## Saved declaration

An input task uses its existing Engineer work-step and structured output binding:

```json
{
  "version": 3,
  "kind": "input",
  "instructions": "Choose the material for this comparison.",
  "response_schema": {
    "type": "object",
    "properties": {"material": {"type": "string", "enum": ["steel", "aluminum"]}},
    "required": ["material"],
    "additionalProperties": false
  },
  "output_port": "material_response",
  "when": {
    "kind": "unresolved_fields",
    "source": "requirements.requirements_result",
    "fields": ["material"]
  }
}
```

The condition source must be a connected task's exact structured output address.
`fields` must match the complete fixed response property names, with at most 32
unique fields. The closed schema remains unchanged during execution; an input
answer cannot become engineering/action approval. Graph connection `when` remains
unsupported; this condition exists only inside the input declaration.

The upstream producer returns a typed JSON object, not a prose question:

```json
{
  "version": "wright.requirements-resolution/1",
  "unresolved_fields": ["material"],
  "resolved_values": {}
}
```

Nonempty unresolved fields create a planned wait. With no unresolved fields, the
upstream `resolved_values` must validate against the **whole original** response
schema. The runner records a skip and publishes those actual resolved values at
the input step's answer port, allowing downstream work to continue. There is no
fabricated human answer receipt, actor, checkpoint or approval.

Unresolved/known names must belong to the fixed fields, cannot overlap, and must
account for required values. Known partial values retain their validators. Unknown
protocol versions, invalid values, undeclared names and malformed evidence produce
`WORKFLOW_INPUT_CONDITION_INVALID`; they cannot invent another question.

## Identity and ownership

Pure typed condition/resolution/evaluation schemas live in
`packages/core/src/core/workflow_input_conditions.py`. The existing human-input
compiler validates the declaration and connection. Runtime helpers evaluate only
the bound inline JSON value and construct skip output/evidence. The canonical
runner retains skip records and condition-evaluation events alongside ordinary
results and records.

An ask checkpoint binds the exact typed evaluation, source address and digest,
definition/declaration, frozen run inputs and connected evidence. The input owner
rechecks the actual encoded source in the retained continuation and validates its
typed contents before accepting a response. Skips likewise retain exact upstream
and frozen-input provenance. Service recreation resumes the same run from its
recorded cursor; completed conditional work is not reevaluated or replayed.

Version 1/2 declaration and checkpoint wire shapes omit the new optional fields;
their prior canonical subject digests and semantics remain intact. Conditional
declarations require version 3. Existing automatic-rework prohibition across
input barriers remains unchanged.

## Verification

104 focused tests passed across shared condition contracts, conditional input,
first input, source authoring and durable continuation. Coverage includes:

- Malformed/unsupported conditions rejected before execution; unconnected and
  untyped sources rejected; invalid requirements payloads produce no question.
- Fully resolved input skips, produces schema-valid actual values, and carries
  no human/approval authority.
- Unresolved input waits on exact evidence; invalid/stale answers leave it pending;
  an answer survives service recreation and resumes the original run/log.
- Changing evaluation evidence, altering retained upstream bytes or converting a
  skip into an ask is rejected.
- A completed skip survives a later unconditional wait, service recreation and
  duplicate resume, without repeating the earlier model work or condition event.
- Version 1/2 source, historical subject digest and existing upstream/approval
  isolation regressions remain passing.

All producer/model values and human responses in this suite are explicit synthetic
test evidence. No live provider, physical action, service restart or commit was
performed. This proof establishes software behavior, not engineering acceptance.
