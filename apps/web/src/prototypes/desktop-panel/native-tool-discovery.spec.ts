import { describe, expect, it, vi } from "vitest";
import { createNativeOptionReader } from "./native-tool-discovery";

describe("scoped engineering options", () => {
  it("uses the MCP owner without browser HTTP and preserves unavailable capability", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const call = vi.fn().mockResolvedValue({
      structuredContent: {
        workspace_id: "w",
        session_id: "s",
        kind: "cad",
        options: { supported: false },
      },
    });
    const read = createNativeOptionReader("w", "s", call);
    expect(await (await read("cad", "s", "tool", true)).json()).toEqual({
      supported: false,
    });
    expect(call).toHaveBeenCalledExactlyOnceWith(
      "wright_workflow_editor_options",
      {
        request: {
          workspace_id: "w",
          session_id: "s",
          kind: "cad",
          server_id: "tool",
          include_resources: true,
        },
      },
    );
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
  it("rejects a different session before dispatch and a reply for another workspace", async () => {
    const call = vi.fn().mockResolvedValue({
      structuredContent: {
        workspace_id: "foreign",
        session_id: "s",
        kind: "application",
        options: {},
      },
    });
    const read = createNativeOptionReader("w", "s", call);
    await expect(read("application", "other", "tool")).rejects.toThrow();
    expect(call).not.toHaveBeenCalled();
    await expect(read("application", "s", "tool")).rejects.toThrow();
  });
});
