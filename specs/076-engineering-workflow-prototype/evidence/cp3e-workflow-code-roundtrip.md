# CP3E Evidence — Workflow Code ↔ Diagram Round Trip

**Status**: Ready for hands-on discovery

**Date**: 2026-08-26
**Decision state**: Provisional experiment, not production architecture

## Ambiguity

Can an engineer-readable diagram and an LLM-friendly, syntactically
verifiable text format be two views of one workflow without creating two
sources of truth? What belongs in the semantic definition, what belongs only
in layout, and where should an edit become executable?

## Hypothesis

A strict, compact JSON document containing phases, typed blocks, output ports,
and connections can be validated and projected into the current four-block
diagram. An explicit Apply boundary and structured errors will make invalid or
unapplied edits understandable enough to diagnose during discovery.

## Smallest useful experiment

The diagnostic route now exposes `Diagram` and `Code` views over one applied
workflow. The Code view can edit the workflow title, phases, block roles and
text, typed output ports, and connections. Parsing has three observable
outcomes:

- valid and applied;
- valid but not applied; or
- invalid, with path/code/message issues while the last valid diagram remains.

The source format has the provisional version `0.1-discovery`. Layout is a
deterministic projection, not part of this document.

## Deliberate exclusions

- No production workflow schema or persistence migration.
- No claim that JSON is better than YAML or a purpose-built DSL.
- No general workflow execution engine.
- No visual drag/edit round trip back into text yet.
- No LLM authoring command protocol yet.
- No layout syntax, routing controls, or viewport state.
- No live MCP invocation or schema argument generation.
- No attempt to remove the diagnostic runner's four stable fixture identities;
  they are validated explicitly so the experiment fails honestly.

## Hands-on test

1. Open `/prototype/engineering-workflow?scenario=diagnostic`.
2. Select **Code** and read the workflow source.
3. Change the workflow `title`, one block `title`, or a connection `label`.
4. Confirm the UI says `Valid · not applied` and the Run action is disabled.
5. Select **Apply to diagram**, switch to **Diagram**, and confirm the same
   identities and edited labels are rendered.
6. Return to **Code**, delete a quote or reference an unknown block/port, and
   confirm a structured error appears.
7. Switch to **Diagram** and confirm the last valid applied diagram is still
   visible rather than a partly invalid one.
8. Select **Reset fixture** to return to the controlled four-block example.

## Automated evidence

Focused domain tests cover full semantic round trip, valid edits, syntax and
referential errors, and the temporary fixture identity constraint. A component
test covers Code editing, explicit Apply, diagram projection, Run blocking, and
last-valid-diagram preservation. All eight focused tests pass. The production
web build also passes.

The complete 72-test prototype batch exposed test-runner resource contention:
several unrelated UI/axe tests exceeded their five-second timeout under
parallel load, but every affected file passed when run alone. This is recorded
under LL-011 as feedback-loop evidence, not classified as a CP3E product
failure and not hidden by globally increasing timeouts.

## Initial observations

- The small domain-only tests run quickly enough for the intended inner loop.
- Excluding layout keeps the semantic source substantially clearer, but means
  visual placement is not yet bidirectional.
- Stable identities make validation and diagnostics tractable, but requiring
  fixture IDs is evidence of runner coupling that production code must remove.
- An explicit Apply step makes stale versus current state testable. Hands-on
  review must determine whether it is reassuring or cumbersome.
- JSON is familiar to tools and exact to validate, but may be verbose for
  engineers and fragile for unconstrained LLM output.

These are observations and hypotheses, not accepted product decisions.

## Remaining questions

1. Is strict JSON understandable enough, or should the authoring surface use
   YAML, a constrained DSL, or form-assisted generation?
2. Should layout be deterministic, stored separately, or represented in the
   same document without becoming executable semantics?
3. Should LLMs emit whole documents, validated atomic edit commands, or both?
4. Can structured errors support a useful propose-fix/review/apply loop without
   hiding what the model changed?
5. What is the smallest generic execution contract that removes fixture block
   identities while preserving diagnostic evidence?

## Recommendation

**Keep for the next experiment**: one semantic model, stable identities,
structured validation issues, last-valid preservation, and a visible apply
boundary.

**Revise/test further**: concrete syntax, layout ownership, LLM edit
granularity, and the amount of source engineers should see by default.

**Discard as production assumptions**: the `0.1-discovery` schema, horizontal
layout projection, and the four required diagnostic block identities.
