import { useState } from "react";

import type {
  WorkflowOutputAction,
  WorkflowOutputReference,
} from "./domain/workflow-output";

const outputIcons: Record<WorkflowOutputReference["kind"], string> = {
  document: "▤",
  model: "⬡",
  file: "▣",
  dataset: "▦",
  link: "↗",
  message: "✦",
  other: "◆",
};

function outputKindLabel(kind: WorkflowOutputReference["kind"]): string {
  if (kind === "model") return "Model";
  if (kind === "dataset") return "Dataset";
  if (kind === "document") return "Document";
  if (kind === "file") return "File";
  if (kind === "link") return "Link";
  if (kind === "message") return "Message";
  return "Output";
}

export function DiagnosticWorkflowOutputs({
  outputs,
  compact = false,
  onAction,
}: {
  outputs: readonly WorkflowOutputReference[];
  compact?: boolean;
  onAction: (
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ) => Promise<string | void>;
}) {
  const [runningAction, setRunningAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  if (!outputs.length) return null;

  return (
    <section
      className="ewp-workflow-outputs"
      data-compact={compact ? "true" : undefined}
      aria-label="Workflow outputs"
    >
      <header>
        <span>
          <small>Run complete</small>
          <h3>
            {outputs.length} output{outputs.length === 1 ? "" : "s"} ready
          </h3>
        </span>
        <strong>Available now</strong>
      </header>
      <ul>
        {outputs.map((output) => (
          <li key={output.outputId}>
            <span className="ewp-workflow-output__icon" aria-hidden="true">
              {outputIcons[output.kind]}
            </span>
            <div className="ewp-workflow-output__body">
              <small>
                {outputKindLabel(output.kind)}
                {output.format ? ` · ${output.format}` : ""}
              </small>
              <strong>{output.title}</strong>
              <p>{output.description}</p>
              <span className="ewp-workflow-output__lifetime">
                {output.durability === "session"
                  ? "Available during this session"
                  : output.durability === "durable"
                    ? "Saved output"
                    : "Temporary output"}
              </span>
              <div className="ewp-workflow-output__actions">
                {output.actions.map((action) => {
                  const actionKey = `${output.outputId}:${action.actionId}`;
                  return (
                    <button
                      key={action.actionId}
                      type="button"
                      disabled={!action.available || runningAction !== null}
                      title={
                        action.available ? undefined : action.unavailableReason
                      }
                      onClick={() => {
                        setRunningAction(actionKey);
                        setMessage(null);
                        void onAction(output, action)
                          .then((resultMessage) =>
                            setMessage(
                              resultMessage ?? `${action.label} opened.`,
                            ),
                          )
                          .catch((error: unknown) =>
                            setMessage(
                              error instanceof Error
                                ? error.message
                                : "The output action failed.",
                            ),
                          )
                          .finally(() => setRunningAction(null));
                      }}
                    >
                      {runningAction === actionKey ? "Opening…" : action.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </li>
        ))}
      </ul>
      {message ? <p role="status">{message}</p> : null}
    </section>
  );
}

export default DiagnosticWorkflowOutputs;
