import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NativeRecentRuns } from "./NativeRecentRuns";

afterEach(cleanup);
const workspace = { workspace_id: "w", session_id: "s", workspace_name: "Test", available: true, reason: null };
const path = "workflows/part.wflow";
const run = { run_id: "r", path: "runs/part/r.json", status: "waiting_human", started_at: null, source_digest: "a".repeat(64) };
const response = (workspaceId = "w") => ({ content: [], structuredContent: {
  workspace_id: workspaceId, session_id: "s", workflow_path: path, runs: [run],
} });

it("reads only on selection and opens the exact recorded run on explicit click", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn().mockResolvedValue(undefined);
  render(<NativeRecentRuns workspace={workspace} paths={[path]} call={call} onOpen={onOpen} />);
  expect(call).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Workflow history"), { target: { value: path } });
  await screen.findByText("waiting human");
  expect(onOpen).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Inspect run" }));
  await waitFor(() => expect(onOpen).toHaveBeenCalledWith(path, run));
  expect(call).toHaveBeenCalledWith("wright_workflow_history", { workspace_id: "w", session_id: "s", path });
});

it("rejects foreign history and does not describe read failure as an empty history", async () => {
  const call = vi.fn().mockResolvedValue(response("other"));
  render(<NativeRecentRuns workspace={workspace} paths={[path]} call={call} />);
  fireEvent.change(screen.getByLabelText("Workflow history"), { target: { value: path } });
  expect(await screen.findByRole("alert")).toHaveTextContent("could not be read");
  expect(screen.queryByText("waiting human")).not.toBeInTheDocument();
  expect(screen.queryByText("No recorded runs for this workflow.")).not.toBeInTheDocument();
});

it("does not retry an unavailable exact run", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn().mockRejectedValue(new Error("source changed"));
  render(<NativeRecentRuns workspace={workspace} paths={[path]} call={call} onOpen={onOpen} />);
  fireEvent.change(screen.getByLabelText("Workflow history"), { target: { value: path } });
  fireEvent.click(await screen.findByRole("button", { name: "Inspect run" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("exact run could not be opened");
  expect(onOpen).toHaveBeenCalledTimes(1);
  expect(call).toHaveBeenCalledTimes(1);
});
