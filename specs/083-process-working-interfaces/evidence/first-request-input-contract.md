# First Request input contract qualification

**Date:** 7 October 2026. **Scope:** versioned declaration/compiler/checkpoint
support and synthetic local runtime regression proof. Browser and live-provider
qualification are separate work in the approved goal.

An author may start a process with a declared Request input step before any
engineering tool runs. The runtime persists the question and resumes the same
run after the exact typed answer. It needs no fake upstream AI producer.

Version 1 declarations preserve their original connected upstream task-evidence
requirement. Version 2 explicitly permits no connected upstream evidence. Both
require an Engineer work step, a bounded object response schema and exactly one
structured response output. Any declared required evidence port still needs its
producer. AI/tool bindings, automatic review authority and replay across an
answered input barrier remain forbidden.

The checkpoint subject's existing shape remains unchanged. Definition digest,
frozen input snapshot/digest, step, declaration/schema and available artifact
identities still pin the question. `upstream_digests` may be empty only in version
2; old version 1 subjects retain both validation and exact canonical digests.
The existing continuation schema version 3 supports cursor zero and no completed
tasks. Version 2 answer-result provenance additionally retains the frozen input
snapshot digest; version 1 historical result serialization remains unchanged.

Existing owners extended:

- `workflow_human_input.py`: versions 1/2 and explicit no-producer support.
- `process_interfaces/interactions.py`: conditional upstream evidence validation,
  preserving source/input scope and response identity.
- `workflow_human_input_runtime.py`: frozen-input provenance for version 2.
- Existing canonical compiler, recorder, SQLite checkpoint owner and resume path
  perform execution; no new runner or approval mechanism was added.

Initial verification passed 73 focused first-input, source and continuation tests.
The new tests prove readiness without preparation inputs, a visible persisted
`waiting_human` state before any model invocation, schema/stale/scope rejection
without altering the pending question, idempotent answers, conflict for changed
answers, service recreation, same run/log completion and no repeated model call
on duplicate resume. Existing upstream, approval separation and continuation
integrity regressions are retained. After adding a version 2 upstream-binding
case, all six current first-input tests passed in a fresh owned test directory.

All model answers and input decisions in these tests are synthetic and labelled
integration tests. They establish software behavior, not engineering acceptance
or a successful live tool/model workflow. The initial default temporary-directory
run hit sandbox access errors; using a fresh workspace-owned test directory avoids
that host limitation. No service restart, physical action or commit was performed.
