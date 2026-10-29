import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NativeRecentRuns } from "./NativeRecentRuns";

afterEach(cleanup);
const workspace = {
  workspace_id: "w",
  session_id: "s",
  workspace_name: "Test",
  available: true,
  reason: null,
};
const path = "workflows/part.wflow";
const run = {
  run_id: "r",
  path: "runs/part/r.json",
  status: "waiting_human",
  started_at: null,
  source_digest: "a".repeat(64),
};
const response = (workspaceId = "w") => ({
  content: [],
  structuredContent: {
    workspace_id: workspaceId,
    session_id: "s",
    workflow_path: path,
    runs: [run],
  },
});

it("reads the remembered workflow only after workspace discovery confirms its path", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn();
  const { rerender } = render(
    <NativeRecentRuns
      workspace={workspace}
      paths={[]}
      initialPath={path}
      call={call}
      onOpen={onOpen}
    />,
  );
  expect(call).not.toHaveBeenCalled();
  rerender(
    <NativeRecentRuns
      workspace={workspace}
      paths={[path]}
      initialPath={path}
      call={call}
      onOpen={onOpen}
    />,
  );
  await screen.findByText("waiting human");
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workflow_history", {
    workspace_id: "w",
    session_id: "s",
    path,
  });
  expect(onOpen).not.toHaveBeenCalled();
});

it("reads only on selection and opens the exact recorded run on explicit click", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn().mockResolvedValue(undefined);
  render(
    <NativeRecentRuns
      workspace={workspace}
      paths={[path]}
      call={call}
      onOpen={onOpen}
    />,
  );
  expect(call).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Workflow history"), {
    target: { value: path },
  });
  await screen.findByText("waiting human");
  expect(onOpen).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Open working view" }));
  await waitFor(() => expect(onOpen).toHaveBeenCalledWith(path, run));
  expect(call).toHaveBeenCalledWith("wright_workflow_history", {
    workspace_id: "w",
    session_id: "s",
    path,
  });
});

it("rejects foreign history and does not describe read failure as an empty history", async () => {
  const call = vi.fn().mockResolvedValue(response("other"));
  render(<NativeRecentRuns workspace={workspace} paths={[path]} call={call} />);
  fireEvent.change(screen.getByLabelText("Workflow history"), {
    target: { value: path },
  });
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "could not be read",
  );
  expect(screen.queryByText("waiting human")).not.toBeInTheDocument();
  expect(
    screen.queryByText("No recorded runs for this workflow."),
  ).not.toBeInTheDocument();
});

it("does not retry an unavailable exact run", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn().mockRejectedValue(new Error("source changed"));
  render(
    <NativeRecentRuns
      workspace={workspace}
      paths={[path]}
      call={call}
      onOpen={onOpen}
    />,
  );
  fireEvent.change(screen.getByLabelText("Workflow history"), {
    target: { value: path },
  });
  fireEvent.click(
    await screen.findByRole("button", { name: "Open working view" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "exact run could not be opened",
  );
  expect(onOpen).toHaveBeenCalledTimes(1);
  expect(call).toHaveBeenCalledTimes(1);
});

it("reads a historical record without opening the current-source working view", async () => {
  const record = {
    content: [],
    structuredContent: {
      workspace_id: "w",
      session_id: "s",
      workflow_path: path,
      record: {
        path: "runs/demo/retained.json",
        run_id: "r",
        source_digest: run.source_digest,
        source_matches_current: false,
        status: "completed",
        results: [],
      },
    },
  };
  const call = vi
    .fn()
    .mockResolvedValueOnce(response())
    .mockResolvedValue(record);
  const onOpen = vi.fn();
  render(
    <NativeRecentRuns
      workspace={workspace}
      paths={[path]}
      call={call}
      onOpen={onOpen}
    />,
  );
  fireEvent.change(screen.getByLabelText("Workflow history"), {
    target: { value: path },
  });
  fireEvent.click(
    await screen.findByRole("button", { name: "Read saved evidence" }),
  );
  await screen.findByText(/workflow has changed since this run/);
  expect(onOpen).not.toHaveBeenCalled();
  expect(call).toHaveBeenLastCalledWith("wright_recorded_run_read", {
    request: {
      workspace_id: "w",
      session_id: "s",
      path,
      run_id: "r",
      source_digest: run.source_digest,
    },
  });
});

// A known historical source is readable, but cannot attach to the current process client.
it("directs an earlier workflow version to its exact saved evidence", async () => {
  const call = vi
    .fn()
    .mockImplementation(async (tool) =>
      tool === "wright_workflow_history"
        ? response()
        : {
            content: [],
            structuredContent: {
              workspace_id: "w",
              session_id: "s",
              workflow_path: path,
              record: { ...run, source_matches_current: false, results: [] },
            },
          },
    );
  const onOpen = vi.fn();
  render(
    <NativeRecentRuns
      workspace={workspace}
      paths={[path]}
      initialPath={path}
      call={call}
      onOpen={onOpen}
      workingSourceDigest={"b".repeat(64)}
    />,
  );
  await screen.findByText(/Earlier workflow version/);
  expect(
    screen.queryByRole("button", { name: "Open working view" }),
  ).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Read saved evidence" }));
  await screen.findByText(/The workflow has changed since this run/);
  expect(call).toHaveBeenCalledWith("wright_recorded_run_read", {
    request: {
      workspace_id: "w",
      session_id: "s",
      path,
      run_id: "r",
      source_digest: run.source_digest,
    },
  });
  expect(onOpen).not.toHaveBeenCalled();
});
