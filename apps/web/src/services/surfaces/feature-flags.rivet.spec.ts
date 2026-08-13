import { describe, expect, it } from "vitest";

import { rivetWorkflowsTabEnabled } from "./feature-flags";

describe("rivetWorkflowsTabEnabled", () => {
  it("is enabled by default and supports an explicit emergency opt-out", () => {
    expect(rivetWorkflowsTabEnabled({})).toBe(true);
    expect(
      rivetWorkflowsTabEnabled({ VITE_RIVET_WORKFLOWS_TAB_ENABLED: "true" }),
    ).toBe(true);
    expect(
      rivetWorkflowsTabEnabled({ VITE_RIVET_WORKFLOWS_TAB_ENABLED: "false" }),
    ).toBe(false);
  });
});
