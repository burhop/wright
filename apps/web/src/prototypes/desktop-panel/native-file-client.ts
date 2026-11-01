import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export interface NativeFileScope {
  workspace_id: string;
  session_id: string;
  path: string;
}

export type NativeFileCall = (
  name: "wright_workspace_file_describe",
  args: { request: NativeFileScope },
) => Promise<CallToolResult>;

/** Presentation only. The backend checks scope and the MCP adapter checks bytes. */
export async function openNativeWorkspaceFile(
  scope: NativeFileScope,
  call: NativeFileCall,
  open: (path: string) => Promise<unknown>,
): Promise<boolean> {
  const result = await call("wright_workspace_file_describe", {
    request: scope,
  });
  const data = result.structuredContent;
  if (
    result.isError ||
    !data ||
    data.schema_version !== "wright.native-workspace-file/1" ||
    data.workspace_id !== scope.workspace_id ||
    data.session_id !== scope.session_id ||
    data.path !== scope.path ||
    !/^[a-f0-9]{64}$/.test(String(data.sha256))
  )
    throw new Error(
      "Wright could not confirm this exact workspace file. Refresh to inspect it.",
    );
  if (data.supported === false) return false;
  if (
    data.supported !== true ||
    !["workflow", "image"].includes(String(data.viewer)) ||
    typeof data.absolute_path !== "string" ||
    !/^(?:\/|[A-Za-z]:[\\/])/.test(data.absolute_path) ||
    !Number.isInteger(data.bytes) ||
    Number(data.bytes) < 0 ||
    Number(data.bytes) > 16 * 1024 * 1024
  )
    throw new Error("Wright has no qualified native viewer for this file.");
  try {
    await open(data.absolute_path);
  } catch {
    throw new Error(
      "The desktop did not confirm opening this file. Check its tabs before trying again.",
    );
  }
  return true;
}
