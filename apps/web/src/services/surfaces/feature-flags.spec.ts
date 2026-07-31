import { describe, expect, it } from "vitest";

import { workspaceSurfacesEnabled } from "./feature-flags";

describe("Workspace Surfaces feature flag", () => {
  it("is default-off and accepts only explicit truthy values", () => {
    expect(workspaceSurfacesEnabled({})).toBe(false);
    expect(
      workspaceSurfacesEnabled({ VITE_WORKSPACE_SURFACES_ENABLED: "0" }),
    ).toBe(false);
    for (const value of ["1", "true", "yes", "on", "TRUE"]) {
      expect(
        workspaceSurfacesEnabled({ VITE_WORKSPACE_SURFACES_ENABLED: value }),
      ).toBe(true);
    }
  });
});
