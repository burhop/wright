import {
  cloneLayout,
  initialLayout,
  recoveryAuthoringSectionKind,
  type RecoveryLayout,
  type RecoveryWorkflow,
} from "./model";

export interface AuthoringPoint {
  x: number;
  y: number;
}

/** Presentation-only placement. Never changes semantic order or identities. */
export function findAuthoringPosition(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  preferred: AuthoringPoint = { x: 380, y: 100 },
  candidateHeight = 168,
): AuthoringPoint {
  const origin = {
    x: Number.isFinite(preferred.x) ? Math.round(preferred.x) : 380,
    y: Number.isFinite(preferred.y) ? Math.round(preferred.y) : 100,
  };
  const occupied = workflow.blocks.flatMap((block) => {
    const position = layout.positions[block.id];
    return position
      ? [
          {
            ...position,
            height: Math.max(
              168,
              100 +
                Math.max(
                  block.inputPortIds.length,
                  block.outputPortIds.length,
                ) *
                  28,
            ),
          },
        ]
      : [];
  });
  // Each column has ten source/step slots; wide graphs remain navigable rather
  // than creating an arbitrarily tall stack from repeated Add operations.
  for (let index = 0; index <= occupied.length * 12 + 100; index += 1) {
    const candidate = {
      x: origin.x + Math.floor(index / 10) * 320,
      y: origin.y + (index % 10) * 220,
    };
    if (
      !occupied.some(
        (position) =>
          candidate.x < position.x + 292 &&
          candidate.x + 292 > position.x &&
          candidate.y < position.y + position.height + 32 &&
          candidate.y + candidateHeight + 32 > position.y,
      )
    )
      return candidate;
  }
  return {
    x: Math.max(origin.x, ...occupied.map((position) => position.x + 320)),
    y: origin.y,
  };
}

/** Place inserted work near its known inputs without rearranging saved nodes. */
export function findInsertedAuthoringPosition(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  blockId: string,
): AuthoringPoint {
  const owners = new Map(
    workflow.ports.map((port) => [port.id, port.ownerBlockId]),
  );
  const predecessors = workflow.relationships
    .filter(
      (edge) =>
        edge.kind !== "feedback" &&
        (owners.get(edge.targetId) ?? edge.targetId) === blockId,
    )
    .map((edge) => owners.get(edge.sourceId) ?? edge.sourceId)
    .filter((id) => id !== blockId)
    .flatMap((id) => (layout.positions[id] ? [layout.positions[id]] : []));
  const nearest = predecessors.reduce<AuthoringPoint | undefined>(
    (rightmost, point) =>
      !rightmost || point.x > rightmost.x ? point : rightmost,
    undefined,
  );
  const block = workflow.blocks.find((item) => item.id === blockId);
  return findAuthoringPosition(
    workflow,
    layout,
    nearest
      ? { x: nearest.x + 340, y: nearest.y }
      : {
          x:
            block && recoveryAuthoringSectionKind(block) === "input" ? 40 : 380,
          y: 100,
        },
    block
      ? Math.max(
          168,
          100 +
            Math.max(block.inputPortIds.length, block.outputPortIds.length) *
              28,
        )
      : 168,
  );
}

/** Initial presentation follows forward dependencies; it grants no execution order. */
function initialDependencyPositions(
  workflow: RecoveryWorkflow,
): RecoveryLayout["positions"] {
  const blocks = new Map(workflow.blocks.map((block) => [block.id, block]));
  const owners = new Map(
    workflow.ports.map((port) => [port.id, port.ownerBlockId]),
  );
  const successors = new Map(
    workflow.blocks.map((block) => [block.id, new Set<string>()]),
  );
  const pending = new Map(workflow.blocks.map((block) => [block.id, 0]));
  const layers = new Map(workflow.blocks.map((block) => [block.id, 0]));
  for (const edge of workflow.relationships) {
    if (edge.kind === "feedback") continue;
    const source = owners.get(edge.sourceId) ?? edge.sourceId;
    const target = owners.get(edge.targetId) ?? edge.targetId;
    if (!blocks.has(source) || !blocks.has(target) || source === target)
      continue;
    const next = successors.get(source)!;
    if (next.has(target)) continue;
    next.add(target);
    pending.set(target, pending.get(target)! + 1);
  }
  const ready = workflow.blocks
    .filter((block) => pending.get(block.id) === 0)
    .map((block) => block.id);
  const visited = new Set<string>();
  for (let index = 0; index < ready.length; index += 1) {
    const source = ready[index];
    visited.add(source);
    for (const target of successors.get(source)!) {
      layers.set(
        target,
        Math.max(layers.get(target)!, layers.get(source)! + 1),
      );
      pending.set(target, pending.get(target)! - 1);
      if (pending.get(target) === 0) ready.push(target);
    }
  }
  // Invalid/cyclic source still needs an inspectable diagram. Validation remains
  // the existing validator's responsibility, and no semantic edge is removed.
  const unresolvedLayer = Math.max(0, ...layers.values()) + 1;
  const nextY = new Map<number, number>();
  const positions: RecoveryLayout["positions"] = {};
  for (const block of workflow.blocks) {
    const layer = visited.has(block.id)
      ? layers.get(block.id)!
      : unresolvedLayer;
    const y = nextY.get(layer) ?? 100;
    positions[block.id] = { x: 40 + layer * 340, y };
    const height = Math.max(
      168,
      100 +
        Math.max(block.inputPortIds.length, block.outputPortIds.length) * 28,
    );
    nextY.set(layer, y + height + 60);
  }
  return positions;
}

/** Rebind safe saved presentation state and fill missing nodes deterministically. */
export function hydrateAuthoringLayout(
  workflow: RecoveryWorkflow,
  previous?: RecoveryLayout,
): RecoveryLayout {
  const seed = previous ?? initialLayout;
  const sameWorkflow = seed.workflowId === workflow.workflowId;
  // A new document made from the starter inherits its readable diagram, not
  // its identity. Explicit saved layout from another document is never reused.
  const reusablePositions =
    previous === undefined || sameWorkflow ? seed.positions : {};
  const layout = cloneLayout(seed);
  layout.documentKind = "workflow-layout";
  layout.schemaVersion = "1.0.0-recovery.1";
  layout.workflowId = workflow.workflowId;
  layout.semanticRevision = workflow.revision;
  layout.layoutRevision =
    Number.isInteger(seed.layoutRevision) && seed.layoutRevision > 0
      ? seed.layoutRevision
      : 1;
  const blockIds = new Set(workflow.blocks.map((block) => block.id));
  layout.positions = Object.fromEntries(
    Object.entries(reusablePositions).filter(
      ([id, point]) =>
        blockIds.has(id) &&
        Number.isFinite(point.x) &&
        Number.isFinite(point.y),
    ),
  );
  if (
    !sameWorkflow ||
    !Number.isFinite(layout.viewport.x) ||
    !Number.isFinite(layout.viewport.y) ||
    !Number.isFinite(layout.viewport.zoom) ||
    layout.viewport.zoom <= 0
  )
    layout.viewport = { x: 0, y: 0, zoom: 1 };
  const dependencyPositions = initialDependencyPositions(workflow);
  if (Object.keys(layout.positions).length === 0)
    layout.positions = dependencyPositions;
  for (const block of [...workflow.blocks].sort(
    (a, b) =>
      dependencyPositions[a.id].x - dependencyPositions[b.id].x ||
      dependencyPositions[a.id].y - dependencyPositions[b.id].y,
  )) {
    if (layout.positions[block.id]) continue;
    layout.positions[block.id] = findInsertedAuthoringPosition(
      workflow,
      layout,
      block.id,
    );
  }
  return layout;
}
