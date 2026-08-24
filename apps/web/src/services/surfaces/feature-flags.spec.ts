import { describe, expect, it } from "vitest";

import {
  engineeringWorkflowPrototypeEnabled,
  workspaceSurfacesEnabled,
} from "./feature-flags";

describe("Workspace Surfaces feature flag", () => {
  it("is default-off even when this document cannot access local storage", () => {
    expect(workspaceSurfacesEnabled({})).toBe(false);
    expect(
      workspaceSurfacesEnabled({ VITE_WORKSPACE_SURFACES_ENABLED: "0" }),
    ).toBe(false);
  });

  it("accepts only explicit truthy environment values", () => {
    for (const value of ["1", "true", "yes", "on", "TRUE"]) {
      expect(
        workspaceSurfacesEnabled({ VITE_WORKSPACE_SURFACES_ENABLED: value }),
      ).toBe(true);
    }
  });
});

describe("Engineering workflow prototype feature flag", () => {
  it("remains off when explicitly disabled", () => {
    expect(
      engineeringWorkflowPrototypeEnabled({
        VITE_ENGINEERING_WORKFLOW_PROTOTYPE: "0",
      }),
    ).toBe(false);
  });

  it("accepts only explicit truthy environment values", () => {
    for (const value of ["1", "true", "yes", "on", "TRUE"]) {
      expect(
        engineeringWorkflowPrototypeEnabled({
          VITE_ENGINEERING_WORKFLOW_PROTOTYPE: value,
        }),
      ).toBe(true);
    }
  });
});
