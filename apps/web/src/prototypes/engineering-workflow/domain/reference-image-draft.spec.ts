import { describe, expect, it } from "vitest";

import {
  createReferenceImageHistory,
  reduceReferenceImageHistory,
  type ReferenceImageHistory,
  type ReferenceImageHistoryAction,
} from "./reference-image-draft";

const allowedImageIds = ["tray", "rack", "stand"];

function reduce(
  history: ReferenceImageHistory,
  action: ReferenceImageHistoryAction,
) {
  return reduceReferenceImageHistory(history, action, allowedImageIds);
}

describe("reference image draft commands", () => {
  it("adds, reorders, and removes deterministic image identities", () => {
    let history = createReferenceImageHistory();
    history = reduce(history, {
      type: "apply",
      command: { type: "add", imageId: "tray" },
    });
    history = reduce(history, {
      type: "apply",
      command: { type: "add", imageId: "rack" },
    });
    history = reduce(history, {
      type: "apply",
      command: { type: "move", imageId: "rack", direction: "earlier" },
    });

    expect(history.present.imageIds).toEqual(["rack", "tray"]);

    history = reduce(history, {
      type: "apply",
      command: { type: "remove", imageId: "tray" },
    });
    expect(history.present.imageIds).toEqual(["rack"]);
    expect(history.present.revision).toBe(4);
  });

  it("supports undo and redo and clears redo after a new edit", () => {
    let history = createReferenceImageHistory();
    for (const imageId of ["tray", "rack"]) {
      history = reduce(history, {
        type: "apply",
        command: { type: "add", imageId },
      });
    }

    history = reduce(history, { type: "undo" });
    expect(history.present.imageIds).toEqual(["tray"]);
    expect(history.future).toHaveLength(1);

    history = reduce(history, { type: "redo" });
    expect(history.present.imageIds).toEqual(["tray", "rack"]);

    history = reduce(history, { type: "undo" });
    history = reduce(history, {
      type: "apply",
      command: { type: "add", imageId: "stand" },
    });
    expect(history.present.imageIds).toEqual(["tray", "stand"]);
    expect(history.future).toEqual([]);
  });

  it("rejects unknown image identities and ignores duplicate or boundary edits", () => {
    let history = createReferenceImageHistory(["tray"]);
    const unchanged = reduce(history, {
      type: "apply",
      command: { type: "add", imageId: "tray" },
    });
    expect(unchanged).toBe(history);

    history = reduce(history, {
      type: "apply",
      command: { type: "move", imageId: "tray", direction: "earlier" },
    });
    expect(history).toBe(unchanged);
    expect(() =>
      reduce(history, {
        type: "apply",
        command: { type: "add", imageId: "missing" },
      }),
    ).toThrow("Unknown reference image");
  });
});
