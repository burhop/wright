import { describe, expect, it } from "vitest";

import { workflowComposerEnabled } from "./workflow-composer";

describe("Workflow Composer feature flag", () => {
  it("defaults off and rejects values outside the explicit allowlist", () => {
    for (const value of [undefined, "", "0", "false", "no", "off", "enabled"]) {
      expect(
        workflowComposerEnabled({ VITE_WRIGHT_WORKFLOW_COMPOSER: value }),
      ).toBe(false);
    }
  });

  it("accepts explicit truthy values without affecting other feature flags", () => {
    for (const value of ["1", "true", "yes", "on", "TRUE", " Yes "]) {
      expect(
        workflowComposerEnabled({ VITE_WRIGHT_WORKFLOW_COMPOSER: value }),
      ).toBe(true);
    }
  });
});
