import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import {
  AuthoringCreateRail,
  AuthoringRunReadiness,
} from "./AuthoringControls";
import { McpBlockEditor } from "./McpBlockEditor";
import { createAuthoringObject } from "./authoring-objects";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
} from "./command-system";
import { createMcpServerBlock, mcpServerChoices } from "./mcp-server-blocks";
import { initialWorkflow, initialLayout } from "./model";
import { connectPromptCommands } from "./prompt-settings";
import {
  listWorkflowMcpTools,
  workflowMcpServerName,
  type WorkflowMcpTool,
} from "./mcp-settings";

const serverId = "b508eb0c-4744-480a-8c1f-fb0fe3f53eac";
const tool: WorkflowMcpTool = {
  name: `${serverId}__browser_click`,
  server_id: serverId,
  tool_name: "browser_click",
  title: "Click",
  description: "Click an element",
  input_schema: { type: "object", properties: {} },
  schema_digest: "schema",
};
function mockDiscovery(namesAvailable = true, tools = [tool]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) =>
      url === "/api/mcp/servers"
        ? namesAvailable
          ? new Response(
              JSON.stringify({
                servers: [
                  { server_id: serverId, name: "Workflow Browser Local" },
                ],
              }),
            )
          : new Response("Unavailable", { status: 503 })
        : new Response(JSON.stringify({ tools })),
    ),
  );
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("resolves registry names without changing tool routing identities", async () => {
  mockDiscovery();
  expect(await listWorkflowMcpTools("workspace session")).toEqual([
    { ...tool, server_name: "Workflow Browser Local", workspace_server: true },
  ]);
  expect(fetch).toHaveBeenCalledWith(
    "/api/workspace/workflow-sources/tools?session_id=workspace%20session",
    expect.anything(),
  );
});

it("reports registry failures instead of offering indistinguishable unnamed servers", async () => {
  mockDiscovery(false);
  await expect(listWorkflowMcpTools("session")).rejects.toThrow(
    "MCP server registry",
  );
  expect(workflowMcpServerName({ server_name: serverId })).toBe("MCP server");
});

it("offers server tasks without exposing any individual tool as a block", async () => {
  const titles = [
    "Click",
    "Drag mouse",
    "Close browser",
    "Evaluate JavaScript",
    "Custom operation",
  ];
  mockDiscovery(
    true,
    titles.map((title, index) => ({
      ...tool,
      title,
      name: `${serverId}__operation_${index}`,
      tool_name: `operation_${index}`,
    })),
  );
  const onCreate = vi.fn();
  const onCreateServer = vi.fn();
  render(
    <AuthoringCreateRail
      disabled={false}
      sessionId="session"
      onCreate={onCreate}
      onCreateServer={onCreateServer}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Add step" }));
  fireEvent.click(screen.getByRole("button", { name: "MCP servers" }));
  const primary = await screen.findByTestId(
    `workflow-recovery-create-server-${serverId}`,
  );
  expect(document.querySelector(".recovery-create-template")).toBe(
    screen.getByTestId("workflow-recovery-create-template-mcp-task"),
  );
  expect(document.querySelectorAll(".recovery-create-template")).toHaveLength(
    2,
  );
  for (const title of titles)
    expect(screen.queryByText(title)).not.toBeInTheDocument();
  expect(screen.queryByText("Advanced")).not.toBeInTheDocument();
  expect(screen.queryByText("Choose an exact tool")).not.toBeInTheDocument();
  expect(screen.queryByText(serverId)).not.toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: "Add or enable a server" }),
  ).toHaveAttribute("href", "/tool-registry");
  fireEvent.click(primary);
  expect(onCreateServer).toHaveBeenCalledWith(
    expect.objectContaining({
      id: serverId,
      name: "Workflow Browser Local",
      tools: expect.arrayContaining([
        expect.objectContaining({ title: "Click" }),
      ]),
    }),
  );
  expect(onCreate).not.toHaveBeenCalled();
});

it("keeps internal Wright services out of the MCP server palette and allows deferred binding", async () => {
  mockDiscovery(true, [
    tool,
    {
      ...tool,
      server_id: "wright-workspace-files",
      tool_name: "write_text_document",
    },
    { ...tool, server_id: "wright-process-validation", tool_name: "evaluate" },
  ]);
  const onCreate = vi.fn();
  render(
    <AuthoringCreateRail
      disabled={false}
      sessionId="session"
      onCreate={onCreate}
      onCreateServer={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Add step" }));
  fireEvent.click(screen.getByRole("button", { name: "MCP servers" }));
  await screen.findByTestId(`workflow-recovery-create-server-${serverId}`);
  expect(
    document.querySelectorAll(
      '[data-testid^="workflow-recovery-create-server-"]',
    ),
  ).toHaveLength(1);
  expect(
    screen.queryByText("MCP server", { exact: true }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: /MCP task · choose server later/ }),
  );
  expect(onCreate).toHaveBeenCalledExactlyOnceWith("mcp-task");
});

it("clears the previous server choices when the workspace scope disappears", async () => {
  mockDiscovery();
  const onCreate = vi.fn();
  const onCreateServer = vi.fn();
  const view = render(
    <AuthoringCreateRail
      disabled={false}
      sessionId="session"
      onCreate={onCreate}
      onCreateServer={onCreateServer}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Add step" }));
  fireEvent.click(screen.getByRole("button", { name: "MCP servers" }));
  await screen.findByTestId(`workflow-recovery-create-server-${serverId}`);
  view.rerender(
    <AuthoringCreateRail
      disabled={false}
      onCreate={onCreate}
      onCreateServer={onCreateServer}
    />,
  );
  expect(
    screen.queryByTestId(`workflow-recovery-create-server-${serverId}`),
  ).not.toBeInTheDocument();
  expect(
    screen.getByText("Open a workspace to choose an MCP server."),
  ).toBeInTheDocument();
});

it("keeps server names readable in the inspector while binding the original tool ID", async () => {
  mockDiscovery();
  const add = createAuthoringObject("mcp-tool", initialWorkflow, initialLayout);
  const workflow = {
    ...initialWorkflow,
    blocks: [...initialWorkflow.blocks, add.block],
    ports: [...initialWorkflow.ports, ...add.ports],
  };
  const onApply = vi.fn(() => true);
  render(
    <McpBlockEditor
      block={add.block}
      workflow={workflow}
      sessionId="session"
      readOnly={false}
      onApply={onApply}
    />,
  );
  expect(
    await screen.findByRole("option", {
      name: "Click · Workflow Browser Local",
    }),
  ).toHaveValue(tool.name);
  fireEvent.change(screen.getByTestId("workflow-recovery-mcp-tool"), {
    target: { value: tool.name },
  });
  expect(onApply).toHaveBeenCalledWith(
    expect.arrayContaining([
      expect.objectContaining({
        kind: "set_block_configuration",
        key: "mcp_server",
        value: serverId,
      }),
      expect.objectContaining({
        kind: "set_block_configuration",
        key: "mcp_tool",
        value: tool.name,
      }),
    ]),
  );
  expect(screen.queryByText(serverId)).not.toBeInTheDocument();
});

it("shows server-scoped tasks as available and supports an explicit inventory recheck", async () => {
  mockDiscovery();
  const server = mcpServerChoices([tool])[0]!;
  const commands = createMcpServerBlock(server, initialWorkflow, initialLayout);
  const result = applyRecoveryBatch(
    initialWorkflow,
    initialLayout,
    recoveryCommandBatch(initialWorkflow.revision, "graph", commands),
  );
  const workflow = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    result,
  )!.workflow;
  render(
    <AuthoringRunReadiness
      workflow={workflow}
      saved={true}
      executionConnected={true}
      sessionId="session"
      onSelect={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-run-readiness-toggle"));
  expect(
    await screen.findByText(/AI selects the operation · available/),
  ).toBeInTheDocument();
  expect(screen.queryByText("Unbound tasks")).not.toBeInTheDocument();
  expect(screen.getByText("Task instructions needed")).toBeInTheDocument();
  const callsBeforeRefresh = vi.mocked(fetch).mock.calls.length;
  const refresh = screen.getByTestId("workflow-recovery-mcp-refresh");
  fireEvent.click(refresh);
  expect(vi.mocked(fetch).mock.calls.length).toBeGreaterThan(
    callsBeforeRefresh,
  );
});

it.each(["ai-prompt", "mcp-task"])(
  "reports an empty %s prompt and focuses its exact inspector",
  (template) => {
    const task = createAuthoringObject(
      template,
      initialWorkflow,
      initialLayout,
    );
    task.block.instructions = "";
    const added = applyRecoveryBatch(
      initialWorkflow,
      initialLayout,
      recoveryCommandBatch(initialWorkflow.revision, "graph", [task]),
    );
    const workflow = acceptRecoveryResult(
      initialWorkflow,
      initialLayout,
      added,
    )!.workflow;
    const onSelect = vi.fn();
    const props = { saved: true, executionConnected: true, onSelect };
    const { rerender } = render(
      <AuthoringRunReadiness {...props} workflow={workflow} />,
    );
    const issueId = `workflow-recovery-readiness-prompt-${task.block.id}`;
    fireEvent.click(screen.getByTestId(issueId));
    expect(onSelect).toHaveBeenCalledWith(task.block.id);
    rerender(
      <AuthoringRunReadiness
        {...props}
        workflow={{
          ...workflow,
          blocks: workflow.blocks.map((block) =>
            block.id === task.block.id
              ? { ...block, instructions: "Calculate volume." }
              : block,
          ),
        }}
      />,
    );
    expect(screen.queryByTestId(issueId)).not.toBeInTheDocument();
  },
);

it("requires the declared prompt connection even when retained inline text is present", () => {
  const input = createAuthoringObject(
    "text-input",
    initialWorkflow,
    initialLayout,
  );
  const first = applyRecoveryBatch(
    initialWorkflow,
    initialLayout,
    recoveryCommandBatch(initialWorkflow.revision, "graph", [input]),
  );
  let state = acceptRecoveryResult(initialWorkflow, initialLayout, first)!;
  const task = createAuthoringObject("mcp-task", state.workflow, state.layout);
  const added = applyRecoveryBatch(
    state.workflow,
    state.layout,
    recoveryCommandBatch(state.workflow.revision, "graph", [task]),
  );
  state = acceptRecoveryResult(state.workflow, state.layout, added)!;
  const connected = applyRecoveryBatch(
    state.workflow,
    state.layout,
    recoveryCommandBatch(
      state.workflow.revision,
      "graph",
      connectPromptCommands(task.block, state.workflow, input.ports[0]!.id),
    ),
  );
  state = acceptRecoveryResult(state.workflow, state.layout, connected)!;
  const props = { saved: true, executionConnected: true, onSelect: vi.fn() };
  const { rerender } = render(
    <AuthoringRunReadiness {...props} workflow={state.workflow} />,
  );
  const issueId = `workflow-recovery-readiness-prompt-${task.block.id}`;
  expect(screen.queryByTestId(issueId)).not.toBeInTheDocument();
  rerender(
    <AuthoringRunReadiness
      {...props}
      workflow={{
        ...state.workflow,
        blocks: state.workflow.blocks.map((block) =>
          block.id === task.block.id
            ? { ...block, instructions: "Old inline instructions" }
            : block,
        ),
        relationships: state.workflow.relationships.filter(
          (edge) => edge.sourceId !== input.ports[0]!.id,
        ),
      }}
    />,
  );
  expect(screen.getByTestId(issueId)).toBeInTheDocument();
});
