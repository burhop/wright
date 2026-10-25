import { useState } from "react";
import WorkflowRecoveryConcept from "../workflow-recovery/WorkflowRecoveryConcept";
import type {
  WorkspaceWorkflowRunSummary,
  WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";
import { NativeSourceClient } from "./native-source-client";
import type { NativeEditorDraftClient } from "./native-editor-draft-client";
import type { ProcessNavigationRequest } from "../../services/process-navigation";
import { useNativeEditorDrafts } from "./use-native-editor-drafts";
import "../../styles/presentation-controls.css";
import "./native-panel.css";

/** Shared editor inside one real host work surface, without another chat or executor. */
export function NativeWorkflowPanel({
  initial,
  client,
  draftClient,
  workspaceName,
  onDirty,
  onAccepted,
  onOpenWorkingView,
  onOpenTransfer,
  transferDisabled = false,
  navigation,
  readOnlyRun,
}: {
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly client: NativeSourceClient;
  readonly draftClient?: NativeEditorDraftClient;
  readonly workspaceName: string;
  readonly onAccepted?: (document: WorkspaceWorkflowSourceDocument) => void;
  readonly onOpenWorkingView?: () => void;
  readonly onDirty?: (dirty: boolean) => void;
  readonly onOpenTransfer?: () => void;
  readonly transferDisabled?: boolean;
  readonly navigation?: ProcessNavigationRequest;
  readonly readOnlyRun?: WorkspaceWorkflowRunSummary;
}) {
  const [document, setDocument] = useState(initial);
  const [unsaved, setUnsaved] = useState(false);
  const [reopen, setReopen] = useState(0);
  const drafts = useNativeEditorDrafts(draftClient, initial, setDocument);
  return (
    <main
      className="native-workflow-panel"
      data-control-style="neutral"
      data-presentation="native-panel"
      data-working-view={!!onOpenWorkingView}
    >
      <header className="native-workflow-panel__context">
        <span className="native-workflow-panel__workspace">
          {workspaceName}
        </span>
        <nav className="native-workflow-views" aria-label="Workflow views">
          <button type="button" aria-current="page">
            Edit workflow
          </button>
          {onOpenWorkingView && (
            <button
              type="button"
              disabled={unsaved}
              onClick={onOpenWorkingView}
            >
              Run and results
            </button>
          )}
        </nav>
        {unsaved && (
          <span role="status">Unsaved changes — Save to accept.</span>
        )}
        {onOpenTransfer && (
          <button
            type="button"
            disabled={transferDisabled}
            onClick={onOpenTransfer}
          >
            Export / import workflow
          </button>
        )}
        {!onOpenWorkingView && (
          <small>
            Run controls are not connected in this editor prototype.
          </small>
        )}
        {onOpenWorkingView && (
          <small className="native-workflow-panel__view-hint">
            {readOnlyRun
              ? `Inspecting run ${readOnlyRun.run_id ?? "record"} · ${readOnlyRun.status.replaceAll("_", " ")}. Return to Run and results for its outputs.`
              : "Editing the workflow · no run selected. Open Run and results to check inputs or inspect run history."}
            {unsaved && " Save your changes before switching views."}
          </small>
        )}
      </header>
      {draftClient && (
        <details className="native-editor-drafts">
          <summary>
            {drafts.message || "Editor drafts"}
            {drafts.rows.length > 0 ? ` · ${drafts.rows.length} preserved` : ""}
          </summary>
          <p>
            Drafts preserve editing only. They cannot run, approve work, or
            replace a saved workflow.
          </p>
          <button type="button" onClick={() => void drafts.refresh()}>
            Read saved drafts
          </button>
          {draftClient.requiresRead && (
            <button type="button" onClick={drafts.separate}>
              Preserve as a separate draft
            </button>
          )}
          {drafts.rows.map((row) => (
            <div key={row.draft_id}>
              <span>
                {new Date(row.updated_at * 1000).toLocaleString()} ·{" "}
                {row.base_matches_current &&
                row.base_storage_digest === drafts.acceptedDigest
                  ? "Current base"
                  : "Older workflow"}
              </span>
              <button
                type="button"
                onClick={() => void drafts.inspect(row.draft_id)}
              >
                Inspect draft
              </button>
              <button
                type="button"
                disabled={
                  unsaved ||
                  !row.base_matches_current ||
                  row.base_storage_digest !== drafts.acceptedDigest ||
                  draftClient.requiresRead
                }
                onClick={() => void drafts.resume(row.draft_id, unsaved)}
              >
                Resume draft
              </button>
            </div>
          ))}
          {drafts.inspected && (
            <label>
              Preserved source (read only; copy text to compare)
              <textarea
                readOnly
                value={drafts.inspected.source}
                aria-label="Preserved draft source"
              />
            </label>
          )}
        </details>
      )}
      <div className="native-workflow-panel__editor">
        <WorkflowRecoveryConcept
          key={drafts.generation}
          initialDraft={drafts.restored}
          onDraftChange={draftClient ? drafts.change : undefined}
          workflowSource={document.source}
          workflowLayout={document.layout ?? undefined}
          workflowFilePath={document.path}
          definitionRevision={document.definition_revision}
          storageDigest={document.storage_digest}
          workspaceId={document.workspace_id}
          navigation={navigation}
          readOnlyRun={readOnlyRun}
          reopenRequest={reopen}
          simulationPreview={false}
          onUnsavedChange={(dirty) => {
            setUnsaved(dirty);
            onDirty?.(dirty);
          }}
          onSave={async (source, layout) => {
            const saved = await client.save(source, layout);
            drafts.accepted(saved);
            onAccepted?.(saved);
            return saved;
          }}
          onReadStoredSource={() => client.read()}
          onReloadStoredSource={async (canReplace) => {
            const observed = await client.read();
            if (canReplace && !canReplace(observed)) return;
            client.accept(observed);
            drafts.accepted(observed);
            setDocument(observed);
            onAccepted?.(observed);
            setReopen((value) => value + 1);
          }}
        />
      </div>
    </main>
  );
}
