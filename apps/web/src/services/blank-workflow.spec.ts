import { describe, expect, it } from "vitest";
import { blankWorkflowSource } from "./blank-workflow";

describe("blank workflow creation", () => {
  it("starts without example blocks and uses a fresh identity each time", () => {
    const first = blankWorkflowSource();
    expect(first).toMatch(/^workflow authored_[a-f0-9_]+\n/);
    expect(first).not.toMatch(/\n(?:input|task|output|relationship|link) /);
    expect(first).not.toContain("mounting");
    expect(blankWorkflowSource()).not.toEqual(first);
  });
  it("quotes user supplied names without creating extra source fields", () => {
    const title = 'Fixture "name"\nwith newline';
    expect(blankWorkflowSource(title)).toContain(
      `name: ${JSON.stringify(title)}\n`,
    );
  });
});
