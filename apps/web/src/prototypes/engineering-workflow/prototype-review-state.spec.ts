import { describe, expect, it } from "vitest";

import { prototypeViewStateForSearch } from "./prototype-review-state";

describe("prototypeViewStateForSearch", () => {
  it.each(["loading", "empty", "error"] as const)(
    "selects the deterministic %s review state",
    (view) => {
      expect(prototypeViewStateForSearch(`?view=${view}`)).toBe(view);
    },
  );

  it("keeps ready as the safe default", () => {
    expect(prototypeViewStateForSearch("")).toBe("ready");
    expect(prototypeViewStateForSearch("?view=unknown")).toBe("ready");
  });
});
