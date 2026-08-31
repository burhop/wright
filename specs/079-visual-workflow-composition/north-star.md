# Visual North Star

## Customer promise

Wright should feel like an engineering process workspace, not a generic node editor. An engineer sees a compact staged workflow, understands what each step consumes and intends to produce, changes it safely, and can always compare the diagram with an engineer-readable semantic view.

The frozen prototype image at commit `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d` supplies direction only. The deployed EPP-F02 walkthrough at `artifacts/ui-walkthrough/process-definition-deployed/20260831T150433Z-continuation-2/` supplies the read-only compatibility baseline.

## Representative slice

The acceptance canvas contains exactly four blocks:

1. Capture requirements
2. Define product
3. Review product definition
4. Release product definition

They occupy named ordered phases, connect through explicitly typed left-input/right-output ports, declare intended artifacts near their producers, and include one approval gate with a labeled revision feedback path. Diagram and text expose the same semantic identities.

## Desktop composition grammar

- **Left**: a bounded block palette for this slice, plus clear create controls. It is not a capability marketplace.
- **Center**: numbered/name-labeled phase lanes, compact blocks, typed ports, directional connections, a visually distinct gate, labeled dashed feedback, zoom/fit controls, and an optional minimap only if it remains readable.
- **Right**: a persistent inspector with Definition, Ports & relationships, and Validation sections. It always shows stable ID, draft revision, phase, role, purpose, typed ports, relationships, intended artifacts, and current diagnostics.
- **Top**: unmistakable “Working draft” authority, draft revision, validation state, Save, Close, and Diagram/Text controls. No Run, Publish, Release, MCP, or AI action.

## Visual rules

- Preserve Wright's dark shell and token system.
- Use role colors only as supplemental cues: blue for input/data, purple for authored work, teal for tool-shaped future concepts only when actually in scope, green for intended artifacts, amber for gates, and red dashed lines for revise feedback.
- Every color meaning also has a label, icon, shape, line treatment, or text.
- Blocks show stable short identity, title, purpose, phase, and authoring/validation state; they do not show run badges.
- Ports show stable identity, direction, short name, exact `value_type_id`, requiredness, and cardinality. Connection targets and artifact inspection are distinct.
- Gates are declarations with explicit condition and proceed/revise targets, not executable work blocks or recorded approvals.
- Intended artifacts state expectation and producer; they never imply a file exists.
- Feedback paths remain visible and labeled even when they cross a focused/hidden phase; text/properties always preserve the relationship.

## Interaction rules

- Primary actions use stable verbs: Add block, Connect, Edit, Delete, Validate, Save, Close, Reopen.
- Selection identity is shared across canvas, text, and inspector.
- Invalid gestures do not replace the last valid draft. Diagnostics name affected identities, explain the rule, and give one bounded correction direction.
- Keyboard users can create, select, move, connect, edit, delete, validate, save, close, reopen, and inspect with visible focus.
- At 390 CSS pixels and 200% zoom, inspection, text, diagnostics, and recovery remain reachable without document-level horizontal overflow. Full drag authoring may state its desktop limitation.
- Renderer failure yields an honest diagnostic and complete text/properties fallback.

## Drift guard

At Checkpoints C, D, and E, compare the current evidence to this file and [prototype-parity.md](prototype-parity.md). Any material change is recorded as retain, revise, reject, or defer with a reason before it becomes accepted behavior.

## Explicit non-goals

No Rivet, workflow execution, AI authoring, MCP discovery/binding, run monitoring, output downloads, capability catalog, detached artifact rail, generic plugin system, benchmark qualification, release/publish flow, or 100-block usability claim.

