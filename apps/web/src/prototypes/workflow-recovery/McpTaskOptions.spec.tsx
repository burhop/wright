import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import * as discovery from "./mcp-settings";
import { McpTaskOptions } from "./McpTaskOptions";
import { createAuthoringObject } from "./authoring-objects";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
} from "./command-system";
import { initialWorkflow, initialLayout } from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

afterEach(() => vi.restoreAllMocks());

it("exposes empty and failed discovery, retries, and selects a workspace server with its name", async () => {
  const { workflow, block } = fixture();
  const apply = vi.fn(() => true);
  const load = vi
    .spyOn(discovery, "listWorkflowMcpTools")
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([
      {
        name: "cad__create",
        server_id: "cad",
        server_name: "CAD server",
        tool_name: "create",
        title: "Create",
        description: "",
        input_schema: {},
        schema_digest: "schema",
      },
    ]);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      sessionId="session"
      readOnly={false}
      onApply={apply}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Could not load servers",
  );
  expect(screen.getByRole("combobox", { name: /MCP server/ })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Refresh MCP servers" }));
  expect(
    await screen.findByText("No MCP servers are enabled for this workspace."),
  ).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Refresh MCP servers" }));
  await screen.findByRole("option", { name: "CAD server" });
  fireEvent.change(screen.getByRole("combobox", { name: /MCP server/ }), {
    target: { value: "cad" },
  });
  expect(apply).toHaveBeenCalledWith(
    expect.arrayContaining([
      expect.objectContaining({ key: "mcp_server", value: "cad" }),
      expect.objectContaining({ key: "mcp_server_name", value: "CAD server" }),
    ]),
  );
  expect(load).toHaveBeenCalledTimes(3);
});

it("keeps an unavailable binding visible without substituting or clearing it", async () => {
  const { workflow, block } = fixture();
  Object.assign(block.configuration, {
    mcp_server: "missing",
    mcp_server_name: "Disconnected CAD",
  });
  vi.spyOn(discovery, "listWorkflowMcpTools").mockResolvedValue([]);
  const apply = vi.fn(() => true);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      sessionId="session"
      readOnly
      onApply={apply}
    />,
  );
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent(
      "selected server is unavailable",
    ),
  );
  expect(screen.getByRole("combobox", { name: /MCP server/ })).toHaveValue(
    "missing",
  );
  expect(screen.getByRole("combobox", { name: /MCP server/ })).toBeDisabled();
  expect(apply).not.toHaveBeenCalled();
});

function fixture() {
  const add = createAuthoringObject("mcp-task", initialWorkflow, initialLayout);
  const created = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    applyRecoveryBatch(
      initialWorkflow,
      initialLayout,
      recoveryCommandBatch(initialWorkflow.revision, "form", [add]),
    ),
  )!;
  return {
    ...created,
    block: created.workflow.blocks.find((block) => block.id === add.block.id)!,
  };
}

afterEach(() => vi.unstubAllGlobals());

it("lists configured MCPs without internal services and records an explicit late selection", async () => {
  const { workflow, block } = fixture();
  const tool = {
    name: "cad__create",
    server_id: "cad",
    tool_name: "create",
    title: "Create",
    description: "",
    input_schema: {},
    schema_digest: "digest",
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url === "/api/mcp/servers"
              ? { servers: [{ server_id: "cad", name: "CAD application" }] }
              : {
                  tools: [
                    tool,
                    { ...tool, server_id: "wright-workspace-files" },
                    { ...tool, server_id: "wright-process-validation" },
                  ],
                },
          ),
        ),
    ),
  );
  const apply = vi.fn(() => true);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      sessionId="workspace"
      readOnly={false}
      onApply={apply}
    />,
  );
  await screen.findByRole("option", { name: "CAD application" });
  expect(
    screen.queryByRole("option", { name: "MCP server" }),
  ).not.toBeInTheDocument();
  expect(
    screen.getByRole("option", { name: "Choose server later" }),
  ).toHaveValue("");
  fireEvent.change(screen.getByTestId("workflow-recovery-task-server"), {
    target: { value: "cad" },
  });
  expect(apply).toHaveBeenCalledWith([
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "mcp_server",
      value: "cad",
    },
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "mcp_server_name",
      value: "CAD application",
    },
  ]);
});

it("reports missing server metadata and refreshes without guessing a binding", async () => {
  const { workflow, block } = fixture();
  let available = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) =>
      url === "/api/mcp/servers" && !available
        ? new Response("Unavailable", { status: 503 })
        : new Response(
            JSON.stringify(
              url === "/api/mcp/servers" ? { servers: [] } : { tools: [] },
            ),
          ),
    ),
  );
  const apply = vi.fn(() => true);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      sessionId="workspace"
      readOnly={false}
      onApply={apply}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Could not load workspace MCP servers",
  );
  available = true;
  fireEvent.click(screen.getByRole("button", { name: "Refresh servers" }));
  await screen.findByText(/No MCP servers are available to this workspace/);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(apply).not.toHaveBeenCalled();
});

it("offers32 calls while preserving default8 and the600-second maximum", () => {
  const { workflow, block } = fixture();
  const apply = vi.fn(() => true);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  const calls = screen.getByRole("spinbutton", { name: /Maximum tool calls/ });
  expect(calls).toHaveValue(8);
  expect(calls).toHaveAttribute("max", "32");
  expect(calls).toHaveAttribute("step", "1");
  expect(
    screen.getByText(
      "1–32 calls per task; default 8. The time limit still applies.",
    ),
  ).toBeInTheDocument();
  const timeout = screen.getByRole("spinbutton", {
    name: "Time limit (seconds)",
  });
  expect(timeout).toHaveValue(300);
  expect(timeout).toHaveAttribute("max", "600");
  fireEvent.change(calls, { target: { value: "32" } });
  expect(apply).toHaveBeenCalledWith([
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "max_tool_calls",
      value: 32,
    },
  ]);
});

it("preserves an accepted32-call budget through canonical source reopen", () => {
  const { workflow, layout, block } = fixture();
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", [
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "max_tool_calls",
        value: 32,
      },
    ]),
  );
  expect(result.ok).toBe(true);
  const accepted = acceptRecoveryResult(workflow, layout, result)!;
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(reopened.ok).toBe(true);
  expect(
    reopened.workflow!.blocks.find((item) => item.id === block.id)!
      .configuration.max_tool_calls,
  ).toBe(32);
});

it.each([33, 0, 1.5, true, "32"])(
  "rejects invalid budget %s through the shared authoring command boundary",
  (value) => {
    const { workflow, layout, block } = fixture();
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", [
        {
          kind: "set_block_configuration",
          blockId: block.id,
          key: "max_tool_calls",
          value,
        },
      ]),
    );
    expect(result.ok).toBe(false);
    expect(result.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-MCP-TASK-LIMIT-INVALID" }),
    );
    expect(block.configuration.max_tool_calls).toBe(8);
    const invalidSource = formatRecoveryAuthoringSource({
      ...workflow,
      blocks: workflow.blocks.map((item) =>
        item.id === block.id
          ? {
              ...item,
              configuration: { ...item.configuration, max_tool_calls: value },
            }
          : item,
      ),
    }).text;
    const parsed = parseRecoveryAuthoringSource(invalidSource, initialWorkflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-MCP-TASK-LIMIT-INVALID" }),
    );
  },
);
