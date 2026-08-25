# CP3A reference-image editing vertical slice

Date: 2026-08-25
Branch: `076-engineering-workflow-prototype`

## Hypothesis

A single engineer-facing input can prove typed local editing and undo/redo
without adopting React Flow state, enabling real file upload, or starting the
full CP3 editor.

## Implemented increment

The **Reference Images** block now supports a deterministic, session-only
editing loop:

- start with an explicit `No images selected` state;
- add one or more of three local schematic reference concepts;
- display selected thumbnails and selection count in the inspector and block;
- reorder selected images earlier or later;
- remove selected images;
- undo and redo typed changes;
- disclose `Local CP3A draft · session only` and `not persisted` in Evidence;
- reset the draft on browser reload.

The three sample images are repository-owned SVG fixtures representing an
angled drill index tray, wall-mounted rack, and folded bench stand. They are
clearly sample concepts, not actual user files or generated engineering data.

## Architecture boundary

`domain/reference-image-draft.ts` owns image identities, commands, validation,
and history. It imports no React, React Flow, storage, workspace, LLM, or MCP
code. The visual slice derives optional Wright `imagePreviews` for the selected
canvas adapter. React Flow renders that projection but never becomes the edit
or persistence model.

This increment adds no CAD/FEA services, tool-name dispatch, MCP execution,
LLM call, file upload, browser storage, workspace write, or production schema
change.

## Visual evidence

`cp3a-reference-image-editor.png` shows a fresh 1680 by 950 prototype after
selecting **Reference Images** and adding two sample concepts. The bounded
browser check reported the selected count visible and zero page/console errors.

## Focused verification

```text
Test Files  3 passed (3)
Tests       5 passed (5)
Duration    2.18s
```

The focused suite covers typed add/remove/reorder commands, undo/redo, unknown
image rejection, redo invalidation after a new edit, the complete inspector
interaction, local-only evidence, and the selected React Flow route.

Complete isolated prototype suite:

```text
Test Files  15 passed (15)
Tests       40 passed (40)
Duration    10.92s
```

Production build:

```text
TypeScript build: passed
Vite build:       passed in 2.28s
Prototype chunk:  232.67 kB / 72.78 kB gzip
```

The existing Vite native-config and application-wide chunk warnings remain
informational baseline warnings.

## Human review script

1. Refresh `/prototype/engineering-workflow`.
2. Select **A. Reference Images** and confirm the empty state is unambiguous.
3. Add **Angled drill index tray** and **Wall-mounted bit rack**.
4. Confirm thumbnails/counts appear in both inspector and canvas block.
5. Move the wall rack earlier, remove the tray, then use Undo and Redo.
6. Open Evidence and confirm the draft is explicitly session-only and not
   persisted.
7. Refresh and confirm the sample selection resets.

Review questions:

- Is this a credible first interaction for a mechanical engineer?
- Are add, reorder, remove, Undo, and Redo discoverable without coaching?
- Should real input support upload, workspace selection, drag-and-drop, camera,
  clipboard, or all of those?
- Which image metadata is essential: caption, source, primary image, notes,
  scale/reference dimensions, confidentiality, or something else?

## Known exclusions and next decision

This is not the complete CP3 command/reducer model. It proves the editing seam
on one block before generalizing commands to phases, blocks, ports, and
connections. Real file selection also requires an explicit artifact/storage
decision and should not be inferred from this local sample picker.

The review decision is `continue`, `change`, `stop`, or `defer`. If accepted,
the next CP3 increment should generalize the command/history contract and add a
second structurally different edit rather than immediately integrating upload,
LLM, or MCP execution.
