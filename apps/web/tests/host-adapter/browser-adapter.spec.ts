import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserHostAdapter } from "../../src/services/host-adapter/browser-adapter";

describe("BrowserHostAdapter", () => {
  let adapter: BrowserHostAdapter;

  beforeEach(() => {
    adapter = new BrowserHostAdapter();
    vi.stubGlobal("window", {
      location: {
        hostname: "localhost",
        port: "5173",
        protocol: "http:",
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should have browser mode", () => {
    expect(adapter.mode).toBe("browser");
  });

  it("should return browser router type", () => {
    expect(adapter.getRouterType()).toBe("browser");
  });

  it("should resolve correct API base URL based on port", () => {
    expect(adapter.getApiBaseUrl()).toBe("");
  });

  it("should delegate fetch to global fetch", async () => {
    const mockResponse = new Response(JSON.stringify({ data: "ok" }), { status: 200 });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    const res = await adapter.fetch("/api/test");
    expect(fetchSpy).toHaveBeenCalledWith("/api/test", undefined);
    const data = await res.json();
    expect(data).toEqual({ data: "ok" });
  });

  it("should read files using the API content endpoint", async () => {
    const mockResponse = new Response("file content", { status: 200 });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    const content = await adapter.readFile("some/file.txt", { sessionId: "session-123" });
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/workspace/files/content?session_id=session-123&path=some%2Ffile.txt"
    );
    expect(content).toBe("file content");
  });

  it("should write files using the API content endpoint", async () => {
    const mockResponse = new Response(JSON.stringify({ success: true }), { status: 200 });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    await adapter.writeFile("some/file.txt", "new content", { sessionId: "session-123" });
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/workspace/files/content",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "session-123",
          path: "some/file.txt",
          content: "new content",
        }),
      }
    );
  });
});
