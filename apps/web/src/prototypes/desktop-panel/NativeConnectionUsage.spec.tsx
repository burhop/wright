import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeConnectionUsage } from "./NativeConnectionUsage";

afterEach(cleanup);
const scope = {
  workspace_id: "alpha",
  session_id: "chat-a",
  capability_id: "cad",
  server_id: "cad-provider",
};
const digest = "a".repeat(64);
const usage = {
  scope: "selected-workspace-saved-explicit-bindings",
  scan_complete: true,
  unchecked_paths: [],
  matches: [
    {
      path: "workflows/bracket.workflow.wflow",
      title: "Mounting bracket",
      source_digest: "b".repeat(64),
      steps: [{ id: "measure", title: "Measure mounting holes" }],
    },
  ],
};
function show(extra = {}) {
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: { ...scope, control_digest: digest, usage, ...extra },
  });
  render(
    <NativeConnectionUsage call={call} scope={scope} controlDigest={digest} />,
  );
  fireEvent.click(screen.getByText("Workflows using this connection"));
  expect(call).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Check saved workflows" }),
  );
  return call;
}
it("shows exact workflow and step names on demand without mutating a connection", async () => {
  const call = show();
  expect(await screen.findByText("Mounting bracket")).toBeVisible();
  fireEvent.click(screen.getByText("1 referenced step"));
  expect(screen.getByText("Measure mounting holes")).toBeVisible();
  fireEvent.click(screen.getByText("File location"));
  expect(screen.getByText("workflows/bracket.workflow.wflow")).toBeVisible();
  expect(
    screen.getByText(
      /Other workspaces, active runs and unsaved edits are not checked/,
    ),
  ).toBeVisible();
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_connection_workflows",
    scope,
  );
});
it("does not disguise an incomplete scan as a safe empty result", async () => {
  show({
    usage: {
      ...usage,
      scan_complete: false,
      matches: [],
      unchecked_paths: ["workflows/unready.workflow.wflow"],
    },
  });
  expect(await screen.findByText(/This list is incomplete/)).toBeVisible();
  expect(
    screen.getByText(/No explicit references found in the workflows checked/),
  ).toBeVisible();
  fireEvent.click(screen.getByText("Unchecked files"));
  expect(screen.getByText("workflows/unready.workflow.wflow")).toBeVisible();
});
it.each([
  { workspace_id: "other" },
  { control_digest: "c".repeat(64) },
  {
    usage: {
      ...usage,
      matches: [{ ...usage.matches[0], source_digest: "unknown" }],
    },
  },
])("rejects foreign or stale response identity", async (extra) => {
  show(extra);
  expect(
    await screen.findByText(/Workflow usage could not be confirmed/),
  ).toBeVisible();
  expect(screen.queryByText("Mounting bracket")).not.toBeInTheDocument();
});
