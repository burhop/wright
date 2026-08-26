import type {
  DiagnosticLlmModelGroup,
  DiagnosticLlmModelOption,
  DiagnosticThinkingLevel,
} from "./services/diagnostic-llm-adapter";

export const diagnosticThinkingLevels: readonly {
  value: DiagnosticThinkingLevel;
  label: string;
}[] = [
  { value: "default", label: "Provider default" },
  { value: "none", label: "None" },
  { value: "minimal", label: "Minimal" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "xhigh", label: "Extra high" },
];

export function DiagnosticLlmPanel({
  groups,
  loading,
  loadError,
  selectedModel,
  thinkingLevel,
  running,
  resultText,
  executionError,
  onSelectModel,
  onSelectThinkingLevel,
}: {
  groups: readonly DiagnosticLlmModelGroup[];
  loading: boolean;
  loadError: string | null;
  selectedModel: DiagnosticLlmModelOption | null;
  thinkingLevel: DiagnosticThinkingLevel;
  running: boolean;
  resultText: string | null;
  executionError: string | null;
  onSelectModel: (model: DiagnosticLlmModelOption) => void;
  onSelectThinkingLevel: (level: DiagnosticThinkingLevel) => void;
}) {
  const models = groups.flatMap((group) => group.options);
  return (
    <section className="ewp-llm" aria-labelledby="ewp-llm-title">
      <header>
        <span>
          <h2 id="ewp-llm-title">AI execution</h2>
          <small>Live through Wright · workspace MCP activation disabled</small>
        </span>
        <strong
          data-state={running ? "running" : resultText ? "ready" : "idle"}
        >
          {running ? "Running" : resultText ? "Output ready" : "Not run"}
        </strong>
      </header>

      <p>
        Wright uses its current configured model automatically. Open the
        override only when this workflow needs a deliberate model or reasoning
        change.
      </p>
      <details className="ewp-llm__override">
        <summary>
          Model override ·{" "}
          {selectedModel?.label ??
            (loading ? "loading current model" : "unavailable")}
        </summary>
        <label>
          <span>Configured model</span>
          <select
            aria-label="Workflow AI model"
            disabled={loading || models.length === 0 || running}
            value={selectedModel?.value ?? ""}
            onChange={(event) => {
              const model = models.find(
                ({ value }) => value === event.currentTarget.value,
              );
              if (model) onSelectModel(model);
            }}
          >
            {models.length === 0 ? (
              <option value="">
                {loading
                  ? "Loading Wright's current model…"
                  : "No models available"}
              </option>
            ) : null}
            {groups.map((group) => (
              <optgroup key={group.provider} label={group.label}>
                {group.options.map((model) => (
                  <option key={model.value} value={model.value}>
                    {model.label}
                    {model.isCurrent ? " · current" : ""}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>

        <label>
          <span>Thinking level</span>
          <select
            aria-label="Workflow AI thinking level"
            disabled={running}
            value={thinkingLevel}
            onChange={(event) =>
              onSelectThinkingLevel(
                event.currentTarget.value as DiagnosticThinkingLevel,
              )
            }
          >
            {diagnosticThinkingLevels.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small>
            Support varies by model. Unsupported levels are reported by the
            provider; Wright does not silently substitute another level.
          </small>
        </label>
      </details>

      {loadError ? <p role="alert">{loadError}</p> : null}
      {executionError ? <p role="alert">{executionError}</p> : null}
      {resultText ? (
        <section className="ewp-llm__output" aria-label="AI block output">
          <h3>Produced text</h3>
          <pre>{resultText}</pre>
        </section>
      ) : (
        <p className="ewp-llm__boundary">
          Wright will not activate workspace MCP tools for this AI block. Hermes
          runtime toolsets are not yet a hard per-request sandbox; an observed
          tool event stops the prototype and is reported. MCP argument creation
          waits for the next explicitly bound block.
        </p>
      )}
    </section>
  );
}

export default DiagnosticLlmPanel;
