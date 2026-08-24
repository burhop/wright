# Contract: Canvas Adapter

## Responsibilities

A candidate adapter may:

- project phases, blocks, ports, connections, selection, and layout hints;
- translate pointer/keyboard gestures into Wright workflow or view commands;
- control viewport, focus, and transient candidate state;
- report measured render/interaction diagnostics for the bakeoff.

It may not:

- persist candidate-native node/edge/project JSON;
- validate or execute workflows;
- call LLM or MCP adapters;
- implement approvals or domain logic;
- mutate the canonical model;
- assign semantic IDs without going through a Wright command factory.

## Common harness

Each candidate is mounted in the same page frame with:

- the same frozen reference workflow;
- the same viewport dimensions and Wright tokens;
- the same selection/detail panel;
- the same read-only interaction script for the initial bakeoff;
- the same accessibility and screenshot checks;
- 25-block and 100-block generated fixtures.

Candidate-specific CSS or glue is isolated under that candidate's harness. Shared product components cannot import a candidate package directly.

## Event boundary

```ts
type CanvasIntent =
  | { type: "selectBlock"; blockId: string }
  | { type: "moveBlock"; blockId: string; phaseId: string; position: Point }
  | { type: "connectPorts"; source: PortRef; target: PortRef }
  | { type: "deleteSelection"; ids: string[] }
  | { type: "openBlock"; blockId: string }
  | { type: "viewChanged"; viewport: Viewport };
```

Semantic intents pass through validation/reducer commands. View-only intents use a separate view-state store and do not increment workflow revision.

## Exit requirement

Removing a rejected candidate must require deleting its harness/import/dependency only. No workflow fixture, domain test, LLM contract, MCP contract, or saved workflow may change.
