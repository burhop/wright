import {
  blockDimensions,
  type WorkflowPreview,
  type WorkflowPreviewBlock,
  type WorkflowPreviewConnection,
  type WorkflowPreviewPhase,
} from "../workflow-preview-model";

export const DEFAULT_CANVAS_WIDTH = 1360;
export const DEFAULT_PHASE_GAP = 10;

export type CanvasCandidateId = "react-flow" | "rete" | "litegraph";

export interface CanvasPoint {
  x: number;
  y: number;
}

export interface CanvasSize {
  width: number;
  height: number;
}

export interface CanvasPhaseProjection {
  phase: WorkflowPreviewPhase;
  position: CanvasPoint;
  size: CanvasSize;
}

export interface CanvasBlockProjection {
  block: WorkflowPreviewBlock;
  phaseId: string;
  relativePosition: CanvasPoint;
  absolutePosition: CanvasPoint;
  size: CanvasSize;
}

export interface CanvasConnectionProjection {
  connection: WorkflowPreviewConnection;
  sourceBlockId: string;
  targetBlockId: string;
}

export interface CanvasProjection {
  workflowId: string;
  revision: number;
  size: CanvasSize;
  phases: CanvasPhaseProjection[];
  blocks: CanvasBlockProjection[];
  connections: CanvasConnectionProjection[];
}

export interface CanvasProjectionOptions {
  width?: number;
  phaseGap?: number;
}

export type CanvasIntent =
  | { type: "selectBlock"; blockId: string }
  | { type: "openBlock"; blockId: string }
  | { type: "viewChanged"; viewport: CanvasViewport };

export interface CanvasViewport {
  x: number;
  y: number;
  zoom: number;
}

/**
 * Projects the Wright-owned preview model into neutral canvas coordinates.
 * Candidate packages receive this projection and never become the source of
 * workflow identity, semantics, or persistence.
 */
export function projectWorkflowToCanvas(
  workflow: WorkflowPreview,
  options: CanvasProjectionOptions = {},
): CanvasProjection {
  const width = options.width ?? DEFAULT_CANVAS_WIDTH;
  const phaseGap = options.phaseGap ?? DEFAULT_PHASE_GAP;
  const phaseOffsets = new Map<string, number>();
  let nextPhaseY = 0;

  const phases = workflow.phases.map((phase) => {
    const position = { x: 0, y: nextPhaseY };
    phaseOffsets.set(phase.phaseId, nextPhaseY);
    nextPhaseY += phase.height + phaseGap;

    return {
      phase,
      position,
      size: { width, height: phase.height },
    } satisfies CanvasPhaseProjection;
  });

  const blocks = workflow.blocks.map((block) => {
    const phaseY = phaseOffsets.get(block.phaseId);
    if (phaseY === undefined) {
      throw new Error(
        `Block ${block.blockId} references unknown phase ${block.phaseId}.`,
      );
    }

    return {
      block,
      phaseId: block.phaseId,
      relativePosition: { x: block.position.x, y: block.position.y },
      absolutePosition: {
        x: block.position.x,
        y: phaseY + block.position.y,
      },
      size: blockDimensions(block),
    } satisfies CanvasBlockProjection;
  });

  const knownBlocks = new Set(blocks.map(({ block }) => block.blockId));
  const connections = workflow.connections.map((connection) => {
    if (
      !knownBlocks.has(connection.sourceBlockId) ||
      !knownBlocks.has(connection.targetBlockId)
    ) {
      throw new Error(
        `Connection ${connection.connectionId} references an unknown block.`,
      );
    }

    return {
      connection,
      sourceBlockId: connection.sourceBlockId,
      targetBlockId: connection.targetBlockId,
    } satisfies CanvasConnectionProjection;
  });

  return {
    workflowId: workflow.workflowId,
    revision: workflow.revision,
    size: {
      width,
      height: Math.max(0, nextPhaseY - phaseGap),
    },
    phases,
    blocks,
    connections,
  };
}
