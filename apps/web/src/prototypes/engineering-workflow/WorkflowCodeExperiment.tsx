import type { WorkflowCodeParseResult } from "./domain/workflow-code-experiment";

export function WorkflowCodeExperiment({
  source,
  result,
  applied,
  onChange,
  onApply,
  onFormat,
  onReset,
}: {
  source: string;
  result: WorkflowCodeParseResult;
  applied: boolean;
  onChange: (source: string) => void;
  onApply: () => void;
  onFormat: () => void;
  onReset: () => void;
}) {
  return (
    <section
      className="ewp-workflow-code"
      aria-labelledby="ewp-workflow-code-title"
    >
      <header>
        <span>
          <small>Discovery experiment · provisional JSON</small>
          <h2 id="ewp-workflow-code-title">Workflow code</h2>
        </span>
        <strong
          data-state={result.ok ? (applied ? "applied" : "valid") : "invalid"}
        >
          {result.ok
            ? applied
              ? "Applied to diagram"
              : "Valid · not applied"
            : `${result.errors.length} validation ${result.errors.length === 1 ? "issue" : "issues"}`}
        </strong>
      </header>
      <p>
        Each phase, block, typed output, and connection maps to the diagram.
        Layout remains a replaceable projection in this experiment rather than
        engineer-authored code.
      </p>
      <div className="ewp-workflow-code__instructions">
        Try changing the workflow title, a block title, or a connection label.
        Then apply the valid document and return to Diagram.
      </div>
      <label>
        <span className="ewp-sr-only">Workflow source code</span>
        <textarea
          aria-label="Workflow source code"
          value={source}
          onChange={(event) => onChange(event.currentTarget.value)}
          spellCheck={false}
        />
      </label>
      {!result.ok ? (
        <section className="ewp-workflow-code__errors" role="alert">
          <h3>Document was not applied</h3>
          <p>The diagram still uses the last valid document.</p>
          <ol>
            {result.errors.map((error, index) => (
              <li key={`${error.path}-${error.code}-${index}`}>
                <code>{error.path}</code>
                <span>
                  <strong>{error.code}</strong> · {error.message}
                </span>
              </li>
            ))}
          </ol>
        </section>
      ) : (
        <dl className="ewp-workflow-code__summary">
          <div>
            <dt>Phases</dt>
            <dd>{result.document.phases.length}</dd>
          </div>
          <div>
            <dt>Blocks</dt>
            <dd>{result.document.blocks.length}</dd>
          </div>
          <div>
            <dt>Connections</dt>
            <dd>{result.document.connections.length}</dd>
          </div>
          <div>
            <dt>Revision</dt>
            <dd>{result.document.revision}</dd>
          </div>
        </dl>
      )}
      <footer>
        <button
          type="button"
          onClick={onApply}
          disabled={!result.ok || applied}
        >
          Apply to diagram
        </button>
        <button type="button" onClick={onFormat} disabled={!result.ok}>
          Format JSON
        </button>
        <button type="button" onClick={onReset}>
          Reset fixture
        </button>
      </footer>
    </section>
  );
}

export default WorkflowCodeExperiment;
