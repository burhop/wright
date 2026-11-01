import { expect, it, vi } from "vitest";
import {
  openNativeWorkspaceFile,
  type NativeFileCall,
} from "./native-file-client";

const scope = {
  workspace_id: "workspace",
  session_id: "session",
  path: "workflows/sample.wflow",
};
const descriptor = {
  schema_version: "wright.native-workspace-file/1",
  ...scope,
  supported: true,
  viewer: "workflow",
  absolute_path: "/workspace/workflows/sample.wflow",
  sha256: "a".repeat(64),
  bytes: 120,
};
function fixture(data = descriptor) {
  return {
    call: vi
      .fn<NativeFileCall>()
      .mockResolvedValue({ content: [], structuredContent: data }),
    open: vi.fn<(path: string) => Promise<unknown>>().mockResolvedValue({}),
  };
}
it("opens only the exact backend-resolved file in the host, with no source/run calls", async () => {
  const { call, open } = fixture();
  expect(await openNativeWorkspaceFile(scope, call, open)).toBe(true);
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_workspace_file_describe",
    { request: scope },
  );
  expect(open).toHaveBeenCalledExactlyOnceWith(descriptor.absolute_path);
});
it("leaves unsupported formats to the explicit existing preview fallback", async () => {
  const { call, open } = fixture({ ...descriptor, supported: false });
  expect(await openNativeWorkspaceFile(scope, call, open)).toBe(false);
  expect(open).not.toHaveBeenCalled();
});
it.each([
  { workspace_id: "foreign" },
  { session_id: "foreign" },
  { path: "other.wflow" },
  { sha256: "invalid" },
  { bytes: 17 * 1024 * 1024 },
  { absolute_path: "relative/file" },
  { viewer: "unqualified" },
])(
  "rejects a mismatched/unqualified descriptor without invoking the host: %j",
  async (patch) => {
    const { call, open } = fixture({ ...descriptor, ...patch });
    await expect(openNativeWorkspaceFile(scope, call, open)).rejects.toThrow();
    expect(open).not.toHaveBeenCalled();
  },
);
it("does not retry a failed or uncertain host open", async () => {
  const { call, open } = fixture();
  open.mockRejectedValue(Error("private host diagnostic"));
  await expect(openNativeWorkspaceFile(scope, call, open)).rejects.toThrow(
    "Check its tabs before trying again",
  );
  expect(open).toHaveBeenCalledTimes(1);
  expect(call).toHaveBeenCalledTimes(1);
});
