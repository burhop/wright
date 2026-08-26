# CP3G Evidence — Headless Four-Block Execution

**Status**: Live smoke run passed

**Date**: 2026-08-26
**Decision state**: Keep the semantic runner; revise the MCP application boundary

## Ambiguity

Can the four semantic workflow blocks execute without the workflow UI, using
the diagram only as a view of canonical definition and run records? Can the
selected MCP schema shape the preceding AI output strongly enough to produce a
valid call?

## Hypothesis

A provider-neutral four-step runner can execute request validation, isolated AI
generation, exact generic MCP invocation, and outcome evaluation without React
or a graph library. The AI should produce a small tool-independent engineering
artifact; a deterministic adapter should validate it and compile the selected
tool's exact arguments.

## Smallest useful experiment

The live fixture used one self-contained request:

- 100 × 60 × 8 mm mounting plate;
- four 8 mm through holes with explicit center locations;
- `gpt-5.6-sol`, low thinking, and `tool_policy: none`;
- exact installed `BREP MCP` / `brep.model.apply_history` binding;
- a bounded, typed mounting-plate specification returned by the AI;
- a deterministic fixture adapter that compiles that specification into the
  exact required `history` object; and
- Step 4 acceptance limited to successful application plus three consistent
  inspections of feature count, ordered IDs, and run metadata.

The generic runner owns only ordering, stop behavior, and step evidence. The
live script owns the BREP fixture and Wright HTTP adapters. Neither imports
React nor the selected graph library.

## Result

The revised repeatable live run passed in approximately 12.1 seconds:

| Block         | Result    | Evidence                                                                                                                            |
| ------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1. Request    | Completed | 133 prompt characters; zero attachments; explicit self-contained dimensions                                                         |
| 2. AI         | Completed | `openai-codex/gpt-5.6-sol`; tools disabled; valid tool-independent mounting-plate specification                                     |
| 3. MCP        | Completed | Deterministic compilation to five BREP features; runtime-resolved server; exact `brep.model.apply_history` accepted the history     |
| 4. Evaluation | Completed | Three of three inspections returned five state/history features, the five expected ordered IDs, and `HEADLESS-4-BLOCK-001` metadata |

The terminal outcome was `passed`, with the explicit meaning: BREP accepted the
history and returned consistent inspect evidence. Engineering correctness was
not evaluated.

## Failed attempt that changed the design

The first manual attempt applied five features successfully, but the immediate
inspection returned an empty model. Repeated inspection then alternated from
zero to five features. Wright had mounted one BREP control page and the
headless experiment mounted another. BREP's application command queue allowed
both pages to poll the same queue, so commands could execute against different
in-memory models.

Restarting the BREP runtime and mounting exactly one loopback control surface
produced three consecutive correct inspections. The repeatable script now
fails if any of its three observations disagrees; it never treats eventual
success as sufficient.

A second failure exposed a different boundary error: asking the LLM to emit a
raw BREP `PartHistory` produced syntactically valid JSON with feature IDs in the
wrong location. Hand-written validation rejected the result before the MCP
call. Prompt patching would only couple the workflow more tightly to one
server's internal format. The revised experiment therefore shares one typed
mounting-plate contract and deterministic compiler between the UI and headless
paths.

## Deliberate exclusions

- No browser workflow UI and no projection of the run back into the diagram.
- No uploaded image transfer; browser-local attachment state is not canonical
  workflow input.
- No saved 3MF artifact, rollback, approval UI, or immutable candidate.
- No independent topology, dimension, manufacturing, strength, or engineering
  validation.
- No claim that BREP MCP is truly headless; its application surface is mounted
  in headless Chromium for this experiment.
- No general inference from `CAD` to BREP; the fixture names the exact server
  and tool.

## Automated evidence

- `headless-four-block-runner.spec.ts` proves ordered execution and verifies
  that an invalid AI result stops before MCP.
- `mounting-plate-brep-fixture.spec.ts` proves that the AI contract is
  tool-independent, compiles deterministically to exact BREP IDs and boolean
  targets, and rejects raw BREP history as AI output.
- `run-brep-headless-smoke.mjs` is the repeatable live experiment. It creates
  and cleans up an isolated Wright session, validates the AI JSON before MCP,
  invokes through Wright's existing BREP gateway, and emits a structured run
  record.
- Live run: all four blocks completed and all three inspect observations
  matched.

## Lessons and remaining questions

1. The diagram is not required for execution; both UI and CLI should project
   the same canonical definition and durable run record.
2. Browser-local attachments cannot silently become headless inputs. They need
   stable artifact identities in the canonical request.
3. Binding a server is insufficient. The selected tool schema must be resolved
   before invocation, but application-internal arguments should be produced by
   a deterministic adapter whenever a smaller semantic contract exists.
4. Application-controlled MCP servers need an authoritative surface identity
   or exclusive client lease. A sticky boolean `connected` is insufficient.
5. Step 4 needs declared acceptance criteria. Transport success is not an
   engineering oracle.
6. A production runner must persist events and evidence rather than emitting
   one terminal JSON document.

## Recommendation

**Keep**: the UI-independent four-step runner seam, strict stop behavior,
typed semantic AI output, deterministic exact-argument compilation, exact MCP
binding, and structured step evidence.

**Revise**: replace the fixture prompt with a canonical typed mapping; give MCP
application surfaces stable identity/exclusivity; use durable run storage; and
make acceptance criteria explicit workflow data.

**Discard**: any assumption that an installed MCP is headless, that `connected`
proves one authoritative application, that eventual inspection consistency is
acceptable, or that successful CAD mutation proves design correctness.

**Next bounded experiment**: use a canonical request artifact and exact tool
schema to generate a previewable argument mapping, then persist the headless run
record and project it into the existing four blocks. Do not add a
BREP-specific executor to the generic workflow runtime.
