import { useCallback, useEffect, useId, useRef, useState } from "react";

import WorkflowRecoveryConcept, {
  type WorkflowRunOptions,
  type WorkflowRecoveryStoredSource,
} from "../../prototypes/workflow-recovery/WorkflowRecoveryConcept";
import { EngineeringTemplateDialog } from "../../prototypes/workflow-recovery/EngineeringTemplateDialog";
import {
  initialWorkflow,
  type RecoveryLayout,
} from "../../prototypes/workflow-recovery/model";
import { formatRecoveryAuthoringSource } from "../../prototypes/workflow-recovery/recovery-authoring";
import {
  workspaceService,
  WorkspaceWorkflowSourceNotFoundError,
  type WorkspaceWorkflowSourceDocument,
  type WorkspaceWorkflowSourceReadiness,
} from "../../services/workspace-service";

const starterWorkflowSource =
  formatRecoveryAuthoringSource(initialWorkflow).text;

export interface WorkflowRecoveryPageProps {
  workspaceId: string;
  sessionId: string;
  workspaceName: string;
  workflowFilePath: string;
  reopenRequest?: number;
  onOpenWorkflow?: (path: string) => void;
  onOpenFile?: (path: string) => void;
}

export function WorkflowRecoveryPage({
  workspaceId,
  sessionId,
  workspaceName,
  workflowFilePath,
  reopenRequest = 0,
  onOpenWorkflow,
  onOpenFile,
}: WorkflowRecoveryPageProps) {
  const visiblePath = workflowFilePath.replace(/^\/+/, "");
  const dialogId = useId();
  const [document, setDocument] =
    useState<WorkspaceWorkflowSourceDocument | null>(null);
  const [templateReadiness, setTemplateReadiness] =
    useState<WorkspaceWorkflowSourceReadiness | null>(null);
  const templateReadinessRequest = useRef(0);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("");
  const [editorInstance, setEditorInstance] = useState(0);
  const [fileAction, setFileAction] = useState<"new" | "open" | null>(null);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [fileActionError, setFileActionError] = useState("");
  const [fileActionPending, setFileActionPending] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [workflowChoices, setWorkflowChoices] = useState<
    Array<{ path: string; name: string }>
  >([]);
  const fileDialog = useRef<HTMLDialogElement>(null);
  const bootstrapRequest = useRef<{
    scope: string;
    promise: Promise<WorkspaceWorkflowSourceDocument>;
  } | null>(null);

  const closeTemplateDialog = useCallback(() => {
    setTemplateDialogOpen(false);
    window.requestAnimationFrame(() => {
      const menu = window.document.querySelector<HTMLElement>(
        '[data-testid="workflow-file-menu"]',
      );
      if (menu?.offsetParent) menu.focus();
    });
  }, []);

  const requireScopedDocument = useCallback(
    (loaded: WorkspaceWorkflowSourceDocument) => {
      if (loaded.workspace_id !== workspaceId || loaded.path !== visiblePath) {
        throw new Error(
          "Wright returned a workflow file for a different workspace or path.",
        );
      }
      return loaded;
    },
    [visiblePath, workspaceId],
  );

  const bootstrapWorkflow = useCallback(async () => {
    const match =
      /^\/?workflows\/([a-z0-9][a-z0-9-]{0,62})\.workflow\.wflow$/.exec(
        workflowFilePath,
      );
    if (!match || /^(aux|con|nul|prn|com[1-9]|lpt[1-9])$/.test(match[1])) {
      throw new Error(
        "Choose a valid workspace workflow file. No file was opened or created.",
      );
    }
    try {
      return requireScopedDocument(
        await workspaceService.getWorkspaceWorkflowSource(
          sessionId,
          visiblePath,
        ),
      );
    } catch (error) {
      if (!(error instanceof WorkspaceWorkflowSourceNotFoundError)) {
        throw error;
      }
    }

    let created: WorkspaceWorkflowSourceDocument;
    try {
      created = await workspaceService.createWorkspaceWorkflowSource(
        sessionId,
        visiblePath,
        starterWorkflowSource,
      );
    } catch (createError) {
      try {
        return requireScopedDocument(
          await workspaceService.getWorkspaceWorkflowSource(
            sessionId,
            visiblePath,
          ),
        );
      } catch {
        const detail =
          createError instanceof Error ? ` ${createError.message}` : "";
        throw new Error(
          `The default workflow could not be created in ${workspaceName}. Check that the workspace is writable, then retry.${detail}`,
        );
      }
    }

    return requireScopedDocument(created);
  }, [
    requireScopedDocument,
    sessionId,
    visiblePath,
    workflowFilePath,
    workspaceName,
  ]);

  const workflowScope = `${workspaceId}\u0000${sessionId}\u0000${visiblePath}`;

  const openWorkflow = useCallback(
    (retry = false) => {
      if (!retry && bootstrapRequest.current?.scope === workflowScope) {
        return bootstrapRequest.current.promise;
      }
      const promise = bootstrapWorkflow();
      bootstrapRequest.current = { scope: workflowScope, promise };
      return promise;
    },
    [bootstrapWorkflow, workflowScope],
  );

  const showWorkflow = useCallback(
    async (retry = false) => {
      setDocument(null);
      setState("loading");
      setMessage("");
      try {
        const loaded = await openWorkflow(retry);
        setDocument(loaded);
        setState("ready");
      } catch (error) {
        setDocument(null);
        setMessage(
          error instanceof Error
            ? error.message
            : "Unable to open the default workflow in this workspace.",
        );
        setState("error");
      }
    },
    [openWorkflow],
  );

  useEffect(() => {
    let current = true;
    setDocument(null);
    setState("loading");
    setMessage("");
    void openWorkflow()
      .then((response) => {
        if (!current) return;
        setDocument(response);
        setState("ready");
      })
      .catch((error: unknown) => {
        if (!current) return;
        setDocument(null);
        setMessage(
          error instanceof Error
            ? error.message
            : "Unable to open the default workflow in this workspace.",
        );
        setState("error");
      });
    return () => {
      current = false;
    };
  }, [openWorkflow]);

  useEffect(() => {
    if (!document) {
      templateReadinessRequest.current += 1;
      setTemplateReadiness(null);
      return;
    }
    let current = true;
    const requestId = ++templateReadinessRequest.current;
    setTemplateReadiness(null);
    void workspaceService
      .getWorkspaceWorkflowSourceReadiness(sessionId, visiblePath)
      .then((readiness) => {
        if (current && requestId === templateReadinessRequest.current)
          setTemplateReadiness(readiness);
      })
      .catch((error: unknown) => {
        if (!current || requestId !== templateReadinessRequest.current) return;
        setTemplateReadiness({
          state: "unavailable",
          template_id: null,
          template_version: null,
          source_digest: null,
          layout_digest: null,
          definition_valid: null,
          configured: null,
          qualified: null,
          available: null,
          verified_run: null,
          facts: [],
          blocking_reasons: [],
          message:
            error instanceof Error
              ? error.message
              : "Workflow qualification could not be checked.",
        });
      });
    return () => {
      current = false;
    };
  }, [document, sessionId, visiblePath]);

  const refreshTemplateReadiness = useCallback(async () => {
    if (!document) return;
    const requestScope = `${sessionId}:${visiblePath}`;
    const requestId = ++templateReadinessRequest.current;
    try {
      const readiness =
        await workspaceService.getWorkspaceWorkflowSourceReadiness(
          sessionId,
          visiblePath,
        );
      if (
        requestId === templateReadinessRequest.current &&
        requestScope === `${sessionId}:${visiblePath}`
      )
        setTemplateReadiness(readiness);
    } catch (error: unknown) {
      if (
        requestId !== templateReadinessRequest.current ||
        requestScope !== `${sessionId}:${visiblePath}`
      )
        return;
      setTemplateReadiness({
        state: "unavailable",
        template_id: null,
        template_version: null,
        source_digest: null,
        layout_digest: null,
        definition_valid: null,
        configured: null,
        qualified: null,
        available: null,
        verified_run: null,
        facts: [],
        blocking_reasons: [],
        message:
          error instanceof Error
            ? error.message
            : "Workflow qualification could not be checked.",
      });
    }
  }, [document, sessionId, visiblePath]);

  const saveWorkflow = async (source: string, layout?: RecoveryLayout) => {
    if (
      !document ||
      document.workspace_id !== workspaceId ||
      document.path !== visiblePath
    ) {
      throw new Error(
        "The workspace workflow file is not loaded. Your local edits were kept.",
      );
    }
    const sourceArguments = [
      sessionId,
      visiblePath,
      source,
      document.storage_revision,
      document.storage_digest,
      true,
    ] as const;
    const saved = requireScopedDocument(
      await (layout
        ? workspaceService.updateWorkspaceWorkflowSource(
            ...sourceArguments,
            layout,
            document.layout_revision ?? 0,
          )
        : workspaceService.updateWorkspaceWorkflowSource(...sourceArguments)),
    );
    setDocument(saved);
    return saved;
  };

  const listWorkspaceFiles = useCallback(
    () =>
      workspaceService.getWorkspaceWorkflowInputFiles(sessionId, workspaceId),
    [sessionId, workspaceId],
  );

  const readStoredWorkflow = useCallback(
    async () =>
      requireScopedDocument(
        await workspaceService.getWorkspaceWorkflowSource(
          sessionId,
          visiblePath,
        ),
      ),
    [requireScopedDocument, sessionId, visiblePath],
  );

  const reloadStoredWorkflow = useCallback(
    async (canReplace?: (stored: WorkflowRecoveryStoredSource) => boolean) => {
      const loaded = requireScopedDocument(
        await workspaceService.getWorkspaceWorkflowSource(
          sessionId,
          visiblePath,
        ),
      );
      // Check after the read: edits or another open request may arrive in flight.
      // Explicit conflict-discard reloads omit the guard and keep their behavior.
      if (canReplace && !canReplace(loaded)) return;
      bootstrapRequest.current = {
        scope: workflowScope,
        promise: Promise.resolve(loaded),
      };
      setDocument(loaded);
      setMessage("");
      setState("ready");
      setEditorInstance((current) => current + 1);
    },
    [requireScopedDocument, sessionId, visiblePath, workflowScope],
  );

  const runWorkflow = useCallback(
    async (options?: WorkflowRunOptions) => {
      if (
        !document ||
        document.workspace_id !== workspaceId ||
        document.path !== visiblePath
      ) {
        throw new Error(
          "The saved workspace workflow is not available to run.",
        );
      }
      const result = await workspaceService.runWorkspaceWorkflowSource(
        sessionId,
        visiblePath,
        options?.expectedStorageDigest ?? document.storage_digest,
        options?.onEvent,
        options?.signal,
      );
      if (
        result.workspace_id !== workspaceId ||
        result.workflow_path !== visiblePath
      ) {
        throw new Error(
          "Wright returned a run result for a different workspace workflow.",
        );
      }
      return {
        status: result.status,
        review: result.review,
        approval: result.approval,
        runId: result.run_id,
        verification: result.verification,
        captureRights: result.capture_rights,
        outputPath: result.output_path,
        runLogPath: result.run_log_path,
        outputBytes: result.output_bytes,
        taskTitle: result.task_title,
        taskId: result.task_id,
        workflowTitle: result.workflow_title,
        outputs: result.outputs,
        results: result.results,
        steps: result.steps,
      };
    },
    [document, sessionId, visiblePath, workspaceId],
  );

  const currentDocument =
    document?.workspace_id === workspaceId && document.path === visiblePath
      ? document
      : null;

  useEffect(() => {
    const dialog = fileDialog.current;
    if (!dialog) return;
    if (fileAction && !dialog.open) {
      if (dialog.showModal) dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!fileAction && dialog.open) {
      if (dialog.close) dialog.close();
      else dialog.removeAttribute("open");
    }
  }, [fileAction]);

  const showFileAction = async (action: "new" | "open") => {
    setFileAction(action);
    setFileActionError("");
    setNewWorkflowName("");
    if (action !== "open") return;
    setFileActionPending(true);
    setWorkflowChoices([]);
    try {
      const files = await listWorkspaceFiles();
      setWorkflowChoices(
        files.filter((file) =>
          /^workflows\/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$/.test(
            file.path,
          ),
        ),
      );
    } catch (error) {
      setFileActionError(
        error instanceof Error
          ? error.message
          : "Unable to list workspace workflows.",
      );
    } finally {
      setFileActionPending(false);
    }
  };

  const createNamedWorkflow = async () => {
    const title = newWorkflowName.trim();
    const slug = title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    if (
      !title ||
      !/^[a-z0-9][a-z0-9-]{0,62}$/.test(slug) ||
      /^(aux|con|nul|prn|com[1-9]|lpt[1-9])$/.test(slug)
    ) {
      setFileActionError(
        "Use a short workflow name containing letters and numbers (up to 63 filename characters).",
      );
      return;
    }
    const path = `workflows/${slug}.workflow.wflow`;
    const key = `authored_${crypto.randomUUID().replaceAll("-", "_")}`;
    const source = `workflow ${key}\n  name: ${JSON.stringify(title)}\n  purpose: "Define this workflow's steps and outputs."\n  discipline: "engineering"\n  reviewed_ai_suggestions: true\nend\n`;
    setFileActionPending(true);
    setFileActionError("");
    try {
      const created = await workspaceService.createWorkspaceWorkflowSource(
        sessionId,
        path,
        source,
      );
      if (created.workspace_id !== workspaceId || created.path !== path)
        throw new Error(
          "Wright returned a workflow for a different workspace or path.",
        );
      setFileAction(null);
      onOpenWorkflow?.(path);
    } catch (error) {
      setFileActionError(
        error instanceof Error
          ? error.message
          : "Unable to create the workflow. Existing files were kept.",
      );
    } finally {
      setFileActionPending(false);
    }
  };

  return (
    <section
      className="workflow-recovery-page"
      data-testid="page-workflow-recovery"
      data-workspace-id={workspaceId}
      data-session-id={sessionId}
      data-workflow-file={visiblePath}
      aria-label={`${workspaceName} workflow ${visiblePath}`}
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        width: "100%",
        height: "100%",
        minWidth: 0,
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      {currentDocument?.layout_status === "stale" && (
        <p role="status">
          Diagram placement is from an older file version. Review the current
          layout before saving.
        </p>
      )}
      <EngineeringTemplateDialog
        open={templateDialogOpen}
        sessionId={sessionId}
        workspaceId={workspaceId}
        workspaceName={workspaceName}
        onClose={closeTemplateDialog}
        onCreated={(path) => onOpenWorkflow?.(path)}
      />
      <dialog
        ref={fileDialog}
        aria-labelledby={`${dialogId}-title`}
        onCancel={() => setFileAction(null)}
        style={{
          color: "var(--color-primary)",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: 12,
          padding: 24,
          width: "min(480px, 90vw)",
          maxHeight: "80vh",
        }}
      >
        <h2 id={`${dialogId}-title`}>
          {fileAction === "new" ? "New workflow" : "Open workflow"}
        </h2>
        <p>
          Stored in {workspaceName}/workflows. Existing files are never
          replaced.
        </p>
        {fileAction === "new" ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void createNamedWorkflow();
            }}
          >
            <label htmlFor={`${dialogId}-name`}>Workflow name</label>
            <input
              id={`${dialogId}-name`}
              data-testid="workflow-file-name"
              autoFocus
              value={newWorkflowName}
              maxLength={100}
              onChange={(event) => setNewWorkflowName(event.target.value)}
              placeholder="Inspection checks"
              style={{ display: "block", width: "100%", margin: "8px 0 16px" }}
            />
            <p>
              Starts with the editable engineering example. The Run panel states
              which saved workflow capabilities are available.
            </p>
            <button
              type="submit"
              className="recovery-button"
              data-testid="workflow-file-create"
              disabled={fileActionPending}
            >
              Create workflow
            </button>
          </form>
        ) : (
          <div
            style={{
              display: "grid",
              gap: 8,
              maxHeight: "45vh",
              overflow: "auto",
            }}
          >
            {fileActionPending && (
              <p role="status">Listing workspace workflows…</p>
            )}
            {!fileActionPending &&
              !fileActionError &&
              workflowChoices.length === 0 && (
                <p>No workflow files found in this workspace.</p>
              )}
            {workflowChoices.map((file) => (
              <button
                type="button"
                key={file.path}
                data-testid={`workflow-file-choice-${file.path}`}
                className="recovery-button recovery-button--secondary"
                onClick={() => {
                  setFileAction(null);
                  onOpenWorkflow?.(file.path);
                }}
              >
                {file.name}
              </button>
            ))}
          </div>
        )}
        {fileActionError && (
          <p role="alert" data-testid="workflow-files-error">
            {fileActionError}
          </p>
        )}
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          data-testid="workflow-file-cancel"
          disabled={fileActionPending}
          onClick={() => setFileAction(null)}
          style={{ marginTop: 16 }}
        >
          Cancel
        </button>
      </dialog>
      <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {(state === "loading" || (state === "ready" && !currentDocument)) && (
          <WorkflowRecoveryConcept surfaceState="loading" />
        )}
        {state === "error" && (
          <section
            className="recovery-boundary-state"
            role="alert"
            data-testid="workflow-source-load-error"
          >
            <b>Workflow could not be opened.</b>
            <span>{message}</span>
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid="workflow-source-load-retry"
              onClick={() => void showWorkflow(true)}
            >
              Retry
            </button>
          </section>
        )}
        {state === "ready" && currentDocument && (
          <WorkflowRecoveryConcept
            key={`${sessionId}\u0000${visiblePath}\u0000${editorInstance}`}
            fileActions={
              onOpenWorkflow && (
                <details
                  className="recovery-file-menu"
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      e.currentTarget.open = false;
                      e.currentTarget.querySelector("summary")?.focus();
                    }
                  }}
                >
                  <summary
                    aria-label="Workflow files"
                    title="Workflow files"
                    data-testid="workflow-file-menu"
                  >
                    ⋯
                  </summary>
                  <div>
                    <small>{workspaceName}</small>
                    <button
                      type="button"
                      data-testid="workflow-file-open"
                      onClick={(e) => {
                        e.currentTarget.closest("details")!.open = false;
                        void showFileAction("open");
                      }}
                    >
                      Open workflow
                    </button>
                    <button
                      type="button"
                      data-testid="workflow-file-new"
                      onClick={(e) => {
                        e.currentTarget.closest("details")!.open = false;
                        void showFileAction("new");
                      }}
                    >
                      New workflow
                    </button>
                    <button
                      type="button"
                      data-testid="workflow-start-template"
                      onClick={(e) => {
                        e.currentTarget.closest("details")!.open = false;
                        setTemplateDialogOpen(true);
                      }}
                    >
                      Start from template
                    </button>
                  </div>
                </details>
              )
            }
            workflowSource={currentDocument.source}
            definitionRevision={currentDocument.definition_revision}
            storageDigest={currentDocument.storage_digest}
            workflowFilePath={visiblePath}
            reopenRequest={reopenRequest}
            workflowLayout={currentDocument.layout ?? undefined}
            workspaceSessionId={sessionId}
            workspaceId={workspaceId}
            onSave={saveWorkflow}
            onListWorkspaceFiles={listWorkspaceFiles}
            onReadStoredSource={readStoredWorkflow}
            onReloadStoredSource={reloadStoredWorkflow}
            onRun={runWorkflow}
            templateReadiness={templateReadiness}
            onRefreshTemplateReadiness={refreshTemplateReadiness}
            onOpenFile={onOpenFile}
          />
        )}
      </div>
    </section>
  );
}

export default WorkflowRecoveryPage;
