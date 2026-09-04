# Wright-native authoring: decision package

This is the corrected planning direction, not an implementation or an accepted architecture decision.

1. Review [the proposed ADR](proposed-adr.md) for architecture, persistence, migration, and approval boundaries.
2. Review [the feature specification](spec.md) for user-visible scope and acceptance criteria.
3. Check [requirements quality and remaining approval gates](checklists/requirements.md).

## Visual target

The two existing images remain unchanged under `artifacts/ui-redesign/`. The selected target is [the object-palette version](../../artifacts/ui-redesign/wright-workflow-editor-object-palette-v2.png). Its Run/Ask AI and successful-run labels describe a later integrated product, not functionality or evidence claimed by the proposed first slice.

The intended structure is a dominant native graph, compact Create rail, exact per-port endpoints, input configuration on source steps, one contextual Inspector, and a complete readable-text view. No embedded Rivet UI is part of the target.

## Research used, not promoted wholesale

- The repository's frozen prototype bakeoff and port/composition research at `076-engineering-workflow-prototype` / `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d` support testing a replaceable React Flow adapter. They do not supply production code or accepted authoring studies.
- React Flow supports uniquely identified handles and explicit source/target handle references, which can project Wright's exact port IDs without making renderer state canonical. [Official handles documentation](https://reactflow.dev/learn/customization/handles).
- Its keyboard/focus facilities are useful starting points, not proof that custom Wright nodes are accessible. [Official accessibility documentation](https://reactflow.dev/learn/advanced-use/accessibility).
- The Create rail needs named controls and predictable focus/navigation. [W3C toolbar pattern](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/).
- Drag interactions need non-drag pointer alternatives as well as keyboard support. [W3C dragging-movement guidance](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).

## Current handoff

Spec Kit's specification work is complete as a proposal. The planning skill's architecture-approval gate prevents treating this as an implementation-ready plan: first obtain the bounded ADR/scope decision, then produce the schema/command/storage contracts, preregistered protocol, implementation plan, tasks, and independent consistency review. Product code and dependency installation remain out of scope until their exact subject is approved.

The rejected 081 work remains only in the named recovery stashes. Do not apply it, cite its passing tests as evidence here, or use its plan as authority. No commit, push, merge, release, or program-state transition is authorized by this package.
