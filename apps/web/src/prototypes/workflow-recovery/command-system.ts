import {
  cloneLayout,
  cloneWorkflow,
  validateRecoveryLayoutDocument,
  type RecoveryBlock,
  type RecoveryDiagnostic,
  type RecoveryLayout,
  type RecoveryPort,
  type RecoveryRelationship,
  type RecoveryWorkflow,
} from "./model";
import { toCanonicalWire } from "./canonical-wire";
import { formatRecoveryDsl, parseRecoveryDsl } from "./recovery-dsl";

export type RecoveryCommand =
  | { kind: "move_block"; blockId: string; x: number; y: number }
  | { kind: "set_block_title"; blockId: string; title: string }
  | { kind: "set_block_configuration"; blockId: string; key: string; value: string | number | boolean }
  | { kind: "set_port_contract"; portId: string; required: boolean; cardinality: RecoveryPort["cardinality"] }
  | { kind: "set_binding_tool"; bindingId: string; toolId: string | null }
  | { kind: "update_relationship"; relationshipId: string; patch: Partial<Pick<RecoveryRelationship, "kind" | "sourceId" | "targetId" | "label" | "condition">> }
  | { kind: "add_block"; block: RecoveryBlock; ports: RecoveryPort[]; position: { x: number; y: number } }
  | { kind: "delete_block"; blockId: string }
  | { kind: "connect"; relationship: RecoveryRelationship }
  | { kind: "disconnect"; relationshipId: string }
  | { kind: "restore_snapshot"; direction: "undo" | "redo"; workflow: RecoveryWorkflow; layout: RecoveryLayout };

export interface RecoveryCommandBatch {
  documentKind: "workflow-command-batch";
  schemaVersion: "1.0.0-recovery.1";
  baseRevision: number;
  origin: "graph" | "form" | "text" | "ai_proposal" | "history";
  commands: RecoveryCommand[];
}

export function recoveryCommandBatch(
  baseRevision: number,
  origin: RecoveryCommandBatch["origin"],
  commands: RecoveryCommand[],
): RecoveryCommandBatch {
  return { documentKind: "workflow-command-batch", schemaVersion: "1.0.0-recovery.1", baseRevision, origin, commands };
}

export interface RecoveryApplyResult {
  ok: boolean;
  workflow: RecoveryWorkflow | null;
  layout: RecoveryLayout | null;
  diagnostics: RecoveryDiagnostic[];
  diff: string[];
  semanticChanged: boolean;
}

function failure(code: string, explanation: string, correction: string, semanticId: string | null = null): RecoveryApplyResult {
  return { ok: false, workflow: null, layout: null, diagnostics: [{ code, explanation, correction, semanticId, line: null }], diff: [], semanticChanged: false };
}

function block(workflow: RecoveryWorkflow, id: string): RecoveryBlock {
  const value = workflow.blocks.find((item) => item.id === id);
  if (!value) throw new Error(`WFR-COMMAND-TARGET-MISSING:${id}`);
  return value;
}

function applyCommand(workflow: RecoveryWorkflow, layout: RecoveryLayout, command: RecoveryCommand): void {
  if (command.kind === "restore_snapshot") {
    Object.assign(workflow, cloneWorkflow(command.workflow));
    Object.assign(layout, cloneLayout(command.layout));
    return;
  }
  if (command.kind === "move_block") {
    if (!workflow.blocks.some((item) => item.id === command.blockId) || !Number.isFinite(command.x) || !Number.isFinite(command.y)) {
      throw new Error(`WFR-COMMAND-MOVE-INVALID:${command.blockId}`);
    }
    layout.positions[command.blockId] = { x: Math.round(command.x), y: Math.round(command.y) };
    return;
  }
  if (command.kind === "set_block_title") {
    if (!command.title.trim()) throw new Error(`WFR-COMMAND-TITLE-INVALID:${command.blockId}`);
    block(workflow, command.blockId).title = command.title.trim();
    return;
  }
  if (command.kind === "set_block_configuration") {
    block(workflow, command.blockId).configuration[command.key] = command.value;
    return;
  }
  if (command.kind === "set_port_contract") {
    const port = workflow.ports.find((item) => item.id === command.portId);
    if (!port) throw new Error(`WFR-COMMAND-TARGET-MISSING:${command.portId}`);
    port.required = command.required;
    port.cardinality = command.cardinality;
    return;
  }
  if (command.kind === "set_binding_tool") {
    const binding = workflow.bindings.find((item) => item.id === command.bindingId);
    if (!binding) throw new Error(`WFR-COMMAND-TARGET-MISSING:${command.bindingId}`);
    binding.toolId = command.toolId;
    return;
  }
  if (command.kind === "update_relationship") {
    const relationship = workflow.relationships.find((item) => item.id === command.relationshipId);
    if (!relationship || Object.keys(command.patch).length === 0) throw new Error(`WFR-COMMAND-TARGET-MISSING:${command.relationshipId}`);
    Object.assign(relationship, structuredClone(command.patch));
    return;
  }
  if (command.kind === "add_block") {
    if (workflow.blocks.some((item) => item.id === command.block.id) || workflow.ports.some((item) => command.ports.some((port) => port.id === item.id))) {
      throw new Error(`WFR-ID-DUPLICATE:${command.block.id}`);
    }
    const phase = workflow.phases.find((item) => item.id === command.block.phaseId);
    if (!phase) throw new Error(`WFR-REFERENCE-DANGLING:${command.block.phaseId}`);
    workflow.blocks.push(structuredClone(command.block));
    workflow.ports.push(...structuredClone(command.ports));
    phase.blockIds.push(command.block.id);
    layout.positions[command.block.id] = { ...command.position };
    return;
  }
  if (command.kind === "delete_block") {
    const target = block(workflow, command.blockId);
    const portIds = new Set([...target.inputPortIds, ...target.outputPortIds]);
    const dependencies = workflow.relationships.filter((item) => portIds.has(item.sourceId) || portIds.has(item.targetId) || item.sourceId === target.id || item.targetId === target.id);
    if (dependencies.length > 0) throw new Error(`WFR-COMMAND-DEPENDENCY:${dependencies[0]?.id ?? target.id}`);
    workflow.blocks = workflow.blocks.filter((item) => item.id !== target.id);
    workflow.ports = workflow.ports.filter((item) => !portIds.has(item.id));
    for (const phase of workflow.phases) phase.blockIds = phase.blockIds.filter((id) => id !== target.id);
    delete layout.positions[target.id];
    return;
  }
  if (command.kind === "connect") {
    if (workflow.relationships.some((item) => item.id === command.relationship.id)) throw new Error(`WFR-ID-DUPLICATE:${command.relationship.id}`);
    workflow.relationships.push(structuredClone(command.relationship));
    return;
  }
  const count = workflow.relationships.length;
  workflow.relationships = workflow.relationships.filter((item) => item.id !== command.relationshipId);
  if (workflow.relationships.length === count) throw new Error(`WFR-COMMAND-TARGET-MISSING:${command.relationshipId}`);
}

function stableValue(value: unknown): string {
  const normalize = (item: unknown): unknown => {
    if (Array.isArray(item)) return item.map(normalize);
    if (item !== null && typeof item === "object") return Object.fromEntries(Object.entries(item as Record<string, unknown>).sort(([left], [right]) => left.localeCompare(right)).map(([key, child]) => [key, normalize(child)]));
    return item;
  };
  return JSON.stringify(normalize(value));
}

function modelDiff(before: RecoveryWorkflow, after: RecoveryWorkflow): string[] {
  const diff: string[] = [];
  const rootBefore = { documentKind: before.documentKind, schemaVersion: before.schemaVersion, workflowId: before.workflowId, metadata: before.metadata };
  const rootAfter = { documentKind: after.documentKind, schemaVersion: after.schemaVersion, workflowId: after.workflowId, metadata: after.metadata };
  for (const field of Object.keys(rootBefore).sort() as (keyof typeof rootBefore)[]) {
    if (stableValue(rootBefore[field]) !== stableValue(rootAfter[field])) diff.push(`Change workflow.${field} · ${stableValue(rootBefore[field])} → ${stableValue(rootAfter[field])}`);
  }

  const compareCollection = <T extends { id: string }>(
    kind: string,
    leftItems: readonly T[],
    rightItems: readonly T[],
    label: (item: T) => string,
  ) => {
    const leftById = new Map(leftItems.map((item) => [item.id, item]));
    const rightById = new Map(rightItems.map((item) => [item.id, item]));
    for (const id of [...new Set([...leftById.keys(), ...rightById.keys()])].sort()) {
      const left = leftById.get(id);
      const right = rightById.get(id);
      if (!left && right) {
        const verb = kind === "relationship" ? "Connect" : `Add ${kind}`;
        diff.push(`${verb} · ${label(right)} (${id}) · ${stableValue(right)}`);
        continue;
      }
      if (left && !right) {
        const verb = kind === "relationship" ? "Disconnect" : `Delete ${kind}`;
        diff.push(`${verb} · ${label(left)} (${id}) · ${stableValue(left)}`);
        continue;
      }
      if (!left || !right) continue;
      const fields = [...new Set([...Object.keys(left), ...Object.keys(right)])].filter((field) => field !== "id").sort();
      for (const field of fields) {
        const beforeValue = (left as Record<string, unknown>)[field];
        const afterValue = (right as Record<string, unknown>)[field];
        if (stableValue(beforeValue) === stableValue(afterValue)) continue;
        if (kind === "block" && field === "title") diff.push(`Rename ${id} · ${stableValue(beforeValue)} → ${stableValue(afterValue)}`);
        else if (kind === "block" && field === "configuration") diff.push(`Configure ${id} · ${stableValue(beforeValue)} → ${stableValue(afterValue)}`);
        else diff.push(`Change ${kind} ${id}.${field} · ${stableValue(beforeValue)} → ${stableValue(afterValue)}`);
      }
    }
  };

  compareCollection("phase", before.phases, after.phases, (item) => item.name);
  compareCollection("block", before.blocks, after.blocks, (item) => item.title);
  compareCollection("port", before.ports, after.ports, (item) => item.name);
  compareCollection("relationship", before.relationships, after.relationships, (item) => item.label);
  compareCollection("artifact", before.artifactContracts, after.artifactContracts, (item) => item.name);
  compareCollection("binding", before.bindings, after.bindings, (item) => item.capabilityName);
  compareCollection("component", before.components, after.components, (item) => item.title);
  return diff;
}

export function applyRecoveryBatch(
  workflowValue: RecoveryWorkflow,
  layoutValue: RecoveryLayout,
  batch: RecoveryCommandBatch,
): RecoveryApplyResult {
  if (batch.documentKind !== "workflow-command-batch" || batch.schemaVersion !== "1.0.0-recovery.1") {
    return failure("WFR-COMMAND-VERSION-UNSUPPORTED", `Unsupported command document ${String(batch.documentKind)} version ${String(batch.schemaVersion)}.`, "Preserve the original command bytes and use an explicitly compatible reader; never silently rewrite an unknown version.");
  }
  const inputLayoutIssue = validateRecoveryLayoutDocument(workflowValue, layoutValue)[0];
  if (inputLayoutIssue) return failure(inputLayoutIssue.code, inputLayoutIssue.explanation, inputLayoutIssue.correction, inputLayoutIssue.semanticId);
  if (batch.baseRevision !== workflowValue.revision) {
    return failure("WFR-COMMAND-STALE-BASE", `Revision ${batch.baseRevision} is stale; the current definition is revision ${workflowValue.revision}.`, "Refresh, rebase, and review the new semantic diff.");
  }
  if (batch.commands.length === 0) return failure("WFR-COMMAND-BATCH-EMPTY", "A command batch must contain at least one change.", "Add a command or reject the proposal.");
  const historyCommands = batch.commands.filter((command) => command.kind === "restore_snapshot");
  if ((historyCommands.length > 0 && (batch.origin !== "history" || batch.commands.length !== 1)) || (batch.origin === "history" && historyCommands.length !== 1)) {
    return failure("WFR-HISTORY-BATCH-INVALID", "Undo/redo must be one isolated restore command in a history-origin batch.", "Submit exactly one validated restore snapshot command.");
  }
  const hasLayoutOnlyCommand = batch.commands.some((command) => command.kind === "move_block");
  const hasSemanticCommand = batch.commands.some((command) => command.kind !== "move_block" && command.kind !== "restore_snapshot");
  if (hasLayoutOnlyCommand && hasSemanticCommand) {
    return failure("WFR-COMMAND-MIXED-CONTAINMENT", "Layout-only moves and semantic definition changes cannot share one atomic batch.", "Submit one semantic batch and one layout batch so revision ownership remains explicit.");
  }
  const workflow = cloneWorkflow(workflowValue);
  const layout = cloneLayout(layoutValue);
  try {
    for (const command of batch.commands) applyCommand(workflow, layout, command);
  } catch (error) {
    const message = error instanceof Error ? error.message : "WFR-COMMAND-UNKNOWN";
    const [code, identity] = message.split(":");
    return failure(code?.startsWith("WFR-") ? code : "WFR-COMMAND-UNKNOWN", message, "Correct or remove the invalid command; no change was applied.", identity ?? null);
  }
  const candidateText = formatRecoveryDsl(workflow).text;
  const parsed = parseRecoveryDsl(candidateText);
  if (!parsed.ok || parsed.workflow === null) return { ok: false, workflow: null, layout: null, diagnostics: parsed.diagnostics, diff: [], semanticChanged: false };
  const candidateLayoutIssue = validateRecoveryLayoutDocument(parsed.workflow, layout)[0];
  if (candidateLayoutIssue) return failure(candidateLayoutIssue.code, candidateLayoutIssue.explanation, candidateLayoutIssue.correction, candidateLayoutIssue.semanticId);
  const diff = modelDiff(workflowValue, parsed.workflow);
  const semanticChanged = diff.length > 0;
  return { ok: true, workflow: parsed.workflow, layout, diagnostics: [], diff, semanticChanged };
}

export function acceptRecoveryResult(current: RecoveryWorkflow, currentLayout: RecoveryLayout, result: RecoveryApplyResult): { workflow: RecoveryWorkflow; layout: RecoveryLayout } | null {
  if (!result.ok || result.workflow === null || result.layout === null) return null;
  const workflow = cloneWorkflow(result.workflow);
  if (result.semanticChanged) {
    workflow.parentRevision = current.revision;
    workflow.revision = current.revision + 1;
  } else {
    workflow.parentRevision = current.parentRevision;
    workflow.revision = current.revision;
    workflow.semanticSha256 = current.semanticSha256;
  }
  const layout = cloneLayout(result.layout);
  const layoutChanged = stableValue({ positions: currentLayout.positions, viewport: currentLayout.viewport }) !== stableValue({ positions: layout.positions, viewport: layout.viewport });
  layout.workflowId = workflow.workflowId;
  layout.semanticRevision = workflow.revision;
  layout.layoutRevision = layoutChanged || result.semanticChanged ? currentLayout.layoutRevision + 1 : currentLayout.layoutRevision;
  return { workflow, layout };
}

function normalized(workflow: RecoveryWorkflow): string {
  const value = toCanonicalWire(workflow);
  value.revision = 0;
  value.parent_revision = null;
  value.semantic_sha256 = null;
  value.blocks.sort((left, right) => left.id.localeCompare(right.id));
  value.ports.sort((left, right) => left.id.localeCompare(right.id));
  value.relationships.sort((left, right) => left.id.localeCompare(right.id));
  value.artifact_contracts.sort((left, right) => left.id.localeCompare(right.id));
  value.bindings.sort((left, right) => left.id.localeCompare(right.id));
  value.components.sort((left, right) => left.id.localeCompare(right.id));
  return stableValue(value);
}

export function textEditCommands(before: RecoveryWorkflow, after: RecoveryWorkflow): RecoveryCommand[] | RecoveryDiagnostic[] {
  const commands: RecoveryCommand[] = [];
  const afterById = new Map(after.blocks.map((item) => [item.id, item]));
  for (const current of before.blocks) {
    const edited = afterById.get(current.id);
    if (!edited) return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: current.id, line: null, explanation: "This recovery Code treatment only promotes reviewed block title/config edits.", correction: "Use the canvas for structural edits or restore the last-valid source." }];
    if (current.title !== edited.title) commands.push({ kind: "set_block_title", blockId: current.id, title: edited.title });
    const keys = new Set([...Object.keys(current.configuration), ...Object.keys(edited.configuration)]);
    for (const key of keys) {
      if (edited.configuration[key] === undefined) return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: current.id, line: null, explanation: "Configuration key deletion is not promoted by this recovery parser.", correction: "Restore the key or configure the block in the inspector." }];
      if (current.configuration[key] !== edited.configuration[key]) commands.push({ kind: "set_block_configuration", blockId: current.id, key, value: edited.configuration[key] as string | number | boolean });
    }
  }
  const afterPorts = new Map(after.ports.map((item) => [item.id, item]));
  for (const current of before.ports) {
    const edited = afterPorts.get(current.id);
    if (!edited) return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: current.id, line: null, explanation: "This recovery Code treatment cannot add or remove ports.", correction: "Restore the canonical port or use a later approved structural editor." }];
    if (current.required !== edited.required || current.cardinality !== edited.cardinality) commands.push({ kind: "set_port_contract", portId: current.id, required: edited.required, cardinality: edited.cardinality });
  }
  const afterRelationships = new Map(after.relationships.map((item) => [item.id, item]));
  for (const current of before.relationships) {
    const edited = afterRelationships.get(current.id);
    if (!edited) return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: current.id, line: null, explanation: "This recovery Code treatment cannot add or remove relationships.", correction: "Use the canvas for connection structure or restore the relationship." }];
    const patch: Partial<Pick<RecoveryRelationship, "kind" | "sourceId" | "targetId" | "label" | "condition">> = {};
    if (current.kind !== edited.kind) patch.kind = edited.kind;
    if (current.sourceId !== edited.sourceId) patch.sourceId = edited.sourceId;
    if (current.targetId !== edited.targetId) patch.targetId = edited.targetId;
    if (current.label !== edited.label) patch.label = edited.label;
    if (current.condition !== edited.condition) patch.condition = edited.condition;
    if (Object.keys(patch).length > 0) commands.push({ kind: "update_relationship", relationshipId: current.id, patch });
  }
  const afterBindings = new Map(after.bindings.map((item) => [item.id, item]));
  for (const current of before.bindings) {
    const edited = afterBindings.get(current.id);
    if (!edited) return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: current.id, line: null, explanation: "This recovery Code treatment cannot add or remove bindings.", correction: "Restore the canonical binding or use a later approved binding editor." }];
    if (current.toolId !== edited.toolId) commands.push({ kind: "set_binding_tool", bindingId: current.id, toolId: edited.toolId });
  }
  const candidate = cloneWorkflow(before);
  for (const command of commands) applyCommand(candidate, {
    documentKind: "workflow-layout",
    schemaVersion: "1.0.0-recovery.1",
    workflowId: before.workflowId,
    semanticRevision: before.revision,
    layoutRevision: 1,
    positions: {},
    viewport: { x: 0, y: 0, zoom: 1 },
  }, command);
  if (normalized(candidate) !== normalized(after)) {
    return [{ code: "WFR-TEXT-STRUCTURE-UNSUPPORTED", semanticId: null, line: null, explanation: "The text contains a structural or authority change outside this disposable Code treatment.", correction: "Restore the last-valid source or make the structural change on the canvas." }];
  }
  return commands;
}

export function paletteBlock(
  kind: "tolerance" | "drawing",
  x = 580,
  y = 650,
  usedBlockIds: ReadonlySet<string> = new Set(),
): RecoveryCommand {
  let index = 1;
  while (usedBlockIds.has(`block.${kind}-${index}`)) index += 1;
  const suffix = `${kind}-${index}`;
  const blockId = `block.${suffix}`;
  const inputId = `port.${suffix}-in`;
  const outputId = `port.${suffix}-out`;
  const drawing = kind === "drawing";
  return {
    kind: "add_block",
    block: {
      id: blockId, kind: "work", title: drawing ? "Create inspection drawing" : "Inspect critical tolerances",
      purpose: drawing ? "Create a reviewable drawing from approved geometry." : "Check critical dimensions against the bracket brief.",
      phaseId: drawing ? "phase.deliver" : "phase.verify", executionKind: "deterministic",
      instructions: drawing ? "Create an A3 drawing with dimensions and source revision." : "Report each tolerance with units and evidence.",
      configuration: drawing ? { sheet: "A3", standard: "ASME Y14.5" } : { tolerance_mm: 0.2 },
      inputPortIds: [inputId], outputPortIds: [outputId], bindingId: null, componentRef: null,
    },
    ports: [
      { id: inputId, ownerBlockId: blockId, direction: "input", name: drawing ? "Approved geometry" : "Bracket geometry", typeId: drawing ? "type.geometry.approved" : "type.geometry.brep", required: true, cardinality: "one", artifactContractId: drawing ? "artifact.approved-geometry" : "artifact.geometry", description: "Selected source geometry." },
      { id: outputId, ownerBlockId: blockId, direction: "output", name: drawing ? "Inspection drawing" : "Tolerance report", typeId: drawing ? "type.file.drawing" : "type.report.tolerance", required: true, cardinality: "one", artifactContractId: null, description: "Reviewable engineering output." },
    ],
    position: { x, y },
  };
}

export function aiDrawingProposal(workflow: RecoveryWorkflow): RecoveryCommandBatch {
  const first: RecoveryBlock = {
    id: "block.create-inspection-drawing", kind: "work", title: "Create inspection drawing",
    purpose: "Create a dimensioned drawing from the approved bracket geometry.", phaseId: "phase.deliver", executionKind: "deterministic",
    instructions: "Create an A3 drawing with critical dimensions, datums, tolerances, and exact source revision.",
    configuration: { sheet: "A3", standard: "ASME Y14.5" }, inputPortIds: ["port.drawing-geometry-in"], outputPortIds: ["port.drawing-out"], bindingId: null, componentRef: null,
  };
  const second: RecoveryBlock = {
    id: "block.review-inspection-drawing", kind: "approval", title: "Review inspection drawing",
    purpose: "Confirm drawing completeness before it enters the review package.", phaseId: "phase.deliver", executionKind: "human",
    instructions: "Accept only when dimensions, tolerances, revision, and source geometry agree.",
    configuration: { required_role: "drawing-checker" }, inputPortIds: ["port.drawing-review-in"], outputPortIds: ["port.drawing-approved-out"], bindingId: null, componentRef: null,
  };
  const ports: RecoveryPort[] = [
    { id: "port.drawing-geometry-in", ownerBlockId: first.id, direction: "input", name: "Approved geometry", typeId: "type.geometry.approved", required: true, cardinality: "one", artifactContractId: "artifact.approved-geometry", description: "Approved bracket geometry." },
    { id: "port.drawing-out", ownerBlockId: first.id, direction: "output", name: "Inspection drawing", typeId: "type.file.drawing", required: true, cardinality: "one", artifactContractId: null, description: "Dimensioned A3 drawing." },
    { id: "port.drawing-review-in", ownerBlockId: second.id, direction: "input", name: "Inspection drawing", typeId: "type.file.drawing", required: true, cardinality: "one", artifactContractId: null, description: "Drawing presented for checking." },
    { id: "port.drawing-approved-out", ownerBlockId: second.id, direction: "output", name: "Approved drawing", typeId: "type.file.drawing.approved", required: true, cardinality: "one", artifactContractId: null, description: "Drawing plus checker decision." },
  ];
  return recoveryCommandBatch(workflow.revision, "ai_proposal", [
      { kind: "add_block", block: first, ports: ports.slice(0, 2), position: { x: 1030, y: 400 } },
      { kind: "add_block", block: second, ports: ports.slice(2), position: { x: 1380, y: 410 } },
      { kind: "connect", relationship: { id: "rel.approved-to-drawing", kind: "data", sourceId: "port.approved-geometry-out", targetId: "port.drawing-geometry-in", label: "approved geometry", condition: "decision.accepted" } },
      { kind: "connect", relationship: { id: "rel.drawing-to-review", kind: "data", sourceId: "port.drawing-out", targetId: "port.drawing-review-in", label: "drawing", condition: null } },
  ]);
}
