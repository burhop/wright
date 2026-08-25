import { useEffect, useState } from "react";

import type {
  KnowledgeLookupHistory,
  KnowledgeLookupHistoryAction,
} from "./domain/knowledge-lookup-draft";
import type { KnowledgeLookupSourceOption } from "./fixtures/knowledge-lookup-sources";

import "./knowledge-lookup-editor.css";

export function KnowledgeLookupEditor({
  history,
  dispatch,
  sources,
}: {
  history: KnowledgeLookupHistory;
  dispatch: (action: KnowledgeLookupHistoryAction) => void;
  sources: readonly KnowledgeLookupSourceOption[];
}) {
  const [queryDraft, setQueryDraft] = useState(history.present.query);

  useEffect(() => {
    setQueryDraft(history.present.query);
  }, [history.present.query]);

  const queryChanged = queryDraft !== history.present.query;
  const queryPresent = history.present.query.trim().length > 0;
  const selectedSourceCount = history.present.sourceIds.length;
  const lookupConfigured = queryPresent && selectedSourceCount > 0;

  return (
    <section
      className="ewp-knowledge-lookup"
      aria-labelledby="ewp-knowledge-lookup-title"
    >
      <header className="ewp-knowledge-lookup__header">
        <span>
          <h2 id="ewp-knowledge-lookup-title">Knowledge lookup</h2>
          <small>Query + source scope · session only</small>
        </span>
        <strong>
          {selectedSourceCount} source{selectedSourceCount === 1 ? "" : "s"}
        </strong>
      </header>

      <div className="ewp-knowledge-lookup__history">
        <button
          type="button"
          disabled={history.past.length === 0}
          onClick={() => dispatch({ type: "undo" })}
        >
          Undo
        </button>
        <button
          type="button"
          disabled={history.future.length === 0}
          onClick={() => dispatch({ type: "redo" })}
        >
          Redo
        </button>
        <output aria-live="polite">
          Draft revision {history.present.revision}
        </output>
      </div>

      <label className="ewp-knowledge-lookup__query">
        <span>What information should Wright find?</span>
        <textarea
          aria-label="Knowledge lookup prompt"
          value={queryDraft}
          rows={5}
          placeholder="For example: Find applicable company standards, preferred component sizes, prior designs, or other information needed for this work."
          onChange={(event) => setQueryDraft(event.currentTarget.value)}
        />
      </label>
      <div className="ewp-knowledge-lookup__query-actions">
        <button
          type="button"
          disabled={!queryChanged}
          onClick={() =>
            dispatch({
              type: "apply",
              command: { type: "replace-query", query: queryDraft },
            })
          }
        >
          Apply lookup prompt
        </button>
        <small>
          {queryDraft.length} characters
          {queryChanged ? " · changes not applied" : " · applied"}
        </small>
      </div>

      <fieldset className="ewp-knowledge-lookup__sources">
        <legend>Search within</legend>
        {sources.map((source) => (
          <label key={source.sourceId}>
            <input
              type="checkbox"
              checked={history.present.sourceIds.includes(source.sourceId)}
              onChange={() =>
                dispatch({
                  type: "apply",
                  command: {
                    type: "toggle-source",
                    sourceId: source.sourceId,
                  },
                })
              }
            />
            <span>
              <strong>{source.label}</strong>
              <small>{source.description}</small>
            </span>
          </label>
        ))}
      </fieldset>

      <p
        className="ewp-knowledge-lookup__status"
        data-ready={lookupConfigured}
        aria-live="polite"
      >
        {lookupConfigured
          ? "Lookup draft configured. Retrieval has not run."
          : queryPresent
            ? "Choose at least one source scope."
            : selectedSourceCount > 0
              ? "Add and apply a lookup prompt."
              : "Add a lookup prompt and choose where Wright may search."}
      </p>

      <section className="ewp-knowledge-lookup__output">
        <h3>Retrieved context</h3>
        <p>
          No lookup has run. A later retrieval checkpoint should return
          reviewable passages, source citations, and retrieval evidence here.
        </p>
      </section>
      <p className="ewp-knowledge-lookup__boundary">
        Retrieval execution, provider selection, permissions, citations, and
        persistence come later. Source labels never select runtime code.
      </p>
    </section>
  );
}

export default KnowledgeLookupEditor;
