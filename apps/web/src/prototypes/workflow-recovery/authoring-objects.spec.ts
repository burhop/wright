import { describe, expect, it } from "vitest";

import { canonicalDefinitionBytes } from "./canonical-wire";
import { acceptRecoveryResult, applyRecoveryBatch, recoveryCommandBatch, textEditCommands, type RecoveryCommand } from "./command-system";
import { cloneLayout, cloneWorkflow, initialLayout, initialWorkflow, type RecoveryLayout, type RecoveryWorkflow } from "./model";
import { formatRecoveryAuthoringSource, parseRecoveryAuthoringSource, validateRecoveryAuthoringRoundTrip } from "./recovery-authoring";
import {
  AUTHORING_GROUPS, AUTHORING_TEMPLATES, authoringConfigurationCommands,
  authoringDeletionImpact, authoringInputState, authoringReadiness,
  buildDeletionCommands, createAuthoringObject, findAuthoringPosition,
  hydrateAuthoringLayout,
} from "./authoring-objects";

function apply(workflow: RecoveryWorkflow, layout: RecoveryLayout, commands: RecoveryCommand[]) {
  const result = applyRecoveryBatch(workflow, layout, recoveryCommandBatch(workflow.revision, "graph", commands));
  expect(result.ok, result.diagnostics.map((item) => `${item.code}: ${item.explanation}`).join("\n")).toBe(true);
  return acceptRecoveryResult(workflow, layout, result)!;
}

describe("native authoring objects", () => {
  it("offers seven curated groups with real, independently identified unbound templates", () => {
    expect(AUTHORING_GROUPS.map((group) => group.label)).toEqual(["Input", "LLM document", "MCP tools", "3D check", "Drawing", "FDM", "More"]);
    for (const group of AUTHORING_GROUPS) expect(AUTHORING_TEMPLATES.some((template) => template.group === group.id)).toBe(true);
    for (const template of AUTHORING_TEMPLATES) {
      const command = createAuthoringObject(template.id, initialWorkflow, initialLayout);
      expect(command.block.bindingId).toBeNull();
      expect(command.block.phaseId).toBeNull();
      expect(command.block.componentRef).toBeNull();
      expect(command.ports.every((port) => port.artifactContractId === null && port.ownerBlockId === command.block.id)).toBe(true);
      const accepted = apply(initialWorkflow, initialLayout, [command]);
      const roundTrip = validateRecoveryAuthoringRoundTrip(accepted.workflow);
      expect(roundTrip.ok, `${template.id}: ${roundTrip.diagnostics.map((item) => item.code)}`).toBe(true);
      expect(canonicalDefinitionBytes(roundTrip.workflow!, true)).toBe(canonicalDefinitionBytes(accepted.workflow, true));
    }
  });

  it("keeps repeated objects and each exact port distinct after source reconstruction", () => {
    let state = { workflow: cloneWorkflow(initialWorkflow), layout: cloneLayout(initialLayout) };
    for (let index = 0; index < 8; index += 1) {
      const command = createAuthoringObject("text-input", state.workflow, state.layout);
      state = apply(state.workflow, state.layout, [command]);
    }
    const blocks = state.workflow.blocks.filter((block) => block.configuration.authoring_template === "text-input");
    expect(new Set(blocks.map((block) => block.id)).size).toBe(8);
    expect(new Set(blocks.flatMap((block) => block.outputPortIds)).size).toBe(8);
    expect(new Set(blocks.map((block) => JSON.stringify(state.layout.positions[block.id]))).size).toBe(8);
    const reopened = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(state.workflow).text, initialWorkflow);
    expect(reopened.ok).toBe(true);
    expect(reopened.workflow!.blocks.filter((block) => block.configuration.authoring_template === "text-input").map((block) => block.id)).toEqual(blocks.map((block) => block.id));
  });

  it("persists actual multiline text and workspace references through commands and cold reopen", () => {
    const command = createAuthoringObject("text-input", initialWorkflow, initialLayout);
    const added = apply(initialWorkflow, initialLayout, [command]);
    const text = 'Support the enclosure.\nLoad: 1.8 kN; material: 6061-T6.\nDo not assume a "PDF brief".';
    const configured = apply(added.workflow, added.layout, authoringConfigurationCommands(command.block, { input_text: text }));
    const reopened = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(configured.workflow).text, initialWorkflow);
    const input = reopened.workflow!.blocks.find((block) => block.id === command.block.id)!;
    expect(input.configuration.input_text).toBe(text);
    expect(authoringInputState(input).status).toBe("configured");
    const file = apply(configured.workflow, configured.layout, authoringConfigurationCommands(input, { input_mode: "workspace-file", workspace_file: "design/Requirements rev 3.docx" }));
    const loadedFile = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(file.workflow).text, initialWorkflow).workflow!.blocks.find((block) => block.id === input.id)!;
    expect(authoringInputState(loadedFile).summary).toContain("Requirements rev 3.docx");
    expect(authoringInputState(loadedFile, []).status).toBe("unavailable");
    expect(authoringInputState(loadedFile, ["design/Requirements rev 3.docx"]).status).toBe("configured");
  });

  it("does not infer configured inputs from demo filenames or tool bindings", () => {
    const readiness = authoringReadiness(initialWorkflow);
    expect(readiness.totalCount).toBe(3);
    expect(readiness.configuredCount).toBe(0);
    expect(readiness.inputs.every((input) => input.status === "missing")).toBe(true);
  });

  it("connects a real workspace document to the distinct file input of a document step", () => {
    const input = createAuthoringObject("file-input", initialWorkflow, initialLayout);
    let state = apply(initialWorkflow, initialLayout, [input]);
    state = apply(state.workflow, state.layout, authoringConfigurationCommands(input.block, { workspace_file: "requirements/design-notes.txt" }));
    const document = createAuthoringObject("document", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [document]);
    const filePort = document.ports.find((port) => port.typeId === "type.file.workspace")!;
    state = apply(state.workflow, state.layout, [{ kind: "connect", relationship: { id: "rel.file-to-document", kind: "data", sourceId: input.block.outputPortIds[0]!, targetId: filePort.id, label: "Reference document", condition: null } }]);
    expect(validateRecoveryAuthoringRoundTrip(state.workflow).ok).toBe(true);
    expect(document.block.inputPortIds).toHaveLength(2);
    expect(filePort.id).not.toBe(document.block.inputPortIds[0]);
  });

  it("preserves exact fan-out endpoints and rejects incompatible or collection-to-single wiring atomically", () => {
    let state = { workflow: cloneWorkflow(initialWorkflow), layout: cloneLayout(initialLayout) };
    const input = createAuthoringObject("text-input", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [input]);
    const first = createAuthoringObject("document", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [first]);
    const second = createAuthoringObject("document", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [second]);
    state = apply(state.workflow, state.layout, [first, second].map((document, index) => ({ kind: "connect", relationship: { id: `rel.document-fanout-${index}`, kind: "data", sourceId: input.block.outputPortIds[0]!, targetId: document.block.inputPortIds[0]!, label: "Design text", condition: null } })));
    const source = formatRecoveryAuthoringSource(state.workflow).text;
    const reopened = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(reopened.ok).toBe(true);
    expect(reopened.workflow!.relationships.filter((relationship) => relationship.sourceId === input.block.outputPortIds[0])).toHaveLength(2);
    const before = canonicalDefinitionBytes(state.workflow);
    const invalid = applyRecoveryBatch(state.workflow, state.layout, recoveryCommandBatch(state.workflow.revision, "graph", [{ kind: "connect", relationship: { id: "rel.wrong-kind", kind: "data", sourceId: first.block.outputPortIds[0]!, targetId: second.block.inputPortIds[0]!, label: "Wrong type", condition: null } }]));
    expect(invalid.ok).toBe(false);
    expect(canonicalDefinitionBytes(state.workflow)).toBe(before);
    const collection = applyRecoveryBatch(state.workflow, state.layout, recoveryCommandBatch(state.workflow.revision, "form", [{ kind: "set_port_contract", portId: input.block.outputPortIds[0]!, required: true, cardinality: "many" }]));
    expect(collection.ok).toBe(false);
    expect(collection.diagnostics.some((item) => item.code === "WFR-PORT-COLLECTION-MISMATCH")).toBe(true);
    expect(canonicalDefinitionBytes(state.workflow)).toBe(before);
    const unsafeSource = cloneWorkflow(state.workflow);
    unsafeSource.ports.find((port) => port.id === input.block.outputPortIds[0])!.cardinality = "many";
    expect(parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(unsafeSource).text, initialWorkflow).ok).toBe(false);
    const collectingInput = apply(state.workflow, state.layout, [{ kind: "set_port_contract", portId: first.block.inputPortIds[0]!, required: true, cardinality: "many" }]);
    expect(validateRecoveryAuthoringRoundTrip(collectingInput.workflow).ok).toBe(true);
  });

  it.each(["../outside.txt", "/outside.txt", "C:/outside.txt", "\\\\server\\share.txt", "inputs/../../outside", "inputs/%2e%2e/secret", "inputs/.wright/head.json", "inputs/file.txt:secret", "inputs\\file.txt", "https://example.com/file.txt", "inputs/CON.txt", "inputs/file.txt\u0000"])("rejects unsafe workspace reference %s in graph and source", (workspaceFile) => {
    const command = createAuthoringObject("file-input", initialWorkflow, initialLayout);
    expect(() => authoringConfigurationCommands(command.block, { workspace_file: workspaceFile })).toThrow();
    command.block.configuration.workspace_file = workspaceFile;
    const rejected = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "graph", [command]));
    expect(rejected.ok).toBe(false);
    expect(rejected.diagnostics.some((item) => item.code === "WFR-INPUT-PATH-INVALID")).toBe(true);
    const unsafe = cloneWorkflow(initialWorkflow);
    unsafe.blocks[1]!.configuration.workspace_file = workspaceFile;
    const parsed = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(unsafe).text, initialWorkflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.diagnostics.some((item) => item.code === "WFR-INPUT-PATH-INVALID")).toBe(true);
  });

  it("places objects away from existing nodes and hydrates missing/deleted positions without changing semantics", () => {
    const first = findAuthoringPosition(initialWorkflow, initialLayout, { x: 40, y: 130 });
    expect(Object.values(initialLayout.positions).some((position) => Math.abs(position.x - first.x) < 250 && Math.abs(position.y - first.y) < 150)).toBe(false);
    const command = createAuthoringObject("text-input", initialWorkflow, initialLayout);
    const added = apply(initialWorkflow, initialLayout, [command]);
    const remembered = cloneLayout(initialLayout);
    remembered.positions["block.deleted"] = { x: 123, y: 456 };
    const bytes = canonicalDefinitionBytes(added.workflow);
    const hydrated = hydrateAuthoringLayout(added.workflow, remembered);
    expect(hydrated.positions["block.deleted"]).toBeUndefined();
    expect(hydrated.positions[command.block.id]).toBeDefined();
    expect(hydrated.semanticRevision).toBe(added.workflow.revision);
    expect(canonicalDefinitionBytes(added.workflow)).toBe(bytes);
    expect(hydrateAuthoringLayout(added.workflow, hydrated)).toEqual(hydrated);
  });

  it("uses readable starter positions for a new workflow identity while preserving its own saved moves", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    workflow.workflowId = "workflow.authored-new-design";
    const layout = hydrateAuthoringLayout(workflow);
    expect(layout.workflowId).toBe(workflow.workflowId);
    expect(layout.positions).toEqual(initialLayout.positions);
    layout.positions["block.design-intent"] = { x: 123, y: 567 };
    expect(hydrateAuthoringLayout(workflow, layout).positions["block.design-intent"]).toEqual({ x: 123, y: 567 });
    expect(hydrateAuthoringLayout(workflow, initialLayout).positions).not.toEqual(initialLayout.positions);
  });

  it("places source additions without overlap across sequential additions", () => {
    let state = { workflow: cloneWorkflow(initialWorkflow), layout: cloneLayout(initialLayout) };
    for (let index = 0; index < 3; index += 1) {
      const addition = createAuthoringObject("document", state.workflow, state.layout);
      const proposed = apply(state.workflow, state.layout, [addition]);
      const source = formatRecoveryAuthoringSource(proposed.workflow).text;
      const parsed = parseRecoveryAuthoringSource(source, state.workflow);
      expect(parsed.ok).toBe(true);
      const commands = textEditCommands(state.workflow, parsed.workflow!, state.layout) as RecoveryCommand[];
      expect(commands.every((item) => "kind" in item)).toBe(true);
      state = apply(state.workflow, state.layout, commands);
    }
    const positions = state.workflow.blocks.filter((block) => block.configuration.authoring_template === "document").map((block) => state.layout.positions[block.id]!);
    for (let left = 0; left < positions.length; left += 1) for (let right = left + 1; right < positions.length; right += 1) {
      expect(Math.abs(positions[left]!.x - positions[right]!.x) >= 250 || Math.abs(positions[left]!.y - positions[right]!.y) >= 150).toBe(true);
    }
  });

  it("reviews complete connection impact and deletes added objects atomically", () => {
    let state = { workflow: cloneWorkflow(initialWorkflow), layout: cloneLayout(initialLayout) };
    const input = createAuthoringObject("text-input", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [input]);
    const document = createAuthoringObject("document", state.workflow, state.layout);
    state = apply(state.workflow, state.layout, [document]);
    state = apply(state.workflow, state.layout, [{ kind: "connect", relationship: { id: "rel.new-input", kind: "data", sourceId: input.ports[0]!.id, targetId: document.ports[0]!.id, label: "Design text", condition: null } }]);
    expect(authoringDeletionImpact(state.workflow, input.block.id).relationships.map((item) => item.id)).toEqual(["rel.new-input"]);
    const removal = buildDeletionCommands(state.workflow, input.block.id);
    expect(removal.map((item) => item.kind)).toEqual(["disconnect", "delete_block"]);
    const deleted = apply(state.workflow, state.layout, removal);
    expect(deleted.workflow.blocks.some((block) => block.id === input.block.id)).toBe(false);
    expect(deleted.workflow.relationships.some((relationship) => relationship.id === "rel.new-input")).toBe(false);
    expect(validateRecoveryAuthoringRoundTrip(deleted.workflow).ok).toBe(true);
    expect(authoringDeletionImpact(initialWorkflow, "block.generate-geometry").blockedReason).toBeTruthy();
  });
});
