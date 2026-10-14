import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeConnections } from "./NativeConnections";
const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const reply = (scope = "a") => ({
  content: [],
  structuredContent: {
    workspace_id: scope,
    session_id: "chat-a",
    next_cursor: null,
    connections: [
      {
        capability_id: "cad",
        name: "CAD",
        description: "Design",
        installed: true,
        active: true,
        enabled_here: false,
        credentials_missing: false,
        process_status: "stopped",
        installed_version: null,
        compatibility: { status: "uncertain", reasons: [] },
      },
    ],
  },
});
afterEach(cleanup);
it("shows catalog state without implying workspace grant or live health", async () => {
  const call = vi.fn().mockResolvedValue(reply());
  render(<NativeConnections workspace={workspace} call={call} />);
  expect(
    await screen.findByText("Not enabled in this workspace"),
  ).toBeVisible();
  fireEvent.click(screen.getByText("Readiness details"));
  expect(screen.getByText(/Process: stopped/)).toBeVisible();
  expect(screen.getByText(/not yet available in this panel/)).toBeVisible();
  expect(call).toHaveBeenCalledWith("wright_connections_list", {
    workspace_id: "a",
    session_id: "chat-a",
    search: "",
  });
});
it("rejects mismatched scope and permits an explicit search retry", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply("other"))
    .mockResolvedValue(reply());
  render(<NativeConnections workspace={workspace} call={call} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "could not be read",
  );
  expect(screen.queryByText("CAD")).toBeNull();
  expect(screen.queryByText("No matching connections.")).toBeNull();
  fireEvent.change(screen.getByLabelText("Find an MCP"), {
    target: { value: "CAD" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Search / refresh" }));
  expect(await screen.findByText("CAD")).toBeVisible();
  expect(call).toHaveBeenLastCalledWith("wright_connections_list", {
    workspace_id: "a",
    session_id: "chat-a",
    search: "CAD",
  });
});
