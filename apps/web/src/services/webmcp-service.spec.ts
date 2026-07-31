import { describe, expect, it, vi } from "vitest";

import { WebMcpService } from "./webmcp-service";

describe("legacy WebMCP compatibility relay", () => {
  it("is default-off and installs no global event bridge", () => {
    const add = vi.spyOn(window, "addEventListener");
    const service = new WebMcpService();
    service.connect();
    expect(service.compatibilityEnabled).toBe(false);
    expect(add).not.toHaveBeenCalledWith("webmcp:response", expect.anything());
    service.disconnect();
  });

  it("requires an explicit one-release compatibility flag", () => {
    const add = vi.spyOn(window, "addEventListener");
    const service = new WebMcpService({ enabled: true });
    expect(service.compatibilityEnabled).toBe(true);
    expect(add).toHaveBeenCalledWith("webmcp:response", expect.any(Function));
    service.disconnect();
  });
});
