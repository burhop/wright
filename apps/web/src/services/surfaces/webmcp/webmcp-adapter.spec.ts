import { describe, expect, it, vi } from "vitest";

import { detectNativeWebMcp, registerWebMcpTool } from "./webmcp-adapter";

function documentWith(values: Record<string, unknown>): Document {
  return values as unknown as Document;
}

function tool() {
  return {
    name: "select_part",
    description: "Select a part",
    inputSchema: { type: "object" },
    handler: vi.fn(async () => ({ ok: true })),
    signal: new AbortController().signal,
  };
}

describe("WebMCP native adapter", () => {
  it("feature-detects absence, current shape, and Permissions Policy denial", () => {
    expect(detectNativeWebMcp(documentWith({}))).toBe("absent");
    expect(
      detectNativeWebMcp(
        documentWith({ modelContext: { registerTool: vi.fn() } }),
      ),
    ).toBe("available");
    expect(
      detectNativeWebMcp(
        documentWith({
          modelContext: { registerTool: vi.fn() },
          permissionsPolicy: { allowsFeature: () => false },
        }),
      ),
    ).toBe("policy_denied");
  });

  it("keeps the scoped Wright registration when native registration rejects", async () => {
    const stableDispose = vi.fn(async () => undefined);
    const sdk = {
      registerTool: vi.fn(async () => ({ dispose: stableDispose })),
    };
    const result = await registerWebMcpTool(tool(), {
      sdk: sdk as never,
      dualRegisterNative: true,
      document: documentWith({
        modelContext: {
          registerTool: vi.fn(async () => {
            throw new Error("draft changed");
          }),
        },
      }),
    });
    expect(result.nativeState).toBe("rejected");
    expect(sdk.registerTool).toHaveBeenCalledOnce();
    await result.dispose();
    expect(stableDispose).toHaveBeenCalledOnce();
  });

  it("does not polyfill document.modelContext when native support is absent", async () => {
    const documentValue = documentWith({});
    const result = await registerWebMcpTool(tool(), {
      sdk: { registerTool: vi.fn(async () => ({ dispose: vi.fn() })) } as never,
      document: documentValue,
      dualRegisterNative: true,
    });
    expect(result.nativeState).toBe("absent");
    expect("modelContext" in documentValue).toBe(false);
  });
});
