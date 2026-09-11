import { expect, it } from "vitest";
import { initialWorkflow, initialLayout } from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import { createMcpServerBlock, mcpServerChoices } from "./mcp-server-blocks";
import type { WorkflowMcpTool } from "./mcp-settings";

const tools: WorkflowMcpTool[] = [
  "cad.list_providers",
  "cad.list_documents",
  "cad.save_document",
  "cad.create_part_from_recipe",
  "cad.create_sheet_metal_from_recipe",
].map((tool_name) => ({
  name: `server-id__${tool_name}`,
  server_id: "server-id",
  server_name: "Solid Edge Local",
  tool_name,
  title: tool_name,
  description: "",
  input_schema: {},
  schema_digest: "schema",
}));

it("adds one server-bound CAD task with a model output and editable prompt in one undoable transaction", () => {
  const servers = mcpServerChoices(tools);
  expect(servers).toHaveLength(1);
  const commands = createMcpServerBlock(
    servers[0]!,
    initialWorkflow,
    initialLayout,
  );
  const result = applyRecoveryBatch(
    initialWorkflow,
    initialLayout,
    recoveryCommandBatch(initialWorkflow.revision, "graph", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    result,
  )!;
  expect(accepted.workflow.revision).toBe(initialWorkflow.revision + 1);
  const task = accepted.workflow.blocks.at(-1)!;
  expect(task).toMatchObject({
    title: "Solid Edge Local",
    instructions: "",
    executionKind: "ai_capable",
    configuration: {
      authoring_template: "mcp-task",
      mcp_server: "server-id",
      file_policy: "indexed",
    },
  });
  expect(JSON.parse(String(task.configuration.cad))).toMatchObject({
    source: "new",
    native_path: "model.par",
    policy: "indexed",
    exports: [],
  });
  expect(
    accepted.workflow.ports
      .filter((port) => port.ownerBlockId === task.id)
      .map((port) => port.name),
  ).toEqual(["Task result", "CAD model"]);
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(reopened.ok).toBe(true);
  expect(
    reopened.workflow!.blocks.find((block) => block.id === task.id)!
      .configuration,
  ).toEqual(task.configuration);
});

it("uses the same AI task for servers with other operations without inventing CAD capabilities", () => {
  const server = mcpServerChoices([
    { ...tools[0]!, server_name: "BREP", tool_name: "create_shape" },
  ])[0]!;
  const commands = createMcpServerBlock(server, initialWorkflow, initialLayout);
  expect(commands).toHaveLength(1);
  expect(commands[0]).toMatchObject({
    kind: "add_block",
    block: {
      title: "BREP",
      configuration: {
        authoring_template: "mcp-task",
        mcp_server: "server-id",
      },
    },
  });
  if (commands[0]!.kind === "add_block")
    expect(commands[0]!.block.configuration.cad).toBeUndefined();
});
