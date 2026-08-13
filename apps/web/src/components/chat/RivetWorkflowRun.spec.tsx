import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type RivetCallApproval,
  type RivetWorkflowRun as RivetWorkflowRunRecord,
} from "../../services/workspace-service";
import { RivetWorkflowRun } from "./RivetWorkflowRun";

vi.mock("../../services/workspace-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...original,
    workspaceService: {
      getRivetWorkflowRun: vi.fn(),
      getRivetCallApprovals: vi.fn(),
      getRivetWorkflowHistory: vi.fn(),
      getRivetRunEvidence: vi.fn(),
      exportRivetRunEvidence: vi.fn(),
      decideRivetCallApproval: vi.fn(),
    },
  };
});

const run: RivetWorkflowRunRecord = {
  run_id: "run-1",
  workflow_id: "workflow-1",
  revision: 1,
  digest: "a".repeat(64),
  graph: "Main",
  generation: 1,
  state: "succeeded",
  reason: null,
  outputs: {},
  duration_ms: 10,
  output_truncated: false,
};

const approval: RivetCallApproval = {
  approval_id: "approval-1",
  run_id: "run-1",
  node_id: "node-beta",
  qualified_tool_name: "beta__write",
  binding_digest: "b".repeat(64),
  argument_digest: "c".repeat(64),
  argument_summary: { length: 2, credential: "[REDACTED]" },
  required_gates: ["engineering.write"],
  state: "pending",
  expires_at: "2099-01-01T00:00:00Z",
  approval_digest: "d".repeat(64),
  decided_by: null,
  decision_reason: null,
};

describe("RivetWorkflowRun", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.getRivetWorkflowRun).mockResolvedValue(run);
    vi.mocked(workspaceService.getRivetCallApprovals).mockResolvedValue([
      approval,
    ]);
    vi.mocked(workspaceService.getRivetWorkflowHistory).mockResolvedValue([
      { sequence: 1, kind: "started", payload: {} },
      {
        sequence: 2,
        kind: "progress",
        payload: { phase: "mcp-approval-required" },
      },
    ]);
    vi.mocked(workspaceService.getRivetRunEvidence).mockRejectedValue(
      new Error("Evidence is not terminal yet"),
    );
    vi.mocked(workspaceService.exportRivetRunEvidence).mockResolvedValue();
    vi.mocked(workspaceService.decideRivetCallApproval).mockResolvedValue({
      ...approval,
      state: "approved",
    });
  });

  it("shows an exact-call dialog, timeline, redaction, and keyboard close", async () => {
    const user = userEvent.setup();
    render(
      <RivetWorkflowRun
        sessionId="session-1"
        run={run}
        onRunUpdate={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveFocus();
    expect(screen.getByText(/beta__write/)).toBeInTheDocument();
    expect(screen.getByText(/engineering.write/)).toBeInTheDocument();
    expect(screen.getByText(/mcp-approval-required/)).toBeInTheDocument();
    expect(dialog).toHaveTextContent("[REDACTED]");
    expect(dialog.textContent).not.toContain("d".repeat(64));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Review pending call" }),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Review pending call" }),
      ).toHaveFocus(),
    );
  });

  it("sends the server-issued digest and one explicit approval decision", async () => {
    const user = userEvent.setup();
    render(
      <RivetWorkflowRun
        sessionId="session-1"
        run={run}
        onRunUpdate={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    await user.click(
      await screen.findByRole("button", { name: "Approve exact call" }),
    );
    await waitFor(() =>
      expect(workspaceService.decideRivetCallApproval).toHaveBeenCalledWith(
        "session-1",
        "run-1",
        approval,
        "approved",
      ),
    );
  });

  it("distinguishes acknowledged cancellation from possible residue", async () => {
    vi.mocked(workspaceService.getRivetCallApprovals).mockResolvedValue([]);
    vi.mocked(workspaceService.getRivetWorkflowRun).mockResolvedValue({
      ...run,
      state: "cancelled",
      reason: "RIVET_MCP_RESIDUE_POSSIBLE",
      manifest: {
        terminal_state: "cancelled",
        manifest_digest: "f".repeat(64),
        cancellation: {
          authority_revoked: true,
          child_acknowledged: false,
          residue_state: "possible",
          recovery_code: "RIVET_MCP_RESIDUE_POSSIBLE",
        },
      },
    });
    const { rerender } = render(
      <RivetWorkflowRun
        sessionId="session-1"
        run={{
          ...run,
          manifest: {
            terminal_state: "cancelled",
            manifest_digest: "f".repeat(64),
            cancellation: {
              authority_revoked: true,
              child_acknowledged: false,
              residue_state: "possible",
              recovery_code: "RIVET_MCP_RESIDUE_POSSIBLE",
            },
          },
        }}
        onRunUpdate={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    await screen.findByText(/Cleanup could not be confirmed/);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "RIVET_MCP_RESIDUE_POSSIBLE",
    );

    rerender(
      <RivetWorkflowRun
        sessionId="session-1"
        run={{
          ...run,
          manifest: {
            terminal_state: "cancelled",
            manifest_digest: "e".repeat(64),
            cancellation_acknowledged: true,
            residue_possible: false,
            recovery_code: "RIVET_MCP_CANCELLED_CLEAN",
          },
        }}
        onRunUpdate={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(
      screen.getByText("Cancellation was acknowledged and cleanup completed."),
    ).toBeInTheDocument();
  });

  it("shows complete durable accounting, stale recovery, artifacts, and export", async () => {
    const user = userEvent.setup();
    vi.mocked(workspaceService.getRivetCallApprovals).mockResolvedValue([]);
    vi.mocked(workspaceService.getRivetRunEvidence).mockResolvedValue({
      schema_version: 1,
      run_id: "run-1",
      manifest: {
        terminal_state: "succeeded",
        manifest_digest: "f".repeat(64),
        cancellation: null,
      },
      bindings: [
        { node_id: "node-alpha", qualified_tool_name: "alpha__inspect" },
      ],
      child_calls: [{ call_id: "call-1", state: "succeeded" }],
      approvals: [{ approval_id: "approval-1", state: "consumed" }],
      artifacts: [{ artifact_id: "mesh.vtk", label: "Validated mesh" }],
      timeline: [
        {
          kind: "binding",
          node_id: "node-alpha",
          qualified_tool_name: "alpha__inspect",
          state: "reviewed",
        },
        {
          kind: "child-call",
          call_id: "call-1",
          qualified_tool_name: "alpha__inspect",
          state: "succeeded",
        },
      ],
      reproducibility: {
        reproducible: false,
        summary: "A new review is required before reproducing this run.",
        differences: [
          {
            code: "tool_schema_changed",
            recorded: "a".repeat(64),
            current: "b".repeat(64),
            recovery_action: "review_current_bindings",
          },
        ],
      },
      accounting: {
        binding_count: 1,
        child_call_count: 1,
        approval_count: 1,
        artifact_count: 1,
        redaction_count: 1,
        truncated: false,
      },
    });
    render(
      <RivetWorkflowRun
        sessionId="session-1"
        run={{
          ...run,
          manifest: {
            terminal_state: "succeeded",
            manifest_digest: "f".repeat(64),
          },
        }}
        onRunUpdate={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(await screen.findByText(/1 bindings/)).toHaveTextContent(
      "1 child calls",
    );
    expect(screen.getByRole("status")).toHaveTextContent("new review");
    expect(screen.getByText(/tool_schema_changed/)).toHaveTextContent(
      "review_current_bindings",
    );
    expect(screen.getByText("Validated mesh")).toBeInTheDocument();
    expect(screen.getByTestId("rivet-run-timeline")).toHaveTextContent(
      "alpha__inspect",
    );
    expect(document.body.textContent).not.toContain("Bearer");
    await user.click(
      screen.getByRole("button", { name: "Export evidence JSON" }),
    );
    expect(workspaceService.exportRivetRunEvidence).toHaveBeenCalledWith(
      "session-1",
      "run-1",
    );
  });
});
