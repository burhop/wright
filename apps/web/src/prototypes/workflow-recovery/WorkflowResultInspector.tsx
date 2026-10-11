import { useState } from "react";
import { ReviewImage } from "./EngineeringReviewFiles";
import { fileKind, fileName } from "./engineering-run-presentation";
import {
  resultAvailability,
  type WorkflowResultBlock,
} from "./workflow-result-blocks";

function unavailableMessage(
  run: NonNullable<WorkflowResultBlock["unavailableRun"]>,
): string {
  switch (run.status) {
    case "failed":
      return run.failedStepTitle
        ? `The workflow failed at “${run.failedStepTitle}”. This run did not produce this output.`
        : "The workflow failed. This run did not produce this output.";
    case "cancelled":
      return "The workflow was cancelled. This output has not been recorded.";
    case "running":
      return "The workflow is running. This output has not been produced yet.";
    case "interrupted":
    case "unknown":
      return "Wright cannot confirm execution has finished. This output has not been recorded. Check the saved run before retrying.";
    case "completed":
      return "The run finished, but this expected output was not recorded. Inspect the producing step and saved run.";
    case "external_action_not_dispatched":
      return "The external action was not dispatched. This output has not been recorded.";
    case "external_action_outcome_unknown":
      return "The external action's outcome is unknown. This output has not been recorded. Inspect the saved run before retrying.";
    case "awaiting_external_outcome":
      return "The workflow is waiting for an external outcome. This output has not been produced yet.";
    case "changes_requested":
      return "Changes were requested. Inspect the saved run for the requested changes. This output has not been produced yet.";
    default:
      return "The workflow is waiting for review. This output has not been produced yet.";
  }
}

export function WorkflowResultsNavigator({
  results,
  onSelect,
}: {
  results: WorkflowResultBlock[];
  onSelect: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const available = results.filter((result) =>
    result.files.some((file) => file.available),
  ).length;
  return (
    <div className="recovery-results-navigation">
      <button
        type="button"
        data-testid="workflow-results-toggle"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="recovery-results-toggle"
      >
        ↗ Results · {available}/{results.length} available{" "}
        <span aria-hidden="true">⌄</span>
      </button>
      {open && (
        <section
          className="recovery-results-menu"
          aria-label="Workflow results"
        >
          <p>
            Results are files produced by the steps. Open a result to inspect
            its files; this does not run or approve anything.
          </p>
          {!results.length && (
            <p>No saved files or expected output files are recorded yet.</p>
          )}
          {results.map((result) => (
            <button
              key={result.id}
              type="button"
              onClick={() => {
                onSelect(result.id);
                setOpen(false);
              }}
            >
              <b>{result.title}</b>
              <span>{result.producerTitle}</span>
              <small>
                {resultAvailability(result)}
                {result.reviewLabel && ` · ${result.reviewLabel}`}
              </small>
            </button>
          ))}
        </section>
      )}
    </div>
  );
}

export function WorkflowResultInspector({
  result,
  sessionId,
  onOpenFile,
  onSelectProducer,
  onShowRunDetails,
}: {
  result: WorkflowResultBlock;
  sessionId?: string;
  onOpenFile?: (path: string) => void;
  onSelectProducer: (id: string) => void;
  onShowRunDetails?: () => void;
}) {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const available = result.files.filter((file) => file.available);
  const selected =
    available.find((file) => file.path === selectedPath) ?? available[0];
  const unavailableRun = !available.length ? result.unavailableRun : undefined;
  return (
    <section
      data-testid="workflow-result-inspector"
      className="recovery-result-inspector"
    >
      <p className="recovery-result-status">{resultAvailability(result)}</p>
      {result.sourceMismatch && (
        <p role="status">
          These files belong to the saved run, not the current edited workflow.
          They do not verify your changes.
        </p>
      )}
      {available.length > 0 && (
        <p>
          {result.reviewLabel ||
            "Availability does not mean the engineering result has been checked or approved."}
        </p>
      )}
      {unavailableRun && (
        <section
          className="recovery-result-unavailable"
          data-testid="workflow-result-unavailable"
          role="status"
        >
          <h3>Why this output is unavailable</h3>
          <p>{unavailableMessage(unavailableRun)}</p>
          {unavailableRun.diagnostic && (
            <p data-testid="workflow-result-diagnostic">
              Step reported: {unavailableRun.diagnostic}
            </p>
          )}
          {unavailableRun.failedStepId && (
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid="workflow-result-failed-step"
              onClick={() => onSelectProducer(unavailableRun.failedStepId!)}
            >
              Inspect failed step
            </button>
          )}
          {onShowRunDetails && (
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid="workflow-result-run-details"
              onClick={onShowRunDetails}
            >
              View run details
            </button>
          )}
          {unavailableRun.error && (
            <details className="recovery-result-location">
              <summary>Technical details</summary>
              <p className="recovery-result-path">{unavailableRun.error}</p>
            </details>
          )}
        </section>
      )}
      {!available.length && !unavailableRun && (
        <p>
          No output files from this step have been recorded for the current
          workflow. Inspect the producing step and run status to see what is
          still needed.
        </p>
      )}
      {selected && (
        <section
          className="recovery-result-preview"
          aria-label="Selected result file"
        >
          <h3 title={selected.path}>{fileName(selected.path)}</h3>
          {onOpenFile && (
            <button
              type="button"
              className="recovery-button recovery-button--primary"
              data-testid="workflow-result-open"
              title={selected.path}
              onClick={() => onOpenFile(selected.path)}
            >
              Open{" "}
              {fileKind(selected.path) === "Plot or image"
                ? "plot or image"
                : fileKind(selected.path) === "Document"
                  ? "document"
                  : "file"}{" "}
              in tab ↗
            </button>
          )}
          {fileKind(selected.path) === "Plot or image" &&
            selected.sha256 &&
            sessionId && (
              <ReviewImage
                key={`${selected.path}:${selected.sha256}`}
                path={selected.path}
                sha256={selected.sha256}
                sessionId={sessionId}
              />
            )}
          <details className="recovery-result-location">
            <summary>File location</summary>
            <p className="recovery-result-path">{selected.path}</p>
            <p>
              The tab opens the current workspace file. Image previews are
              checked against the recorded file version.
            </p>
          </details>
          {!onOpenFile && (
            <p>
              File viewing is unavailable in this editor. Open the workflow from
              its workspace to view files.
            </p>
          )}
        </section>
      )}
      <h3>Files in this result</h3>
      <ul className="recovery-result-file-list">
        {result.files.map((file) => (
          <li key={file.path}>
            <button
              type="button"
              disabled={!file.available}
              title={file.path}
              aria-pressed={selected?.path === file.path}
              onClick={() => setSelectedPath(file.path)}
            >
              <b>{fileName(file.path)}</b>
              <small>
                {fileKind(file.path)} ·{" "}
                {file.available ? "Available" : "Not produced yet"}
              </small>
            </button>
          </li>
        ))}
      </ul>
      <details className="recovery-result-origin" open={!available.length}>
        <summary>How this result is produced</summary>
        <p>
          The line to this result means “produces these files.” This result is
          not another processing step.
        </p>
        <h3>Produced by</h3>
        {result.producerId ? (
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            onClick={() => onSelectProducer(result.producerId!)}
          >
            {result.producerTitle}
          </button>
        ) : (
          <p>{result.producerTitle}</p>
        )}
      </details>
    </section>
  );
}
