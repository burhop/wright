import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  BrowserHostAdapter,
  SurfaceHostAdapterError,
} from "./browser-adapter";

describe("BrowserHostAdapter surface presentation boundary", () => {
  const openWindow = vi.fn();
  const adapter = new BrowserHostAdapter({
    controlUrl: "https://wright.example.test/workspace/ws-1",
    openWindow,
  });

  beforeEach(() => openWindow.mockReset());

  it("resolves backend paths and validates a distinct absolute preview URL", () => {
    expect(adapter.resolveBackendUrl("/api/workspace/surfaces")).toBe(
      "https://wright.example.test/api/workspace/surfaces",
    );
    const issued =
      "https://s-presentation.preview.example.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345";
    expect(adapter.validateIssuedPreviewUrl(issued)).toBe(issued);
  });

  it.each([
    "/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345",
    "javascript:alert(1)",
    "https://user:secret@preview.example.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345",
    "https://wright.example.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345",
    "https://preview.example.test/app#abcdefghijklmnopqrstuvwxyz012345",
    "https://preview.example.test/__wright/bootstrap",
  ])("rejects malformed or control-origin preview authority: %s", (url) => {
    expect(() => adapter.validateIssuedPreviewUrl(url)).toThrow(
      SurfaceHostAdapterError,
    );
  });

  it("opens issued previews with noopener and reports browser refusal", async () => {
    const issued =
      "https://s-presentation.preview.example.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345";
    const replace = vi.fn();
    const append = vi.fn();
    openWindow.mockReturnValue({
      opener: {},
      document: {
        createElement: () => ({ name: "", content: "" }),
        head: { append },
      },
      location: { replace },
      close: vi.fn(),
    } as unknown as Window);
    await adapter.openExternal(issued);
    expect(openWindow).toHaveBeenCalledWith("about:blank", "_blank", "popup");
    expect(append).toHaveBeenCalledOnce();
    expect(replace).toHaveBeenCalledWith(issued);

    openWindow.mockReturnValue(null);
    await expect(adapter.openExternal(issued)).rejects.toMatchObject({
      code: "SURFACE_HOST_EXTERNAL_OPEN_FAILED",
    });
  });

  it("allows an explicitly approved direct HTTP URL but never credentials", async () => {
    openWindow.mockReturnValue({
      opener: null,
      document: {
        createElement: () => ({ name: "", content: "" }),
        head: { append: vi.fn() },
      },
      location: { replace: vi.fn() },
      close: vi.fn(),
    } as unknown as Window);
    await adapter.openExternal("https://brep.example.test/design/42", {
      approvedDirectUrl: true,
    });
    expect(openWindow).toHaveBeenCalledTimes(1);
    await expect(
      adapter.openExternal("https://user:secret@brep.example.test/design/42", {
        approvedDirectUrl: true,
      }),
    ).rejects.toMatchObject({ code: "SURFACE_HOST_URL_REJECTED" });
  });
});
