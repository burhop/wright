import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { NativeFilePreview } from "./NativeFilePreview";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

afterEach(cleanup);
const workspace = { workspace_id: "a", session_id: "chat-a", workspace_name: "A", available: true, reason: null };
const response = (extra = {}): CallToolResult => ({ content: [], structuredContent: {
  workspace_id: "a", session_id: "chat-a", path: "note.md", supported: true,
  content: "<script>not executed</script>", sha256: "a".repeat(64), ...extra,
} });
it("displays text literally through the exact read-only port", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const { container } = render(<NativeFilePreview call={call} workspace={workspace} path="note.md" onClose={() => {}} />);
  await screen.findByText("<script>not executed</script>");
  expect(container.querySelector("script")).toBeNull();
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workspace_file_preview", { workspace_id: "a", session_id: "chat-a", path: "note.md" });
});
it("rejects another workspace's result", async () => {
  const call = vi.fn().mockResolvedValue(response({ workspace_id: "b" }));
  render(<NativeFilePreview call={call} workspace={workspace} path="note.md" onClose={() => {}} />);
  await screen.findByText(/Preview could not be read/);
  expect(screen.queryByText("<script>not executed</script>")).toBeNull();
});
it("discards a late result after the selected file closes", async () => {
  let resolve!: (value: CallToolResult) => void;
  const call = vi.fn(() => new Promise<CallToolResult>((done) => { resolve = done; }));
  const view = render(<NativeFilePreview call={call} workspace={workspace} path="note.md" onClose={() => {}} />);
  view.unmount();
  resolve(response());
  await Promise.resolve();
  expect(screen.queryByText("<script>not executed</script>")).toBeNull();
});
