# Renderer Adapter Contract

The composer host passes an immutable renderer-neutral projection and current selection to one injected renderer. The renderer emits intents; it never assigns IDs, validates, persists, executes, or serializes vendor-native state.

```ts
type DraftCanvasAdapterProps = {
  projection: Readonly<DraftProjection>;
  selectedSemanticId: string | null;
  onIntent(intent: DraftCanvasIntent): void;
};
```

`DraftProjection` contains phase lanes, blocks, typed port anchors, directed connections, gates, labeled feedback paths, intended-artifact summaries, and integer positions. Every record carries its canonical semantic ID.

`DraftCanvasIntent` is a closed union for select, create block, move block, edit block, create/delete connection, create/edit gate, create/edit feedback, create/edit intended artifact, and delete concept. Save, close, reopen, and validation are host/application intents, not renderer responsibilities.

The host must:

- derive canvas, text, and inspector from one canonical draft;
- assert exact semantic-ID parity between projection and text;
- own keyboard command routing, diagnostics, last-valid state, and draft authority labels;
- provide complete text/properties fallback if the renderer fails or is unavailable;
- expose stable test IDs and non-color state cues.

A contract fake replacing the first-party SVG/HTML renderer must leave semantic bytes, digests, validation, persistence identity, and text output unchanged. This proves the seam without creating a discovery or plugin framework.
