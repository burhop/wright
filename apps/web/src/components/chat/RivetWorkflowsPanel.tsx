import { useCallback, useEffect, useState } from "react";

import {
  workspaceService,
  type RivetWorkflowOperation,
  type RivetWorkflowRun,
} from "../../services/workspace-service";
import {
  declareLiveApp,
  operateLiveApp,
  type LiveAppOperation,
} from "../../services/surfaces/surface-client";

export function RivetWorkflowsPanel({
  sessionId,
  workspaceId,
  onOpenEditor,
  onCreateWorkflow,
}: {
  sessionId: string | null;
  workspaceId: string | null;
  onOpenEditor?: (slug?: string) => void | Promise<void>;
  onCreateWorkflow?: () => void | Promise<void>;
}) {
  const [workflows, setWorkflows] = useState<RivetWorkflowOperation[]>([]);
  const [runs, setRuns] = useState<Record<string, RivetWorkflowRun>>({});
  const [history, setHistory] = useState<Record<string, string>>({});
  const [message, setMessage] = useState(
    "Workflows remain inside this workspace.",
  );

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    try {
      setWorkflows(
        await workspaceService.listRivetWorkflowOperations(sessionId),
      );
      setMessage("Workflow catalog is up to date.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Rivet workflows are unavailable.",
      );
    }
  }, [sessionId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const approve = async (workflow: RivetWorkflowOperation) => {
    if (!sessionId) return;
    await workspaceService.reviewRivetWorkflow(
      sessionId,
      workflow.slug,
      "approved",
      "local-user",
    );
    await refresh();
  };
  const run = async (workflow: RivetWorkflowOperation) => {
    if (!sessionId) return;
    try {
      const result = await workspaceService.runRivetWorkflow(
        sessionId,
        workflow.slug,
        {
          expectedRevision: workflow.revision,
          expectedDigest: workflow.etag,
        },
      );
      setRuns((current) => ({ ...current, [workflow.workflow_id]: result }));
      setMessage(`Run ${result.run_id} is ${result.state}.`);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Workflow could not start.",
      );
    }
  };
  const showHistory = async (workflowId: string) => {
    if (!sessionId || !runs[workflowId]) return;
    try {
      const events = await workspaceService.getRivetWorkflowHistory(
        sessionId,
        runs[workflowId].run_id,
      );
      setHistory((current) => ({
        ...current,
        [workflowId]:
          events.map((event) => event.kind).join(" → ") || "No events yet",
      }));
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Workflow history is unavailable.",
      );
    }
  };
  const cancel = async (workflowId: string) => {
    if (!sessionId || !runs[workflowId]) return;
    try {
      const result = await workspaceService.cancelRivetWorkflow(
        sessionId,
        runs[workflowId],
      );
      setRuns((current) => ({ ...current, [workflowId]: result }));
      setMessage(`Run ${result.run_id} is ${result.state}.`);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Workflow cancellation failed.",
      );
    }
  };
  const openEditor = async () => {
    if (!sessionId || !workspaceId) return;
    try {
      if (onOpenEditor) {
        await onOpenEditor();
        setMessage("Rivet editor opened in the workspace.");
        return;
      }
      const surface = await workspaceService.getRivetEditorSurface(sessionId);
      if (!surface.manifest)
        throw new Error(surface.detail || "Rivet editor is unavailable.");
      const descriptor = await declareLiveApp(
        surface.manifest,
        workspaceId,
        sessionId,
      );
      const operation: LiveAppOperation | null =
        descriptor.lifecycle === "declared"
          ? "start"
          : descriptor.lifecycle === "stopped"
            ? "restart"
            : descriptor.lifecycle === "failed"
              ? "retry"
              : null;
      if (operation) {
        await operateLiveApp(
          descriptor.surfaceId,
          descriptor.workspaceId,
          sessionId,
          operation,
        );
      }
      window.dispatchEvent(new Event("wright-surfaces-changed"));
      setMessage("Rivet editor opened as an isolated workspace tab.");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Rivet editor is unavailable.",
      );
    }
  };
  const createWorkflow = async () => {
    if (!sessionId || !workspaceId || !onCreateWorkflow) return;
    try {
      await onCreateWorkflow();
      await refresh();
      setMessage("Blank Rivet workflow created in the workspace.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to create Rivet workflow.",
      );
    }
  };

  return (
    <section
      data-testid="rivet-workflows-tab"
      style={{ padding: "var(--space-md)" }}
    >
      <h2 style={{ fontSize: "0.8rem", marginTop: 0 }}>Rivet Workflows</h2>
      <p
        style={{
          color: "var(--color-secondary)",
          fontSize: "0.75rem",
          lineHeight: 1.5,
        }}
      >
        {message}
      </p>
      <button
        data-testid="rivet-workflows-refresh"
        type="button"
        onClick={() => void refresh()}
      >
        Refresh
      </button>
      <button
        data-testid="rivet-editor-open"
        type="button"
        disabled={!sessionId || !workspaceId}
        onClick={() => void openEditor()}
      >
        Open Rivet editor
      </button>
      <button
        data-testid="rivet-workflow-new"
        type="button"
        disabled={!sessionId || !workspaceId || !onCreateWorkflow}
        onClick={() => void createWorkflow()}
      >
        New blank workflow
      </button>
      {workflows.map((workflow) => (
        <div
          key={workflow.workflow_id}
          style={{
            borderTop: "1px solid var(--color-border)",
            marginTop: "var(--space-sm)",
            paddingTop: "var(--space-sm)",
          }}
        >
          <strong>{workflow.slug}</strong>
          <br />
          <small>
            Revision {workflow.revision} ·{" "}
            {workflow.review_state || "needs review"}
          </small>
          <br />
          <button
            data-testid={`rivet-workflow-open-${workflow.slug}`}
            type="button"
            onClick={() => void onOpenEditor?.(workflow.slug)}
          >
            Open
          </button>{" "}
          <button
            data-testid={`rivet-workflow-approve-${workflow.slug}`}
            type="button"
            onClick={() => void approve(workflow)}
          >
            Approve revision
          </button>{" "}
          <button
            data-testid={`rivet-workflow-run-${workflow.slug}`}
            type="button"
            disabled={workflow.review_state !== "approved"}
            onClick={() => void run(workflow)}
          >
            Run
          </button>
          {runs[workflow.workflow_id] && (
            <>
              <small> {runs[workflow.workflow_id].state}</small>{" "}
              <button
                data-testid={`rivet-workflow-history-${workflow.slug}`}
                type="button"
                onClick={() => void showHistory(workflow.workflow_id)}
              >
                History
              </button>{" "}
              <button
                data-testid={`rivet-workflow-cancel-${workflow.slug}`}
                type="button"
                onClick={() => void cancel(workflow.workflow_id)}
              >
                Cancel
              </button>
              {history[workflow.workflow_id] && (
                <small> {history[workflow.workflow_id]}</small>
              )}
            </>
          )}
        </div>
      ))}
      <p
        style={{
          color: "var(--color-secondary)",
          fontSize: "0.72rem",
          lineHeight: 1.5,
        }}
      >
        Manual import/export mode: use the browser file picker to open or export
        projects. This does not save into the Wright workspace.
      </p>
    </section>
  );
}
