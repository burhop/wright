import { describe, expect, it } from "vitest";

import { rivetWorkflowsTabEnabled } from "./feature-flags";

describe("rivetWorkflowsTabEnabled", () => {
  it("is disabled by default and requires an explicit flag", () => {
    expect(rivetWorkflowsTabEnabled({})).toBe(false);
    expect(rivetWorkflowsTabEnabled({ VITE_RIVET_WORKFLOWS_TAB_ENABLED: "true" })).toBe(true);
  });
});
