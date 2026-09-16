# Canonical validator task source

Status: compiler implemented; execution/authoring integration in progress.

A validator is an ordinary `task` in the existing `.wflow` language. Use
`step_type: work`, `performed_by: configured_tool`, an empty prompt, and null
`tool`/`reusable_step`. Its settings are a closed object:

```json
{
  "authoring_template": "process-validator",
  "output_format": "json",
  "max_revisions": 0,
  "validation": {
    "profile": {
      "source": "packaged",
      "name": "structured-demo",
      "reference": {"id": "PROFILE_ID", "version": "VERSION", "sha256": "PROFILE_SHA256"}
    },
    "baseline": {"id": "BASELINE_ID", "version": "VERSION", "sha256": "BASELINE_SHA256"},
    "subjects": {"result": "check_subject"},
    "budget": {"max_bytes": 16777216, "max_entities": 100000, "timeout_seconds": 120, "memory_limit_mb": 512}
  }
}
```

The uppercase reference values are placeholders, not valid digests. Obtain exact
references from the selected profile's `reference()` and
`baseline.reference()`; never fill them from candidate output. `output_format`
and `budget` may be omitted for their defaults. `max_revisions` is an integer
0â€“3, default 0. A nonzero limit alone never schedules a producer.

`subjects` maps each profile subject **role** to a distinct task input port key.
Every such port needs exactly one `item` connection from a producing task's
output, with matching kind and quantity `one`. Input blocks and unbound,
collection or duplicate role bindings are rejected. All profile roles must be
bound; no search for neighboring files or implicit output selection occurs.
The validator has exactly one `engineering_document` output of quantity `one`:
the JSON assessment reference/check report. It does not replace the checked
producer's output with report content.

The `profile.source` may instead be `workspace`, with `name` a confined
workspace-relative `.json` path. Profiles are loaded and checked against both
pinned references before dispatch, then again at evaluation. Closed profile
schemas contain data constraints, not executable predicates or commands.
Changing a profile/baseline requires updating and saving its explicit pin.

An `approval` connection from validator task ID to consumer task ID uses
`when: pass` and establishes the same canonical gate ordering as legacy design
checks. A consumer that also needs the original output keeps its ordinary data
connection from that producer. A `revision` connection uses `when: revise`;
the existing bounded-rework compiler validates its safety. Generic repair
eligibility is implemented separately in T015; a nonzero setting is not proof
of an accepted replay path.

Canonical document and port fields (`purpose`, `group`, `item`, `description`,
etc.) remain required by the normal authoring validator. Settings remain the
existing JSON-valued model field; no second workflow schema or editor is
introduced. `ValidatorConfiguration` is the shared closed backend schema owner,
while `recovery-dsl.ts` preserves and validates the corresponding authoring
configuration. Existing AI prompt, MCP task and CAD design-check syntax is
unchanged.

Compile controls cover missing/invalid pins, unsafe profile paths, undeclared
fields, executable configuration, ambiguous/missing subjects, collections,
wrong performer, mixed MCP settings and unsafe file policies. Runtime evidence
is published under the verification/diagnostic artifact roles before a gate
stops downstream work; a transport success is not a validation pass.
