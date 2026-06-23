import { describe, it, expect, afterEach, vi } from "vitest";
import { BrowserHostAdapter } from "../../src/services/host-adapter/browser-adapter";
import { DesktopHostAdapter } from "../../src/services/host-adapter/desktop-adapter";

describe("selectFiles", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should create input file element and trigger click in BrowserHostAdapter", async () => {
    const adapter = new BrowserHostAdapter();
    const mockInput = {
      click: vi.fn(),
      addEventListener: vi.fn(),
      setAttribute: vi.fn(),
      type: "",
      multiple: false,
      accept: "",
      files: [{ name: "test-file.txt" }],
    };

    const createElementSpy = vi.fn().mockReturnValue(mockInput);
    vi.stubGlobal("document", {
      createElement: createElementSpy,
    });

    const promise = adapter.selectFiles({ multiple: true });

    setTimeout(() => {
      if ((mockInput as any).onchange) {
        (mockInput as any).onchange();
      }
    }, 10);

    const result = await promise;
    expect(createElementSpy).toHaveBeenCalledWith("input");
    expect(mockInput.type).toBe("file");
    expect(mockInput.multiple).toBe(true);
    expect(mockInput.click).toHaveBeenCalled();
    expect(result).toEqual(["test-file.txt"]);
  });

  it("should delegate to wrightDesktop in DesktopHostAdapter", async () => {
    const mockBridge = {
      selectFiles: vi.fn().mockResolvedValue(["/abs/path/to/file.txt"]),
      getConfig: vi.fn().mockResolvedValue({ apiPort: 8000 }),
    };
    vi.stubGlobal("window", {
      wrightDesktop: mockBridge,
    });

    const adapter = new DesktopHostAdapter();
    const result = await adapter.selectFiles({ multiple: false });
    expect(mockBridge.selectFiles).toHaveBeenCalledWith({ multiple: false });
    expect(result).toEqual(["/abs/path/to/file.txt"]);
  });
});
