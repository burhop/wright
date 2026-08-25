# CP3C Knowledge Lookup vertical slice

Date: 2026-08-25
Branch: `076-engineering-workflow-prototype`

## Hypothesis

Engineers will understand an active **Knowledge Lookup** input more readily
than a static **Company Context** bucket or an implementation label such as
**RAG**. The minimum understandable configuration is a plain-language lookup
prompt plus a governed source scope.

## Implemented increment

The former **Company Context** input is now **Knowledge Lookup**. It supports a
session-only configuration loop:

- describe what information Wright should find;
- apply the complete lookup-prompt edit as one reversible command;
- choose one or more generic source scopes:
  - workspace documents;
  - connected knowledge; and
  - approved web sources;
- see missing-query, missing-source, and configured-but-not-run states;
- remove or add source scopes through the same typed history;
- undo and redo query/source changes;
- project query/source counts and retrieval status onto the canvas block;
- reserve a visible output area for reviewable retrieved context;
- disclose `Local CP3C draft · session only`, `not persisted`, and `Not
executed` in Evidence.

The palette also says **Knowledge lookup** rather than **Company context**.

## Product and architecture boundary

**Knowledge Lookup** describes user intent. **RAG**, full-text search, semantic
search, an LLM, a catalog service, a generic MCP tool, or a combination of
those may eventually satisfy that intent. None of those implementation
choices should appear as a block taxonomy or dispatch branch.

`domain/knowledge-lookup-draft.ts` owns the query, selected source identities,
typed commands, validation, and undo/redo history. Source options are generic
fixture metadata. Unknown source identities are rejected by the pure reducer.
The React Flow adapter receives only the resulting Wright visual projection.

This increment performs no search, embedding, vector lookup, reranking, LLM
call, MCP call, network request, permission check, citation generation, or
persistence. Future retrieval must honor workspace permissions and return
reviewable passages, citations, and evidence through a governed generic
boundary.

## Visual and browser evidence

`cp3c-knowledge-lookup-editor.png` shows the 1680 by 960 normal workflow route
after entering a prompt for company standards, bolt sizes, and prior designs,
then selecting **Workspace documents** and **Connected knowledge**.

The bounded browser check confirmed:

- two source scopes were selected;
- the canvas status was `Draft · retrieval not run`;
- no result was presented as if retrieval had occurred;
- `RAG` did not appear in the user-facing editor; and
- no page or console errors were reported.

## Verification

Focused model, component, and route suite:

```text
Test Files  3 passed (3)
Tests       6 passed (6)
Duration    4.91s
```

Complete isolated prototype suite:

```text
Test Files  19 passed (19)
Tests       51 passed (51)
Duration    16.02s
```

Focused ESLint passed with no findings.

Production build:

```text
TypeScript build: passed
Vite build:       passed in 2.66s
Prototype chunk:  241.07 kB / 75.12 kB gzip
```

The existing Vite native-config and application-wide chunk warnings remain
informational baseline warnings.

## Human review script

1. Refresh `/prototype/engineering-workflow`.
2. Confirm the Inputs palette says **Knowledge lookup**, not **Company
   context**.
3. Select **C. Knowledge Lookup** and confirm the empty state explains both
   required decisions.
4. Enter any lookup prompt, such as finding standards, common component sizes,
   regulations, prior products, or reference research.
5. Confirm the prompt is marked as not applied until **Apply lookup prompt** is
   selected.
6. Apply it and confirm the UI asks for a source scope.
7. Select two source scopes and confirm the block becomes a configured draft
   while still saying retrieval has not run.
8. Use Undo and Redo to remove and restore the last source selection.
9. Confirm **Retrieved context** remains empty and describes the future cited
   output.
10. Open Evidence and confirm prompt characters, source count, session-only
    status, no persistence, and no execution.

Review questions:

- Is **Knowledge Lookup** the right engineer-facing term?
- Is a dedicated lookup prompt clearer than inheriting the Design Input prompt
  automatically?
- Are the three source scopes understandable and sufficiently generic?
- Should source selection eventually show exact connected repositories or
  systems beneath these broad scopes?
- What must every retrieved item display: passage, document title, revision,
  URL, effective date, confidence, or permission boundary?

## Known exclusions and next decision

This is not a retrieval implementation. It does not prove source discovery,
query rewriting, result quality, citations, permission enforcement, context
limits, or use by a downstream LLM.

The immediate review decision is `continue`, `change`, `stop`, or `defer` for
the Knowledge Lookup interaction. A later execution slice should remain
generic and should be evaluated separately from this user-language decision.
