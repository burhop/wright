import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { AuthoringCreateRail } from "./AuthoringControls";
import { McpBlockEditor } from "./McpBlockEditor";
import { createAuthoringObject } from "./authoring-objects";
import { initialWorkflow, initialLayout } from "./model";
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
    { ...tool, server_name: "Workflow Browser Local" },
  ]);
  expect(fetch).toHaveBeenCalledWith(
    "/api/workspace/workflow-sources/tools?session_id=workspace%20session",
    expect.anything(),
  );
});

it("does not replace a missing display name with a server GUID", async () => {
  mockDiscovery(false);
  const [available] = await listWorkflowMcpTools("session");
  expect(available.server_id).toBe(serverId);
  expect(workflowMcpServerName(available)).toBe("MCP server");
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
  fireEvent.click(screen.getByRole("button", { name: "MCP servers" }));
  const primary = await screen.findByTestId(
    `workflow-recovery-create-server-${serverId}`,
  );
  expect(document.querySelector(".recovery-create-template")).toBe(primary);
  expect(document.querySelectorAll(".recovery-create-template")).toHaveLength(
    1,
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
