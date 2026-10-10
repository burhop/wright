# Canonical validator task source

Status: compiler, canonical execution, bounded repair, authoring controls and served browser qualification implemented; structured, geometry and thermal process demonstrations retained.

A validator is an ordinary `task` in the existing `.wflow` language. Use
`step_type: work`, `performed_by: configured_tool`, an empty/absent prompt, and null
`tool`/`reusable_step`. Descriptive `instructions` metadata is allowed and never
executed as a model prompt. Its settings are a closed object:

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

The editor's Review → Validate output control loads generated choices from the
runtime profiles, creates distinct subject ports and preserves profile/baseline
pins through commands, Undo/Redo and Source round-trip. Its internal scalar
configuration stores serialized JSON; the public source writes a `validation`
object. The compiler also accepts its equivalent serialized JSON string.

The uppercase reference values are placeholders, not valid digests. Obtain exact
references from the selected profile's `reference()` and
`baseline.reference()`; never fill them from candidate output. `output_format`
and `budget` may be omitted for their defaults. `max_revisions` is an integer
0–3, default 0. A nonzero limit alone never schedules a producer.

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
the bounded-rework compiler validates its safety. For a local validator, it may
target one preceding producer that owns all checked subjects: an ordinary AI
text/structured producer with indexed files, a create-new CAD task with indexed
native outputs, or an explicitly isolated AI MCP file producer. The file producer
requires `revision_policy: create_new_files`, indexed response publication,
named file outputs, and the attempt allocation contract below. Exact tool calls,
existing-document application edits, reviews, external actions, overwrite policy,
unrelated outputs, multi-step segments and arbitrary back-edges are rejected. Selecting a
target in the editor sets an initial limit of one; selecting zero disconnects the
revision path. A nonzero limit alone never schedules a producer.

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

## 9 October 2026 — preserve corrected file attempts

A controlled canonical-runtime regression exposed that the former
`create_new_files` compiler gate alone did not allocate new output paths: the
second attempt could overwrite the file behind the first assessment. Historical
source/run evidence is retained. Starting a legacy literal-path automatic MCP
file loop now reports a readiness defect; updating it requires a visible source
revision, not an implicit filename rewrite.

The producer declares `run_path_template: wright.run-path/2`. Each saved response
and expected output has one `{{wright.run_id}}` directory followed by one
`{{wright.producer_attempt}}` directory, for example
`outputs/{{wright.run_id}}/design/{{wright.producer_attempt}}/part.step`.
Expected-file port mappings use those same templates. Version 1 retains its
existing semantics and rejects the attempt token. Version 2 is scoped to isolated
create-new AI MCP file tasks; approval, validation, existing-document and process
input configuration cannot be templated with the attempt identity.

The existing preparer binds the run identity. The canonical runner binds the
attempt from retained producer records, exclusively reserves its output
directories before model/tool dispatch, records the resolved file binding, and
retains every prior attempt. An existing directory prevents uncertain replay.
Previous files are checked before/after correction and on durable continuation.
A changed/missing prior file holds downstream work. These checks do not sandbox
an arbitrary external provider's filesystem access or repair damaged evidence.

A downstream MCP file input can declare
`mcp_file_dependencies: {"input_port": {"source": "connected_output"}}`.
It receives the exact connected output's confined path, hash and source port;
the usual byte verification still applies. It does not guess which attempt
passed or read a model-authored path. Literal-path dependency maps retain their
strict equality checks. The editor preserves both forms on save/reopen.

Controlled tests exercise failed/corrected JSON files through the real validator,
historical/current assessments, no progress, revision exhaustion, downstream MCP
handoff, file mutation, directory collisions, and durable review continuation.
Live engineering-provider and served-workspace qualification of this new version
remain separate requirements; these tests do not establish native CAD capability.
