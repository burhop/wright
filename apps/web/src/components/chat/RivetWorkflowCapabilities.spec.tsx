import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type RivetMcpCapabilities,
  type RivetWorkflowOperation,
} from "../../services/workspace-service";
import { RivetWorkflowCapabilities } from "./RivetWorkflowCapabilities";

vi.mock("../../services/workspace-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...original,
    workspaceService: {
      getRivetMcpCapabilities: vi.fn(),
      previewRivetMcpBindings: vi.fn(),
    },
  };
});

const workflow: RivetWorkflowOperation = {
  workflow_id: "workflow-a",
  slug: "multi-mcp",
  revision: 2,
  etag: "d".repeat(64),
  review_state: null,
  reviewer: null,
  reviewed_at: null,
  stale_reasons: [],
};

const capabilities: RivetMcpCapabilities = {
  workflow_id: "workflow-a",
  slug: "multi-mcp",
  revision: 2,
  etag: "d".repeat(64),
  graph_id: "graph-a",
  snapshot_digest: "e".repeat(64),
  policy_snapshot_digest: "f".repeat(64),
  requirements: [
    {
      graph_id: "graph-a",
      node_id: "node-a",
      node_type: "mcpToolCall",
      static_tool_name: "inspect",
    },
  ],
  issues: [],
  capabilities: ["alpha", "beta"].map((server) => ({
    qualified_tool_name: `${server}__inspect`,
    server_id: server,
    tool_name: "inspect",
    title: `${server} inspect`,
    description: "Inspect a part",
    server_revision: `${server}-v1`,
    capability_digest: "a".repeat(64),
    validation_evidence_id: `${server}-validation`,
    workspace_grant_digest: "b".repeat(64),
    input_schema: { type: "object" },
    output_schema: { type: "object" },
    schema_digest: "c".repeat(64),
    annotations: { readOnlyHint: server === "alpha" },
    required_approvals: server === "beta" ? ["engineering.write"] : [],
    compatibility: "compatible",
    binding_eligible: true,
    blocking_reasons: [],
  })),
  next_after: null,
};

describe("RivetWorkflowCapabilities", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.getRivetMcpCapabilities).mockResolvedValue(
      capabilities,
    );
    vi.mocked(workspaceService.previewRivetMcpBindings).mockResolvedValue({
      workflow_id: "workflow-a",
      slug: "multi-mcp",
      revision: 2,
      etag: "d".repeat(64),
      graph_id: "graph-a",
      snapshot_digest: "e".repeat(64),
      policy_snapshot_digest: "f".repeat(64),
      binding_set_id: "binding-set-a",
      binding_set_digest: "8".repeat(64),
      expires_at: "2099-01-01T00:00:00Z",
      ready: true,
      bindings: [
        {
          node_id: "node-a",
          node_handle: "wright:abcdefghijklmnop",
          selected_tool: "beta__inspect",
          binding_digest: "7".repeat(64),
          server_id: "beta",
          server_revision: "beta-v1",
          schema_digest: "c".repeat(64),
          validation_evidence_id: "beta-validation",
          workspace_grant_digest: "b".repeat(64),
          risk: { required_approvals: ["engineering.write"] },
          units_policy: {},
          material_defaults: {},
          blockers: [],
        },
      ],
    });
  });

  it("resolves an ambiguous node by keyboard and prepares the exact binding", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <RivetWorkflowCapabilities sessionId="session-a" workflow={workflow} />,
    );

    const select = await screen.findByTestId("workflow-binding-select-node-a");
    expect(select).toHaveValue("");
    expect(
      screen.getByTestId("workflow-prepare-binding-summary"),
    ).toBeDisabled();
    await user.selectOptions(select, "beta__inspect");
    await user.click(screen.getByTestId("workflow-prepare-binding-summary"));
    expect(
      await screen.findByTestId("workflow-binding-details-node-a"),
    ).toBeInTheDocument();
    expect(screen.getByText("engineering.write")).toBeInTheDocument();
    expect(container.querySelector("div[style*='auto-fit']")).toBeTruthy();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Tool connections are ready",
    );
    expect(
      screen.queryByText(/approve exact workflow/i),
    ).not.toBeInTheDocument();
  });

  it("never renders review blockers or secret-like fields", async () => {
    render(
      <RivetWorkflowCapabilities
        sessionId="session-a"
        workflow={{
          ...workflow,
          review_state: "approved",
          stale_reasons: ["tool_schema_changed"],
        }}
      />,
    );
    await screen.findByTestId("workflow-binding-select-node-a");
    expect(screen.queryByText(/review is stale/i)).not.toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("token");
    expect(document.body.textContent?.toLowerCase()).not.toContain(
      "authorization",
    );
  });

  it("shows a non-MCP workflow as ready without an approval action", async () => {
    vi.mocked(workspaceService.getRivetMcpCapabilities).mockResolvedValue({
      ...capabilities,
      requirements: [],
      capabilities: [],
    });
    render(
      <RivetWorkflowCapabilities sessionId="session-a" workflow={workflow} />,
    );
    expect(
      await screen.findByText(
        /has no MCP tool-call nodes and is ready to run/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve/i }),
    ).not.toBeInTheDocument();
  });
});
