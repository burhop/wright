import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  runningInspection,
  runningRun,
  succeededInspection,
} from "../components/workflows/rivet-run-inspector.fixtures";
import { workspaceService } from "../services/workspace-service";
import { useRivetRunInspection } from "./useRivetRunInspection";

vi.mock("../services/workspace-service", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../services/workspace-service")>();
  return {
    ...actual,
    workspaceService: {
      ...actual.workspaceService,
      getRecentRivetRuns: vi.fn(),
      getRivetRunInspection: vi.fn(),
      runRivetWorkflow: vi.fn(),
    },
  };
});

describe("useRivetRunInspection", () => {
  beforeEach(() => vi.clearAllMocks());

  it("reattaches to an active recent run without starting another run", async () => {
    vi.mocked(workspaceService.getRecentRivetRuns).mockResolvedValue({
      workflow_id: "workflow-1",
      current_revision: 2,
      runs: [runningRun],
    });
    vi.mocked(workspaceService.getRivetRunInspection).mockResolvedValue(
      succeededInspection,
    );

    const { result } = renderHook(() =>
      useRivetRunInspection({
        sessionId: "session-1",
        workflowSlug: "workflow-1",
      }),
    );

    await waitFor(() => expect(result.current.selectedRunId).toBe("run-1"));
    await waitFor(() =>
      expect(result.current.inspection?.run.state).toBe("succeeded"),
    );
    expect(workspaceService.getRivetRunInspection).toHaveBeenCalledWith(
      "session-1",
      "run-1",
      0,
    );
    expect(workspaceService.runRivetWorkflow).not.toHaveBeenCalled();
  });

  it("continues from the event cursor and stops polling at terminal state", async () => {
    vi.mocked(workspaceService.getRecentRivetRuns).mockResolvedValue({
      workflow_id: "workflow-1",
      current_revision: 2,
      runs: [runningRun],
    });
    vi.mocked(workspaceService.getRivetRunInspection)
      .mockResolvedValueOnce(runningInspection)
      .mockResolvedValueOnce(succeededInspection);

    const { result } = renderHook(() =>
      useRivetRunInspection({
        sessionId: "session-1",
        workflowSlug: "workflow-1",
        runId: "run-1",
      }),
    );

    await waitFor(
      () => expect(result.current.inspection?.run.state).toBe("succeeded"),
      { timeout: 2000 },
    );
    expect(
      vi.mocked(workspaceService.getRivetRunInspection).mock.calls.slice(0, 2),
    ).toEqual([
      ["session-1", "run-1", 0],
      ["session-1", "run-1", 2],
    ]);
    await new Promise((resolve) => window.setTimeout(resolve, 650));
    expect(workspaceService.getRivetRunInspection).toHaveBeenCalledTimes(2);
  });

  it("selects historical runs without mutating workflow execution", async () => {
    vi.mocked(workspaceService.getRecentRivetRuns).mockResolvedValue({
      workflow_id: "workflow-1",
      current_revision: 2,
      runs: [
        runningRun,
        { ...runningRun, run_id: "run-old", state: "succeeded", revision: 1 },
      ],
    });
    vi.mocked(workspaceService.getRivetRunInspection).mockResolvedValue(
      succeededInspection,
    );
    const { result } = renderHook(() =>
      useRivetRunInspection({
        sessionId: "session-1",
        workflowSlug: "workflow-1",
      }),
    );
    await waitFor(() => expect(result.current.selectedRunId).toBe("run-1"));
    act(() => result.current.selectRun("run-old"));
    await waitFor(() =>
      expect(workspaceService.getRivetRunInspection).toHaveBeenCalledWith(
        "session-1",
        "run-old",
        0,
      ),
    );
    expect(workspaceService.runRivetWorkflow).not.toHaveBeenCalled();
  });
});
