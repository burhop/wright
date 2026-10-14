// Controlled component checks; actual installed desktop rendering is separate.
import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { NativeHomePanel } from "./NativeHomePanel";

afterEach(cleanup);
const alpha = {
  workspace_id: "a",
  session_id: "a-chat",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const beta = {
  workspace_id: "b",
  session_id: "b-chat",
  workspace_name: "Beta",
  available: true,
  reason: null,
};
const result = (data: Record<string, unknown>): CallToolResult => ({
  content: [],
  structuredContent: data,
});
const files = (workspace: typeof alpha, name: string) =>
  result({
    workspace_id: workspace.workspace_id,
    session_id: workspace.session_id,
    tree: {
      type: "directory",
      children: [{ type: "file", name, path: `/workflows/${name}` }],
    },
  });

it("opens a selected workflow with the exact workspace and desktop session", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(files(alpha, "part.wflow"));
  const onOpen = vi.fn().mockResolvedValue(undefined);
  render(<NativeHomePanel call={call} onOpen={onOpen} />);
  await screen.findByRole("option", { name: "Alpha" });
  fireEvent.change(screen.getByLabelText("Workspace"), {
    target: { value: "a" },
  });
  fireEvent.click(await screen.findByRole("button", { name: "part.wflow" }));
  await waitFor(() =>
    expect(onOpen).toHaveBeenCalledWith(alpha, "workflows/part.wflow"),
  );
  expect(call.mock.calls).toEqual([
    ["wright_workspace_list", {}],
    ["wright_workspace_files", { workspace_id: "a", session_id: "a-chat" }],
  ]);
});

it("ignores a previous workspace's late file response", async () => {
  let finishAlpha!: (value: CallToolResult) => void;
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha, beta] }))
    .mockImplementationOnce(
      () =>
        new Promise<CallToolResult>((resolve) => {
          finishAlpha = resolve;
        }),
    )
    .mockResolvedValueOnce(files(beta, "beta.wflow"));
  render(<NativeHomePanel call={call} onOpen={vi.fn()} />);
  await screen.findByRole("option", { name: "Beta" });
  fireEvent.change(screen.getByLabelText("Workspace"), {
    target: { value: "a" },
  });
  fireEvent.change(screen.getByLabelText("Workspace"), {
    target: { value: "b" },
  });
  await screen.findByRole("button", { name: "beta.wflow" });
  finishAlpha(files(alpha, "alpha.wflow"));
  await waitFor(() =>
    expect(
      screen.queryByRole("button", { name: "alpha.wflow" }),
    ).not.toBeInTheDocument(),
  );
  expect(screen.getByLabelText("Workspace")).toHaveValue("b");
});

it("rejects mismatched file scope instead of displaying another workspace", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(files(beta, "private.wflow"));
  render(<NativeHomePanel call={call} onOpen={vi.fn()} />);
  await screen.findByRole("option", { name: "Alpha" });
  fireEvent.change(screen.getByLabelText("Workspace"), {
    target: { value: "a" },
  });
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "could not be read",
  );
  expect(screen.queryByText("private.wflow")).not.toBeInTheDocument();
  expect(screen.queryByText(/No saved workflows/)).not.toBeInTheDocument();
});

it("reports a failed workspace load separately from an empty catalog", async () => {
  const call = vi.fn().mockResolvedValue({ isError: true, content: [] });
  render(<NativeHomePanel call={call} onOpen={vi.fn()} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "could not be refreshed",
  );
  expect(
    screen.queryByText(/No Wright workspaces yet/),
  ).not.toBeInTheDocument();
  expect(call).toHaveBeenCalledTimes(1);
});

it("keeps unavailable workspaces visible and does not automatically open anything", async () => {
  const call = vi.fn().mockResolvedValue(
    result({
      workspaces: [
        {
          ...alpha,
          available: false,
          reason: "Workspace directory is unavailable",
        },
      ],
    }),
  );
  const onOpen = vi.fn();
  render(<NativeHomePanel call={call} onOpen={onOpen} />);
  expect(
    await screen.findByRole("option", { name: "Alpha — unavailable" }),
  ).toBeDisabled();
  expect(onOpen).not.toHaveBeenCalled();
  expect(call).toHaveBeenCalledTimes(1);
});

it("restores the exact prior workspace/session without opening a workflow", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha, beta] }))
    .mockResolvedValueOnce(files(beta, "part.wflow"));
  const onOpen = vi.fn();
  render(
    <NativeHomePanel call={call} onOpen={onOpen} initialSelection={beta} />,
  );
  await screen.findByRole("button", { name: "part.wflow" });
  expect(screen.getByLabelText("Workspace")).toHaveValue("b");
  expect(onOpen).not.toHaveBeenCalled();
});

it("does not redirect a restored selection to a replacement desktop session", async () => {
  const call = vi
    .fn()
    .mockResolvedValue(
      result({ workspaces: [{ ...alpha, session_id: "replacement" }] }),
    );
  render(
    <NativeHomePanel call={call} onOpen={vi.fn()} initialSelection={alpha} />,
  );
  await screen.findByRole("option", { name: "Alpha" });
  expect(screen.getByLabelText("Workspace")).toHaveValue("");
  expect(call).toHaveBeenCalledTimes(1);
});
