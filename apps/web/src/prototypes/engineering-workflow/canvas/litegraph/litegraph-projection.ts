import type {
  CanvasPoint,
  CanvasProjection,
  CanvasSize,
} from "../canvas-adapter";
import type {
  WorkflowBlockRole,
  WorkflowConnectionSemantics,
} from "../../workflow-preview-model";

export interface LiteGraphCandidateNode {
  blockId: string;
  code: string;
  title: string;
  subtitle: string;
  badge?: string;
  phaseId: string;
  role: WorkflowBlockRole;
  position: CanvasPoint;
  size: CanvasSize;
  incomingConnectionIds: string[];
}

export interface LiteGraphCandidateLink {
  connectionId: string;
  sourceBlockId: string;
  targetBlockId: string;
  targetSlot: number;
  semantics: WorkflowConnectionSemantics;
  label?: string;
}

export interface LiteGraphCandidateProjection {
  nodes: LiteGraphCandidateNode[];
  links: LiteGraphCandidateLink[];
}

/**
 * Keeps LiteGraph's required per-input-slot indexing outside the Wright model.
 * The result is a disposable render projection, never serialized workflow state.
 */
export function projectLiteGraphCandidate(
  projection: CanvasProjection,
): LiteGraphCandidateProjection {
  const incomingByBlock = new Map<string, string[]>();
  for (const { connection } of projection.connections) {
    const incoming = incomingByBlock.get(connection.targetBlockId) ?? [];
    incoming.push(connection.connectionId);
    incomingByBlock.set(connection.targetBlockId, incoming);
  }

  const nodes = projection.blocks.map(({ block, absolutePosition, size }) => ({
    blockId: block.blockId,
    code: block.sequence,
    title: block.title,
    subtitle: block.purpose,
    ...(block.badge === undefined ? {} : { badge: block.badge }),
    phaseId: block.phaseId,
    role: block.role,
    position: {
      x: absolutePosition.x,
      y: absolutePosition.y,
    },
    size: { ...size },
    incomingConnectionIds: [...(incomingByBlock.get(block.blockId) ?? [])],
  }));

  const links = projection.connections.map(({ connection }) => {
    const incoming = incomingByBlock.get(connection.targetBlockId) ?? [];
    const targetSlot = incoming.indexOf(connection.connectionId);
    if (targetSlot < 0) {
      throw new Error(
        `LiteGraph projection lost ${connection.connectionId}'s target slot.`,
      );
    }

    return {
      connectionId: connection.connectionId,
      sourceBlockId: connection.sourceBlockId,
      targetBlockId: connection.targetBlockId,
      targetSlot,
      semantics: connection.semantics,
      ...(connection.label === undefined ? {} : { label: connection.label }),
    };
  });

  return { nodes, links };
}
