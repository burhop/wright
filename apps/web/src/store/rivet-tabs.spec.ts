import { describe, expect, it } from "vitest";

import { dedupeEditorTabs } from "./viewer";

describe("Rivet workspace tabs", () => {
  it("keeps one Wright tab per workflow path", () => {
    const tabs = dedupeEditorTabs([
      {
        name: "Rivet",
        path: "/.wright/rivet-workflows/rivet/workflow.rivet-project",
        type: "rivet",
      },
      {
        name: "rivet.rivet-project",
        path: "/.wright/rivet-workflows/rivet/workflow.rivet-project",
        type: "rivet",
      },
    ]);

    expect(tabs).toHaveLength(1);
    expect(tabs[0].name).toBe("rivet.rivet-project");
  });
});
