import type { WorkflowDraft } from "../../services/workflow-drafts";

export type DraftPhase = WorkflowDraft["semantic"]["phases"][number];
export type DraftBlock = WorkflowDraft["semantic"]["blocks"][number];
export type DraftPort = WorkflowDraft["semantic"]["ports"][number];
export type DraftConnection = WorkflowDraft["semantic"]["connections"][number];
export type DraftGate = WorkflowDraft["semantic"]["gates"][number];
export type DraftFeedbackPath = WorkflowDraft["semantic"]["feedback_paths"][number];
export type DraftArtifact = WorkflowDraft["semantic"]["intended_artifacts"][number];
export type DraftPosition = WorkflowDraft["layout"]["positions"][number];

export type DraftSemanticKind =
  | "phase"
  | "block"
  | "port"
  | "connection"
  | "gate"
  | "feedback_path"
  | "intended_artifact";

export interface DraftSemanticReference {
  readonly semanticId: string;
  readonly kind: DraftSemanticKind;
}

export function draftSemanticReferences(
  draft: WorkflowDraft,
): readonly DraftSemanticReference[] {
  return [
    ...draft.semantic.phases.map((item) => ({ semanticId: item.id, kind: "phase" as const })),
    ...draft.semantic.blocks.map((item) => ({ semanticId: item.id, kind: "block" as const })),
    ...draft.semantic.ports.map((item) => ({ semanticId: item.id, kind: "port" as const })),
    ...draft.semantic.connections.map((item) => ({ semanticId: item.id, kind: "connection" as const })),
    ...draft.semantic.gates.map((item) => ({ semanticId: item.id, kind: "gate" as const })),
    ...draft.semantic.feedback_paths.map((item) => ({ semanticId: item.id, kind: "feedback_path" as const })),
    ...draft.semantic.intended_artifacts.map((item) => ({ semanticId: item.id, kind: "intended_artifact" as const })),
  ];
}

export function requireUniqueSemanticIds(ids: readonly string[]): readonly string[] {
  const unique = new Set(ids);
  if (unique.size !== ids.length) {
    throw new Error("WORKFLOW_DRAFT_SEMANTIC_ID_DUPLICATE");
  }
  return Object.freeze([...ids].sort());
}
