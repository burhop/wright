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

it("lists and filters workspace files without opening or executing them", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(
      result({
        workspace_id: alpha.workspace_id,
        session_id: alpha.session_id,
        tree: {
          type: "directory",
          children: [
            { type: "file", name: "part.wflow", path: "/workflows/part.wflow" },
            {
              type: "file",
              name: "uploaded.wflow",
              path: "/uploads/opaque/uploaded.wflow",
            },
            {
              type: "directory",
              children: [
                {
                  type: "file",
                  name: "plate.step",
                  path: "/outputs/plate.step",
                },
              ],
            },
          ],
        },
      }),
    );
  const onOpen = vi.fn();
  render(
    <NativeHomePanel call={call} onOpen={onOpen} initialSelection={alpha} />,
  );
  await screen.findByRole("button", { name: "part.wflow" });
  expect(screen.queryByRole("button", { name: "uploaded.wflow" })).toBeNull();
  expect(screen.queryByText("plate.step")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Files" }));
  expect(screen.getByText("/outputs/plate.step")).toBeVisible();
  fireEvent.change(screen.getByLabelText("Find a file"), {
    target: { value: "PLATE" },
  });
  expect(screen.getByText("plate.step")).toBeVisible();
  expect(screen.queryByText("part.wflow")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Find a file"), {
    target: { value: "missing" },
  });
  expect(screen.getByText("No files match this search.")).toBeVisible();
  expect(
    screen.getByText(/downloads support visible files up to 16 MiB/),
  ).toBeVisible();
  expect(call).toHaveBeenCalledTimes(2);
  expect(onOpen).not.toHaveBeenCalled();
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

it("creates once and selects only the discovered exact workspace/session", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [] }))
    .mockResolvedValueOnce(result(alpha))
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(files(alpha, "part.wflow"));
  const onSelect = vi.fn();
  render(<NativeHomePanel call={call} onOpen={vi.fn()} onSelect={onSelect} />);
  await screen.findByText(/No Wright workspaces yet/);
  fireEvent.click(screen.getByRole("button", { name: "New workspace" }));
  fireEvent.change(screen.getByLabelText("Workspace name"), {
    target: { value: "Alpha" },
  });
  const button = screen.getByRole("button", { name: "Create workspace" });
  fireEvent.click(button);
  fireEvent.click(button);
  await screen.findByRole("button", { name: "part.wflow" });
  expect(onSelect).toHaveBeenCalledWith(alpha);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_workspace_create"),
  ).toEqual([["wright_workspace_create", { name: "Alpha" }]]);
});

it("does not repeat uncertain creation and allows read-only discovery", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [] }))
    .mockRejectedValueOnce(new Error("lost acknowledgement"))
    .mockResolvedValueOnce(result({ workspaces: [alpha] }));
  render(<NativeHomePanel call={call} onOpen={vi.fn()} />);
  await screen.findByText(/No Wright workspaces yet/);
  fireEvent.click(screen.getByRole("button", { name: "New workspace" }));
  fireEvent.change(screen.getByLabelText("Workspace name"), {
    target: { value: "Alpha" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create workspace" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("will not repeat");
  expect(
    screen.getByRole("button", { name: "Create workspace" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  await screen.findByRole("option", { name: "Alpha" });
  expect(screen.getByRole("button", { name: "New workspace" })).toBeDisabled();
  expect(
    call.mock.calls.filter(([name]) => name === "wright_workspace_create"),
  ).toHaveLength(1);
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

it("refreshes the exact selected scope while keeping the Files view", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(files(alpha, "before.wflow"))
    .mockResolvedValueOnce(result({ workspaces: [beta, alpha] }))
    .mockResolvedValueOnce(files(alpha, "after.wflow"));
  const onOpen = vi.fn();
  render(
    <NativeHomePanel call={call} onOpen={onOpen} initialSelection={alpha} />,
  );
  await screen.findByRole("button", { name: "before.wflow" });
  fireEvent.click(screen.getByRole("button", { name: "Files" }));
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  await screen.findByRole("button", { name: "after.wflow" });
  expect(screen.getByLabelText("Workspace")).toHaveValue("a");
  expect(screen.getByLabelText("Find a file")).toBeVisible();
  expect(screen.queryByText("before.wflow")).not.toBeInTheDocument();
  expect(call.mock.calls).toEqual([
    ["wright_workspace_list", {}],
    ["wright_workspace_files", { workspace_id: "a", session_id: "a-chat" }],
    ["wright_workspace_list", {}],
    ["wright_workspace_files", { workspace_id: "a", session_id: "a-chat" }],
  ]);
  expect(onOpen).not.toHaveBeenCalled();
});

it("does not redirect refreshed selection to a changed session", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha] }))
    .mockResolvedValueOnce(files(alpha, "part.wflow"))
    .mockResolvedValueOnce(
      result({ workspaces: [{ ...alpha, session_id: "replacement" }, beta] }),
    );
  render(
    <NativeHomePanel call={call} onOpen={vi.fn()} initialSelection={alpha} />,
  );
  await screen.findByRole("button", { name: "part.wflow" });
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "no longer available",
  );
  expect(screen.getByLabelText("Workspace")).toHaveValue("");
  expect(call).toHaveBeenCalledTimes(3);
  expect(
    screen.queryByRole("button", { name: "part.wflow" }),
  ).not.toBeInTheDocument();
});

it("restores the requested view only after reconciling the exact workspace/session and reports navigation", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(result({ workspaces: [alpha, beta] }))
    .mockResolvedValue(files(beta, "part.wflow"));
  const onNavigate = vi.fn();
  render(
    <NativeHomePanel
      call={call}
      onOpen={vi.fn()}
      initialSelection={beta}
      initialView="files"
      onNavigate={onNavigate}
    />,
  );
  await screen.findByRole("heading", { name: "Files" });
  expect(screen.getByLabelText("Workspace")).toHaveValue("b");
  expect(call).toHaveBeenLastCalledWith("wright_workspace_files", {
    workspace_id: "b",
    session_id: "b-chat",
  });
  fireEvent.click(screen.getByRole("button", { name: "Recent runs" }));
  expect(onNavigate).toHaveBeenCalledExactlyOnceWith("runs");
});
