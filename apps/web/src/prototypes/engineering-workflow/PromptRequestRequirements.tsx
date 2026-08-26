import {
  diagnosticRequestIssues,
  type DiagnosticPromptRequestDefinition,
  type DiagnosticPromptRequestSnapshot,
} from "./domain/diagnostic-demo";
import {
  promptRequestOutputLabels,
  promptRequestRouteIssues,
  type PromptRequestOutputKind,
} from "./domain/prompt-request-routing";

export function PromptRequestRequirements({
  definition,
  value,
  readableDocumentCount,
  output,
  acceptedOutputs,
  onSelectOutput,
}: {
  definition: DiagnosticPromptRequestDefinition;
  value: DiagnosticPromptRequestSnapshot;
  readableDocumentCount: number;
  output: PromptRequestOutputKind;
  acceptedOutputs: readonly PromptRequestOutputKind[];
  onSelectOutput: (output: PromptRequestOutputKind) => void;
}) {
  const issues = diagnosticRequestIssues(value, definition.requirements);
  const routeIssues = promptRequestRouteIssues(
    {
      promptPresent: value.prompt.trim().length > 0,
      imageCount: value.imageCount,
      documentCount: value.documentCount,
      readableDocumentCount,
    },
    output,
    acceptedOutputs,
  );
  const errorCount =
    issues.length +
    routeIssues.filter(({ severity }) => severity === "error").length;
  const missingFields = new Set(issues.map(({ field }) => field));
  const { requirements } = definition;

  return (
    <section className="ewp-prompt-request" aria-labelledby="ewp-request-title">
      <header>
        <span>
          <h2 id="ewp-request-title">Prompt / Request</h2>
          <small>Text + images + readable files · session only</small>
        </span>
        <strong data-state={errorCount === 0 ? "ready" : "missing"}>
          {errorCount === 0
            ? "Ready"
            : `${errorCount} issue${errorCount === 1 ? "" : "s"}`}
        </strong>
      </header>
      <p>
        This generic input package can feed an AI task, an MCP request, or any
        later workflow block that accepts the same typed artifacts.
      </p>
      <ul aria-label="Prompt request requirements">
        <li data-state={missingFields.has("prompt") ? "missing" : "ready"}>
          <span>Prompt</span>
          <strong>
            {requirements.promptRequired ? "Required" : "Optional"} ·{" "}
            {value.prompt.trim() ? "present" : "missing"}
          </strong>
        </li>
        <li data-state={missingFields.has("images") ? "missing" : "ready"}>
          <span>Images</span>
          <strong>
            {requirements.minImages === 0
              ? "Optional"
              : `Minimum ${requirements.minImages}`}{" "}
            · {value.imageCount} provided
          </strong>
        </li>
        <li data-state={missingFields.has("documents") ? "missing" : "ready"}>
          <span>Readable files</span>
          <strong>
            {requirements.minDocuments === 0
              ? "Optional"
              : `Minimum ${requirements.minDocuments}`}{" "}
            · {value.documentCount} provided
          </strong>
        </li>
      </ul>
      <label className="ewp-prompt-request__route">
        <span>Output on the next connection</span>
        <select
          aria-label="Prompt request output"
          value={output}
          onChange={(event) =>
            onSelectOutput(event.currentTarget.value as PromptRequestOutputKind)
          }
        >
          {(
            Object.keys(promptRequestOutputLabels) as PromptRequestOutputKind[]
          ).map((kind) => (
            <option key={kind} value={kind}>
              {promptRequestOutputLabels[kind]}
              {kind === "request" ? " · recommended" : ""}
            </option>
          ))}
        </select>
        <small>
          One Prompt / Request block exposes a compound request plus typed text,
          image, and document connectors. The connection chooses what travels.
        </small>
      </label>
      {routeIssues.length > 0 ? (
        <ul
          className="ewp-prompt-request__route-issues"
          aria-label="Connection compatibility"
        >
          {routeIssues.map((issue) => (
            <li key={issue.code} data-state={issue.severity}>
              <strong>
                {issue.severity === "error" ? "Cannot run" : "Notice"}
              </strong>
              <span>{issue.message}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <p
        className="ewp-prompt-request__preflight"
        data-state={errorCount === 0 ? "ready" : "missing"}
        role="status"
      >
        {errorCount === 0
          ? `Preflight ready. ${promptRequestOutputLabels[output]} can be sent to the AI task.`
          : `Preflight will stop before execution: ${[...issues.map(({ message }) => message), ...routeIssues.filter(({ severity }) => severity === "error").map(({ message }) => message)].join(" ")}`}
      </p>
    </section>
  );
}

export default PromptRequestRequirements;
