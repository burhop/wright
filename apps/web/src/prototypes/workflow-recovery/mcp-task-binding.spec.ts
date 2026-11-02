import templateSource from "../../../../../packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/lightweight-equipment-bracket.workflow.wflow?raw";
import { expect, it } from "vitest";
import { initialWorkflow } from "./model";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  textEditCommands,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import {
  configureMcpTaskServer,
  isUnboundToolTask,
  mcpTaskLabel,
} from "./mcp-task-binding";
import { unconfiguredMcpDiagnostics } from "./run-readiness";

function fixture() {
  const source = templateSource.replaceAll("__instance__", "binding_test");
  const parsed = parseRecoveryAuthoringSource(source, {
    ...initialWorkflow,
    workflowId: "workflow.binding-test",
  });
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const workflow = parsed.workflow!;
  return {
    workflow,
    layout: hydrateAuthoringLayout(workflow),
    block: workflow.blocks[1]!,
  };
}

it("recognizes both unbound tasks without claiming the reference template is runnable", () => {
  const { workflow, block } = fixture();
  expect(isUnboundToolTask(block)).toBe(true);
  expect(mcpTaskLabel(block)).toBe("MCP: not selected");
  expect(
    unconfiguredMcpDiagnostics(workflow).map((issue) => issue.semanticId),
  ).toEqual(workflow.blocks.slice(1).map((block) => block.id));
  expect(configureMcpTaskServer(block, "", "")).toEqual([]);
  expect(isUnboundToolTask({ ...block, bindingId: "existing-binding" })).toBe(
    false,
  );
  expect(
    isUnboundToolTask({
      ...block,
      configuration: { authoring_template: "mcp-tool" },
    }),
  ).toBe(false);
});

it("binds a template task atomically, retaining instructions, ports, identity and order connections through source reopen and undo", () => {
  const { workflow, layout, block } = fixture();
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      configureMcpTaskServer(block, "cad-server", "CAD test server"),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const updated = result.workflow!;
  const task = updated.blocks[1]!;
  expect(task).toMatchObject({
    id: block.id,
    title: block.title,
    purpose: block.purpose,
    instructions: block.instructions,
    executionKind: "ai_capable",
    configuration: {
      authoring_template: "mcp-task",
      mcp_server: "cad-server",
      mcp_server_name: "CAD test server",
    },
  });
  expect(updated.ports).toEqual(workflow.ports);
  expect(updated.relationships).toEqual(workflow.relationships);
  expect(updated.blocks[0]).toEqual(workflow.blocks[0]);
  const source = formatRecoveryAuthoringSource(updated).text;
  expect(source).toContain("performed_by: ai_assisted");
  const reopened = parseRecoveryAuthoringSource(source, workflow);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(reopened.workflow!.blocks[1]).toEqual(task);
  const commands = textEditCommands(workflow, reopened.workflow!, layout);
  expect(commands).toContainEqual({
    kind: "assign_mcp_work_operation",
    blockId: block.id,
  });
  const undone = applyRecoveryBatch(
    updated,
    result.layout!,
    recoveryCommandBatch(updated.revision, "history", [
      { kind: "restore_snapshot", direction: "undo", workflow, layout },
    ]),
  );
  expect(undone.ok, JSON.stringify(undone.diagnostics)).toBe(true);
  expect(undone.workflow!.blocks[1]).toEqual(block);
});

it("updates the server name and identity together on switch and clear without resetting settings", () => {
  const { workflow, layout, block } = fixture();
  block.executionKind = "ai_capable";
  Object.assign(block.configuration, {
    authoring_template: "mcp-task",
    mcp_server: "old",
    mcp_server_name: "Old server",
    max_tool_calls: 16,
  });
  for (const [id, name] of [
    ["other", "Other server"],
    ["", ""],
  ]) {
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(
        workflow.revision,
        "form",
        configureMcpTaskServer(block, id!, name!),
      ),
    );
    expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
    expect(result.workflow!.blocks[1]!.configuration).toMatchObject({
      mcp_server: id,
      mcp_server_name: name,
      max_tool_calls: 16,
      binding_state: id ? "configured" : "unbound",
    });
  }
});
