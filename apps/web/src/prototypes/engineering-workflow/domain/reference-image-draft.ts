export interface ReferenceImageSelection {
  imageIds: string[];
  revision: number;
}

export interface ReferenceImageHistory {
  past: ReferenceImageSelection[];
  present: ReferenceImageSelection;
  future: ReferenceImageSelection[];
}

export type ReferenceImageCommand =
  | { type: "add"; imageId: string }
  | { type: "remove"; imageId: string }
  | {
      type: "move";
      imageId: string;
      direction: "earlier" | "later";
    };

export type ReferenceImageHistoryAction =
  | { type: "apply"; command: ReferenceImageCommand }
  | { type: "undo" }
  | { type: "redo" };

export function createReferenceImageHistory(
  imageIds: readonly string[] = [],
): ReferenceImageHistory {
  return {
    past: [],
    present: { imageIds: [...imageIds], revision: 0 },
    future: [],
  };
}

function applyReferenceImageCommand(
  selection: ReferenceImageSelection,
  command: ReferenceImageCommand,
  allowedImageIds: ReadonlySet<string>,
): ReferenceImageSelection {
  if (!allowedImageIds.has(command.imageId)) {
    throw new Error(`Unknown reference image ${command.imageId}.`);
  }

  const imageIds = [...selection.imageIds];
  const currentIndex = imageIds.indexOf(command.imageId);

  if (command.type === "add") {
    if (currentIndex !== -1) return selection;
    imageIds.push(command.imageId);
  } else if (command.type === "remove") {
    if (currentIndex === -1) return selection;
    imageIds.splice(currentIndex, 1);
  } else {
    if (currentIndex === -1) return selection;
    const targetIndex =
      command.direction === "earlier" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= imageIds.length) return selection;
    [imageIds[currentIndex], imageIds[targetIndex]] = [
      imageIds[targetIndex],
      imageIds[currentIndex],
    ];
  }

  return {
    imageIds,
    revision: selection.revision + 1,
  };
}

/**
 * Applies local, typed reference-image edits without importing React, a canvas
 * package, browser storage, or workspace APIs.
 */
export function reduceReferenceImageHistory(
  history: ReferenceImageHistory,
  action: ReferenceImageHistoryAction,
  allowedImageIds: readonly string[],
): ReferenceImageHistory {
  if (action.type === "undo") {
    const previous = history.past.at(-1);
    if (!previous) return history;
    return {
      past: history.past.slice(0, -1),
      present: previous,
      future: [history.present, ...history.future],
    };
  }

  if (action.type === "redo") {
    const next = history.future[0];
    if (!next) return history;
    return {
      past: [...history.past, history.present],
      present: next,
      future: history.future.slice(1),
    };
  }

  const next = applyReferenceImageCommand(
    history.present,
    action.command,
    new Set(allowedImageIds),
  );
  if (next === history.present) return history;

  return {
    past: [...history.past, history.present],
    present: next,
    future: [],
  };
}
