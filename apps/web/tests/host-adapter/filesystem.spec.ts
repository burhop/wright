import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { DesktopHostAdapter } from "../../src/services/host-adapter/desktop-adapter";
import { BrowserHostAdapter } from "../../src/services/host-adapter/browser-adapter";

describe("Filesystem Adapter Methods", () => {
  let desktopAdapter: DesktopHostAdapter;
  let browserAdapter: BrowserHostAdapter;
  let mockBridge: any;

  beforeEach(() => {
    mockBridge = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      listDirectory: vi.fn(),
      getConfig: vi.fn().mockResolvedValue({ apiPort: 8000 }),
    };

    vi.stubGlobal("window", {
      wrightDesktop: mockBridge,
    });

    desktopAdapter = new DesktopHostAdapter();
    browserAdapter = new BrowserHostAdapter();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should delegate readFile to bridge in desktop mode", async () => {
    mockBridge.readFile.mockResolvedValue("hello world");
    const result = await desktopAdapter.readFile("/path/file.txt");
    expect(mockBridge.readFile).toHaveBeenCalledWith("/path/file.txt");
    expect(result).toBe("hello world");
  });

  it("should delegate writeFile to bridge in desktop mode", async () => {
    mockBridge.writeFile.mockResolvedValue(undefined);
    await desktopAdapter.writeFile("/path/file.txt", "hello");
    expect(mockBridge.writeFile).toHaveBeenCalledWith("/path/file.txt", "hello");
  });

  it("should delegate listDirectory to bridge in desktop mode", async () => {
    const mockEntries = [{ name: "a.txt", path: "/path/a.txt", isDirectory: false }];
    mockBridge.listDirectory.mockResolvedValue(mockEntries);
    const result = await desktopAdapter.listDirectory("/path");
    expect(mockBridge.listDirectory).toHaveBeenCalledWith("/path");
    expect(result).toEqual(mockEntries);
  });

  it("should throw in browser mode for listDirectory", async () => {
    await expect(browserAdapter.listDirectory("/path")).rejects.toThrow("listDirectory is not supported in browser mode");
  });
});
