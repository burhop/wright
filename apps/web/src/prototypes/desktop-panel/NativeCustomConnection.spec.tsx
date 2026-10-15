import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeCustomConnection } from "./NativeCustomConnection";
const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const preview = {
  content: [],
  structuredContent: {
    workspace_id: "a",
    session_id: "chat-a",
    preview_token: "token",
    preview: {
      document_errors: [],
      expires_at: "2026-10-15T12:15:00Z",
      drafts: [
        {
          draft_id: "draft",
          draft_digest: "a".repeat(64),
          name: "Custom CAD",
          endpoint: "https://example.invalid/mcp",
          errors: [],
        },
      ],
    },
  },
};
afterEach(cleanup);
function fill(url = "https://example.invalid/mcp") {
  fireEvent.change(screen.getByLabelText("Connection name"), {
    target: { value: "Custom CAD" },
  });
  fireEvent.change(screen.getByLabelText("Public MCP endpoint"), {
    target: { value: url },
  });
  fireEvent.click(screen.getByRole("button", { name: "Preview connection" }));
}
it("previews without effects and forwards exact draft with publisher completion false by default", async () => {
  const plan = {
    plan_id: "saved",
    plan_digest: "b".repeat(64),
    capability_id: "import:custom",
    workspace_id: "a",
    requested_scope: "workspace",
    state: "blocked",
    blocking_reasons: [],
    effects: [],
  };
  const call = vi
    .fn()
    .mockResolvedValueOnce(preview)
    .mockResolvedValueOnce({
      content: [],
      structuredContent: { workspace_id: "a", session_id: "chat-a", plan },
    });
  const onPlan = vi.fn();
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={onPlan}
    />,
  );
  fill();
  await screen.findByRole("region", { name: "Custom connection preview" });
  expect(call).toHaveBeenCalledTimes(1);
  expect(onPlan).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Review custom setup" }));
  fireEvent.click(screen.getByRole("button", { name: "Review custom setup" }));
  await vi.waitFor(() => expect(onPlan).toHaveBeenCalledWith(plan));
  expect(call).toHaveBeenCalledTimes(2);
  expect(call).toHaveBeenLastCalledWith("wright_connection_import_plan", {
    workspace_id: "a",
    session_id: "chat-a",
    preview_token: "token",
    draft_id: "draft",
    draft_digest: "a".repeat(64),
    independently_completed_license: false,
  });
});
it("rejects credential-bearing endpoint before sending any host tool call", async () => {
  const call = vi.fn();
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fill("https://example.invalid/mcp?token=private");
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Nothing was sent",
  );
  expect(call).not.toHaveBeenCalled();
});
it("stops after uncertain plan creation and directs recovery through saved plans", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(preview)
    .mockRejectedValueOnce(Error("lost response"));
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fill();
  fireEvent.click(
    await screen.findByRole("button", { name: "Review custom setup" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Saved setup in this workspace",
  );
  expect(
    screen.getByRole("button", { name: "Review custom setup" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Preview connection" }),
  ).toBeDisabled();
  expect(call).toHaveBeenCalledTimes(2);
});
