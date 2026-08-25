export interface KnowledgeLookupSnapshot {
  query: string;
  sourceIds: string[];
  revision: number;
}

export interface KnowledgeLookupHistory {
  past: KnowledgeLookupSnapshot[];
  present: KnowledgeLookupSnapshot;
  future: KnowledgeLookupSnapshot[];
}

export type KnowledgeLookupCommand =
  | { type: "replace-query"; query: string }
  | { type: "toggle-source"; sourceId: string };

export type KnowledgeLookupHistoryAction =
  | { type: "apply"; command: KnowledgeLookupCommand }
  | { type: "undo" }
  | { type: "redo" };

export function createKnowledgeLookupHistory(): KnowledgeLookupHistory {
  return {
    past: [],
    present: { query: "", sourceIds: [], revision: 0 },
    future: [],
  };
}

function applyKnowledgeLookupCommand(
  snapshot: KnowledgeLookupSnapshot,
  command: KnowledgeLookupCommand,
  allowedSourceIds: ReadonlySet<string>,
): KnowledgeLookupSnapshot {
  if (command.type === "replace-query") {
    if (command.query === snapshot.query) return snapshot;
    return {
      ...snapshot,
      query: command.query,
      revision: snapshot.revision + 1,
    };
  }

  if (!allowedSourceIds.has(command.sourceId)) return snapshot;
  const sourceSelected = snapshot.sourceIds.includes(command.sourceId);
  return {
    ...snapshot,
    sourceIds: sourceSelected
      ? snapshot.sourceIds.filter((sourceId) => sourceId !== command.sourceId)
      : [...snapshot.sourceIds, command.sourceId],
    revision: snapshot.revision + 1,
  };
}

/**
 * Captures only a user's lookup intent and source scope. Retrieval engines,
 * vector stores, search providers, LLMs, MCP clients, and storage stay outside
 * this pure prototype model.
 */
export function reduceKnowledgeLookupHistory(
  history: KnowledgeLookupHistory,
  action: KnowledgeLookupHistoryAction,
  allowedSourceIds: readonly string[],
): KnowledgeLookupHistory {
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

  const next = applyKnowledgeLookupCommand(
    history.present,
    action.command,
    new Set(allowedSourceIds),
  );
  if (next === history.present) return history;
  return {
    past: [...history.past, history.present],
    present: next,
    future: [],
  };
}
