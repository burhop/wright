import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  act,
} from "@testing-library/react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { NativeFileDownload } from "./NativeFileDownload";

const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "A",
  available: true,
  reason: null,
};
const bytes = new Uint8Array([0, 255, 60, 62, 13, 10]);
const result = (extra = {}): CallToolResult => ({
  content: [],
  structuredContent: {
    workspace_id: "a",
    session_id: "chat-a",
    path: "part.step",
    filename: "part.step",
    supported: true,
    bytes: bytes.length,
    sha256: "9c17195371edce04de3f349ccc57d389a1ca5c687a1c6a0d00153227fe52987e",
    content_base64: btoa(String.fromCharCode(...bytes)),
    ...extra,
  },
});
beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:verified-file");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
function show(call = vi.fn().mockResolvedValue(result())) {
  const view = render(
    <NativeFileDownload call={call} workspace={workspace} path="part.step" />,
  );
  return { call, ...view };
}
it("requests exact current bytes once and downloads only after digest verification", async () => {
  const { call } = show();
  fireEvent.click(screen.getByRole("button", { name: "Download file" }));
  fireEvent.click(screen.getByRole("button", { name: "Preparing download…" }));
  await screen.findByText(/Download requested/);
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_workspace_file_download",
    { workspace_id: "a", session_id: "chat-a", path: "part.step" },
  );
  expect(URL.createObjectURL).toHaveBeenCalledOnce();
  const blob = vi.mocked(URL.createObjectURL).mock.calls[0][0] as Blob;
  expect(blob.size).toBe(bytes.length);
  expect(blob.type).toBe("application/octet-stream");
  expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledOnce();
  expect(screen.getByText(/not verified run evidence/)).toBeVisible();
});
it.each([
  { workspace_id: "b" },
  { session_id: "other" },
  { path: "other.step" },
  { filename: "other.step" },
  { sha256: "f".repeat(64) },
  { bytes: 7 },
  { bytes: 16777217 },
  { content_base64: "!invalid!" },
])("rejects unverified download response %j", async (extra) => {
  show(vi.fn().mockResolvedValue(result(extra)));
  fireEvent.click(screen.getByRole("button", { name: "Download file" }));
  await screen.findByText(/Download could not be verified/);
  expect(URL.createObjectURL).not.toHaveBeenCalled();
  expect(HTMLAnchorElement.prototype.click).not.toHaveBeenCalled();
});
it("shows unsupported files without requesting host delivery", async () => {
  show(vi.fn().mockResolvedValue(result({ supported: false })));
  fireEvent.click(screen.getByRole("button", { name: "Download file" }));
  await screen.findByText(/Download unavailable/);
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
it("discards a late reply after closing the selected file", async () => {
  let resolve!: (value: CallToolResult) => void;
  const call = vi.fn(
    () =>
      new Promise<CallToolResult>((done) => {
        resolve = done;
      }),
  );
  const view = show(call);
  fireEvent.click(screen.getByRole("button", { name: "Download file" }));
  view.unmount();
  await act(async () => {
    resolve(result());
  });
  await waitFor(() => expect(call).toHaveBeenCalledOnce());
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
