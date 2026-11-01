import { useEffect, useState } from "react";
import {
  workspaceService,
  type RivetRunInspection,
  type WorkspaceWorkflowRunSummary,
} from "../../services/workspace-service";
import { approvalPresentation } from "./engineering-run-presentation";
import { WorkflowTracePage } from "../../components/workflow-trace/WorkflowTracePage";

function CanonicalWorkflowTrace({
  sessionId,
  runPath,
  onOpenFile,
}: {
  sessionId: string;
  runPath: string;
  onOpenFile?: (path: string) => void;
}) {
  const [inspection, setInspection] = useState<RivetRunInspection | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true;
    setError("");
    workspaceService
      .getWorkspaceWorkflowRunTrace(sessionId, runPath)
      .then((value) => {
        if (current) setInspection(value);
      })
      .catch((reason) => {
        if (current)
          setError(
            reason instanceof Error
              ? reason.message
              : "This saved run review could not be loaded.",
          );
      });
    return () => {
      current = false;
    };
  }, [runPath, sessionId]);
  return (
    <WorkflowTracePage
      inspection={inspection}
      recentRuns={inspection ? [inspection.run] : []}
      currentRevision={inspection?.run.revision ?? null}
      elapsedMs={inspection?.run.duration_ms || 0}
      error={error || null}
      onSelectRun={() => undefined}
      onExportTrace={(mode) =>
        void workspaceService.exportWorkspaceWorkflowRunTrace(
          sessionId,
          runPath,
          mode,
        )
      }
      onOpenArtifact={(artifact) => {
        const path = artifact.workspace_path;
        if (onOpenFile && typeof path === "string") onOpenFile(path);
      }}
    />
  );
}

function traceAnchor(value: string) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `workflow-trace-${(hash >>> 0).toString(16)}`;
}

export function WorkflowRunHistory({
  sessionId,
  path,
  refreshKey,
  onOpenFile,
  currentSourceDigest,
  onOpenRunWorkingView,
}: {
  sessionId?: string;
  path: string;
  refreshKey: string;
  onOpenFile?: (path: string) => void;
  currentSourceDigest?: string;
  onOpenRunWorkingView?: (runId: string, sourceDigest: string) => void;
}) {
  const [open, setOpen] = useState(() =>
    window.location.hash.startsWith("#workflow-trace-"),
  );
  const [retry, setRetry] = useState(0);
  const [runs, setRuns] = useState<WorkspaceWorkflowRunSummary[]>([]);
  const [expandedRuns, setExpandedRuns] = useState<Set<string>>(new Set());
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
        if (current) {
          setRuns(value);
          setExpandedRuns(
            new Set(
              value
                .filter(
                  (run) =>
                    run.status === "interrupted" ||
                    run.status === "unknown" ||
                    window.location.hash === `#${traceAnchor(run.path)}`,
                )
                .map((run) => run.path),
            ),
          );
        }
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
    waiting_human: "Waiting for your input",
    awaiting_approval: "Awaiting external action approval",
    awaiting_external_outcome: "Awaiting external action outcome",
    external_action_not_dispatched: "External action was not dispatched",
    external_action_outcome_unknown: "External action outcome unknown",
    changes_requested: "Changes requested",
    failed: "Failed",
    cancelled: "Cancelled",
    interrupted: "Interrupted",
    reconciliation_required: "Operation status unconfirmed",
    unknown: "Status needs checking",
  };
  return (
    <details
      className="recovery-technical-details"
      data-testid="workflow-run-history"
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary>Trace: previous runs</summary>
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
              id={traceAnchor(run.path)}
              open={expandedRuns.has(run.path)}
              onToggle={(event) => {
                const expanded = event.currentTarget.open;
                setExpandedRuns((current) => {
                  const next = new Set(current);
                  if (expanded) next.add(run.path);
                  else next.delete(run.path);
                  return next;
                });
              }}
            >
              <summary>
                {(run.status === "awaiting_approval" ||
                run.status === "changes_requested"
                  ? approvalPresentation(run.approval)?.label
                  : null) ??
                  labels[run.status] ??
                  "Status needs checking"}{" "}
                · {new Date(run.started_at).toLocaleString()}
              </summary>
              {(run.status === "interrupted" ||
                run.status === "unknown" ||
                run.status === "reconciliation_required") && (
                <p>
                  The execution host did not record completion. A submitted
                  application operation may still be running. Check its status
                  and the saved log before retrying; nothing has been restarted.
                </p>
              )}
              {run.error && <p>{run.error}</p>}
              <a href={`#${traceAnchor(run.path)}`}>
                Link to this Trace review
              </a>
              {run.last_event?.task_title && (
                <p>
                  Last recorded step: {run.last_event.task_title}
                  {run.last_event.message ? ` · ${run.last_event.message}` : ""}
                </p>
              )}
              {expandedRuns.has(run.path) && (
                <CanonicalWorkflowTrace
                  sessionId={sessionId}
                  runPath={run.path}
                  onOpenFile={onOpenFile}
                />
              )}
              {onOpenRunWorkingView &&
                run.run_id &&
                run.source_digest === currentSourceDigest &&
                run.source_matches_current !== false && (
                  <button
                    type="button"
                    className="recovery-button recovery-button--secondary"
                    onClick={() =>
                      onOpenRunWorkingView(run.run_id!, run.source_digest)
                    }
                  >
                    Open run in working view
                  </button>
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
              <details>
                <summary>Recorded execution details</summary>
                <p>
                  This historical record shows only data captured by its
                  execution. Missing graph, prompt, or iteration detail is not
                  reconstructed from the current workflow.
                </p>
                {onOpenFile && (
                  <button
                    type="button"
                    className="recovery-button recovery-button--secondary"
                    onClick={() => onOpenFile(run.path)}
                  >
                    Inspect complete saved record
                  </button>
                )}
              </details>
            </details>
          ))}
        </>
      )}
    </details>
  );
}
