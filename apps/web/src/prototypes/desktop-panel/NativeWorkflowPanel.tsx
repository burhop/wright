import { useState } from "react";
import WorkflowRecoveryConcept from "../workflow-recovery/WorkflowRecoveryConcept";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { NativeSourceClient } from "./native-source-client";
import "../../styles/presentation-controls.css";
import "./native-panel.css";

/** Shared editor inside one real host work surface, without another chat or executor. */
export function NativeWorkflowPanel({
  initial,
  client,
  workspaceName,
  onDirty,
  onAccepted,
  onOpenWorkingView,
}: {
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly client: NativeSourceClient;
  readonly workspaceName: string;
  readonly onAccepted?: (document: WorkspaceWorkflowSourceDocument) => void;
  readonly onOpenWorkingView?: () => void;
  readonly onDirty?: (dirty: boolean) => void;
}) {
  const [document, setDocument] = useState(initial);
  const [unsaved, setUnsaved] = useState(false);
  const [reopen, setReopen] = useState(0);
  return (
    <main
      className="native-workflow-panel"
      data-control-style="neutral"
      data-presentation="native-panel"
      data-working-view={!!onOpenWorkingView}
    >
      <header className="native-workflow-panel__context">
        <b>{workspaceName}</b>
        <span>
          {unsaved ? "Unsaved changes — save before closing." : "Workflow"}
        </span>
        {onOpenWorkingView && (
          <button type="button" disabled={unsaved} onClick={onOpenWorkingView}>
            Run and results
          </button>
        )}
        <small>
          {onOpenWorkingView
            ? "Save your workflow, then open Run and results. AI tasks use this conversation."
            : "Use this desktop conversation for reasoning. Run controls are not connected in this editor prototype."}
        </small>
      </header>
      <div className="native-workflow-panel__editor">
        <WorkflowRecoveryConcept
          workflowSource={document.source}
          workflowLayout={document.layout ?? undefined}
          workflowFilePath={document.path}
          definitionRevision={document.definition_revision}
          storageDigest={document.storage_digest}
          reopenRequest={reopen}
          simulationPreview={false}
          onUnsavedChange={(dirty) => {
            setUnsaved(dirty);
            onDirty?.(dirty);
          }}
          onSave={async (source, layout) => {
            const saved = await client.save(source, layout);
            onAccepted?.(saved);
            return saved;
          }}
          onReadStoredSource={() => client.read()}
          onReloadStoredSource={async (canReplace) => {
            const observed = await client.read();
            if (canReplace && !canReplace(observed)) return;
            client.accept(observed);
            setDocument(observed);
            onAccepted?.(observed);
            setReopen((value) => value + 1);
          }}
        />
      </div>
    </main>
  );
}
