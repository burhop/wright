import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { isDesktop, detectEnvironment } from "../../src/services/host-adapter/detect";

describe("detectEnvironment", () => {
  beforeEach(() => {
    vi.stubGlobal("window", undefined);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should return browser when window is undefined", () => {
    expect(isDesktop()).toBe(false);
    expect(detectEnvironment()).toBe("browser");
  });

  it("should return browser when window is defined but wrightDesktop is missing", () => {
    vi.stubGlobal("window", {});
    expect(isDesktop()).toBe(false);
    expect(detectEnvironment()).toBe("browser");
  });

  it("should return desktop when window and wrightDesktop are defined", () => {
    vi.stubGlobal("window", { wrightDesktop: {} });
    expect(isDesktop()).toBe(true);
    expect(detectEnvironment()).toBe("desktop");
  });
});
