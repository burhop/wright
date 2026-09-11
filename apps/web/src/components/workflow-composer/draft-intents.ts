import {
  bindWorkflowDraftIdentities,
  type WorkflowDraft,
  type WorkflowDraftValidation,
} from "../../services/workflow-drafts";
import type { DraftBlock, DraftSemanticKind } from "./draft-model";

export type DraftCanvasIntent =
  | { readonly type: "select"; readonly semanticId: string | null }
  | {
      readonly type: "create-block";
      readonly phaseId: string;
      readonly role: DraftBlock["role"];
      readonly x: number;
      readonly y: number;
    }
  | {
      readonly type: "move-block";
      readonly semanticId: string;
      readonly x: number;
      readonly y: number;
    }
  | {
      readonly type: "edit-block";
      readonly semanticId: string;
      readonly title: string;
      readonly purpose: string;
    }
  | {
      readonly type: "create-connection";
      readonly sourcePortId: string;
      readonly targetPortId: string;
    }
  | { readonly type: "delete-connection"; readonly semanticId: string }
  | {
      readonly type: "create-gate";
      readonly ownerBlockId: string;
      readonly condition: string;
      readonly proceedTargetBlockId: string;
      readonly reviseTargetBlockId: string;
    }
  | {
      readonly type: "edit-gate";
      readonly semanticId: string;
      readonly condition: string;
      readonly proceedTargetBlockId: string;
      readonly reviseTargetBlockId: string;
    }
  | {
      readonly type: "create-feedback";
      readonly fromGateId: string;
      readonly toBlockId: string;
      readonly reason: string;
    }
  | {
      readonly type: "edit-feedback";
      readonly semanticId: string;
      readonly toBlockId: string;
      readonly reason: string;
    }
  | {
      readonly type: "create-intended-artifact";
      readonly ownerBlockId: string;
      readonly title: string;
      readonly artifactTypeId: string;
      readonly description: string;
    }
  | {
      readonly type: "edit-intended-artifact";
      readonly semanticId: string;
      readonly title: string;
      readonly artifactTypeId: string;
      readonly description: string;
    }
  | { readonly type: "delete-concept"; readonly semanticId: string };

export type DraftDiagnostic = WorkflowDraftValidation["diagnostics"][number];

export interface DraftIntentState {
  readonly lastValidDraft: WorkflowDraft;
  readonly selectedSemanticId: string | null;
  readonly diagnostics: readonly DraftDiagnostic[];
}

const IDENTIFIER = /^[a-z0-9][a-z0-9._-]*$/;
const KIND_PREFIX: Record<DraftSemanticKind, string> = {
  phase: "phase",
  block: "block",
  port: "port",
  connection: "connection",
  gate: "gate",
  feedback_path: "feedback",
  intended_artifact: "artifact",
};

function diagnostic(
  code: string,
  path: string,
  affected: readonly string[],
  explanation: string,
  correction: string,
): DraftDiagnostic {
  return {
    code,
    path,
    affected_semantic_ids: [...new Set(affected)].sort(),
    explanation,
    correction,
  };
}

function allSemanticIds(draft: WorkflowDraft): string[] {
  return [
    ...draft.semantic.phases.map((item) => item.id),
    ...draft.semantic.blocks.map((item) => item.id),
    ...draft.semantic.ports.map((item) => item.id),
    ...draft.semantic.connections.map((item) => item.id),
    ...draft.semantic.gates.map((item) => item.id),
    ...draft.semantic.feedback_paths.map((item) => item.id),
    ...draft.semantic.intended_artifacts.map((item) => item.id),
  ];
}

function allocateSemanticId(
  draft: WorkflowDraft,
  kind: DraftSemanticKind,
): string {
  const used = new Set(allSemanticIds(draft));
  const prefix = KIND_PREFIX[kind];
  for (let index = 1; index <= 999; index += 1) {
    const candidate = `${prefix}.draft-${index}`;
    if (!used.has(candidate)) return candidate;
  }
  throw new Error("WORKFLOW_DRAFT_ID_SPACE_EXHAUSTED");
}

function cloneDraft(draft: WorkflowDraft): WorkflowDraft {
  return structuredClone(draft);
}

function isText(value: string): boolean {
  return value.trim().length > 0 && value.length <= 500;
}

function isCoordinate(value: number): boolean {
  return Number.isInteger(value) && value >= -10_000 && value <= 10_000;
}

function validateCandidate(draft: WorkflowDraft): DraftDiagnostic[] {
  const found: DraftDiagnostic[] = [];
  const identities = new Map<string, string[]>();
  const collections = [
    ["phases", draft.semantic.phases],
    ["blocks", draft.semantic.blocks],
    ["ports", draft.semantic.ports],
    ["connections", draft.semantic.connections],
    ["gates", draft.semantic.gates],
    ["feedback_paths", draft.semantic.feedback_paths],
    ["intended_artifacts", draft.semantic.intended_artifacts],
  ] as const;
  for (const [name, rows] of collections) {
    for (const row of rows)
      identities.set(row.id, [...(identities.get(row.id) ?? []), name]);
  }
  for (const [id, owners] of identities) {
    if (owners.length > 1)
      found.push(
        diagnostic(
          "SEMANTIC_ID_DUPLICATE",
          "/semantic",
          [id],
          "One semantic identity is assigned to more than one concept.",
          "Assign a distinct stable identity to each concept.",
        ),
      );
  }

  const phases = new Map(draft.semantic.phases.map((item) => [item.id, item]));
  const blocks = new Map(draft.semantic.blocks.map((item) => [item.id, item]));
  const ports = new Map(draft.semantic.ports.map((item) => [item.id, item]));
  const gates = new Map(draft.semantic.gates.map((item) => [item.id, item]));
  const feedback = new Map(
    draft.semantic.feedback_paths.map((item) => [item.id, item]),
  );
  const artifacts = new Map(
    draft.semantic.intended_artifacts.map((item) => [item.id, item]),
  );

  const orders = draft.semantic.phases
    .map((phase) => phase.order)
    .sort((a, b) => a - b);
  if (orders.some((order, index) => order !== index))
    found.push(
      diagnostic(
        "PHASE_ORDER_NOT_CONTIGUOUS",
        "/semantic/phases/order",
        draft.semantic.phases.map((phase) => phase.id),
        "Phase order values are not one contiguous zero-based sequence.",
        "Assign phase orders from zero through the phase count minus one.",
      ),
    );
  for (const phase of draft.semantic.phases) {
    for (const blockId of phase.block_ids) {
      const block = blocks.get(blockId);
      if (!block || block.phase_id !== phase.id)
        found.push(
          diagnostic(
            "PHASE_BLOCK_RECIPROCITY",
            `/semantic/phases/${phase.id}/block_ids`,
            [phase.id, blockId],
            "The phase and block ownership references do not agree.",
            "Make the phase block list and block phase identity reciprocal.",
          ),
        );
    }
  }
  for (const block of draft.semantic.blocks) {
    const phase = phases.get(block.phase_id);
    if (!phase || !phase.block_ids.includes(block.id))
      found.push(
        diagnostic(
          "BLOCK_PHASE_RECIPROCITY",
          `/semantic/blocks/${block.id}/phase_id`,
          [block.id, block.phase_id],
          "The block phase reference is missing or not reciprocal.",
          "Reference an existing phase that lists this block exactly once.",
        ),
      );
    for (const [direction, ids] of [
      ["input", block.input_port_ids],
      ["output", block.output_port_ids],
    ] as const) {
      for (const portId of ids) {
        const port = ports.get(portId);
        if (
          !port ||
          port.owner_block_id !== block.id ||
          port.direction !== direction
        )
          found.push(
            diagnostic(
              `BLOCK_${direction.toUpperCase()}_PORT_RECIPROCITY`,
              `/semantic/blocks/${block.id}/${direction}_port_ids`,
              [block.id, portId],
              "The block and typed-port references do not agree.",
              "Make port ownership, direction, and the block port list reciprocal.",
            ),
          );
      }
    }
    for (const gateId of block.gate_ids) {
      if (gates.get(gateId)?.owner_block_id !== block.id)
        found.push(
          diagnostic(
            "BLOCK_GATE_RECIPROCITY",
            `/semantic/blocks/${block.id}/gate_ids`,
            [block.id, gateId],
            "The block and gate ownership references do not agree.",
            "Make gate ownership and the block gate list reciprocal.",
          ),
        );
    }
    for (const artifactId of block.intended_artifact_ids) {
      if (artifacts.get(artifactId)?.produced_by_block_id !== block.id)
        found.push(
          diagnostic(
            "ARTIFACT_BLOCK_RECIPROCITY",
            `/semantic/blocks/${block.id}/intended_artifact_ids`,
            [block.id, artifactId],
            "The block and intended-artifact references do not agree.",
            "Make artifact producer and the block artifact list reciprocal.",
          ),
        );
    }
  }
  for (const port of draft.semantic.ports) {
    const owner = blocks.get(port.owner_block_id);
    const ownerIds =
      port.direction === "input"
        ? owner?.input_port_ids
        : owner?.output_port_ids;
    if (!owner || !ownerIds?.includes(port.id))
      found.push(
        diagnostic(
          "PORT_BLOCK_RECIPROCITY",
          `/semantic/ports/${port.id}/owner_block_id`,
          [port.id, port.owner_block_id],
          "The typed port owner does not list this port in its direction.",
          "Reference an existing owner and list the port exactly once.",
        ),
      );
  }

  const endpointPairs = new Map<string, string[]>();
  for (const connection of draft.semantic.connections) {
    const source = ports.get(connection.source_port_id);
    const target = ports.get(connection.target_port_id);
    const pair = `${connection.source_port_id}\u0000${connection.target_port_id}`;
    endpointPairs.set(pair, [
      ...(endpointPairs.get(pair) ?? []),
      connection.id,
    ]);
    if (!source || source.direction !== "output")
      found.push(
        diagnostic(
          "CONNECTION_SOURCE_INVALID",
          `/semantic/connections/${connection.id}/source_port_id`,
          [connection.id, connection.source_port_id],
          "The connection source is not an existing output port.",
          "Choose an existing output port as the source.",
        ),
      );
    if (!target || target.direction !== "input")
      found.push(
        diagnostic(
          "CONNECTION_TARGET_INVALID",
          `/semantic/connections/${connection.id}/target_port_id`,
          [connection.id, connection.source_port_id, connection.target_port_id],
          "The connection target is not an existing input port.",
          "Choose an existing input port as the target.",
        ),
      );
    if (source && target && source.value_type_id !== target.value_type_id)
      found.push(
        diagnostic(
          "CONNECTION_VALUE_TYPE_MISMATCH",
          `/semantic/connections/${connection.id}`,
          [connection.id, source.id, target.id],
          "The connected port value types do not match.",
          "Connect ports with exactly matching value-type identities.",
        ),
      );
  }
  for (const ids of endpointPairs.values()) {
    if (ids.length > 1)
      found.push(
        diagnostic(
          "CONNECTION_ENDPOINT_DUPLICATE",
          "/semantic/connections",
          ids,
          "More than one connection uses the same source and target.",
          "Keep one connection for this endpoint pair.",
        ),
      );
  }

  for (const gate of draft.semantic.gates) {
    const owner = blocks.get(gate.owner_block_id);
    const path = feedback.get(gate.feedback_path_id);
    if (!owner || !owner.gate_ids.includes(gate.id))
      found.push(
        diagnostic(
          "GATE_BLOCK_RECIPROCITY",
          `/semantic/gates/${gate.id}/owner_block_id`,
          [gate.id, gate.owner_block_id],
          "The gate owner does not list this gate.",
          "Make gate ownership reciprocal.",
        ),
      );
    for (const [field, target] of [
      ["proceed_target_block_id", gate.proceed_target_block_id],
      ["revise_target_block_id", gate.revise_target_block_id],
    ] as const) {
      if (!blocks.has(target))
        found.push(
          diagnostic(
            "GATE_TARGET_MISSING",
            `/semantic/gates/${gate.id}/${field}`,
            [gate.id, target],
            "The gate target block does not exist.",
            "Choose an existing block target.",
          ),
        );
    }
    if (!path || path.from_gate_id !== gate.id)
      found.push(
        diagnostic(
          "GATE_FEEDBACK_RECIPROCITY",
          `/semantic/gates/${gate.id}/feedback_path_id`,
          [gate.id, gate.feedback_path_id],
          "The gate feedback reference is missing or not reciprocal.",
          "Reference one feedback path that points back to this gate.",
        ),
      );
    else if (path.to_block_id !== gate.revise_target_block_id)
      found.push(
        diagnostic(
          "FEEDBACK_REVISE_TARGET_MISMATCH",
          `/semantic/gates/${gate.id}/revise_target_block_id`,
          [gate.id, path.id, path.to_block_id, gate.revise_target_block_id],
          "The feedback target differs from the gate revise target.",
          "Use the same block identity for feedback and revise targets.",
        ),
      );
  }
  for (const path of draft.semantic.feedback_paths) {
    const gate = gates.get(path.from_gate_id);
    if (!gate || gate.feedback_path_id !== path.id)
      found.push(
        diagnostic(
          "FEEDBACK_GATE_RECIPROCITY",
          `/semantic/feedback_paths/${path.id}/from_gate_id`,
          [path.id, path.from_gate_id],
          "The feedback path gate reference is missing or not reciprocal.",
          "Reference a gate that lists this feedback path.",
        ),
      );
    if (!blocks.has(path.to_block_id))
      found.push(
        diagnostic(
          "FEEDBACK_TARGET_MISSING",
          `/semantic/feedback_paths/${path.id}/to_block_id`,
          [path.id, path.to_block_id],
          "The feedback target block does not exist.",
          "Choose an existing block target.",
        ),
      );
  }
  for (const artifact of draft.semantic.intended_artifacts) {
    const producer = blocks.get(artifact.produced_by_block_id);
    if (!producer || !producer.intended_artifact_ids.includes(artifact.id))
      found.push(
        diagnostic(
          "ARTIFACT_PRODUCER_RECIPROCITY",
          `/semantic/intended_artifacts/${artifact.id}/produced_by_block_id`,
          [artifact.id, artifact.produced_by_block_id],
          "The intended artifact producer does not list this artifact.",
          "Make artifact producer references reciprocal.",
        ),
      );
  }

  const positionCounts = new Map<string, number>();
  for (const position of draft.layout.positions) {
    positionCounts.set(
      position.semantic_id,
      (positionCounts.get(position.semantic_id) ?? 0) + 1,
    );
    if (!blocks.has(position.semantic_id))
      found.push(
        diagnostic(
          "LAYOUT_SEMANTIC_ID_INVALID",
          "/layout/positions",
          [position.semantic_id],
          "A layout position refers to a non-block concept.",
          "Keep exactly one position for each workflow block only.",
        ),
      );
  }
  for (const block of draft.semantic.blocks) {
    const count = positionCounts.get(block.id) ?? 0;
    if (count === 0)
      found.push(
        diagnostic(
          "LAYOUT_BLOCK_POSITION_MISSING",
          "/layout/positions",
          [block.id],
          "A workflow block has no saved layout position.",
          "Add exactly one integer-grid position for this block.",
        ),
      );
    if (count > 1)
      found.push(
        diagnostic(
          "LAYOUT_BLOCK_POSITION_DUPLICATE",
          "/layout/positions",
          [block.id],
          "A workflow block has more than one layout position.",
          "Keep exactly one position for this block.",
        ),
      );
  }
  return found.sort((left, right) =>
    `${left.code}\u0000${left.path}\u0000${left.affected_semantic_ids.join("\u0000")}`.localeCompare(
      `${right.code}\u0000${right.path}\u0000${right.affected_semantic_ids.join("\u0000")}`,
    ),
  );
}

function rejected(
  state: DraftIntentState,
  diagnostics: readonly DraftDiagnostic[],
): DraftIntentState {
  return { ...state, diagnostics };
}

async function accepted(
  state: DraftIntentState,
  candidate: WorkflowDraft,
  selectedSemanticId = state.selectedSemanticId,
): Promise<DraftIntentState> {
  const diagnostics = validateCandidate(candidate);
  if (diagnostics.length > 0) return rejected(state, diagnostics);
  const bound = await bindWorkflowDraftIdentities(candidate);
  return { lastValidDraft: bound, selectedSemanticId, diagnostics: [] };
}

function localFailure(
  state: DraftIntentState,
  code: string,
  path: string,
  affected: readonly string[],
  explanation: string,
  correction: string,
): DraftIntentState {
  return rejected(state, [
    diagnostic(code, path, affected, explanation, correction),
  ]);
}

export function createDraftIntentState(draft: WorkflowDraft): DraftIntentState {
  return { lastValidDraft: draft, selectedSemanticId: null, diagnostics: [] };
}

export async function reduceDraftCanvasIntent(
  state: DraftIntentState,
  intent: DraftCanvasIntent,
): Promise<DraftIntentState> {
  const draft = state.lastValidDraft;
  if (intent.type === "select") {
    if (
      intent.semanticId !== null &&
      !allSemanticIds(draft).includes(intent.semanticId)
    )
      return localFailure(
        state,
        "SELECTION_IDENTITY_MISSING",
        "/selection",
        [intent.semanticId],
        "The selected concept does not exist in the last valid draft.",
        "Select one of the visible workflow concepts.",
      );
    return { ...state, selectedSemanticId: intent.semanticId, diagnostics: [] };
  }

  const candidate = cloneDraft(draft);
  switch (intent.type) {
    case "create-block": {
      const phase = candidate.semantic.phases.find(
        (item) => item.id === intent.phaseId,
      );
      if (!phase || !isCoordinate(intent.x) || !isCoordinate(intent.y))
        return localFailure(
          state,
          "BLOCK_CREATE_INVALID",
          "/semantic/blocks",
          [intent.phaseId],
          "The new block requires an existing phase and bounded integer position.",
          "Choose an existing phase and coordinates between -10000 and 10000.",
        );
      const id = allocateSemanticId(candidate, "block");
      const label = intent.role[0].toUpperCase() + intent.role.slice(1);
      candidate.semantic.blocks.push({
        id,
        title: `${label} work`,
        purpose: `Describe this provisional ${intent.role} work.`,
        role: intent.role,
        phase_id: phase.id,
        input_port_ids: [],
        output_port_ids: [],
        gate_ids: [],
        intended_artifact_ids: [],
      });
      phase.block_ids.push(id);
      candidate.layout.positions.push({
        semantic_id: id,
        x: intent.x,
        y: intent.y,
      });
      return accepted(state, candidate, id);
    }
    case "move-block": {
      const position = candidate.layout.positions.find(
        (item) => item.semantic_id === intent.semanticId,
      );
      if (!position || !isCoordinate(intent.x) || !isCoordinate(intent.y))
        return localFailure(
          state,
          "BLOCK_POSITION_INVALID",
          "/layout/positions",
          [intent.semanticId],
          "The block position is missing or outside the bounded integer grid.",
          "Choose an existing block and integer coordinates between -10000 and 10000.",
        );
      position.x = intent.x;
      position.y = intent.y;
      return accepted(state, candidate);
    }
    case "edit-block": {
      const block = candidate.semantic.blocks.find(
        (item) => item.id === intent.semanticId,
      );
      if (!block || !isText(intent.title) || !isText(intent.purpose))
        return localFailure(
          state,
          "BLOCK_DEFINITION_INVALID",
          `/semantic/blocks/${intent.semanticId}`,
          [intent.semanticId],
          "The block definition is missing or contains empty or oversized text.",
          "Choose an existing block and enter 1 to 500 characters for title and purpose.",
        );
      block.title = intent.title.trim();
      block.purpose = intent.purpose.trim();
      return accepted(state, candidate);
    }
    case "create-connection": {
      const id = allocateSemanticId(candidate, "connection");
      candidate.semantic.connections.push({
        id,
        source_port_id: intent.sourcePortId,
        target_port_id: intent.targetPortId,
      });
      return accepted(state, candidate, id);
    }
    case "delete-connection": {
      const index = candidate.semantic.connections.findIndex(
        (item) => item.id === intent.semanticId,
      );
      if (index < 0)
        return localFailure(
          state,
          "CONNECTION_MISSING",
          "/semantic/connections",
          [intent.semanticId],
          "The connection to delete does not exist.",
          "Choose an existing connection.",
        );
      candidate.semantic.connections.splice(index, 1);
      return accepted(
        state,
        candidate,
        state.selectedSemanticId === intent.semanticId
          ? null
          : state.selectedSemanticId,
      );
    }
    case "create-gate": {
      const owner = candidate.semantic.blocks.find(
        (item) => item.id === intent.ownerBlockId,
      );
      if (!owner || !isText(intent.condition))
        return localFailure(
          state,
          "GATE_DEFINITION_INVALID",
          "/semantic/gates",
          [intent.ownerBlockId],
          "The gate requires an existing owner and a bounded condition.",
          "Choose an existing block and enter a condition from 1 to 500 characters.",
        );
      const gateId = allocateSemanticId(candidate, "gate");
      const feedbackId = allocateSemanticId(candidate, "feedback_path");
      candidate.semantic.gates.push({
        id: gateId,
        owner_block_id: owner.id,
        condition: intent.condition.trim(),
        proceed_target_block_id: intent.proceedTargetBlockId,
        revise_target_block_id: intent.reviseTargetBlockId,
        feedback_path_id: feedbackId,
      });
      candidate.semantic.feedback_paths.push({
        id: feedbackId,
        from_gate_id: gateId,
        to_block_id: intent.reviseTargetBlockId,
        reason: "Revise the named workflow work to satisfy this gate.",
      });
      owner.gate_ids.push(gateId);
      return accepted(state, candidate, gateId);
    }
    case "edit-gate": {
      const gate = candidate.semantic.gates.find(
        (item) => item.id === intent.semanticId,
      );
      if (!gate || !isText(intent.condition))
        return localFailure(
          state,
          "GATE_DEFINITION_INVALID",
          `/semantic/gates/${intent.semanticId}`,
          [intent.semanticId],
          "The gate definition is missing or contains invalid text.",
          "Choose an existing gate and enter a condition from 1 to 500 characters.",
        );
      gate.condition = intent.condition.trim();
      gate.proceed_target_block_id = intent.proceedTargetBlockId;
      gate.revise_target_block_id = intent.reviseTargetBlockId;
      const path = candidate.semantic.feedback_paths.find(
        (item) => item.id === gate.feedback_path_id,
      );
      if (path) path.to_block_id = intent.reviseTargetBlockId;
      return accepted(state, candidate);
    }
    case "create-feedback": {
      const gate = candidate.semantic.gates.find(
        (item) => item.id === intent.fromGateId,
      );
      if (!gate || !isText(intent.reason))
        return localFailure(
          state,
          "FEEDBACK_DEFINITION_INVALID",
          "/semantic/feedback_paths",
          [intent.fromGateId],
          "The feedback path requires an existing gate and bounded reason.",
          "Choose an existing gate and enter a reason from 1 to 500 characters.",
        );
      const oldId = gate.feedback_path_id;
      const id = allocateSemanticId(candidate, "feedback_path");
      candidate.semantic.feedback_paths =
        candidate.semantic.feedback_paths.filter((item) => item.id !== oldId);
      candidate.semantic.feedback_paths.push({
        id,
        from_gate_id: gate.id,
        to_block_id: intent.toBlockId,
        reason: intent.reason.trim(),
      });
      gate.feedback_path_id = id;
      gate.revise_target_block_id = intent.toBlockId;
      return accepted(state, candidate, id);
    }
    case "edit-feedback": {
      const path = candidate.semantic.feedback_paths.find(
        (item) => item.id === intent.semanticId,
      );
      if (!path || !isText(intent.reason))
        return localFailure(
          state,
          "FEEDBACK_DEFINITION_INVALID",
          `/semantic/feedback_paths/${intent.semanticId}`,
          [intent.semanticId],
          "The feedback path is missing or contains invalid text.",
          "Choose an existing feedback path and enter a reason from 1 to 500 characters.",
        );
      path.to_block_id = intent.toBlockId;
      path.reason = intent.reason.trim();
      const gate = candidate.semantic.gates.find(
        (item) => item.id === path.from_gate_id,
      );
      if (gate) gate.revise_target_block_id = intent.toBlockId;
      return accepted(state, candidate);
    }
    case "create-intended-artifact": {
      const owner = candidate.semantic.blocks.find(
        (item) => item.id === intent.ownerBlockId,
      );
      if (
        !owner ||
        !isText(intent.title) ||
        !isText(intent.description) ||
        !IDENTIFIER.test(intent.artifactTypeId)
      )
        return localFailure(
          state,
          "ARTIFACT_DEFINITION_INVALID",
          "/semantic/intended_artifacts",
          [intent.ownerBlockId],
          "The intended artifact requires an owner, bounded text, and a valid type identity.",
          "Choose an existing block and enter a valid title, description, and type identity.",
        );
      const id = allocateSemanticId(candidate, "intended_artifact");
      candidate.semantic.intended_artifacts.push({
        id,
        title: intent.title.trim(),
        artifact_type_id: intent.artifactTypeId,
        description: intent.description.trim(),
        produced_by_block_id: owner.id,
      });
      owner.intended_artifact_ids.push(id);
      return accepted(state, candidate, id);
    }
    case "edit-intended-artifact": {
      const artifact = candidate.semantic.intended_artifacts.find(
        (item) => item.id === intent.semanticId,
      );
      if (
        !artifact ||
        !isText(intent.title) ||
        !isText(intent.description) ||
        !IDENTIFIER.test(intent.artifactTypeId)
      )
        return localFailure(
          state,
          "ARTIFACT_DEFINITION_INVALID",
          `/semantic/intended_artifacts/${intent.semanticId}`,
          [intent.semanticId],
          "The intended artifact is missing or contains an invalid definition.",
          "Choose an existing intended artifact and enter valid bounded values.",
        );
      artifact.title = intent.title.trim();
      artifact.artifact_type_id = intent.artifactTypeId;
      artifact.description = intent.description.trim();
      return accepted(state, candidate);
    }
    case "delete-concept": {
      const connectionIndex = candidate.semantic.connections.findIndex(
        (item) => item.id === intent.semanticId,
      );
      if (connectionIndex >= 0) {
        candidate.semantic.connections.splice(connectionIndex, 1);
        return accepted(
          state,
          candidate,
          state.selectedSemanticId === intent.semanticId
            ? null
            : state.selectedSemanticId,
        );
      }
      const artifactIndex = candidate.semantic.intended_artifacts.findIndex(
        (item) => item.id === intent.semanticId,
      );
      if (artifactIndex >= 0) {
        const artifact = candidate.semantic.intended_artifacts[artifactIndex];
        candidate.semantic.intended_artifacts.splice(artifactIndex, 1);
        const owner = candidate.semantic.blocks.find(
          (item) => item.id === artifact?.produced_by_block_id,
        );
        if (owner)
          owner.intended_artifact_ids = owner.intended_artifact_ids.filter(
            (id) => id !== intent.semanticId,
          );
        return accepted(
          state,
          candidate,
          state.selectedSemanticId === intent.semanticId
            ? null
            : state.selectedSemanticId,
        );
      }
      const gateIndex = candidate.semantic.gates.findIndex(
        (item) => item.id === intent.semanticId,
      );
      if (gateIndex >= 0) {
        const gate = candidate.semantic.gates[gateIndex];
        candidate.semantic.gates.splice(gateIndex, 1);
        candidate.semantic.feedback_paths =
          candidate.semantic.feedback_paths.filter(
            (item) => item.id !== gate?.feedback_path_id,
          );
        const owner = candidate.semantic.blocks.find(
          (item) => item.id === gate?.owner_block_id,
        );
        if (owner)
          owner.gate_ids = owner.gate_ids.filter(
            (id) => id !== intent.semanticId,
          );
        return accepted(
          state,
          candidate,
          state.selectedSemanticId === intent.semanticId
            ? null
            : state.selectedSemanticId,
        );
      }
      if (
        candidate.semantic.feedback_paths.some(
          (item) => item.id === intent.semanticId,
        )
      )
        return localFailure(
          state,
          "DELETE_CONCEPT_DEPENDENCY",
          `/semantic/feedback_paths/${intent.semanticId}`,
          [intent.semanticId],
          "The feedback path is required by its gate and cannot be deleted alone.",
          "Delete the owning gate or replace its feedback path atomically.",
        );
      const blockIndex = candidate.semantic.blocks.findIndex(
        (item) => item.id === intent.semanticId,
      );
      if (blockIndex >= 0) {
        const block = candidate.semantic.blocks[blockIndex];
        const ownedPorts = new Set([
          ...(block?.input_port_ids ?? []),
          ...(block?.output_port_ids ?? []),
        ]);
        const dependencies = [
          ...candidate.semantic.connections
            .filter(
              (item) =>
                ownedPorts.has(item.source_port_id) ||
                ownedPorts.has(item.target_port_id),
            )
            .map((item) => item.id),
          ...candidate.semantic.gates
            .filter(
              (item) =>
                item.proceed_target_block_id === intent.semanticId ||
                item.revise_target_block_id === intent.semanticId,
            )
            .map((item) => item.id),
          ...candidate.semantic.feedback_paths
            .filter((item) => item.to_block_id === intent.semanticId)
            .map((item) => item.id),
        ];
        if (dependencies.length > 0)
          return localFailure(
            state,
            "DELETE_CONCEPT_DEPENDENCY",
            `/semantic/blocks/${intent.semanticId}`,
            [intent.semanticId, ...dependencies],
            "Deleting this block would leave declared workflow relationships dangling.",
            "Delete or redirect the named dependent relationships before deleting the block.",
          );
        const ownedGateIds = new Set(block?.gate_ids ?? []);
        const ownedGates = candidate.semantic.gates.filter((item) =>
          ownedGateIds.has(item.id),
        );
        const ownedFeedbackIds = new Set(
          ownedGates.map((item) => item.feedback_path_id),
        );
        candidate.semantic.blocks.splice(blockIndex, 1);
        candidate.semantic.ports = candidate.semantic.ports.filter(
          (item) => !ownedPorts.has(item.id),
        );
        candidate.semantic.intended_artifacts =
          candidate.semantic.intended_artifacts.filter(
            (item) => item.produced_by_block_id !== intent.semanticId,
          );
        candidate.semantic.gates = candidate.semantic.gates.filter(
          (item) => !ownedGateIds.has(item.id),
        );
        candidate.semantic.feedback_paths =
          candidate.semantic.feedback_paths.filter(
            (item) => !ownedFeedbackIds.has(item.id),
          );
        candidate.layout.positions = candidate.layout.positions.filter(
          (item) => item.semantic_id !== intent.semanticId,
        );
        for (const phase of candidate.semantic.phases)
          phase.block_ids = phase.block_ids.filter(
            (id) => id !== intent.semanticId,
          );
        return accepted(
          state,
          candidate,
          state.selectedSemanticId === intent.semanticId
            ? null
            : state.selectedSemanticId,
        );
      }
      return localFailure(
        state,
        "CONCEPT_MISSING",
        "/semantic",
        [intent.semanticId],
        "The concept to delete does not exist.",
        "Choose an existing editable concept.",
      );
    }
    default:
      return assertDraftCanvasIntentExhaustive(intent);
  }
}

export function assertDraftCanvasIntentExhaustive(value: never): never {
  throw new Error(`WORKFLOW_DRAFT_INTENT_UNSUPPORTED:${String(value)}`);
}
