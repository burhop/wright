export interface DesignInputDocumentDraft {
  documentId: string;
  name: string;
  mediaType: string;
  sizeBytes: number;
  textPreview: string | null;
  textPreviewTruncated: boolean;
}

export interface DesignInputSnapshot {
  prompt: string;
  documents: DesignInputDocumentDraft[];
  revision: number;
}

export interface DesignInputHistory {
  past: DesignInputSnapshot[];
  present: DesignInputSnapshot;
  future: DesignInputSnapshot[];
}

export type DesignInputCommand =
  | { type: "replace-prompt"; prompt: string }
  | {
      type: "add-documents";
      documents: readonly DesignInputDocumentDraft[];
    }
  | { type: "remove-document"; documentId: string };

export type DesignInputHistoryAction =
  | { type: "apply"; command: DesignInputCommand }
  | { type: "undo" }
  | { type: "redo" };

export function createDesignInputHistory(): DesignInputHistory {
  return {
    past: [],
    present: { prompt: "", documents: [], revision: 0 },
    future: [],
  };
}

function applyDesignInputCommand(
  snapshot: DesignInputSnapshot,
  command: DesignInputCommand,
): DesignInputSnapshot {
  if (command.type === "replace-prompt") {
    if (command.prompt === snapshot.prompt) return snapshot;
    return {
      ...snapshot,
      prompt: command.prompt,
      revision: snapshot.revision + 1,
    };
  }

  if (command.type === "add-documents") {
    const documentIds = new Set(
      snapshot.documents.map(({ documentId }) => documentId),
    );
    const documentsToAdd = command.documents.filter(({ documentId }) => {
      if (documentIds.has(documentId)) return false;
      documentIds.add(documentId);
      return true;
    });
    if (documentsToAdd.length === 0) return snapshot;
    return {
      ...snapshot,
      documents: [...snapshot.documents, ...documentsToAdd],
      revision: snapshot.revision + 1,
    };
  }

  const documentIndex = snapshot.documents.findIndex(
    ({ documentId }) => documentId === command.documentId,
  );
  if (documentIndex === -1) return snapshot;
  return {
    ...snapshot,
    documents: snapshot.documents.filter(
      ({ documentId }) => documentId !== command.documentId,
    ),
    revision: snapshot.revision + 1,
  };
}

/**
 * Applies prompt and document edits without importing React, a canvas package,
 * browser storage, LLMs, MCP clients, or file-format parsers.
 */
export function reduceDesignInputHistory(
  history: DesignInputHistory,
  action: DesignInputHistoryAction,
): DesignInputHistory {
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

  const next = applyDesignInputCommand(history.present, action.command);
  if (next === history.present) return history;
  return {
    past: [...history.past, history.present],
    present: next,
    future: [],
  };
}
