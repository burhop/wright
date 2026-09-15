import { useEffect, useState } from "react";
import {
  workspaceService,
  type WorkspaceWorkflowRunSummary,
} from "../../services/workspace-service";
import { EngineeringResults } from "./EngineeringResults";

export function WorkflowRunHistory({
  sessionId,
  path,
  refreshKey,
  onOpenFile,
}: {
  sessionId?: string;
  path: string;
  refreshKey: string;
  onOpenFile?: (path: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [retry, setRetry] = useState(0);
  const [runs, setRuns] = useState<WorkspaceWorkflowRunSummary[]>([]);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  useEffect(() => {
    if (!open || !sessionId) return;
    let current = true;
    setPending(true);
    setError("");
    setRuns([]);
    workspaceService
      .getWorkspaceWorkflowRuns(sessionId, path)
      .then((value) => {
        if (current) setRuns(value);
      })
      .catch((error) => {
        if (current)
          setError(
            error instanceof Error
              ? error.message
              : "Run history could not be loaded.",
          );
      })
      .finally(() => {
        if (current) setPending(false);
      });
    return () => {
      current = false;
    };
  }, [open, sessionId, path, refreshKey, retry]);
  if (!sessionId) return null;
  const labels = {
    running: "Running",
    completed: "Completed",
    pending_review: "Awaiting your review",
    awaiting_approval: "Awaiting external action approval",
    awaiting_external_outcome: "Awaiting external action outcome",
    external_action_not_dispatched: "External action was not dispatched",
    external_action_outcome_unknown: "External action outcome unknown",
    changes_requested: "Changes requested",
    failed: "Failed",
    cancelled: "Cancelled",
    interrupted: "Interrupted",
    unknown: "Status needs checking",
  };
  return (
    <details
      className="recovery-technical-details"
      data-testid="workflow-run-history"
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary>Previous runs</summary>
      {open && (
        <>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            disabled={pending}
            onClick={() => setRetry((n) => n + 1)}
          >
            Refresh run history
          </button>
          {pending && <p role="status">Loading previous runs…</p>}
          {error && <p role="alert">{error}</p>}
          {!pending && !error && !runs.length && (
            <p>No saved runs for this workflow.</p>
          )}
          {runs.map((run) => (
            <details
              key={run.path}
              open={run.status === "interrupted" || run.status === "unknown"}
            >
              <summary>
                {labels[run.status] ?? "Status needs checking"} ·{" "}
                {new Date(run.started_at).toLocaleString()}
              </summary>
              {(run.status === "interrupted" || run.status === "unknown") && (
                <p>
                  The execution host did not record completion. A submitted
                  application operation may still be running. Check its status
                  and the saved log before retrying; nothing has been restarted.
                </p>
              )}
              {run.error && <p>{run.error}</p>}
              {run.last_event?.task_title && (
                <p>
                  Last recorded step: {run.last_event.task_title}
                  {run.last_event.message ? ` · ${run.last_event.message}` : ""}
                </p>
              )}
              {run.results.length > 0 && (
                <EngineeringResults
                  results={run.results}
                  onOpenFile={onOpenFile}
                />
              )}
              {onOpenFile && (
                <button
                  type="button"
                  className="recovery-button recovery-button--secondary"
                  onClick={() => onOpenFile(run.path)}
                >
                  Open saved run log
                </button>
              )}
            </details>
          ))}
        </>
      )}
    </details>
  );
}
