import { describe, expect, it } from "vitest";

import { isBrepToolActivity } from "./brep-panel-activity";

describe("isBrepToolActivity", () => {
  it("recognizes a namespaced BREP MCP tool", () => {
    expect(
      isBrepToolActivity({
        server: "1f4a1d20-429c-41c6-a0d6-6788e8544396",
        tool: "1f4a1d20-429c-41c6-a0d6-6788e8544396__brep.app.status",
        title: "Report visible application status",
      }),
    ).toBe(true);
  });

  it("recognizes the Wright-owned BREP panel progress title", () => {
    expect(
      isBrepToolActivity({ title: "Opening BREP in Wright" }),
    ).toBe(true);
  });

  it("does not react to unrelated MCP activity", () => {
    expect(
      isBrepToolActivity({
        server: "rivet-workflows",
        tool: "rivet-workflows__run_workflow",
        title: "Run Rivet workflow",
      }),
    ).toBe(false);
  });
});
