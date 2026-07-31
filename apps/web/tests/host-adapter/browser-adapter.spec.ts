import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserHostAdapter } from "../../src/services/host-adapter/browser-adapter";
import { AUTH_TOKEN_STORAGE_KEY } from "../../src/services/auth-session";

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
      localStorage: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
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
    const mockResponse = new Response(JSON.stringify({ data: "ok" }), {
      status: 200,
    });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    const res = await adapter.fetch("/api/test");
    expect(fetchSpy).toHaveBeenCalledWith("/api/test", {
      credentials: "same-origin",
    });
    const data = await res.json();
    expect(data).toEqual({ data: "ok" });
  });

  it("should exchange a stored token and retry once after a protected API 401", async () => {
    const unauthorized = new Response(JSON.stringify({ detail: "nope" }), {
      status: 401,
    });
    const session = new Response(null, { status: 204 });
    const retried = new Response(JSON.stringify({ data: "ok" }), {
      status: 200,
    });
    const fetchSpy = vi
      .fn()
      .mockResolvedValueOnce(unauthorized)
      .mockResolvedValueOnce(session)
      .mockResolvedValueOnce(retried);
    vi.stubGlobal("fetch", fetchSpy);
    vi.mocked(window.localStorage.getItem).mockImplementation((key) =>
      key === AUTH_TOKEN_STORAGE_KEY ? "stored-token" : null,
    );

    const res = await adapter.fetch("/api/workspace/create", {
      method: "POST",
    });

    expect(fetchSpy).toHaveBeenNthCalledWith(1, "/api/workspace/create", {
      method: "POST",
      credentials: "same-origin",
    });
    expect(fetchSpy).toHaveBeenNthCalledWith(2, "/api/auth/session", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: "stored-" + "token" }),
    });
    expect(fetchSpy).toHaveBeenNthCalledWith(3, "/api/workspace/create", {
      method: "POST",
      credentials: "same-origin",
    });
    expect(await res.json()).toEqual({ data: "ok" });
  });

  it("should read files using the API content endpoint", async () => {
    const mockResponse = new Response("file content", { status: 200 });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    const content = await adapter.readFile("some/file.txt", {
      sessionId: "session-123",
    });
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/workspace/files/content?session_id=session-123&path=some%2Ffile.txt",
      { credentials: "same-origin" },
    );
    expect(content).toBe("file content");
  });

  it("should write files using the API content endpoint", async () => {
    const mockResponse = new Response(JSON.stringify({ success: true }), {
      status: 200,
    });
    const fetchSpy = vi.fn().mockResolvedValue(mockResponse);
    vi.stubGlobal("fetch", fetchSpy);

    await adapter.writeFile("some/file.txt", "new content", {
      sessionId: "session-123",
    });
    expect(fetchSpy).toHaveBeenCalledWith("/api/workspace/files/content", {
      method: "PUT",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: "session-123",
        path: "some/file.txt",
        content: "new content",
      }),
    });
  });
});
