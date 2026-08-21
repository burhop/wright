import { describe, expect, it } from "vitest";

describe.sequential("browser storage test isolation", () => {
  it("allows a test to persist browser state", () => {
    window.localStorage.setItem("wright-test-isolation", "previous-test");
    window.sessionStorage.setItem("wright-test-isolation", "previous-test");

    expect(window.localStorage.getItem("wright-test-isolation")).toBe(
      "previous-test",
    );
    expect(window.sessionStorage.getItem("wright-test-isolation")).toBe(
      "previous-test",
    );
  });

  it("starts the next test with clean browser state", () => {
    expect(window.localStorage.getItem("wright-test-isolation")).toBeNull();
    expect(window.sessionStorage.getItem("wright-test-isolation")).toBeNull();
  });
});
