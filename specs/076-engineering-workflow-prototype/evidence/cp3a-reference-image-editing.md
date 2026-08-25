# CP3A reference-image upload vertical slice

Date: 2026-08-25
Branch: `076-engineering-workflow-prototype`

## Hypothesis

A generic engineer-facing image input can prove real local file selection,
reviewable previews, typed editing, and undo/redo without adopting React Flow
state or starting persistence, LLM, MCP, or the complete CP3 editor.

## Implemented increment

The **Reference Images** block now supports a session-only multi-file upload
loop:

- start with an explicit `No images selected` state;
- choose one or more arbitrary local files through an `image/*` file picker;
- automatically attach every selected image to the block;
- display file-name, media-type, size, thumbnail, and selection count;
- reorder selected images earlier or later;
- remove selected images;
- undo and redo typed changes;
- disclose `Local CP3A draft · session only` and `not persisted` in Evidence;
- reset uploaded image data when the browser page reloads.

The former drill-index sample picker and its three drill-specific SVG assets
were removed. No predefined image category, product type, or engineering test
is encoded in the user interface.

## Architecture boundary

`domain/reference-image-draft.ts` still owns image identities, typed commands,
validation, and history. A small UI draft reducer adds transient file metadata
and FileReader data-URL previews, then applies the same typed add command for
each uploaded file. React Flow receives optional Wright `imagePreviews` and
never owns edit or persistence state.

This increment adds no browser storage, workspace write, backend upload,
production schema, LLM call, MCP execution, CAD/FEA service, tool-name
dispatch, or candidate-native persistence. Data URLs are deliberately
session-only prototype state.

## Visual evidence

`cp3a-reference-image-editor.png` shows a fresh 1680 by 950 prototype after
selecting **Reference Images** and uploading two unrelated repository-owned
images. The bounded browser check confirmed the selected count and upload
control were visible with zero page or console errors.

## Focused verification

```text
Test Files  3 passed (3)
Tests       6 passed (6)
Duration    2.64s
```

The focused suite covers arbitrary multi-file upload, automatic attachment,
file previews, add/remove/reorder commands, undo/redo, unknown-ID rejection,
redo invalidation, session-only evidence, absence of predefined product
choices, and the selected React Flow route.

Complete isolated prototype suite:

```text
Test Files  15 passed (15)
Tests       41 passed (41)
Duration    8.60s
```

Production build:

```text
TypeScript build: passed
Vite build:       passed in 2.32s
Prototype chunk:  228.48 kB / 72.06 kB gzip
```

The existing Vite native-config and application-wide chunk warnings remain
informational baseline warnings.

## Human review script

1. Refresh `/prototype/engineering-workflow`.
2. Select **A. Reference Images** and confirm the empty state is unambiguous.
3. Choose **Upload images** and select two unrelated photos or image files.
4. Confirm both files appear in the inspector and as thumbnails/counts on the
   canvas block.
5. Move the second image earlier, remove one image, then use Undo and Redo.
6. Add another image with **Add more images**.
7. Open Evidence and confirm the draft is session-only and not persisted.
8. Refresh and confirm the uploaded images are cleared.

Review questions:

- Is multi-file upload the expected primary action?
- Are reorder, remove, Undo, and Redo discoverable without coaching?
- Should production input also support workspace selection, drag-and-drop,
  camera capture, clipboard paste, or external document systems?
- Which metadata is essential: caption, source, primary image, notes, scale,
  reference dimensions, confidentiality, or something else?

## Recorded next slice: Design Input

Product review clarified that **Design Input** should accept both:

- a direct prompt for concise, one-off instructions; and
- one or more readable documents for long or reusable text.

This should be a separate CP3 editing checkpoint. The first prototype can keep
the prompt and attached documents session-only. Long-term reusable documents
should be selected from a Wright workspace or template library, and document
parsing should use a generic ingestion boundary rather than block-specific
file-format logic.

## Known exclusions and next decision

This is not the complete CP3 command/reducer model. Real persistence, artifact
governance, upload limits, malware scanning, image metadata, workspace reuse,
and downstream execution remain outside this checkpoint.

The immediate review decision is `continue`, `change`, `stop`, or `defer` for
the image-upload interaction. After that review, the next bounded increment is
the Design Input prompt/document editor rather than generalized execution, LLM,
or MCP integration.
