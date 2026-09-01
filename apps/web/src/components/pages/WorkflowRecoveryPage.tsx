import { useCallback, useEffect, useRef, useState } from "react";

import WorkflowRecoveryConcept from "../../prototypes/workflow-recovery/WorkflowRecoveryConcept";
import { initialWorkflow } from "../../prototypes/workflow-recovery/model";
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
}

export function WorkflowRecoveryPage({
  workspaceId,
  sessionId,
  workspaceName,
  workflowFilePath,
}: WorkflowRecoveryPageProps) {
  const visiblePath = workflowFilePath.replace(/^\/+/, "");
  const [document, setDocument] = useState<WorkspaceWorkflowSourceDocument | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("");
  const [editorInstance, setEditorInstance] = useState(0);
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
  }, [requireScopedDocument, sessionId, visiblePath, workspaceName]);

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

  const saveWorkflow = async (source: string) => {
    if (!document || document.workspace_id !== workspaceId || document.path !== visiblePath) {
      throw new Error("The workspace workflow file is not loaded. Your local edits were kept.");
    }
    const saved = requireScopedDocument(
      await workspaceService.updateWorkspaceWorkflowSource(
        sessionId,
        visiblePath,
        source,
        document.storage_revision,
        document.storage_digest,
        true,
      ),
    );
    setDocument(saved);
    return saved;
  };

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
        height: "100%",
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
        <strong style={{ color: "var(--color-primary)" }}>{workspaceName}</strong>
        <span aria-hidden="true">/</span>
        <span>Workflows</span>
        <span aria-hidden="true">/</span>
        <code>{visiblePath.split("/").at(-1)}</code>
      </div>
      <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {(state === "loading" || (state === "ready" && !currentDocument)) && <WorkflowRecoveryConcept surfaceState="loading" />}
        {state === "error" && <section className="recovery-boundary-state" role="alert" data-testid="workflow-source-load-error"><b>Workflow could not be opened.</b><span>{message}</span><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-source-load-retry" onClick={() => void showWorkflow(true)}>Retry</button></section>}
        {state === "ready" && currentDocument && <WorkflowRecoveryConcept
          key={`${sessionId}\u0000${visiblePath}\u0000${editorInstance}`}
          workflowSource={currentDocument.source}
          definitionRevision={currentDocument.definition_revision}
          storageDigest={currentDocument.storage_digest}
          workflowFilePath={visiblePath}
          onSave={saveWorkflow}
          onReadStoredSource={readStoredWorkflow}
          onReloadStoredSource={reloadStoredWorkflow}
        />}
      </div>
    </section>
  );
}

export default WorkflowRecoveryPage;
