import { hydrateAuthoringLayout } from "./authoring-positioning";
import source from "../../../../../prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow?raw";
import { expect, it } from "vitest";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  parseRecoverySourceDocument,
} from "./recovery-authoring";

it("opens the actual desktop handle draft and preserves its evidence and review connections on save", () => {
  const parsed = parseRecoverySourceDocument(source, 1);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const workflow = parsed.workflow!;
  expect(
    workflow.blocks.some(
      (block) => block.title === "Review the proposed print package",
    ),
  ).toBe(true);
  const formatted = formatRecoveryAuthoringSource(workflow);
  const reopened = parseRecoveryAuthoringSource(formatted.text, workflow);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(reopened.workflow!.relationships).toEqual(workflow.relationships);
  expect(reopened.workflow!.ports).toEqual(workflow.ports);
  expect(reopened.workflow!.blocks.map((block) => block.configuration)).toEqual(
    workflow.blocks.map((block) => block.configuration),
  );
});

it("places the handle stages in forward dependency order without changing source or saved moves", () => {
  const parsed = parseRecoverySourceDocument(source, 1);
  expect(parsed.ok).toBe(true);
  const workflow = parsed.workflow!;
  const before = JSON.stringify(workflow);
  const layout = hydrateAuthoringLayout(workflow);
  const owners = new Map(
    workflow.ports.map((port) => [port.id, port.ownerBlockId]),
  );
  let checked = 0;
  for (const edge of workflow.relationships) {
    if (edge.kind === "feedback") continue;
    const from = layout.positions[owners.get(edge.sourceId) ?? edge.sourceId];
    const to = layout.positions[owners.get(edge.targetId) ?? edge.targetId];
    if (!from || !to || from === to) continue;
    expect(from.x, edge.id).toBeLessThan(to.x);
    checked++;
  }
  expect(checked).toBeGreaterThan(30);
  expect(JSON.stringify(workflow)).toBe(before);
  const id = workflow.blocks[0].id;
  layout.positions[id] = { x: 987, y: 654 };
  expect(hydrateAuthoringLayout(workflow, layout)).toEqual(layout);
});

it("keeps cyclic or disconnected drafts inspectable and preserves their connections", () => {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const [first, second] = workflow.blocks;
  workflow.relationships = [
    {
      ...workflow.relationships[0],
      id: "cycle-a",
      kind: "control",
      sourceId: first.id,
      targetId: second.id,
    },
    {
      ...workflow.relationships[0],
      id: "cycle-b",
      kind: "control",
      sourceId: second.id,
      targetId: first.id,
    },
  ];
  const before = JSON.stringify(workflow);
  const layout = hydrateAuthoringLayout(workflow);
  expect(Object.keys(layout.positions)).toHaveLength(workflow.blocks.length);
  expect(
    new Set(Object.values(layout.positions).map((p) => `${p.x},${p.y}`)).size,
  ).toBe(workflow.blocks.length);
  expect(JSON.stringify(workflow)).toBe(before);
});
