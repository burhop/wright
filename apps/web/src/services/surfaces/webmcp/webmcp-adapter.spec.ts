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
    handler: vi.fn(async (_args: unknown, _context: { signal: AbortSignal }) => ({ ok: true })),
    signal: new AbortController().signal,
  };
}

describe("WebMCP native adapter", () => {
  it("disposes native registration by abort signal even when the browser returns no handle", async () => {
    const registerTool = vi.fn(async (_definition: unknown, _options: unknown) => undefined);
    const stableDispose = vi.fn(async () => undefined);
    const result = await registerWebMcpTool(tool(), {
      sdk: { registerTool: vi.fn(async () => ({ dispose: stableDispose })) } as never,
      dualRegisterNative: true,
      document: documentWith({ modelContext: { registerTool } }),
    });
    const nativeOptions = registerTool.mock.calls[0]?.[1] as unknown as { signal: AbortSignal };
    expect(nativeOptions.signal.aborted).toBe(false);
    await result.dispose();
    await result.dispose();
    expect(nativeOptions.signal.aborted).toBe(true);
    expect(stableDispose).toHaveBeenCalledOnce();
  });

  it("passes native call cancellation to the handler and rejects calls after disposal", async () => {
    const registerTool = vi.fn(async (_definition: unknown, _options: unknown) => undefined);
    const original = tool();
    const result = await registerWebMcpTool(original, {
      sdk: { registerTool: vi.fn(async () => ({ dispose: vi.fn(async () => undefined) })) } as never,
      dualRegisterNative: true,
      document: documentWith({ modelContext: { registerTool } }),
    });
    const definition = registerTool.mock.calls[0][0] as { execute: (args: object, options: { signal: AbortSignal }) => unknown };
    const call = new AbortController();
    await definition.execute({}, { signal: call.signal });
    const context = original.handler.mock.calls[0]?.[1] as unknown as { signal: AbortSignal };
    call.abort();
    expect(context.signal.aborted).toBe(true);
    await result.dispose();
    expect(() => definition.execute({}, { signal: new AbortController().signal })).toThrow();
    expect(original.handler).toHaveBeenCalledOnce();
  });
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
