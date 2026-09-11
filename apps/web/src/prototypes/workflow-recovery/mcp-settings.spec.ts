import { expect, it } from "vitest";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
  type RecoveryCommand,
} from "./command-system";
import {
  initialWorkflow,
  initialLayout,
  type RecoveryWorkflow,
  type RecoveryLayout,
} from "./model";
import { createAuthoringObject } from "./authoring-objects";
import {
  configureMcpTool,
  connectMcpInput,
  mcpCandidates,
  type WorkflowMcpTool,
} from "./mcp-settings";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
const tool: WorkflowMcpTool = {
  name: "docs__search",
  server_id: "docs",
  tool_name: "search",
  title: "Search docs",
  description: "Search documentation",
  schema_digest: "a".repeat(64),
  input_schema: {
    type: "object",
    properties: {
      query: { type: "string" },
      limit: { type: "integer", default: 3 },
    },
    required: ["query"],
  },
};
function apply(
  state: { workflow: RecoveryWorkflow; layout: RecoveryLayout },
  commands: RecoveryCommand[],
) {
  const result = applyRecoveryBatch(
    state.workflow,
    state.layout,
    recoveryCommandBatch(state.workflow.revision, "form", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  return acceptRecoveryResult(state.workflow, state.layout, result)!;
}
it("binds discovered tool inputs, connects a prompt response, and reconstructs from workspace source", () => {
  let state = { workflow: initialWorkflow, layout: initialLayout };
  const added = createAuthoringObject("mcp-tool", state.workflow, state.layout);
  state = apply(state, [added]);
  state = apply(state, configureMcpTool(added.block, state.workflow, tool));
  const prompt = createAuthoringObject(
    "ai-prompt",
    state.workflow,
    state.layout,
  );
  state = apply(state, [prompt]);
  const block = state.workflow.blocks.find((b) => b.id === added.block.id)!;
  const target = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "query",
  )!;
  const response = prompt.ports.find((p) => p.direction === "output")!;
  expect(
    mcpCandidates(block, state.workflow, target).some(
      (p) => p.id === response.id,
    ),
  ).toBe(true);
  expect(
    mcpCandidates(block, state.workflow, target).some(
      (p) => p.typeId === "type.image.reference-set",
    ),
  ).toBe(false);
  state = apply(
    state,
    connectMcpInput(block, state.workflow, target.id, response.id),
  );
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(state.workflow).text,
    initialWorkflow,
  );
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(
    reopened.workflow!.blocks.find((b) => b.id === block.id)!.configuration
      .mcp_tool,
  ).toBe(tool.name);
  expect(
    reopened.workflow!.relationships.some(
      (e) => e.sourceId === response.id && e.targetId === target.id,
    ),
  ).toBe(true);
  const changed = apply(
    state,
    configureMcpTool(
      state.workflow.blocks.find((b) => b.id === block.id)!,
      state.workflow,
      {
        ...tool,
        name: "docs__list",
        input_schema: { type: "object", properties: {} },
      },
    ),
  );
  expect(
    changed.workflow.ports.filter(
      (p) => p.ownerBlockId === block.id && p.direction === "input",
    ),
  ).toHaveLength(1);
  expect(
    changed.workflow.relationships.some((e) => e.targetId === target.id),
  ).toBe(false);
});
it("converts compatible text connection types atomically and rejects non-JSON whole arguments", () => {
  let state = { workflow: initialWorkflow, layout: initialLayout };
  const added = createAuthoringObject("mcp-tool", state.workflow, state.layout);
  state = apply(state, [added]);
  state = apply(state, configureMcpTool(added.block, state.workflow, tool));
  const block = state.workflow.blocks.find((b) => b.id === added.block.id)!;
  const target = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "query",
  )!;
  const textBlock = createAuthoringObject(
    "text-input",
    state.workflow,
    state.layout,
  );
  state = apply(state, [textBlock]);
  const text = state.workflow.ports.find(
    (p) =>
      p.direction === "output" &&
      p.typeId === "type.value.text" &&
      p.ownerBlockId !== block.id,
  )!;
  state = apply(
    state,
    connectMcpInput(block, state.workflow, target.id, text.id),
  );
  expect(state.workflow.ports.find((p) => p.id === target.id)!.typeId).toBe(
    text.typeId,
  );
  const args = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "Arguments (JSON)",
  )!;
  expect(() =>
    connectMcpInput(block, state.workflow, args.id, text.id),
  ).toThrow("matches");
});
