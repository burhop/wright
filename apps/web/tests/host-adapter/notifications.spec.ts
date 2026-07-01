import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserHostAdapter } from "../../src/services/host-adapter/browser-adapter";
import { DesktopHostAdapter } from "../../src/services/host-adapter/desktop-adapter";

describe("Notifications Adapter Methods", () => {
  let desktopAdapter: DesktopHostAdapter;
  let browserAdapter: BrowserHostAdapter;
  let mockBridge: any;

  beforeEach(() => {
    mockBridge = {
      notify: vi.fn().mockResolvedValue(true),
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

  it("should delegate notify to bridge in desktop mode", async () => {
    const result = await desktopAdapter.notify("Hello", "World");
    expect(mockBridge.notify).toHaveBeenCalledWith({
      title: "Hello",
      body: "World",
    });
    expect(result).toBe(true);
  });

  it("should request permission and show notification in browser mode if not denied", async () => {
    const mockNotificationSpy = vi.fn();
    const mockNotificationClass = Object.assign(mockNotificationSpy, {
      permission: "default",
      requestPermission: vi.fn().mockResolvedValue("granted"),
    });

    vi.stubGlobal("Notification", mockNotificationClass);
    vi.stubGlobal("window", {
      Notification: mockNotificationClass,
    });

    const result = await browserAdapter.notify("Hello", "World");
    expect(mockNotificationClass.requestPermission).toHaveBeenCalled();
    expect(mockNotificationSpy).toHaveBeenCalledWith("Hello", {
      body: "World",
    });
    expect(result).toBe(true);
  });

  it("should return false in browser mode if permission is denied", async () => {
    const mockNotificationClass = {
      permission: "denied",
      requestPermission: vi.fn(),
    };
    vi.stubGlobal("Notification", mockNotificationClass);
    vi.stubGlobal("window", {
      Notification: mockNotificationClass,
    });

    const result = await browserAdapter.notify("Hello", "World");
    expect(result).toBe(false);
  });
});
