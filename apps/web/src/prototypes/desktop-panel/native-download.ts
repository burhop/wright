import type { App } from "@modelcontextprotocol/ext-apps";
import type { FileDownloadResult } from "@wright/ui-kit";

/** Public MCP Apps delivery: embed already-scoped bytes, never a remote URL. */
export async function downloadNativeFile(
  app: Pick<App, "getHostCapabilities" | "downloadFile">,
  blob: Blob,
  name: string,
): Promise<FileDownloadResult> {
  if (!app.getHostCapabilities()?.downloadFile) return "unavailable";
  const hasControl = Array.from(name).some((char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127);
  if (!name || name.startsWith(".") || /[\\/]/.test(name) || hasControl || blob.size > 32 * 1024 * 1024)
    throw new Error("Invalid bounded file download");
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 8192)
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  const result = await app.downloadFile({ contents: [{
    type: "resource",
    resource: {
      // The URI supplies a basename, not a GB10 path or a host-fetch destination.
      uri: `file:///${encodeURIComponent(name)}`,
      mimeType: blob.type || "application/octet-stream",
      blob: btoa(binary),
    },
  }] }, { timeout: 60_000 });
  return result.isError ? "declined" : "requested";
}
