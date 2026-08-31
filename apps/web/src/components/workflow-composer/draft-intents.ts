import type {
  DraftBlock,
} from "./draft-model";

export type DraftCanvasIntent =
  | { readonly type: "select"; readonly semanticId: string | null }
  | { readonly type: "create-block"; readonly phaseId: string; readonly role: DraftBlock["role"]; readonly x: number; readonly y: number }
  | { readonly type: "move-block"; readonly semanticId: string; readonly x: number; readonly y: number }
  | { readonly type: "edit-block"; readonly semanticId: string; readonly title: string; readonly purpose: string }
  | { readonly type: "create-connection"; readonly sourcePortId: string; readonly targetPortId: string }
  | { readonly type: "delete-connection"; readonly semanticId: string }
  | { readonly type: "create-gate"; readonly ownerBlockId: string; readonly condition: string; readonly proceedTargetBlockId: string; readonly reviseTargetBlockId: string }
  | { readonly type: "edit-gate"; readonly semanticId: string; readonly condition: string; readonly proceedTargetBlockId: string; readonly reviseTargetBlockId: string }
  | { readonly type: "create-feedback"; readonly fromGateId: string; readonly toBlockId: string; readonly reason: string }
  | { readonly type: "edit-feedback"; readonly semanticId: string; readonly toBlockId: string; readonly reason: string }
  | { readonly type: "create-intended-artifact"; readonly ownerBlockId: string; readonly title: string; readonly artifactTypeId: string; readonly description: string }
  | { readonly type: "edit-intended-artifact"; readonly semanticId: string; readonly title: string; readonly artifactTypeId: string; readonly description: string }
  | { readonly type: "delete-concept"; readonly semanticId: string };

export function assertDraftCanvasIntentExhaustive(value: never): never {
  throw new Error(`WORKFLOW_DRAFT_INTENT_UNSUPPORTED:${String(value)}`);
}
