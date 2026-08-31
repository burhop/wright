import type { WorkflowDraft } from "../../services/workflow-drafts";
import {
  draftSemanticReferences,
  requireUniqueSemanticIds,
  type DraftArtifact,
  type DraftBlock,
  type DraftConnection,
  type DraftFeedbackPath,
  type DraftGate,
  type DraftPhase,
  type DraftPort,
  type DraftPosition,
} from "./draft-model";

export interface DraftPortProjection extends DraftPort { readonly semanticId: string }
export interface DraftGateProjection extends DraftGate { readonly semanticId: string }
export interface DraftArtifactProjection extends DraftArtifact { readonly semanticId: string }
export interface DraftBlockProjection extends DraftBlock {
  readonly semanticId: string;
  readonly position: DraftPosition;
  readonly inputs: readonly DraftPortProjection[];
  readonly outputs: readonly DraftPortProjection[];
  readonly gates: readonly DraftGateProjection[];
  readonly artifacts: readonly DraftArtifactProjection[];
}
export interface DraftPhaseProjection extends DraftPhase {
  readonly semanticId: string;
  readonly blocks: readonly DraftBlockProjection[];
}
export interface DraftConnectionProjection extends DraftConnection {
  readonly semanticId: string;
  readonly sourceBlockId: string;
  readonly targetBlockId: string;
}
export interface DraftFeedbackProjection extends DraftFeedbackPath {
  readonly semanticId: string;
  readonly label: string;
}
export interface DraftProjection {
  readonly draftId: string;
  readonly revision: number;
  readonly title: string;
  readonly purpose: string;
  readonly phases: readonly DraftPhaseProjection[];
  readonly connections: readonly DraftConnectionProjection[];
  readonly feedbackPaths: readonly DraftFeedbackProjection[];
}

function required<T>(registry: ReadonlyMap<string, T>, id: string): T {
  const value = registry.get(id);
  if (value === undefined) throw new Error(`WORKFLOW_DRAFT_REFERENCE_UNRESOLVED:${id}`);
  return value;
}

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    for (const child of Object.values(value as Record<string, unknown>)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

export function buildDraftProjection(draft: WorkflowDraft): DraftProjection {
  const source = structuredClone(draft);
  const blocks = new Map(source.semantic.blocks.map((item) => [item.id, item]));
  const ports = new Map(source.semantic.ports.map((item) => [item.id, item]));
  const gates = new Map(source.semantic.gates.map((item) => [item.id, item]));
  const artifacts = new Map(source.semantic.intended_artifacts.map((item) => [item.id, item]));
  const positions = new Map(source.layout.positions.map((item) => [item.semantic_id, item]));
  if (positions.size !== source.layout.positions.length || positions.size !== blocks.size) {
    throw new Error("WORKFLOW_DRAFT_LAYOUT_POSITION_IDENTITY_INVALID");
  }
  const portProjection = (id: string): DraftPortProjection => ({ ...required(ports, id), semanticId: id });
  const gateProjection = (id: string): DraftGateProjection => ({ ...required(gates, id), semanticId: id });
  const artifactProjection = (id: string): DraftArtifactProjection => ({ ...required(artifacts, id), semanticId: id });
  const blockProjection = (id: string): DraftBlockProjection => {
    const block = required(blocks, id);
    return {
      ...block,
      semanticId: id,
      position: required(positions, id),
      inputs: block.input_port_ids.map(portProjection),
      outputs: block.output_port_ids.map(portProjection),
      gates: block.gate_ids.map(gateProjection),
      artifacts: block.intended_artifact_ids.map(artifactProjection),
    };
  };
  const portOwners = new Map(source.semantic.ports.map((item) => [item.id, item.owner_block_id]));
  const projection: DraftProjection = {
    draftId: source.draft_id,
    revision: source.revision,
    title: source.semantic.title,
    purpose: source.semantic.purpose,
    phases: source.semantic.phases.map((phase, index) => {
      if (phase.order !== index) throw new Error("WORKFLOW_DRAFT_PHASE_ORDER_INVALID");
      return ({
      ...phase,
      semanticId: phase.id,
      blocks: phase.block_ids.map(blockProjection),
      });
    }),
    connections: source.semantic.connections.map((item) => ({
      ...item,
      semanticId: item.id,
      sourceBlockId: required(portOwners, item.source_port_id),
      targetBlockId: required(portOwners, item.target_port_id),
    })),
    feedbackPaths: source.semantic.feedback_paths.map((item) => ({
      ...item,
      semanticId: item.id,
      label: item.reason,
    })),
  };
  assertSemanticIdParity(draft, projection);
  return deepFreeze(projection);
}

export function draftSemanticIds(draft: WorkflowDraft): readonly string[] {
  return requireUniqueSemanticIds(draftSemanticReferences(draft).map((item) => item.semanticId));
}

export function projectionSemanticIds(projection: DraftProjection): readonly string[] {
  const ids = [
    ...projection.phases.map((item) => item.semanticId),
    ...projection.phases.flatMap((phase) => phase.blocks.map((item) => item.semanticId)),
    ...projection.phases.flatMap((phase) => phase.blocks.flatMap((block) => [...block.inputs, ...block.outputs].map((item) => item.semanticId))),
    ...projection.connections.map((item) => item.semanticId),
    ...projection.phases.flatMap((phase) => phase.blocks.flatMap((block) => block.gates.map((item) => item.semanticId))),
    ...projection.feedbackPaths.map((item) => item.semanticId),
    ...projection.phases.flatMap((phase) => phase.blocks.flatMap((block) => block.artifacts.map((item) => item.semanticId))),
  ];
  return requireUniqueSemanticIds(ids);
}

export function assertSemanticIdParity(
  draft: WorkflowDraft,
  projection: DraftProjection,
): void {
  let matches = false;
  try {
    matches = draftSemanticIds(draft).join("\n") === projectionSemanticIds(projection).join("\n");
  } catch {
    matches = false;
  }
  if (!matches) {
    throw new Error("WORKFLOW_DRAFT_SEMANTIC_ID_PARITY_MISMATCH");
  }
}
