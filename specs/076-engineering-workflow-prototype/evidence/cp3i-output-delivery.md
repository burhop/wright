# CP3I Evidence — Actionable Workflow Outputs

**Status**: Component and build verification passed; live human BREP-view review pending

**Date**: 2026-08-26
**Decision state**: Keep the generic output reference; revise durability and presenter ownership for production

## Ambiguity

What does a successful workflow deliver, and how can a user interact with the
result without teaching the workflow UI about every document, CAD system,
simulation package, or external website?

## Failure that motivated the experiment

The first correct four-block UI run completed and turned green, but its terminal
result was only structured data. The live BREP model had been created in a
hidden application surface and then destroyed during cleanup. The run was
technically successful but practically unusable.

## Smallest useful experiment

The prototype adds one serializable output reference containing:

- output identity, title, model kind, and BREP format;
- a user-readable description;
- session durability and exact producer provenance;
- `View in BREP`; and
- `Download model definition`.

The generic runner only carries the reference in the final result. The BREP
fixture adapter retains the successful control surface, resolves the two
actions, and releases the session when the demo resets. The diagram and output
components do not dispatch on BREP or CAD.

## UI concept

- The success banner states that an output is ready.
- The central completion monitor replaces terminal JSON with a prominent output
  card.
- The selected final block repeats the card in its Run result view.
- Format, lifetime, and description are visible before any action.
- Exact values and evidence remain available in technical disclosures.
- The live model opens in an application-owned overlay and returns to the
  workflow without deleting the session model.

The same contract can describe a document with View/Download, a durable STEP
file with Download/Open in application, an Onshape model with Open link, or a
Solid Edge file with Open in Solid Edge. An unavailable action remains visible
only when explaining why it cannot currently run is useful.

## Verification

- Focused Vitest run: 4 files, 12 tests passed.
- Output-reference model test rejects arbitrary objects.
- Shared-runner component test proves a completed run announces one output,
  renders its model card, and dispatches its action through the producing
  runtime.
- Production web TypeScript and Vite build passed.

## Remaining questions

1. Should the canonical run own outputs directly, or derive an aggregate from
   per-step artifact references?
2. What retention, expiry, and cleanup policy applies to session and native-app
   results?
3. How are output actions re-authorized when opened later from run history?
4. What common preview metadata is needed for documents, images, meshes, CAD,
   reports, and datasets?
5. How should Wright choose among embedded, browser, and native application
   presenters while preserving one artifact identity?
6. Which MCP output schemas can declare artifact production automatically, and
   when must an adapter supply the declaration?

## Recommendation

**Keep** typed output references, generic action vocabulary, producer-resolved
actions, obvious completion cards, and explicit durability.

**Revise** the prototype's in-memory presenter registry into durable artifact
storage plus the existing governed Surface system before production.

**Discard** green-only success, raw terminal payloads as deliverables, and
automatic cleanup that destroys the only usable result.
