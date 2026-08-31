import { describe, expect, it } from "vitest";

import {
  processDefinitionViewEnabled,
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

describe("Process Definition View feature flag", () => {
  it("is default-off and rejects values outside the explicit allowlist", () => {
    for (const value of [undefined, "", "0", "false", "no", "off", "enabled"]) {
      expect(
        processDefinitionViewEnabled({
          VITE_WRIGHT_PROCESS_DEFINITION_VIEW: value,
        }),
      ).toBe(false);
    }
  });

  it("accepts only explicit truthy environment values", () => {
    for (const value of ["1", "true", "yes", "on", "TRUE"]) {
      expect(
        processDefinitionViewEnabled({
          VITE_WRIGHT_PROCESS_DEFINITION_VIEW: value,
        }),
      ).toBe(true);
    }
  });
});
