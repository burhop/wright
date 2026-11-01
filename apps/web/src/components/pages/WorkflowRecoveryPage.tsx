import { copyWorkspaceWorkflowSource } from "../../services/workflow-source-copy";
import type { OpenWorkspaceToolSetup } from "../../services/workspace-tool-setup";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { ProcessRef } from "@wright/process-client";

import WorkflowRecoveryConcept, {
  type WorkflowRunOptions,
  type WorkflowRecoveryStoredSource,
} from "../../prototypes/workflow-recovery/WorkflowRecoveryConcept";
import { HistoricalResultView } from "../process-interfaces/HistoricalResultView";
import { EngineeringTemplateDialog } from "../../prototypes/workflow-recovery/EngineeringTemplateDialog";
import { PrintedHandleSetupDialog } from "../../prototypes/workflow-recovery/PrintedHandleSetupDialog";
import { WorkflowBundleDialog } from "../../prototypes/workflow-recovery/WorkflowBundleDialog";
import { type RecoveryLayout } from "../../prototypes/workflow-recovery/model";
import { blankWorkflowSource } from "../../services/blank-workflow";
import { readDesktopReasoningWait } from "../../services/desktop-reasoning-status";
import {
  workspaceService,
  WorkspaceWorkflowSourceNotFoundError,
  type WorkspaceWorkflowSourceDocument,
  type WorkspaceWorkflowSourceReadiness,
} from "../../services/workspace-service";

export interface WorkflowRecoveryPageProps {
  workspaceId: string;
  sessionId: string;
  workspaceName: string;
  workflowFilePath: string;
  reopenRequest?: number;
  onOpenWorkflow?: (path: string) => void;
  onUnsavedChange?: (path: string, unsaved: boolean) => void;
  onSavingChange?: (path: string, saving: boolean) => void;
  onOpenFile?: (path: string) => void;
  onOpenProcess?: (process: ProcessRef, runId?: string) => void;
  onConfigureTools?: OpenWorkspaceToolSetup;
  createIfMissing?: boolean;
  navigation?: import("../../services/process-navigation").ProcessNavigationRequest;
}

export function WorkflowRecoveryPage({
  workspaceId,
  sessionId,
  workspaceName,
  workflowFilePath,
  reopenRequest = 0,
  onOpenWorkflow,
  onUnsavedChange,
  onSavingChange,
  onOpenFile,
  onOpenProcess,
  onConfigureTools,
  createIfMissing = false,
  navigation,
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
  const [fileAction, setFileAction] = useState<
    "new" | "open" | "save-as" | "clone" | null
  >(null);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const templateEntry = useRef<"explore" | "menu">("menu");
  const [transferOpen, setTransferOpen] = useState(false);
  const [setupSubject, setSetupSubject] = useState<string | null>(null);
  const [setupNotice, setSetupNotice] = useState("");
  const setupButton = useRef<HTMLButtonElement>(null);
  const page = useRef<HTMLElement>(null);
  const [fileActionError, setFileActionError] = useState("");
  const [fileActionPending, setFileActionPending] = useState(false);
  const [editorUnsaved, setEditorUnsaved] = useState(false);
  const [workingViewPending, setWorkingViewPending] = useState(false);
  const [workingViewError, setWorkingViewError] = useState("");
  const workingViewRequest = useRef(0);
  useEffect(() => {
    workingViewRequest.current += 1;
    setWorkingViewPending(false);
    setWorkingViewError("");
    return () => {
      workingViewRequest.current += 1;
    };
  }, [workspaceId, sessionId, visiblePath, document?.storage_digest, editorUnsaved]);
  const handleUnsavedChange = useCallback(
    (unsaved: boolean) => {
      setEditorUnsaved(unsaved);
      if (unsaved) setSetupSubject(null);
      onUnsavedChange?.(workflowFilePath, unsaved);
    },
    [onUnsavedChange, workflowFilePath],
  );
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const historicalQuery = new URLSearchParams(window.location.search);
  // This selects a read-only presentation adapter, never execution authority.
  const desktopConversation = historicalQuery.get("host") === "openai-desktop";
  const readReasoningStatus = useCallback(
    (runId: string, signal: AbortSignal) =>
      readDesktopReasoningWait(
        { workspaceId, sessionId, runId, workspaceName },
        signal,
      ),
    [workspaceId, sessionId, workspaceName],
  );
  const historicalWorkflow = historicalQuery
    .get("workflowPath")
    ?.replace(/^\/+/, "");
  const initialPrintDemoRun =
    historicalWorkflow === visiblePath
      ? historicalQuery.get("printDemoRun")
      : null;
  const [printDemoOpen, setPrintDemoOpen] = useState(
    Boolean(initialPrintDemoRun),
  );
  useEffect(() => {
    if (initialPrintDemoRun) setPrintDemoOpen(true);
  }, [initialPrintDemoRun]);
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
        templateEntry.current === "explore"
          ? '[data-testid="workflow-explore-example"]'
          : '[data-testid="workflow-file-menu"]',
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
      if (!createIfMissing) {
        throw new Error(
          "The saved workflow file is no longer available. Choose an existing workflow or create a new one explicitly.",
          { cause: error },
        );
      }
    }

    let created: WorkspaceWorkflowSourceDocument;
    try {
      created = await workspaceService.createWorkspaceWorkflowSource(
        sessionId,
        visiblePath,
        blankWorkflowSource(),
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
    createIfMissing,
    requireScopedDocument,
    sessionId,
    visiblePath,
    workflowFilePath,
    workspaceName,
  ]);

  const workflowScope = `${workspaceId}\u0000${sessionId}\u0000${visiblePath}\u0000${createIfMissing}`;

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
    setSetupSubject(null);
    setSetupNotice("");
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
    onSavingChange?.(workflowFilePath, true);
    try {
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
    } finally {
      onSavingChange?.(workflowFilePath, false);
    }
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
        inputCheckpoint: result.input_checkpoint,
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

  const showFileAction = async (
    action: "new" | "open" | "save-as" | "clone",
  ) => {
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
    const source = blankWorkflowSource(title);
    const copying = fileAction === "save-as" || fileAction === "clone";
    if (copying && (!currentDocument || editorUnsaved)) {
      setFileActionError("Save your edits before copying this workflow.");
      return;
    }
    setFileActionPending(true);
    setFileActionError("");
    try {
      const created =
        copying && currentDocument
          ? await copyWorkspaceWorkflowSource(
              sessionId,
              currentDocument.path,
              path,
              currentDocument.storage_digest,
            )
          : await workspaceService.createWorkspaceWorkflowSource(
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
      ref={page}
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
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "flex-end",
          padding: "5px 12px",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        {onOpenWorkflow && (
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-explore-example"
            onClick={() => {
              templateEntry.current = "explore";
              setTemplateDialogOpen(true);
            }}
            style={{ padding: "5px 12px", marginRight: "auto" }}
          >
            Explore an example
          </button>
        )}
        {templateReadiness?.template_id === "replacement-drawer-handle" &&
          templateReadiness.starter_unchanged !== false &&
          templateReadiness.state === "setup_required" && (
            <button
              ref={setupButton}
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid="workflow-handle-setup-open"
              disabled={state !== "ready" || !currentDocument || editorUnsaved}
              title={
                editorUnsaved
                  ? "Setup requires an unchanged starter. Preserve your edits or create a fresh starter."
                  : "Inspect and bind the handle process to this workspace"
              }
              onClick={() => {
                if (!currentDocument || editorUnsaved) return;
                setSetupNotice("");
                setSetupSubject(
                  `${sessionId}:${currentDocument.path}:${currentDocument.storage_digest}`,
                );
              }}
              style={{ padding: "5px 12px", marginRight: 8 }}
            >
              Set up this job
            </button>
          )}
        {templateReadiness?.template_id === "replacement-drawer-handle" &&
          templateReadiness.starter_unchanged === false &&
          templateReadiness.accepted_source_digest === currentDocument?.storage_digest && (
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid="workflow-edited-process-setup-open"
              disabled={state !== "ready" || !currentDocument}
              title="Inspect setup issues and configure the existing steps. Your edits stay in this process."
              style={{ padding: "5px 12px", marginRight: 8 }}
              onClick={() => {
                const readiness = page.current?.querySelector<HTMLDetailsElement>(
                  '[data-testid="workflow-recovery-run-readiness"]',
                );
                if (!readiness) {
                  setSetupNotice("Open this process in the editor to inspect its step setup.");
                  return;
                }
                readiness.open = true;
                readiness.querySelector("summary")?.focus();
                readiness.scrollIntoView({ block: "nearest" });
              }}
            >
              Configure existing steps
            </button>
          )}
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          data-testid="workflow-transfer-open"
          disabled={state !== "ready" || !currentDocument || editorUnsaved}
          onClick={() => setTransferOpen(true)}
          style={{ padding: "5px 12px", marginRight: 8 }}
        >
          Export / import workflow
        </button>
        {onOpenProcess && (
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-working-view-open"
            disabled={state !== "ready" || !currentDocument || editorUnsaved || workingViewPending}
            onClick={async () => {
              if (!currentDocument || editorUnsaved || workingViewPending) return;
              const request = ++workingViewRequest.current;
              const process = {
                workspace_id: currentDocument.workspace_id,
                source_path: currentDocument.path,
                source_digest: currentDocument.storage_digest,
              };
              setWorkingViewPending(true);
              setWorkingViewError("");
              try {
                // Reconcile through the same durable history as the editor.
                // Opening a view never starts or repeats a process.
                const [latest] = await workspaceService.getWorkspaceWorkflowRuns(
                  sessionId,
                  process.source_path,
                  { latestOnly: true, workspaceId: process.workspace_id },
                );
                if (request !== workingViewRequest.current) return;
                if (
                  latest?.source_digest === process.source_digest &&
                  latest.source_matches_current !== false &&
                  !latest.run_id
                )
                  throw new Error(
                    "The saved run has no usable identity. Open Previous runs to inspect it; no new process was started.",
                  );
                const runId =
                  latest?.source_digest === process.source_digest &&
                  latest.source_matches_current !== false
                    ? latest.run_id ?? undefined
                    : undefined;
                onOpenProcess(process, runId);
              } catch (error) {
                if (request !== workingViewRequest.current) return;
                setWorkingViewError(
                  error instanceof Error
                    ? error.message
                    : "The existing run could not be checked. Try opening the working view again.",
                );
              } finally {
                if (request === workingViewRequest.current)
                  setWorkingViewPending(false);
              }
            }}
            style={{ padding: "5px 12px", marginRight: 8 }}
            title={
              editorUnsaved
                ? "Save your changes before opening the working view"
                : "Open the latest run for this saved workflow, or its inputs if it has no matching run. Nothing runs automatically."
            }
          >
            {workingViewPending ? "Opening working view…" : "Open working view"}
          </button>
        )}
        {onOpenProcess && editorUnsaved && (
          <small style={{ alignSelf: "center" }}>
            Save your changes to open the working view.
          </small>
        )}
        {initialPrintDemoRun && (
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-print-demo-open"
            onClick={() => setPrintDemoOpen(true)}
            style={{ padding: "5px 12px" }}
          >
            View saved result
          </button>
        )}
      </div>
      {workingViewError && <p role="alert">{workingViewError}</p>}
      {setupNotice && <p role="status">{setupNotice}</p>}
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
      {currentDocument &&
        !editorUnsaved &&
        setupSubject ===
          `${sessionId}:${currentDocument.path}:${currentDocument.storage_digest}` && (
          <PrintedHandleSetupDialog
            key={setupSubject}
            document={currentDocument}
            sessionId={sessionId}
            onListFiles={listWorkspaceFiles}
            onConfigureTools={onConfigureTools}
            onClose={() => {
              setSetupSubject(null);
              window.requestAnimationFrame(() => setupButton.current?.focus());
            }}
            onAccepted={(accepted) => {
              const saved = requireScopedDocument(accepted);
              bootstrapRequest.current = {
                scope: workflowScope,
                promise: Promise.resolve(saved),
              };
              setDocument(saved);
              setEditorInstance((current) => current + 1);
              setSetupSubject(null);
              setSetupNotice(
                "Prepared revision saved. Open working view to check the current inputs, tools, model and authority before starting. Engineering review remains separate.",
              );
              window.requestAnimationFrame(() => setupButton.current?.focus());
            }}
          />
        )}
      {transferOpen && currentDocument && (
        <WorkflowBundleDialog
          document={currentDocument}
          sessionId={sessionId}
          onClose={() => setTransferOpen(false)}
          onImported={(path) => {
            if (onOpenWorkflow) {
              setTransferOpen(false);
              onOpenWorkflow(path);
            } else onOpenFile?.(path);
          }}
        />
      )}
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
          {fileAction === "new"
            ? "New workflow"
            : fileAction === "save-as"
              ? "Save workflow as"
              : fileAction === "clone"
                ? "Clone workflow"
                : "Open workflow"}
        </h2>
        <p>
          Stored in {workspaceName}/workflows. Existing files are never
          replaced.
        </p>
        {fileAction && fileAction !== "open" ? (
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
              {fileAction === "new"
                ? "Starts with a blank workflow. Add inputs and steps in the editor. Check run readiness before starting work."
                : "Copies the saved definition, instructions and current diagram to a new file. Run history and approvals stay with the original."}
            </p>
            <button
              type="submit"
              className="recovery-button"
              data-testid="workflow-file-create"
              disabled={fileActionPending}
            >
              {fileAction === "new"
                ? "Create workflow"
                : fileAction === "clone"
                  ? "Clone workflow"
                  : "Save copy"}
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
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {printDemoOpen && initialPrintDemoRun && (
          <HistoricalResultView
            sessionId={sessionId}
            workflowPath={visiblePath}
            runLogPath={initialPrintDemoRun}
            onOpenFile={onOpenFile}
            onClose={() => setPrintDemoOpen(false)}
          />
        )}
        {!printDemoOpen && (
          <>
            {(state === "loading" ||
              (state === "ready" && !currentDocument)) && (
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
                        {(["save-as", "clone"] as const).map((action) => (
                          <button
                            key={action}
                            type="button"
                            data-testid={`workflow-file-${action}`}
                            disabled={editorUnsaved || !currentDocument}
                            title={
                              editorUnsaved
                                ? "Save your edits before copying this workflow."
                                : undefined
                            }
                            onClick={(event) => {
                              event.currentTarget.closest("details")!.open =
                                false;
                              void showFileAction(action);
                            }}
                          >
                            {action === "save-as"
                              ? "Save as…"
                              : "Clone workflow…"}
                          </button>
                        ))}
                        <button
                          type="button"
                          data-testid="workflow-start-template"
                          onClick={(e) => {
                            e.currentTarget.closest("details")!.open = false;
                            templateEntry.current = "menu";
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
                navigation={navigation}
                workflowLayout={currentDocument.layout ?? undefined}
                workspaceSessionId={sessionId}
                workspaceId={workspaceId}
                onSave={saveWorkflow}
                onLoadInstructionDefaults={() =>
                  workspaceService.getWorkflowInstructionDefaults(sessionId)
                }
                onReviewInstructionProtocolUpgrade={(instructions) =>
                  workspaceService.proposeWorkflowActionIntentUpgrade(
                    instructions,
                  )
                }
                onExportSource={async () => {
                  const stored = await readStoredWorkflow();
                  if (stored.storage_digest !== currentDocument.storage_digest)
                    throw new Error(
                      "The saved workflow changed elsewhere. Reload or compare it before exporting.",
                    );
                  const blob = new Blob([stored.source], {
                    type: "text/plain;charset=utf-8",
                  });
                  const url = URL.createObjectURL(blob);
                  const link = window.document.createElement("a");
                  link.href = url;
                  link.download =
                    visiblePath.split("/").at(-1) ?? "workflow.wflow";
                  window.document.body.append(link);
                  link.click();
                  link.remove();
                  window.setTimeout(() => URL.revokeObjectURL(url), 0);
                }}
                onUnsavedChange={handleUnsavedChange}
                onListWorkspaceFiles={listWorkspaceFiles}
                onReadStoredSource={readStoredWorkflow}
                onReloadStoredSource={reloadStoredWorkflow}
                onRun={runWorkflow}
                onReadReasoningStatus={
                  desktopConversation ? readReasoningStatus : undefined
                }
                templateReadiness={templateReadiness}
                onRefreshTemplateReadiness={refreshTemplateReadiness}
                onOpenFile={onOpenFile}
                onOpenRunWorkingView={
                  onOpenProcess
                    ? (runId, sourceDigest) =>
                        onOpenProcess(
                          {
                            workspace_id: workspaceId,
                            source_path: visiblePath,
                            source_digest: sourceDigest,
                          },
                          runId,
                        )
                    : undefined
                }
              />
            )}
          </>
        )}
      </div>
    </section>
  );
}

export default WorkflowRecoveryPage;
