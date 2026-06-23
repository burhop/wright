import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { DesktopHostAdapter } from "../../src/services/host-adapter/desktop-adapter";

describe("DesktopHostAdapter", () => {
  let adapter: DesktopHostAdapter;
  let mockBridge: any;

  beforeEach(() => {
    mockBridge = {
      api: vi.fn(),
      readFile: vi.fn(),
      writeFile: vi.fn(),
      listDirectory: vi.fn(),
      selectFiles: vi.fn(),
      notify: vi.fn(),
      getConfig: vi.fn().mockResolvedValue({ apiPort: 8888, workspacePath: "/mock/workspace" }),
    };

    vi.stubGlobal("window", {
      wrightDesktop: mockBridge,
    });

    adapter = new DesktopHostAdapter();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should have desktop mode", () => {
    expect(adapter.mode).toBe("desktop");
  });

  it("should return hash router type", () => {
    expect(adapter.getRouterType()).toBe("hash");
  });

  it("should retrieve API port and base URL from getConfig", async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(adapter.getApiBaseUrl()).toBe("http://localhost:8888");
  });

  it("should route fetch through wrightDesktop api bridge", async () => {
    mockBridge.api.mockResolvedValue({ success: true, count: 42 });

    const res = await adapter.fetch("http://localhost:8000/api/workspace/list", {
      method: "POST",
      body: JSON.stringify({ active: true }),
      headers: { "X-Test": "yes" },
    });

    expect(mockBridge.api).toHaveBeenCalledWith({
      path: "/api/workspace/list",
      method: "POST",
      body: { active: true },
      headers: { "X-Test": "yes" },
    });

    expect(res.ok).toBe(true);
    const json = await res.json();
    expect(json).toEqual({ success: true, count: 42 });
  });

  it("should return ok=false response when bridge API rejects", async () => {
    const errorObj = { status: 400, code: "BAD_REQUEST", message: "Invalid parameters" };
    mockBridge.api.mockRejectedValue(errorObj);

    const res = await adapter.fetch("/api/bad-endpoint");
    expect(res.ok).toBe(false);
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json).toEqual({
      error_code: "BAD_REQUEST",
      message: "Invalid parameters",
      trace_id: "unknown",
      details: undefined,
    });
  });

  it("should delegate readFile to bridge", async () => {
    mockBridge.readFile.mockResolvedValue("file content text");
    const content = await adapter.readFile("/path/to/file.txt");
    expect(mockBridge.readFile).toHaveBeenCalledWith("/path/to/file.txt");
    expect(content).toBe("file content text");
  });

  it("should delegate writeFile to bridge", async () => {
    mockBridge.writeFile.mockResolvedValue(undefined);
    await adapter.writeFile("/path/to/file.txt", "content text");
    expect(mockBridge.writeFile).toHaveBeenCalledWith("/path/to/file.txt", "content text");
  });

  it("should delegate listDirectory to bridge", async () => {
    const entries = [{ name: "foo.txt", path: "/path/foo.txt", isDirectory: false }];
    mockBridge.listDirectory.mockResolvedValue(entries);
    const result = await adapter.listDirectory("/path");
    expect(mockBridge.listDirectory).toHaveBeenCalledWith("/path");
    expect(result).toEqual(entries);
  });

  it("should delegate selectFiles to bridge", async () => {
    const files = ["/path/a.txt", "/path/b.txt"];
    mockBridge.selectFiles.mockResolvedValue(files);
    const result = await adapter.selectFiles({ title: "Choose Files" });
    expect(mockBridge.selectFiles).toHaveBeenCalledWith({ title: "Choose Files" });
    expect(result).toEqual(files);
  });

  it("should delegate notify to bridge", async () => {
    mockBridge.notify.mockResolvedValue(true);
    const result = await adapter.notify("Title", "Body");
    expect(mockBridge.notify).toHaveBeenCalledWith({ title: "Title", body: "Body" });
    expect(result).toBe(true);
  });
});
