# CP3B Design Input vertical slice

Date: 2026-08-25
Branch: `076-engineering-workflow-prototype`

## Hypothesis

An engineer-facing Design Input block can accept concise instructions and
longer readable documents through one understandable interaction without
starting generalized workflow editing, persistence, document parsing, LLM
execution, or MCP execution.

## Implemented increment

The **Design Input** block now supports a session-only editing loop:

- start with an explicit `No design input` state;
- enter a direct prompt and apply the full edit as one reversible command;
- attach one or more text, Markdown, PDF, Word, CSV, JSON, YAML, XML, or RTF
  documents;
- show a bounded local preview for text-readable formats;
- show PDF and Word files as attached metadata with parsing clearly deferred;
- remove attached documents;
- undo and redo prompt and document changes;
- project prompt/document counts and draft status onto the canvas block;
- disclose `Local CP3B draft · session only` and `not persisted` in Evidence;
- reset the draft when the browser page reloads.

The UI is product-independent. It does not assume a drill holder, CAD, FEA,
or any other specific product or engineering category.

## Architecture boundary

`domain/design-input-draft.ts` owns the prompt, attached-document metadata,
typed commands, immutable snapshots, and undo/redo history. The React
component reads uploaded text through `FileReader` only to create a bounded
review preview, then dispatches a typed document-batch command. React Flow
receives a Wright-owned visual projection and does not own edit state.

This increment adds no browser storage, workspace write, backend upload,
production schema, document extraction service, LLM call, MCP execution,
tool-name dispatch, or candidate-native persistence. Reusable documents should
eventually be chosen from a governed Wright workspace or template library;
they should not require repeated local uploads.

## Visual and browser evidence

`cp3b-design-input-editor.png` shows the 1680 by 960 normal workflow route
after selecting **Design Input**, applying a 119-character generic prompt, and
attaching two repository-owned Markdown documents.

The bounded browser check confirmed:

- the prompt reached the applied state;
- both documents appeared in the attached-document list;
- the normal product workflow was used rather than a scale fixture; and
- no page or console errors were reported.

## Verification

Focused model, component, and route suite:

```text
Test Files  3 passed (3)
Tests       6 passed (6)
Duration    4.28s
```

Complete isolated prototype suite:

```text
Test Files  17 passed (17)
Tests       46 passed (46)
Duration    9.96s
```

Focused ESLint passed with no findings.

Production build:

```text
TypeScript build: passed
Vite build:       passed in 2.40s
Prototype chunk:  235.39 kB / 73.62 kB gzip
```

The existing Vite native-config and application-wide chunk warnings remain
informational baseline warnings.

## Human review script

1. Refresh `/prototype/engineering-workflow`.
2. Select **B. Design Input** and confirm the empty state is unambiguous.
3. Enter a concise prompt describing any product, goal, constraints, and
   priorities.
4. Confirm the prompt is visibly marked as not applied until **Apply prompt**
   is selected.
5. Apply the prompt and confirm the canvas block changes from `EMPTY` to
   `PROMPT` with session-only draft status.
6. Attach one Markdown or text file and one PDF or Word file.
7. Confirm the text document has a bounded preview while the PDF or Word file
   states that parsing is deferred.
8. Remove one document, then use Undo and Redo.
9. Open Evidence and confirm prompt characters, document count, session-only
   status, and no persistence.
10. Refresh and confirm the prompt and documents are cleared.

Review questions:

- Is **Apply prompt** clearer than saving every keystroke automatically?
- Is prompt plus attached documents the expected minimum input model?
- Are file types and deferred parsing limits understandable?
- Should document order, title, source, confidentiality, or reuse policy be
  editable before persistence is added?
- Should the next persistence prototype introduce workspace selection first,
  or downstream AI consumption of this session-only draft first?

## Known exclusions and next decision

This is not generalized graph editing. It does not parse PDF or Word content,
persist files, reuse workspace documents, generate a specification, call an
LLM, or invoke an MCP tool.

The immediate review decision is `continue`, `change`, `stop`, or `defer` for
the Design Input interaction. The next increment should be chosen only after
this UI review; it should remain bounded to one end-to-end behavior.
