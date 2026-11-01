import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { workspaceService } from "../../services/workspace-service";
import { failedInspection } from "../../components/workflows/rivet-run-inspector.fixtures";
import { WorkflowRunHistory } from "./WorkflowRunHistory";

afterEach(() => vi.restoreAllMocks());

it("opens the exact saved run in its working view without starting it", async () => {
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
    {
      path: "runs/task/run.json",
      status: "waiting_human",
      started_at: "2026-10-10T22:08:44Z",
      source_digest: "accepted",
      source_matches_current: true,
      run_id: "existing-run",
      results: [],
    },
  ]);
  const open = vi.fn();
  render(
    <WorkflowRunHistory
      sessionId="session"
      path="workflows/task.wflow"
      refreshKey=""
      currentSourceDigest="accepted"
      onOpenRunWorkingView={open}
    />,
  );
  fireEvent.click(screen.getByText("Previous runs"));
  fireEvent.click(await screen.findByText(/Waiting for your input ·/));
  fireEvent.click(
    screen.getByRole("button", { name: "Open run in working view" }),
  );
  expect(open).toHaveBeenCalledExactlyOnceWith("existing-run", "accepted");
});

it.each([
  { source_digest: "old", run_id: "old-run", source_matches_current: true },
  {
    source_digest: "accepted",
    run_id: "old-run",
    source_matches_current: false,
  },
  {
    source_digest: "accepted",
    run_id: undefined,
    source_matches_current: true,
  },
])(
  "keeps historical logs without inventing a current run binding: %j",
  async (identity) => {
    vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
      {
        path: "runs/task/old.json",
        status: "completed",
        started_at: "2026-10-10T22:08:44Z",
        results: [],
        ...identity,
      },
    ]);
    const open = vi.fn(),
      openFile = vi.fn();
    render(
      <WorkflowRunHistory
        sessionId="session"
        path="workflows/task.wflow"
        refreshKey=""
        currentSourceDigest="accepted"
        onOpenRunWorkingView={open}
        onOpenFile={openFile}
      />,
    );
    fireEvent.click(screen.getByText("Previous runs"));
    fireEvent.click(await screen.findByText(/Completed ·/));
    expect(
      screen.queryByRole("button", { name: "Open run in working view" }),
    ).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open saved run log" }));
    expect(openFile).toHaveBeenCalledWith("runs/task/old.json");
    expect(open).not.toHaveBeenCalled();
  },
);

it("reports an interrupted operation without restarting and opens its existing log", async () => {
  const fetch = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockResolvedValue([
      {
        path: "runs/task/run.json",
        status: "interrupted",
        started_at: "2026-09-07T10:00:00Z",
        source_digest: "digest",
        results: [],
        last_event: {
          kind: "operation_progress",
          task_title: "Solve analysis",
          message: "Remote job submitted",
        },
      },
    ]);
  const trace = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRunTrace")
    .mockResolvedValue(failedInspection);
  const open = vi.fn();
  render(
    <WorkflowRunHistory
      sessionId="session"
      path="workflows/task.wflow"
      refreshKey=""
      onOpenFile={open}
    />,
  );
  expect(fetch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Trace: previous runs"));
  await waitFor(() => expect(screen.getByText(/Interrupted ·/)).toBeVisible());
  expect(screen.getByText(/nothing has been restarted/)).toBeVisible();
  expect(screen.getByText(/Remote job submitted/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Open saved run log" }));
  expect(open).toHaveBeenCalledWith("runs/task/run.json");
  expect(fetch).toHaveBeenCalledWith("session", "workflows/task.wflow");
  expect(trace).toHaveBeenCalledWith("session", "runs/task/run.json");
  fetch.mockRestore();
  trace.mockRestore();
});

it("opens a results-first Trace review from normal workflow history", async () => {
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
    {
      path: "runs/task/completed.json",
      status: "completed",
      started_at: "2026-09-07T10:00:00Z",
      completed_at: "2026-09-07T10:01:00Z",
      source_digest: "a".repeat(64),
      results: [],
    },
  ]);
  const trace = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRunTrace")
    .mockResolvedValue({
      ...failedInspection,
      run: { ...failedInspection.run, state: "succeeded" },
      diagnostic: null,
    });
  render(
    <WorkflowRunHistory
      sessionId="session"
      path="workflows/task.wflow"
      refreshKey=""
    />,
  );
  fireEvent.click(screen.getByText("Trace: previous runs"));
  const run = await screen.findByText(/Completed ·/);
  fireEvent.click(run);
  expect(
    await screen.findByRole("region", { name: "Run results" }),
  ).toBeVisible();
  expect(screen.getByText("Created artifacts")).toBeVisible();
  expect(trace).toHaveBeenCalledWith("session", "runs/task/completed.json");
});
