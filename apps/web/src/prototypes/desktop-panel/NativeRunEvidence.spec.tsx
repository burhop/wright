import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeRunEvidence } from "./NativeRunEvidence";
const workspace = {
  workspace_id: "w",
  session_id: "s",
  workspace_name: "Test",
  available: true,
  reason: null,
};
const run = {
  run_id: "recorded",
  source_digest: "a".repeat(64),
  path: "runs/demo/one.json",
  status: "completed",
  started_at: null,
};
const path = "workflows/demo.workflow.wflow";
const result = () => ({
  content: [],
  structuredContent: {
    workspace_id: "w",
    session_id: "s",
    workflow_path: path,
    record: {
      path: "runs/demo/one.json",
      run_id: "recorded",
      source_digest: run.source_digest,
      source_matches_current: false,
      status: "completed",
      results: [
        {
          schema_version: 1,
          id: "output",
          name: "Saved engineering result",
          kind: "file",
          provenance: {
            run_id: "recorded",
            task_id: "task",
            output_port: "result",
            input_revisions: [],
          },
          exports: [],
          representations: [
            {
              kind: "workspace_file",
              location: "results/answer.txt",
              format: "text",
              durability: "persistent",
              size_bytes: 5,
              sha256: "b".repeat(64),
            },
          ],
        },
      ],
    },
  },
});
afterEach(cleanup);
it("reads exact old-source evidence through one read-only port with no process actions", async () => {
  const call = vi.fn().mockResolvedValue(result());
  render(
    <NativeRunEvidence
      workspace={workspace}
      path={path}
      run={run}
      call={call}
    />,
  );
  await screen.findByText(/workflow has changed since this run/);
  expect(screen.getByText("Saved engineering result")).toBeVisible();
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_recorded_run_read", {
    request: {
      workspace_id: "w",
      session_id: "s",
      path,
      run_id: "recorded",
      source_digest: run.source_digest,
    },
  });
  expect(
    screen.queryByRole("button", { name: /Approve|Resume|Continue|Start/ }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Download file" })).toBeEnabled();
});
it.each(["workspace", "source", "run"])(
  "rejects mismatched %s evidence without presenting files",
  async (field) => {
    const value = result();
    if (field === "workspace") value.structuredContent.workspace_id = "foreign";
    else if (field === "source")
      value.structuredContent.record.source_digest = "f".repeat(64);
    else value.structuredContent.record.run_id = "foreign";
    render(
      <NativeRunEvidence
        workspace={workspace}
        path={path}
        run={run}
        call={vi.fn().mockResolvedValue(value)}
      />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "exact saved run could not be read",
    );
    expect(
      screen.queryByText("Saved engineering result"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Download file" }),
    ).not.toBeInTheDocument();
  },
);
it("retries observation only on explicit refresh", async () => {
  const call = vi
    .fn()
    .mockRejectedValueOnce(Error("unavailable"))
    .mockResolvedValue(result());
  render(
    <NativeRunEvidence
      workspace={workspace}
      path={path}
      run={run}
      call={call}
    />,
  );
  await screen.findByRole("alert");
  expect(call).toHaveBeenCalledTimes(1);
  fireEvent.click(
    screen.getByRole("button", { name: "Refresh saved evidence" }),
  );
  await screen.findByText("Saved engineering result");
  expect(call).toHaveBeenCalledTimes(2);
});
