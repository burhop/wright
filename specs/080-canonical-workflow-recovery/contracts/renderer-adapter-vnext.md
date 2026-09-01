# Renderer Adapter vNext Contract

The recovery renderer extends the existing `DraftCanvasAdapterProps` seam by adapting IR vNext into the retained immutable `DraftProjection`. No vendor-native serialization crosses the boundary.

## Host responsibilities

- Own canonical definition, layout, accepted revision, undo/redo, candidates, diagnostics, selection, proposals, and run records.
- Project IR/layout/run facts into immutable node/edge/overlay records.
- Translate renderer gestures into canonical semantic or layout commands.
- Apply and validate commands through the conformance kernel.
- Synchronize selection with code spans and inspector sections.
- Retain the last-valid definition on renderer failure or invalid intent.

## Renderer responsibilities

- Render readable blocks and routed relationships.
- Put connectable input handles on the left and output handles on the right.
- Display port name, type, requiredness, and cardinality.
- Keep connection handles distinct from adjacent artifact inspect/open controls.
- Emit select, move, connect, disconnect, and keyboard gesture intents.
- Render active block/connection overlays and all run states using non-color cues.
- Expose stable test IDs and accessible names.
- Support fit/focus/navigation for the acceptance graph. The frozen prototype's
  single 100-block observation remains explicitly non-qualifying; production
  large-graph qualification is deferred until after product approval.

## Forbidden renderer authority

The renderer must not assign semantic IDs, validate graph semantics, persist vendor state as definition, directly mutate accepted IR, accept proposals, infer run causality, or execute a binding.

## Three-treatment laboratory

1. **Dot socket**: compact circular connection target with adjacent text.
2. **Engineering terminal**: larger square terminal with name/type inside the block edge.
3. **Hybrid typed port**: distinct socket plus adjacent typed label and separate artifact icon/button.

The selected treatment must prove that a first-time reviewer can identify connection target versus artifact inspection without explanation. The recovery hypothesis is treatment 3; evidence, not preference, closes the choice.

## Replacement proof

`model.spec.ts` supplies two renderer contract fakes. Both consume the same
immutable projection and emit the same stable selection intent while canonical
definition bytes remain byte-identical. This is the bounded recovery proof that
the React Flow implementation can be replaced without transferring authority.
Promotion still requires broader text, validation, diff, layout, and run
contract qualification against a production replacement.
