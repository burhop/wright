import { beforeEach, describe, expect, it, vi } from "vitest";

import { BrowserHostAdapter, SurfaceHostAdapterError } from "./browser-adapter";

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

  it("validates a development proxy exactly once and accepts its own result", () => {
    const development = new BrowserHostAdapter({
      controlUrl: "http://localhost:5173/workspace/ws-1",
    });
    const issued =
      "http://s-panel.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345";
    const proxy = development.validateIssuedPreviewUrl(issued);

    expect(proxy).toBe(
      "http://localhost:5173/__wright-surface/s-panel.localhost%3A5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345",
    );
    expect(development.validateIssuedPreviewUrl(proxy)).toBe(proxy);
  });

  it("opens a validated development proxy at its issued browser origin", async () => {
    const openDevelopmentWindow = vi.fn();
    const replace = vi.fn();
    openDevelopmentWindow.mockReturnValue({
      opener: {},
      document: {
        createElement: () => ({ name: "", content: "" }),
        head: { append: vi.fn() },
      },
      location: { replace },
      close: vi.fn(),
    } as unknown as Window);
    const development = new BrowserHostAdapter({
      controlUrl: "http://localhost:5173/workspace/ws-1",
      openWindow: openDevelopmentWindow,
    });
    const issued =
      "http://s-panel.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345";
    const proxy = development.validateIssuedPreviewUrl(issued);

    await development.openExternal(proxy);

    expect(replace).toHaveBeenCalledWith(issued);
  });

  it.each([
    "http://localhost:5173/__wright-surface/s-panel.localhost%3A5173/app#abcdefghijklmnopqrstuvwxyz012345",
    "http://localhost:5173/__wright-surface/s-panel.localhost%3A5173/__wright/bootstrap#short",
    "http://localhost:5173/__wright-surface/user%3Asecret%40preview.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345",
  ])("rejects malformed development preview proxies: %s", (url) => {
    const development = new BrowserHostAdapter({
      controlUrl: "http://localhost:5173/workspace/ws-1",
    });
    expect(() => development.validateIssuedPreviewUrl(url)).toThrow(
      SurfaceHostAdapterError,
    );
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
