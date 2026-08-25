export type WorkflowPhaseTone = "define" | "verify" | "manufacture";

export type WorkflowBlockRole =
  "input" | "ai-task" | "mcp-action" | "artifact" | "decision" | "notification";

export type WorkflowConnectionSemantics = "data" | "control" | "feedback";

export interface WorkflowBlockPosition {
  x: number;
  y: number;
  width?: number;
  height?: number;
}

export interface WorkflowInspectorField {
  label: string;
  value: string;
}

export interface WorkflowBlockImagePreview {
  imageId: string;
  title: string;
  alt: string;
  thumbnailUrl: string;
}

export interface WorkflowReferenceImageOption extends WorkflowBlockImagePreview {
  description: string;
}

export interface WorkflowPreviewBlock {
  blockId: string;
  phaseId: string;
  sequence: string;
  role: WorkflowBlockRole;
  title: string;
  purpose: string;
  badge?: string;
  status?: string;
  imagePreviews?: WorkflowBlockImagePreview[];
  position: WorkflowBlockPosition;
  inspector?: {
    summary: string;
    fields: WorkflowInspectorField[];
  };
}

export interface WorkflowPreviewConnection {
  connectionId: string;
  sourceBlockId: string;
  targetBlockId: string;
  semantics: WorkflowConnectionSemantics;
  label?: string;
}

export interface WorkflowPreviewPhase {
  phaseId: string;
  index: number;
  label: string;
  description: string;
  tone: WorkflowPhaseTone;
  height: number;
}

export interface WorkflowPreview {
  schemaVersion: "0.1-visual-slice";
  workflowId: string;
  revision: number;
  title: string;
  purpose: string;
  phases: WorkflowPreviewPhase[];
  blocks: WorkflowPreviewBlock[];
  connections: WorkflowPreviewConnection[];
}

export const DEFAULT_BLOCK_WIDTH = 148;
export const DEFAULT_BLOCK_HEIGHT = 86;

export function blockDimensions(block: WorkflowPreviewBlock): {
  width: number;
  height: number;
} {
  return {
    width: block.position.width ?? DEFAULT_BLOCK_WIDTH,
    height: block.position.height ?? DEFAULT_BLOCK_HEIGHT,
  };
}
