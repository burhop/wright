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
        cancellation_acknowledged: false,
        residue_possible: true,
        recovery_code: "RIVET_MCP_RESIDUE_POSSIBLE",
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
            cancellation_acknowledged: false,
            residue_possible: true,
            recovery_code: "RIVET_MCP_RESIDUE_POSSIBLE",
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
});
