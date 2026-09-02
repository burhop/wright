import { useCallback, useEffect, useId, useRef, useState } from "react";

import WorkflowRecoveryConcept from "../../prototypes/workflow-recovery/WorkflowRecoveryConcept";
import { initialWorkflow, type RecoveryLayout } from "../../prototypes/workflow-recovery/model";
import { formatRecoveryAuthoringSource } from "../../prototypes/workflow-recovery/recovery-authoring";
import {
  workspaceService,
  WorkspaceWorkflowSourceNotFoundError,
  type WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";

const starterWorkflowSource = formatRecoveryAuthoringSource(initialWorkflow).text;

export interface WorkflowRecoveryPageProps {
  workspaceId: string;
  sessionId: string;
  workspaceName: string;
  workflowFilePath: string;
  onOpenWorkflow?: (path: string) => void;
}

export function WorkflowRecoveryPage({
  workspaceId,
  sessionId,
  workspaceName,
  workflowFilePath,
  onOpenWorkflow,
}: WorkflowRecoveryPageProps) {
  const visiblePath = workflowFilePath.replace(/^\/+/, "");
  const dialogId = useId();
  const [document, setDocument] = useState<WorkspaceWorkflowSourceDocument | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("");
  const [editorInstance, setEditorInstance] = useState(0);
  const [fileAction, setFileAction] = useState<"new" | "open" | null>(null);
  const [fileActionError, setFileActionError] = useState("");
  const [fileActionPending, setFileActionPending] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [workflowChoices, setWorkflowChoices] = useState<Array<{ path: string; name: string }>>([]);
  const fileDialog = useRef<HTMLDialogElement>(null);
  const bootstrapRequest = useRef<{
    scope: string;
    promise: Promise<WorkspaceWorkflowSourceDocument>;
  } | null>(null);

  const requireScopedDocument = useCallback((loaded: WorkspaceWorkflowSourceDocument) => {
    if (loaded.workspace_id !== workspaceId || loaded.path !== visiblePath) {
      throw new Error("Wright returned a workflow file for a different workspace or path.");
    }
    return loaded;
  }, [visiblePath, workspaceId]);

  const bootstrapWorkflow = useCallback(async () => {
    const match = /^\/?workflows\/([a-z0-9][a-z0-9-]{0,62})\.workflow\.wflow$/.exec(workflowFilePath);
    if (!match || /^(aux|con|nul|prn|com[1-9]|lpt[1-9])$/.test(match[1])) {
      throw new Error("Choose a valid workspace workflow file. No file was opened or created.");
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
        const detail = createError instanceof Error
          ? ` ${createError.message}`
          : "";
        throw new Error(
          `The default workflow could not be created in ${workspaceName}. Check that the workspace is writable, then retry.${detail}`,
        );
      }
    }

    return requireScopedDocument(created);
  }, [requireScopedDocument, sessionId, visiblePath, workflowFilePath, workspaceName]);

  const workflowScope = `${workspaceId}\u0000${sessionId}\u0000${visiblePath}`;

  const openWorkflow = useCallback((retry = false) => {
    if (!retry && bootstrapRequest.current?.scope === workflowScope) {
      return bootstrapRequest.current.promise;
    }
    const promise = bootstrapWorkflow();
    bootstrapRequest.current = { scope: workflowScope, promise };
    return promise;
  }, [bootstrapWorkflow, workflowScope]);

  const showWorkflow = useCallback(async (retry = false) => {
    setDocument(null);
    setState("loading");
    setMessage("");
    try {
      const loaded = await openWorkflow(retry);
      setDocument(loaded);
      setState("ready");
    } catch (error) {
      setDocument(null);
      setMessage(error instanceof Error ? error.message : "Unable to open the default workflow in this workspace.");
      setState("error");
    }
  }, [openWorkflow]);

  useEffect(() => {
    let current = true;
    setDocument(null);
    setState("loading");
    setMessage("");
    void openWorkflow().then((response) => {
      if (!current) return;
      setDocument(response);
      setState("ready");
    }).catch((error: unknown) => {
      if (!current) return;
      setDocument(null);
      setMessage(error instanceof Error ? error.message : "Unable to open the default workflow in this workspace.");
      setState("error");
    });
    return () => { current = false; };
  }, [openWorkflow]);

  const saveWorkflow = async (source: string, layout?: RecoveryLayout) => {
    if (!document || document.workspace_id !== workspaceId || document.path !== visiblePath) {
      throw new Error("The workspace workflow file is not loaded. Your local edits were kept.");
    }
    const sourceArguments = [sessionId, visiblePath, source, document.storage_revision, document.storage_digest, true] as const;
    const saved = requireScopedDocument(await (layout
      ? workspaceService.updateWorkspaceWorkflowSource(...sourceArguments, layout, document.layout_revision ?? 0)
      : workspaceService.updateWorkspaceWorkflowSource(...sourceArguments)));
    setDocument(saved);
    return saved;
  };

  const listWorkspaceFiles = useCallback(
    () => workspaceService.getWorkspaceWorkflowInputFiles(sessionId, workspaceId),
    [sessionId, workspaceId],
  );

  const readStoredWorkflow = useCallback(
    async () => requireScopedDocument(
      await workspaceService.getWorkspaceWorkflowSource(sessionId, visiblePath),
    ),
    [requireScopedDocument, sessionId, visiblePath],
  );

  const reloadStoredWorkflow = useCallback(async () => {
    const loaded = requireScopedDocument(
      await workspaceService.getWorkspaceWorkflowSource(sessionId, visiblePath),
    );
    setDocument(loaded);
    setMessage("");
    setState("ready");
    setEditorInstance((current) => current + 1);
  }, [requireScopedDocument, sessionId, visiblePath]);

  const currentDocument = document?.workspace_id === workspaceId && document.path === visiblePath
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
      setWorkflowChoices(files.filter((file) => /^workflows\/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$/.test(file.path)));
    } catch (error) {
      setFileActionError(error instanceof Error ? error.message : "Unable to list workspace workflows.");
    } finally {
      setFileActionPending(false);
    }
  };

  const createNamedWorkflow = async () => {
    const title = newWorkflowName.trim();
    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!title || !/^[a-z0-9][a-z0-9-]{0,62}$/.test(slug) || /^(aux|con|nul|prn|com[1-9]|lpt[1-9])$/.test(slug)) {
      setFileActionError("Use a short workflow name containing letters and numbers (up to 63 filename characters).");
      return;
    }
    const path = `workflows/${slug}.workflow.wflow`;
    const candidate = structuredClone(initialWorkflow);
    candidate.workflowId = `workflow.authored-${crypto.randomUUID()}`;
    candidate.metadata.title = title;
    setFileActionPending(true);
    setFileActionError("");
    try {
      const source = formatRecoveryAuthoringSource(candidate).text;
      const created = await workspaceService.createWorkspaceWorkflowSource(sessionId, path, source);
      if (created.workspace_id !== workspaceId || created.path !== path) throw new Error("Wright returned a workflow for a different workspace or path.");
      setFileAction(null);
      onOpenWorkflow?.(path);
    } catch (error) {
      setFileActionError(error instanceof Error ? error.message : "Unable to create the workflow. Existing files were kept.");
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
      <div
        data-testid="workflow-workspace-context"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-sm)",
          minHeight: 32,
          padding: "0 var(--space-md)",
          borderBottom: "1px solid var(--color-border)",
          backgroundColor: "var(--color-surface-elevated)",
          color: "var(--color-secondary)",
          fontSize: "0.72rem",
          flex: "0 0 auto",
        }}
      >
        <strong style={{ color: "var(--color-primary)", maxWidth: "22ch", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{workspaceName}</strong>
        <span aria-hidden="true">/</span>
        <span>Workflows</span>
        <span aria-hidden="true">/</span>
        <code style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={visiblePath}>{visiblePath.split("/").at(-1)}</code>
        {currentDocument?.layout_status === "stale" && <span role="status">Diagram placement is from an older file version. Review the current layout before saving.</span>}
        {onOpenWorkflow && <span style={{ marginLeft: "auto", display: "flex", gap: 8, flexShrink: 0 }}>
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-file-open" onClick={() => void showFileAction("open")}>Open workflow</button>
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-file-new" onClick={() => void showFileAction("new")}>New workflow</button>
        </span>}
      </div>
      <dialog ref={fileDialog} aria-labelledby={`${dialogId}-title`} onCancel={() => setFileAction(null)} style={{ color: "var(--color-primary)", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 12, padding: 24, width: "min(480px, 90vw)", maxHeight: "80vh" }}>
        <h2 id={`${dialogId}-title`}>{fileAction === "new" ? "New workflow" : "Open workflow"}</h2>
        <p>Stored in {workspaceName}/workflows. Existing files are never replaced.</p>
        {fileAction === "new" ? <form onSubmit={(event) => { event.preventDefault(); void createNamedWorkflow(); }}>
          <label htmlFor={`${dialogId}-name`}>Workflow name</label>
          <input id={`${dialogId}-name`} data-testid="workflow-file-name" autoFocus value={newWorkflowName} maxLength={100} onChange={(event) => setNewWorkflowName(event.target.value)} placeholder="Inspection checks" style={{ display: "block", width: "100%", margin: "8px 0 16px" }} />
          <p>Starts with the editable engineering example. Runs remain simulated.</p>
          <button type="submit" className="recovery-button" data-testid="workflow-file-create" disabled={fileActionPending}>Create workflow</button>
        </form> : <div style={{ display: "grid", gap: 8, maxHeight: "45vh", overflow: "auto" }}>
          {fileActionPending && <p role="status">Listing workspace workflows…</p>}
          {!fileActionPending && !fileActionError && workflowChoices.length === 0 && <p>No workflow files found in this workspace.</p>}
          {workflowChoices.map((file) => <button type="button" key={file.path} data-testid={`workflow-file-choice-${file.path}`} className="recovery-button recovery-button--secondary" onClick={() => { setFileAction(null); onOpenWorkflow?.(file.path); }}>{file.name}</button>)}
        </div>}
        {fileActionError && <p role="alert" data-testid="workflow-files-error">{fileActionError}</p>}
        <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-file-cancel" disabled={fileActionPending} onClick={() => setFileAction(null)} style={{ marginTop: 16 }}>Cancel</button>
      </dialog>
      <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {(state === "loading" || (state === "ready" && !currentDocument)) && <WorkflowRecoveryConcept surfaceState="loading" />}
        {state === "error" && <section className="recovery-boundary-state" role="alert" data-testid="workflow-source-load-error"><b>Workflow could not be opened.</b><span>{message}</span><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-source-load-retry" onClick={() => void showWorkflow(true)}>Retry</button></section>}
        {state === "ready" && currentDocument && <WorkflowRecoveryConcept
          key={`${sessionId}\u0000${visiblePath}\u0000${editorInstance}`}
          workflowSource={currentDocument.source}
          definitionRevision={currentDocument.definition_revision}
          storageDigest={currentDocument.storage_digest}
          workflowFilePath={visiblePath}
          workflowLayout={currentDocument.layout ?? undefined}
          onSave={saveWorkflow}
          onListWorkspaceFiles={listWorkspaceFiles}
          onReadStoredSource={readStoredWorkflow}
          onReloadStoredSource={reloadStoredWorkflow}
        />}
      </div>
    </section>
  );
}

export default WorkflowRecoveryPage;
