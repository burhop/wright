import { cloneLayout, initialLayout, recoveryAuthoringSectionKind, type RecoveryLayout, type RecoveryWorkflow } from "./model";

export interface AuthoringPoint { x: number; y: number }

/** Presentation-only placement. Never changes semantic order or identities. */
export function findAuthoringPosition(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  preferred: AuthoringPoint = { x: 380, y: 100 },
): AuthoringPoint {
  const origin = {
    x: Number.isFinite(preferred.x) ? Math.round(preferred.x) : 380,
    y: Number.isFinite(preferred.y) ? Math.round(preferred.y) : 100,
  };
  const occupied = workflow.blocks.flatMap((block) => {
    const position = layout.positions[block.id];
    return position ? [{ ...position, height: Math.max(168, 100 + Math.max(block.inputPortIds.length, block.outputPortIds.length) * 28) }] : [];
  });
  // Each column has ten source/step slots; wide graphs remain navigable rather
  // than creating an arbitrarily tall stack from repeated Add operations.
  for (let index = 0; index <= occupied.length * 12 + 100; index += 1) {
    const candidate = { x: origin.x + Math.floor(index / 10) * 320, y: origin.y + (index % 10) * 220 };
    if (!occupied.some((position) => candidate.x < position.x + 292 && candidate.x + 292 > position.x && candidate.y < position.y + position.height + 32 && candidate.y + 200 > position.y)) return candidate;
  }
  return { x: Math.max(origin.x, ...occupied.map((position) => position.x + 320)), y: origin.y };
}

/** Rebind safe saved presentation state and fill missing nodes deterministically. */
export function hydrateAuthoringLayout(workflow: RecoveryWorkflow, previous?: RecoveryLayout): RecoveryLayout {
  const seed = previous ?? initialLayout;
  const sameWorkflow = seed.workflowId === workflow.workflowId;
  // A new document made from the starter inherits its readable diagram, not
  // its identity. Explicit saved layout from another document is never reused.
  const reusablePositions = previous === undefined || sameWorkflow ? seed.positions : {};
  const layout = cloneLayout(seed);
  layout.documentKind = "workflow-layout";
  layout.schemaVersion = "1.0.0-recovery.1";
  layout.workflowId = workflow.workflowId;
  layout.semanticRevision = workflow.revision;
  layout.layoutRevision = Number.isInteger(seed.layoutRevision) && seed.layoutRevision > 0 ? seed.layoutRevision : 1;
  const blockIds = new Set(workflow.blocks.map((block) => block.id));
  layout.positions = Object.fromEntries(Object.entries(reusablePositions).filter(([id, point]) => blockIds.has(id) && Number.isFinite(point.x) && Number.isFinite(point.y)));
  if (!sameWorkflow || !Number.isFinite(layout.viewport.x) || !Number.isFinite(layout.viewport.y) || !Number.isFinite(layout.viewport.zoom) || layout.viewport.zoom <= 0) layout.viewport = { x: 0, y: 0, zoom: 1 };
  for (const block of workflow.blocks) {
    if (layout.positions[block.id]) continue;
    layout.positions[block.id] = findAuthoringPosition(workflow, layout, { x: recoveryAuthoringSectionKind(block) === "input" ? 40 : 380, y: 100 });
  }
  return layout;
}
